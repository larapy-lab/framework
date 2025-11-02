"""
Query Logger with Timing

Logs database queries with execution time, detects slow queries,
and provides query performance insights.
"""

import time
import logging
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading


logger = logging.getLogger(__name__)


@dataclass
class QueryLog:
    """
    Represents a logged query with timing and context.
    
    Attributes:
        query: The SQL query string
        bindings: Query parameter bindings
        time: Execution time in milliseconds
        connection: Database connection name
        timestamp: When the query was executed
        stack_trace: Optional stack trace for debugging
    """
    query: str
    bindings: Optional[Dict[str, Any]] = None
    time: float = 0.0  # milliseconds
    connection: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[List[str]] = None
    
    def is_slow(self, threshold: float = 1000.0) -> bool:
        """Check if query is slow based on threshold"""
        return self.time >= threshold
    
    def __str__(self) -> str:
        """Format query log as string"""
        parts = [
            f"[{self.timestamp.strftime('%H:%M:%S')}]",
            f"({self.time:.2f}ms)"
        ]
        
        if self.connection:
            parts.append(f"[{self.connection}]")
        
        # Truncate long queries
        query_display = self.query[:200] + "..." if len(self.query) > 200 else self.query
        parts.append(query_display)
        
        if self.bindings:
            # Sanitize sensitive data
            safe_bindings = {
                k: '***' if 'password' in k.lower() else v 
                for k, v in self.bindings.items()
            }
            parts.append(f"| Bindings: {safe_bindings}")
        
        return " ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'bindings': self.bindings,
            'time': self.time,
            'connection': self.connection,
            'timestamp': self.timestamp.isoformat(),
            'is_slow': self.is_slow(),
        }


