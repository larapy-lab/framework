"""
SQL Query Analyzer

Analyzes SQL queries for potential optimization opportunities
and anti-patterns.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re


class IssueSeverity(Enum):
    """Severity levels for query issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class QueryIssue:
    """
    Represents an issue found in a query.
    
    Attributes:
        severity: Issue severity level
        type: Type of issue
        message: Human-readable message
        suggestion: Suggested fix
        query: The problematic query
    """
    severity: IssueSeverity
    type: str
    message: str
    suggestion: str
    query: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'severity': self.severity.value,
            'type': self.type,
            'message': self.message,
            'suggestion': self.suggestion,
            'query': self.query[:100] + "..." if len(self.query) > 100 else self.query,
        }


class SQLQueryAnalyzer:
    """
    Analyzes SQL queries for optimization opportunities.
    
    Features:
    - Detect SELECT * usage
    - Identify missing WHERE clauses
    - Find N+1 query patterns
    - Detect missing indexes
    - Analyze query complexity
    - Check for common anti-patterns
    
    Example:
        ```python
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT * FROM users")
        for issue in issues:
            print(f"{issue.severity.value}: {issue.message}")
        ```
    """
    
    def __init__(self, strict: bool = False):
        """
        Initialize SQL query analyzer.
        
        Args:
            strict: Whether to report all issues (True) or only important ones (False)
        """
        self.strict = strict
        self._n1_detector = N1QueryDetector()
    
    def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[QueryIssue]:
        """
        Analyze a query for issues.
        
        Args:
            query: SQL query to analyze
            context: Optional context (previous queries, table info, etc.)
            
        Returns:
            List of issues found
        """
        issues = []
        query_lower = query.lower().strip()
        
        # Always check dangerous UPDATE/DELETE, even in non-strict mode
        # But skip INSERT and other non-SELECT queries in non-strict mode
        is_dangerous_query = query_lower.startswith('update') or query_lower.startswith('delete')
        if not self.strict and not query_lower.startswith('select') and not is_dangerous_query:
            return issues
        
        # Check for SELECT *
        issues.extend(self._check_select_star(query, query_lower))
        
        # Check for missing WHERE clause
        issues.extend(self._check_missing_where(query, query_lower))
        
        # Check for inefficient LIKE patterns
        issues.extend(self._check_like_patterns(query, query_lower))
        
        # Check for OR in WHERE clause
        issues.extend(self._check_or_usage(query, query_lower))
        
        # Check for functions in WHERE clause
        issues.extend(self._check_functions_in_where(query, query_lower))
        
        # Check for missing LIMIT on potentially large results
        issues.extend(self._check_missing_limit(query, query_lower))
        
        # Check for subquery issues
        issues.extend(self._check_subquery_issues(query, query_lower))
        
        # Check for JOIN without indexes (if context provided)
        if context and 'joins' in context:
            issues.extend(self._check_join_optimization(query, query_lower, context))
        
        return issues
    
    def analyze_batch(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyze a batch of queries for patterns.
        
        Args:
            queries: List of SQL queries
            
        Returns:
            Dictionary with:
            - issues: All issues found
            - n1_patterns: Detected N+1 query patterns
            - summary: Statistics summary
        """
        all_issues = []
        
        for query in queries:
            issues = self.analyze(query)
            all_issues.extend(issues)
        
        # Detect N+1 patterns
        n1_patterns = self._n1_detector.detect(queries)
        
        # Generate summary
        summary = self._generate_summary(all_issues, n1_patterns)
        
        return {
            'issues': [issue.to_dict() for issue in all_issues],
            'n1_patterns': n1_patterns,
            'summary': summary,
        }
    
    def _check_select_star(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for SELECT * usage"""
        issues = []
        
        # Match SELECT * (not SELECT *_column or SELECT COUNT(*))
        if re.search(r'\bselect\s+\*\s+from\b', query_lower):
            issues.append(QueryIssue(
                severity=IssueSeverity.WARNING,
                type='select_star',
                message='SELECT * retrieves all columns, which can be inefficient',
                suggestion='Specify only the columns you need: SELECT id, name, email FROM ...',
                query=query
            ))
        
        return issues
    
    def _check_missing_where(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for missing WHERE clause on SELECT, UPDATE, DELETE"""
        issues = []
        
        # Check SELECT without WHERE or LIMIT
        if query_lower.startswith('select'):
            if 'where' not in query_lower and 'limit' not in query_lower and 'join' not in query_lower:
                issues.append(QueryIssue(
                    severity=IssueSeverity.WARNING,
                    type='missing_where',
                    message='Query without WHERE clause may retrieve all rows',
                    suggestion='Add a WHERE clause to filter results or LIMIT to restrict result set',
                    query=query
                ))
        
        # Check UPDATE without WHERE (dangerous!)
        elif query_lower.startswith('update') and 'where' not in query_lower:
            issues.append(QueryIssue(
                severity=IssueSeverity.ERROR,
                type='dangerous_update',
                message='UPDATE without WHERE clause will modify ALL rows!',
                suggestion='Add a WHERE clause to specify which rows to update',
                query=query
            ))
        
        # Check DELETE without WHERE (dangerous!)
        elif query_lower.startswith('delete') and 'where' not in query_lower:
            issues.append(QueryIssue(
                severity=IssueSeverity.ERROR,
                type='dangerous_delete',
                message='DELETE without WHERE clause will delete ALL rows!',
                suggestion='Add a WHERE clause to specify which rows to delete',
                query=query
            ))
        
        return issues
    
    def _check_like_patterns(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for inefficient LIKE patterns"""
        issues = []
        
        # Leading wildcard: LIKE '%value'
        if re.search(r"like\s+['\"]%", query_lower):
            issues.append(QueryIssue(
                severity=IssueSeverity.WARNING,
                type='leading_wildcard',
                message='LIKE with leading wildcard cannot use indexes',
                suggestion='If possible, move wildcard to end: LIKE "value%" or use full-text search',
                query=query
            ))
        
        return issues
    
    def _check_or_usage(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for OR in WHERE clause"""
        issues = []
        
        if 'where' in query_lower and ' or ' in query_lower:
            # Only warn if OR is in WHERE (not in CASE or other contexts)
            where_clause = query_lower.split('where', 1)[1].split('group by')[0].split('order by')[0]
            if ' or ' in where_clause:
                issues.append(QueryIssue(
                    severity=IssueSeverity.INFO,
                    type='or_in_where',
                    message='OR in WHERE clause may prevent index usage',
                    suggestion='Consider using UNION or IN clause if possible for better performance',
                    query=query
                ))
        
        return issues
    
    def _check_functions_in_where(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for functions applied to columns in WHERE clause"""
        issues = []
        
        # Common functions that prevent index usage
        function_patterns = [
            r'\bwhere\s+.*\bupper\(',
            r'\bwhere\s+.*\blower\(',
            r'\bwhere\s+.*\bsubstring\(',
            r'\bwhere\s+.*\bdate\(',
            r'\bwhere\s+.*\byear\(',
        ]
        
        for pattern in function_patterns:
            if re.search(pattern, query_lower):
                issues.append(QueryIssue(
                    severity=IssueSeverity.WARNING,
                    type='function_in_where',
                    message='Functions on columns in WHERE clause prevent index usage',
                    suggestion='Store pre-computed values or use generated columns if needed frequently',
                    query=query
                ))
                break  # Only report once
        
        return issues
    
    def _check_missing_limit(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for missing LIMIT on potentially large results"""
        issues = []
        
        if self.strict and query_lower.startswith('select'):
            if 'limit' not in query_lower and 'where' not in query_lower:
                issues.append(QueryIssue(
                    severity=IssueSeverity.INFO,
                    type='missing_limit',
                    message='Query without LIMIT may return large result set',
                    suggestion='Add LIMIT clause for pagination or to prevent memory issues',
                    query=query
                ))
        
        return issues
    
    def _check_subquery_issues(self, query: str, query_lower: str) -> List[QueryIssue]:
        """Check for subquery optimization opportunities"""
        issues = []
        
        # Subquery in SELECT list
        if re.search(r'select[^()]*\([^()]*select', query_lower):
            issues.append(QueryIssue(
                severity=IssueSeverity.INFO,
                type='subquery_in_select',
                message='Subquery in SELECT list may execute once per row',
                suggestion='Consider using JOIN instead of subquery for better performance',
                query=query
            ))
        
        return issues
    
    def _check_join_optimization(
        self,
        query: str,
        query_lower: str,
        context: Dict[str, Any]
    ) -> List[QueryIssue]:
        """Check JOIN optimization (requires context)"""
        issues = []
        
        # This would require table metadata to be fully effective
        # For now, just check basic patterns
        if 'join' in query_lower:
            if not re.search(r'on\s+\w+\.\w+\s*=\s*\w+\.\w+', query_lower):
                issues.append(QueryIssue(
                    severity=IssueSeverity.WARNING,
                    type='join_without_condition',
                    message='JOIN without proper ON condition may cause Cartesian product',
                    suggestion='Ensure all JOINs have proper ON conditions',
                    query=query
                ))
        
        return issues
    
    def _generate_summary(
        self,
        issues: List[QueryIssue],
        n1_patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate analysis summary"""
        severity_counts = {
            'error': sum(1 for issue in issues if issue.severity == IssueSeverity.ERROR),
            'warning': sum(1 for issue in issues if issue.severity == IssueSeverity.WARNING),
            'info': sum(1 for issue in issues if issue.severity == IssueSeverity.INFO),
        }
        
        issue_types = {}
        for issue in issues:
            issue_types[issue.type] = issue_types.get(issue.type, 0) + 1
        
        return {
            'total_issues': len(issues),
            'by_severity': severity_counts,
            'by_type': issue_types,
            'n1_patterns_found': len(n1_patterns),
            'has_critical_issues': severity_counts['error'] > 0,
        }


class N1QueryDetector:
    """
    Detects N+1 query patterns in a sequence of queries.
    
    N+1 pattern: One query followed by N similar queries
    Example:
        SELECT * FROM posts
        SELECT * FROM users WHERE id = 1
        SELECT * FROM users WHERE id = 2
        SELECT * FROM users WHERE id = 3
        ...
    """
    
    def detect(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Detect N+1 query patterns.
        
        Args:
            queries: List of SQL queries in execution order
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Group queries by normalized pattern
        query_groups = self._group_similar_queries(queries)
        
        # Find groups with many repetitions
        for pattern, query_list in query_groups.items():
            if len(query_list) >= 3:  # At least 3 similar queries
                patterns.append({
                    'pattern': pattern,
                    'count': len(query_list),
                    'queries': query_list[:3],  # Show first 3 examples
                    'message': f'Found {len(query_list)} similar queries - possible N+1 pattern',
                    'suggestion': 'Consider using eager loading or a single query with IN clause',
                })
        
        return patterns
    
    def _group_similar_queries(self, queries: List[str]) -> Dict[str, List[str]]:
        """Group queries by normalized pattern"""
        groups = {}
        
        for query in queries:
            pattern = self._normalize_query(query)
            if pattern not in groups:
                groups[pattern] = []
            groups[pattern].append(query)
        
        return groups
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for pattern matching.
        
        Replaces specific values with placeholders:
        - Numbers: ? 
        - Strings: ?
        - Lists: (?)
        """
        # Remove extra whitespace
        normalized = ' '.join(query.split())
        
        # Replace string literals
        normalized = re.sub(r"'[^']*'", '?', normalized)
        normalized = re.sub(r'"[^"]*"', '?', normalized)
        
        # Replace numbers
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        # Replace IN (...) lists
        normalized = re.sub(r'in\s*\([^)]+\)', 'in (?)', normalized, flags=re.IGNORECASE)
        
        return normalized.lower()


def analyze_query(query: str, strict: bool = False) -> List[QueryIssue]:
    """
    Convenience function to analyze a single query.
    
    Args:
        query: SQL query to analyze
        strict: Whether to use strict analysis
        
    Returns:
        List of issues found
    """
    analyzer = SQLQueryAnalyzer(strict=strict)
    return analyzer.analyze(query)


def analyze_queries(queries: List[str], strict: bool = False) -> Dict[str, Any]:
    """
    Convenience function to analyze multiple queries.
    
    Args:
        queries: List of SQL queries to analyze
        strict: Whether to use strict analysis
        
    Returns:
        Analysis results with issues and patterns
    """
    analyzer = SQLQueryAnalyzer(strict=strict)
    return analyzer.analyze_batch(queries)
