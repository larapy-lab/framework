"""
Tests for SQL Query Analyzer
"""

import pytest
from larapy.database.query_analyzer import (
    IssueSeverity,
    QueryIssue,
    SQLQueryAnalyzer,
    N1QueryDetector,
    analyze_query,
    analyze_queries,
)


class TestQueryIssue:
    """Test QueryIssue dataclass"""
    
    def test_basic_issue(self):
        """Test basic issue creation"""
        issue = QueryIssue(
            severity=IssueSeverity.WARNING,
            type='select_star',
            message='SELECT * is inefficient',
            suggestion='Specify columns',
            query='SELECT * FROM users'
        )
        
        assert issue.severity == IssueSeverity.WARNING
        assert issue.type == 'select_star'
        assert issue.message == 'SELECT * is inefficient'
    
    def test_to_dict(self):
        """Test dictionary conversion"""
        issue = QueryIssue(
            severity=IssueSeverity.ERROR,
            type='dangerous_update',
            message='UPDATE without WHERE',
            suggestion='Add WHERE clause',
            query='UPDATE users SET active = 1'
        )
        
        data = issue.to_dict()
        assert data['severity'] == 'error'
        assert data['type'] == 'dangerous_update'
        assert data['message'] == 'UPDATE without WHERE'
        assert data['suggestion'] == 'Add WHERE clause'
        assert 'UPDATE users' in data['query']
    
    def test_to_dict_truncates_long_query(self):
        """Test that long queries are truncated"""
        long_query = "SELECT * FROM users " + "WHERE id = ? " * 50
        issue = QueryIssue(
            severity=IssueSeverity.INFO,
            type='test',
            message='Test',
            suggestion='Test',
            query=long_query
        )
        
        data = issue.to_dict()
        assert len(data['query']) <= 103  # 100 + "..."