class QueryLogger:
    """
    Query logger with timing and slow query detection.
    
    Features:
    - Automatic query timing
    - Slow query detection
    - Query history tracking
    - Statistics aggregation
    - Thread-safe operations
    
    Example:
        ```python
        logger = QueryLogger(slow_query_threshold=500)
        
        # Log a query
        with logger.log_query("SELECT * FROM users WHERE id = ?", {"id": 1}) as log:
            # Execute query
            result = execute_query(...)
        
        # Get statistics
        stats = logger.get_stats()
        print(f"Total queries: {stats['total_queries']}")
        print(f"Slow queries: {stats['slow_queries']}")
        ```
    """
    
    def __init__(
        self,
        enabled: bool = True,
        slow_query_threshold: float = 1000.0,  # milliseconds
        max_history: int = 1000,
        log_slow_queries: bool = True,
        log_all_queries: bool = False
    ):
        """
        Initialize query logger.
        
        Args:
            enabled: Whether logging is enabled
            slow_query_threshold: Threshold in milliseconds for slow queries
            max_history: Maximum number of queries to keep in history
            log_slow_queries: Whether to log slow queries to logger
            log_all_queries: Whether to log all queries to logger
        """
        self.enabled = enabled
        self.slow_query_threshold = slow_query_threshold
        self.max_history = max_history
        self.log_slow_queries = log_slow_queries
        self.log_all_queries = log_all_queries
        
        self._queries: List[QueryLog] = []
        self._lock = threading.Lock()
        self._listeners: List[Callable[[QueryLog], None]] = []
        
        # Statistics
        self._total_time: float = 0.0
        self._query_count: int = 0
        self._slow_query_count: int = 0
    
    def log_query(
        self,
        query: str,
        bindings: Optional[Dict[str, Any]] = None,
        connection: Optional[str] = None
    ) -> 'QueryLogContext':
        """
        Context manager for logging a query with automatic timing.
        
        Args:
            query: SQL query string
            bindings: Query parameter bindings
            connection: Database connection name
            
        Returns:
            QueryLogContext: Context manager for timing
            
        Example:
            ```python
            with logger.log_query("SELECT * FROM users") as log:
                result = execute_query(...)
            # Query is automatically timed and logged
            ```
        """
        return QueryLogContext(self, query, bindings, connection)
    
    def add_query(self, query_log: QueryLog):
        """
        Add a query to the log.
        
        Args:
            query_log: The query log to add
        """
        if not self.enabled:
            return
        
        with self._lock:
            # Add to history
            self._queries.append(query_log)
            
            # Trim history if needed
            if len(self._queries) > self.max_history:
                self._queries = self._queries[-self.max_history:]
            
            # Update statistics
            self._total_time += query_log.time
            self._query_count += 1
            if query_log.is_slow(self.slow_query_threshold):
                self._slow_query_count += 1
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    listener(query_log)
                except Exception as e:
                    logger.error(f"Error in query logger listener: {e}")
        
        # Log to standard logger if configured
        if self.log_all_queries or (self.log_slow_queries and query_log.is_slow(self.slow_query_threshold)):
            if query_log.is_slow(self.slow_query_threshold):
                logger.warning(f"SLOW QUERY: {query_log}")
            else:
                logger.debug(f"QUERY: {query_log}")
    
    def get_queries(self, limit: Optional[int] = None) -> List[QueryLog]:
        """
        Get query history.
        
        Args:
            limit: Optional limit on number of queries to return
            
        Returns:
            List of query logs
        """
        with self._lock:
            if limit:
                return self._queries[-limit:]
            return self._queries.copy()
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryLog]:
        """
        Get slow queries.
        
        Args:
            threshold: Optional custom threshold (uses default if not specified)
            
        Returns:
            List of slow query logs
        """
        threshold = threshold or self.slow_query_threshold
        with self._lock:
            return [q for q in self._queries if q.is_slow(threshold)]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get query statistics.
        
        Returns:
            Dictionary with statistics including:
            - total_queries: Total number of queries
            - slow_queries: Number of slow queries
            - total_time: Total execution time (ms)
            - average_time: Average execution time (ms)
            - slowest_query: The slowest query
        """
        with self._lock:
            stats = {
                'total_queries': self._query_count,
                'slow_queries': self._slow_query_count,
                'total_time': self._total_time,
                'average_time': self._total_time / self._query_count if self._query_count > 0 else 0,
                'slow_query_threshold': self.slow_query_threshold,
            }
            
            if self._queries:
                slowest = max(self._queries, key=lambda q: q.time)
                stats['slowest_query'] = {
                    'query': slowest.query[:100] + "..." if len(slowest.query) > 100 else slowest.query,
                    'time': slowest.time,
                    'timestamp': slowest.timestamp.isoformat(),
                }
            
            return stats
    
    def add_listener(self, callback: Callable[[QueryLog], None]):
        """
        Add a listener that will be called for each query.
        
        Args:
            callback: Function that takes a QueryLog as argument
            
        Example:
            ```python
            def on_query(log: QueryLog):
                if log.is_slow():
                    send_alert(f"Slow query: {log.query}")
            
            logger.add_listener(on_query)
            ```
        """
        with self._lock:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[QueryLog], None]):
        """Remove a listener"""
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
    
    def clear(self):
        """Clear query history and reset statistics"""
        with self._lock:
            self._queries.clear()
            self._total_time = 0.0
            self._query_count = 0
            self._slow_query_count = 0
    
    def enable(self):
        """Enable query logging"""
        self.enabled = True
    
    def disable(self):
        """Disable query logging"""
        self.enabled = False
    
    def reset_stats(self):
        """Reset statistics without clearing history"""
        with self._lock:
            self._total_time = sum(q.time for q in self._queries)
            self._query_count = len(self._queries)
            self._slow_query_count = sum(1 for q in self._queries if q.is_slow(self.slow_query_threshold))


class QueryLogContext:
    """
    Context manager for automatic query timing.
    
    Usage:
        ```python
        with logger.log_query("SELECT * FROM users") as log:
            result = execute_query(...)
        # Query timing is automatically recorded
        ```
    """
    
    def __init__(
        self,
        logger: QueryLogger,
        query: str,
        bindings: Optional[Dict[str, Any]] = None,
        connection: Optional[str] = None
    ):
        self.logger = logger
        self.query_log = QueryLog(
            query=query,
            bindings=bindings,
            connection=connection
        )
        self.start_time: Optional[float] = None
    
    def __enter__(self) -> QueryLog:
        """Start timing"""
        self.start_time = time.time()
        return self.query_log
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log query"""
        if self.start_time:
            elapsed = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.query_log.time = elapsed
            self.logger.add_query(self.query_log)
        return False


# Global query logger instance
_global_logger: Optional[QueryLogger] = None
_logger_lock = threading.Lock()


def get_query_logger() -> QueryLogger:
    """
    Get the global query logger instance.
    
    Returns:
        Global QueryLogger instance
    """
    global _global_logger
    with _logger_lock:
        if _global_logger is None:
            _global_logger = QueryLogger()
        return _global_logger


def set_query_logger(query_logger: QueryLogger):
    """
    Set the global query logger instance.
    
    Args:
        query_logger: QueryLogger instance to use globally
    """
    global _global_logger
    with _logger_lock:
        _global_logger = query_logger


def reset_query_logger():
    """Reset the global query logger"""
    global _global_logger
    with _logger_lock:
        _global_logger = None