class TestSQLQueryAnalyzer:
    """Test SQLQueryAnalyzer class"""
    
    def test_initialization(self):
        """Test analyzer initialization"""
        analyzer = SQLQueryAnalyzer(strict=True)
        assert analyzer.strict is True
        
        analyzer2 = SQLQueryAnalyzer(strict=False)
        assert analyzer2.strict is False
    
    def test_select_star_detection(self):
        """Test SELECT * detection"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT * FROM users WHERE id = 1")
        assert any(issue.type == 'select_star' for issue in issues)
        assert any(issue.severity == IssueSeverity.WARNING for issue in issues)
    
    def test_select_star_with_count_allowed(self):
        """Test that COUNT(*) doesn't trigger SELECT * warning"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT COUNT(*) FROM users")
        # Should not have select_star issue
        assert not any(issue.type == 'select_star' for issue in issues)
    
    def test_missing_where_on_select(self):
        """Test missing WHERE on SELECT"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT id, name FROM users")
        assert any(issue.type == 'missing_where' for issue in issues)
        assert any(issue.severity == IssueSeverity.WARNING for issue in issues)
    
    def test_select_with_limit_no_warning(self):
        """Test that SELECT with LIMIT doesn't warn about missing WHERE"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT id, name FROM users LIMIT 10")
        assert not any(issue.type == 'missing_where' for issue in issues)
    
    def test_select_with_join_no_warning(self):
        """Test that SELECT with JOIN doesn't warn about missing WHERE"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT u.id FROM users u JOIN posts p ON u.id = p.user_id")
        assert not any(issue.type == 'missing_where' for issue in issues)
    
    def test_dangerous_update_without_where(self):
        """Test UPDATE without WHERE detection"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("UPDATE users SET active = 1")
        assert any(issue.type == 'dangerous_update' for issue in issues)
        assert any(issue.severity == IssueSeverity.ERROR for issue in issues)
    
    def test_dangerous_delete_without_where(self):
        """Test DELETE without WHERE detection"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("DELETE FROM users")
        assert any(issue.type == 'dangerous_delete' for issue in issues)
        assert any(issue.severity == IssueSeverity.ERROR for issue in issues)
    
    def test_update_with_where_allowed(self):
        """Test that UPDATE with WHERE is allowed"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("UPDATE users SET active = 1 WHERE id = 5")
        assert not any(issue.type == 'dangerous_update' for issue in issues)
    
    def test_leading_wildcard_detection(self):
        """Test LIKE with leading wildcard"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT * FROM users WHERE name LIKE '%john'")
        assert any(issue.type == 'leading_wildcard' for issue in issues)
        assert any(issue.severity == IssueSeverity.WARNING for issue in issues)
    
    def test_trailing_wildcard_allowed(self):
        """Test that LIKE with trailing wildcard is allowed"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT * FROM users WHERE name LIKE 'john%'")
        # Should still warn about SELECT *, but not about wildcard
        assert not any(issue.type == 'leading_wildcard' for issue in issues)
    
    def test_or_in_where_detection(self):
        """Test OR in WHERE clause detection"""
        analyzer = SQLQueryAnalyzer()
        
        issues = analyzer.analyze("SELECT * FROM users WHERE age > 18 OR status = 'premium'")
        assert any(issue.type == 'or_in_where' for issue in issues)
        assert any(issue.severity == IssueSeverity.INFO for issue in issues)
    
    def test_function_in_where_detection(self):
        """Test function on column in WHERE clause"""
        analyzer = SQLQueryAnalyzer()
        
        test_cases = [
            "SELECT * FROM users WHERE UPPER(name) = 'JOHN'",
            "SELECT * FROM users WHERE LOWER(email) = 'test@example.com'",
            "SELECT * FROM events WHERE YEAR(created_at) = 2024",
        ]
        
        for query in test_cases:
            issues = analyzer.analyze(query)
            assert any(issue.type == 'function_in_where' for issue in issues), f"Failed for: {query}"
    
    def test_missing_limit_strict_mode(self):
        """Test missing LIMIT detection in strict mode"""
        analyzer = SQLQueryAnalyzer(strict=True)
        
        issues = analyzer.analyze("SELECT id, name FROM users")
        assert any(issue.type == 'missing_limit' for issue in issues)
    
    def test_missing_limit_not_in_normal_mode(self):
        """Test that missing LIMIT is not reported in normal mode"""
        analyzer = SQLQueryAnalyzer(strict=False)
        
        issues = analyzer.analyze("SELECT id, name FROM users WHERE id = 1")
        assert not any(issue.type == 'missing_limit' for issue in issues)
    
    def test_subquery_in_select_detection(self):
        """Test subquery in SELECT list detection"""
        analyzer = SQLQueryAnalyzer()
        
        query = """
            SELECT 
                id,
                name,
                (SELECT COUNT(*) FROM posts WHERE user_id = users.id) as post_count
            FROM users
        """
        
        issues = analyzer.analyze(query)
        assert any(issue.type == 'subquery_in_select' for issue in issues)
    
    def test_non_select_queries_in_normal_mode(self):
        """Test that non-SELECT queries are skipped in normal mode"""
        analyzer = SQLQueryAnalyzer(strict=False)
        
        queries = [
            "INSERT INTO users (name) VALUES ('John')",
            "UPDATE users SET name = 'Jane' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
        ]
        
        for query in queries:
            issues = analyzer.analyze(query)
            # Should have no issues in normal mode
            assert len(issues) == 0
    
    def test_analyze_batch(self):
        """Test batch analysis"""
        analyzer = SQLQueryAnalyzer()
        
        queries = [
            "SELECT * FROM users",
            "SELECT * FROM posts WHERE user_id = 1",
            "SELECT * FROM posts WHERE user_id = 2",
            "SELECT * FROM posts WHERE user_id = 3",
        ]
        
        result = analyzer.analyze_batch(queries)
        
        assert 'issues' in result
        assert 'n1_patterns' in result
        assert 'summary' in result
        
        # Should have SELECT * issues
        assert len(result['issues']) > 0
        
        # Should detect N+1 pattern
        assert len(result['n1_patterns']) > 0
    
    def test_analyze_batch_summary(self):
        """Test batch analysis summary"""
        analyzer = SQLQueryAnalyzer()
        
        queries = [
            "SELECT * FROM users",  # WARNING
            "UPDATE users SET active = 1",  # ERROR
            "SELECT id FROM posts WHERE user_id = 1",  # No issues
        ]
        
        result = analyzer.analyze_batch(queries)
        summary = result['summary']
        
        assert 'total_issues' in summary
        assert 'by_severity' in summary
        assert 'by_type' in summary
        assert summary['by_severity']['error'] > 0
        assert summary['by_severity']['warning'] > 0


class TestN1QueryDetector:
    """Test N1QueryDetector class"""
    
    def test_initialization(self):
        """Test detector initialization"""
        detector = N1QueryDetector()
        assert detector is not None
    
    def test_detect_n1_pattern(self):
        """Test N+1 pattern detection"""
        detector = N1QueryDetector()
        
        queries = [
            "SELECT * FROM posts",
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 2",
            "SELECT * FROM users WHERE id = 3",
            "SELECT * FROM users WHERE id = 4",
        ]
        
        patterns = detector.detect(queries)
        assert len(patterns) > 0
        assert patterns[0]['count'] >= 3
        assert 'N+1' in patterns[0]['message'] or 'similar queries' in patterns[0]['message']
    
    def test_no_false_positives_on_different_queries(self):
        """Test that different queries don't trigger N+1 detection"""
        detector = N1QueryDetector()
        
        queries = [
            "SELECT * FROM users",
            "SELECT * FROM posts",
            "SELECT * FROM comments",
        ]
        
        patterns = detector.detect(queries)
        assert len(patterns) == 0
    
    def test_normalize_query(self):
        """Test query normalization"""
        detector = N1QueryDetector()
        
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM users WHERE id = 2"
        query3 = "SELECT * FROM users WHERE id = 999"
        
        norm1 = detector._normalize_query(query1)
        norm2 = detector._normalize_query(query2)
        norm3 = detector._normalize_query(query3)
        
        # All should normalize to same pattern
        assert norm1 == norm2 == norm3
    
    def test_normalize_handles_strings(self):
        """Test that normalization handles string literals"""
        detector = N1QueryDetector()
        
        query1 = "SELECT * FROM users WHERE name = 'John'"
        query2 = "SELECT * FROM users WHERE name = 'Jane'"
        
        norm1 = detector._normalize_query(query1)
        norm2 = detector._normalize_query(query2)
        
        assert norm1 == norm2
    
    def test_normalize_handles_in_clauses(self):
        """Test that normalization handles IN clauses"""
        detector = N1QueryDetector()
        
        query1 = "SELECT * FROM users WHERE id IN (1, 2, 3)"
        query2 = "SELECT * FROM users WHERE id IN (4, 5, 6, 7)"
        
        norm1 = detector._normalize_query(query1)
        norm2 = detector._normalize_query(query2)
        
        assert norm1 == norm2
    
    def test_group_similar_queries(self):
        """Test grouping similar queries"""
        detector = N1QueryDetector()
        
        queries = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM posts WHERE id = 1",
            "SELECT * FROM users WHERE id = 2",
            "SELECT * FROM posts WHERE id = 2",
            "SELECT * FROM users WHERE id = 3",
        ]
        
        groups = detector._group_similar_queries(queries)
        
        # Should have 2 groups (users and posts)
        assert len(groups) == 2
        
        # One group should have 3 queries (users)
        counts = sorted([len(queries) for queries in groups.values()])
        assert counts == [2, 3]


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_analyze_query(self):
        """Test analyze_query convenience function"""
        issues = analyze_query("SELECT * FROM users")
        assert len(issues) > 0
        assert any(issue.type == 'select_star' for issue in issues)
    
    def test_analyze_query_strict(self):
        """Test analyze_query with strict mode"""
        issues = analyze_query("SELECT id FROM users", strict=True)
        # In strict mode, should warn about missing LIMIT
        assert any(issue.type == 'missing_limit' for issue in issues)
    
    def test_analyze_queries(self):
        """Test analyze_queries convenience function"""
        queries = [
            "SELECT * FROM users",
            "SELECT * FROM posts WHERE user_id = 1",
            "SELECT * FROM posts WHERE user_id = 2",
            "SELECT * FROM posts WHERE user_id = 3",
        ]
        
        result = analyze_queries(queries)
        
        assert 'issues' in result
        assert 'n1_patterns' in result
        assert 'summary' in result


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_multiple_issues_in_single_query(self):
        """Test query with multiple issues"""
        analyzer = SQLQueryAnalyzer()
        
        query = "SELECT * FROM users WHERE UPPER(name) LIKE '%john'"
        
        issues = analyzer.analyze(query)
        
        # Should have multiple issues
        issue_types = [issue.type for issue in issues]
        assert 'select_star' in issue_types
        assert 'function_in_where' in issue_types
        assert 'leading_wildcard' in issue_types
    
    def test_well_optimized_query(self):
        """Test that well-optimized query has no issues"""
        analyzer = SQLQueryAnalyzer()
        
        query = "SELECT id, name, email FROM users WHERE id = 1 LIMIT 1"
        
        issues = analyzer.analyze(query)
        
        # Should have no issues
        assert len(issues) == 0
    
    def test_complex_join_query(self):
        """Test complex JOIN query"""
        analyzer = SQLQueryAnalyzer()
        
        query = """
            SELECT u.id, u.name, COUNT(p.id) as post_count
            FROM users u
            JOIN posts p ON u.id = p.user_id
            WHERE u.active = 1
            GROUP BY u.id, u.name
            LIMIT 10
        """
        
        issues = analyzer.analyze(query)
        
        # Should have no major issues
        assert not any(issue.severity == IssueSeverity.ERROR for issue in issues)
    
    def test_realistic_n1_scenario(self):
        """Test realistic N+1 scenario"""
        analyzer = SQLQueryAnalyzer()
        
        # Simulate typical N+1: fetch posts, then fetch user for each post
        queries = [
            "SELECT * FROM posts LIMIT 10",
        ]
        
        # Add N queries for users
        for i in range(1, 11):
            queries.append(f"SELECT * FROM users WHERE id = {i}")
        
        result = analyzer.analyze_batch(queries)
        
        # Should detect N+1 pattern
        assert len(result['n1_patterns']) > 0
        assert result['summary']['n1_patterns_found'] > 0
