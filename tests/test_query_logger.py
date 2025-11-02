"""
Tests for Query Logger with Timing
"""

import pytest
import time
from datetime import datetime
from larapy.database.query_logger import (
    QueryLog,
    QueryLogger,
    QueryLogContext,
    get_query_logger,
    set_query_logger,
    reset_query_logger,
)


class TestQueryLog:
    """Test QueryLog dataclass"""
    
    def test_basic_query_log(self):
        """Test basic query log creation"""
        log = QueryLog(
            query="SELECT * FROM users",
            bindings={"id": 1},
            time=150.5,
            connection="mysql"
        )
        
        assert log.query == "SELECT * FROM users"
        assert log.bindings == {"id": 1}
        assert log.time == 150.5
        assert log.connection == "mysql"
        assert isinstance(log.timestamp, datetime)
    
    def test_is_slow(self):
        """Test slow query detection"""
        fast_log = QueryLog(query="SELECT 1", time=50.0)
        slow_log = QueryLog(query="SELECT * FROM large_table", time=1500.0)
        
        assert not fast_log.is_slow(1000.0)
        assert slow_log.is_slow(1000.0)
        
        # Custom threshold
        assert fast_log.is_slow(40.0)
        assert not fast_log.is_slow(60.0)
    
    def test_str_representation(self):
        """Test string representation"""
        log = QueryLog(
            query="SELECT * FROM users WHERE id = ?",
            bindings={"id": 1},
            time=123.45,
            connection="mysql"
        )
        
        str_rep = str(log)
        assert "123.45ms" in str_rep
        assert "[mysql]" in str_rep
        assert "SELECT * FROM users" in str_rep
        assert "'id': 1" in str_rep
    
    def test_str_truncates_long_queries(self):
        """Test that long queries are truncated in string representation"""
        long_query = "SELECT * FROM users " + "WHERE id = ? " * 50
        log = QueryLog(query=long_query, time=100.0)
        
        str_rep = str(log)
        assert "..." in str_rep
        assert len(str_rep) < len(long_query) + 100
    
    def test_password_sanitization_in_str(self):
        """Test that passwords are sanitized in string representation"""
        log = QueryLog(
            query="INSERT INTO users",
            bindings={"email": "test@example.com", "password": "secret123"},
            time=50.0
        )
        
        str_rep = str(log)
        assert "secret123" not in str_rep
        assert "***" in str_rep
        assert "test@example.com" in str_rep
    
    def test_to_dict(self):
        """Test dictionary conversion"""
        log = QueryLog(
            query="SELECT * FROM users",
            bindings={"id": 1},
            time=150.5,
            connection="mysql"
        )
        
        data = log.to_dict()
        assert data['query'] == "SELECT * FROM users"
        assert data['bindings'] == {"id": 1}
        assert data['time'] == 150.5
        assert data['connection'] == "mysql"
        assert 'timestamp' in data
        assert data['is_slow'] is False


class TestQueryLogger:
    """Test QueryLogger class"""
    
    def test_initialization(self):
        """Test logger initialization"""
        logger = QueryLogger(
            enabled=True,
            slow_query_threshold=500.0,
            max_history=100,
            log_slow_queries=True,
            log_all_queries=False
        )
        
        assert logger.enabled is True
        assert logger.slow_query_threshold == 500.0
        assert logger.max_history == 100
        assert logger.log_slow_queries is True
        assert logger.log_all_queries is False
    
    def test_log_query_context_manager(self):
        """Test logging a query with context manager"""
        logger = QueryLogger()
        
        with logger.log_query("SELECT * FROM users", {"id": 1}, "mysql") as log:
            time.sleep(0.01)  # Simulate query execution
        
        # Query should be logged
        queries = logger.get_queries()
        assert len(queries) == 1
        assert queries[0].query == "SELECT * FROM users"
        assert queries[0].bindings == {"id": 1}
        assert queries[0].connection == "mysql"
        assert queries[0].time >= 10.0  # At least 10ms
    
    def test_add_query_manually(self):
        """Test manually adding a query"""
        logger = QueryLogger()
        log = QueryLog(query="SELECT 1", time=50.0)
        
        logger.add_query(log)
        
        queries = logger.get_queries()
        assert len(queries) == 1
        assert queries[0].query == "SELECT 1"
    
    def test_disabled_logger(self):
        """Test that disabled logger doesn't log queries"""
        logger = QueryLogger(enabled=False)
        
        with logger.log_query("SELECT * FROM users"):
            pass
        
        queries = logger.get_queries()
        assert len(queries) == 0
    
    def test_max_history_limit(self):
        """Test that history is limited to max_history"""
        logger = QueryLogger(max_history=5)
        
        # Add 10 queries
        for i in range(10):
            log = QueryLog(query=f"SELECT {i}", time=50.0)
            logger.add_query(log)
        
        queries = logger.get_queries()
        assert len(queries) == 5
        # Should keep the last 5
        assert queries[0].query == "SELECT 5"
        assert queries[-1].query == "SELECT 9"
    
    def test_get_queries_with_limit(self):
        """Test getting queries with limit"""
        logger = QueryLogger()
        
        for i in range(10):
            log = QueryLog(query=f"SELECT {i}", time=50.0)
            logger.add_query(log)
        
        queries = logger.get_queries(limit=3)
        assert len(queries) == 3
        assert queries[0].query == "SELECT 7"
        assert queries[-1].query == "SELECT 9"
    
    def test_get_slow_queries(self):
        """Test getting slow queries"""
        logger = QueryLogger(slow_query_threshold=100.0)
        
        # Add mix of fast and slow queries
        logger.add_query(QueryLog(query="FAST 1", time=50.0))
        logger.add_query(QueryLog(query="SLOW 1", time=150.0))
        logger.add_query(QueryLog(query="FAST 2", time=75.0))
        logger.add_query(QueryLog(query="SLOW 2", time=200.0))
        
        slow_queries = logger.get_slow_queries()
        assert len(slow_queries) == 2
        assert all("SLOW" in q.query for q in slow_queries)
    
    def test_get_slow_queries_custom_threshold(self):
        """Test getting slow queries with custom threshold"""
        logger = QueryLogger(slow_query_threshold=100.0)
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        logger.add_query(QueryLog(query="Q2", time=75.0))
        logger.add_query(QueryLog(query="Q3", time=125.0))
        
        # With custom threshold of 60ms
        slow_queries = logger.get_slow_queries(threshold=60.0)
        assert len(slow_queries) == 2
        assert slow_queries[0].query == "Q2"
        assert slow_queries[1].query == "Q3"
    
    def test_get_stats(self):
        """Test statistics calculation"""
        logger = QueryLogger(slow_query_threshold=100.0)
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        logger.add_query(QueryLog(query="Q2", time=150.0))
        logger.add_query(QueryLog(query="Q3", time=200.0))
        
        stats = logger.get_stats()
        assert stats['total_queries'] == 3
        assert stats['slow_queries'] == 2
        assert stats['total_time'] == 400.0
        assert stats['average_time'] == pytest.approx(133.33, rel=0.01)
        assert stats['slow_query_threshold'] == 100.0
        assert 'slowest_query' in stats
        assert stats['slowest_query']['time'] == 200.0
    
    def test_get_stats_empty_logger(self):
        """Test statistics with no queries"""
        logger = QueryLogger()
        
        stats = logger.get_stats()
        assert stats['total_queries'] == 0
        assert stats['slow_queries'] == 0
        assert stats['total_time'] == 0.0
        assert stats['average_time'] == 0.0
        assert 'slowest_query' not in stats
    
    def test_listeners(self):
        """Test query listeners"""
        logger = QueryLogger()
        calls = []
        
        def listener(log: QueryLog):
            calls.append(log.query)
        
        logger.add_listener(listener)
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        logger.add_query(QueryLog(query="Q2", time=100.0))
        
        assert calls == ["Q1", "Q2"]
    
    def test_remove_listener(self):
        """Test removing a listener"""
        logger = QueryLogger()
        calls = []
        
        def listener(log: QueryLog):
            calls.append(log.query)
        
        logger.add_listener(listener)
        logger.add_query(QueryLog(query="Q1", time=50.0))
        
        logger.remove_listener(listener)
        logger.add_query(QueryLog(query="Q2", time=100.0))
        
        assert calls == ["Q1"]  # Q2 not captured
    
    def test_listener_exceptions_dont_break_logging(self):
        """Test that listener exceptions don't break logging"""
        logger = QueryLogger()
        
        def bad_listener(log: QueryLog):
            raise Exception("Listener error")
        
        logger.add_listener(bad_listener)
        
        # Should not raise
        logger.add_query(QueryLog(query="Q1", time=50.0))
        
        queries = logger.get_queries()
        assert len(queries) == 1
    
    def test_clear(self):
        """Test clearing history and stats"""
        logger = QueryLogger()
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        logger.add_query(QueryLog(query="Q2", time=100.0))
        
        logger.clear()
        
        queries = logger.get_queries()
        stats = logger.get_stats()
        
        assert len(queries) == 0
        assert stats['total_queries'] == 0
        assert stats['total_time'] == 0.0
    
    def test_enable_disable(self):
        """Test enabling and disabling logger"""
        logger = QueryLogger(enabled=True)
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        assert len(logger.get_queries()) == 1
        
        logger.disable()
        logger.add_query(QueryLog(query="Q2", time=50.0))
        assert len(logger.get_queries()) == 1  # Q2 not logged
        
        logger.enable()
        logger.add_query(QueryLog(query="Q3", time=50.0))
        assert len(logger.get_queries()) == 2  # Q3 logged
    
    def test_reset_stats(self):
        """Test resetting statistics without clearing history"""
        logger = QueryLogger(slow_query_threshold=100.0)
        
        logger.add_query(QueryLog(query="Q1", time=50.0))
        logger.add_query(QueryLog(query="Q2", time=150.0))
        
        # Manually modify stats (simulate corruption)
        logger._query_count = 999
        logger._total_time = 9999.0
        logger._slow_query_count = 99
        
        logger.reset_stats()
        
        # Stats should be recalculated from history
        stats = logger.get_stats()
        assert stats['total_queries'] == 2
        assert stats['total_time'] == 200.0
        assert stats['slow_queries'] == 1
        
        # History should still be intact
        queries = logger.get_queries()
        assert len(queries) == 2


class TestQueryLogContext:
    """Test QueryLogContext context manager"""
    
    def test_timing_accuracy(self):
        """Test that timing is reasonably accurate"""
        logger = QueryLogger()
        
        with logger.log_query("SELECT * FROM users"):
            time.sleep(0.05)  # 50ms
        
        queries = logger.get_queries()
        assert len(queries) == 1
        # Should be close to 50ms (allow 10ms tolerance)
        assert 40.0 <= queries[0].time <= 70.0
    
    def test_context_manager_with_exception(self):
        """Test that query is still logged even if exception occurs"""
        logger = QueryLogger()
        
        try:
            with logger.log_query("SELECT * FROM users"):
                time.sleep(0.01)
                raise ValueError("Query failed")
        except ValueError:
            pass
        
        # Query should still be logged
        queries = logger.get_queries()
        assert len(queries) == 1
        assert queries[0].time >= 10.0


class TestGlobalLogger:
    """Test global logger functions"""
    
    def test_get_query_logger_creates_instance(self):
        """Test that get_query_logger creates a global instance"""
        reset_query_logger()
        
        logger1 = get_query_logger()
        logger2 = get_query_logger()
        
        assert logger1 is logger2  # Same instance
    
    def test_set_query_logger(self):
        """Test setting custom global logger"""
        reset_query_logger()
        
        custom_logger = QueryLogger(slow_query_threshold=500.0)
        set_query_logger(custom_logger)
        
        logger = get_query_logger()
        assert logger is custom_logger
        assert logger.slow_query_threshold == 500.0
    
    def test_reset_query_logger(self):
        """Test resetting global logger"""
        logger1 = get_query_logger()
        logger1.add_query(QueryLog(query="Q1", time=50.0))
        
        reset_query_logger()
        
        logger2 = get_query_logger()
        assert logger2 is not logger1
        assert len(logger2.get_queries()) == 0


class TestThreadSafety:
    """Test thread safety"""
    
    def test_concurrent_logging(self):
        """Test that concurrent logging is thread-safe"""
        import threading
        
        logger = QueryLogger()
        threads = []
        
        def log_queries():
            for i in range(10):
                with logger.log_query(f"SELECT {i}"):
                    time.sleep(0.001)
        
        # Start 5 threads
        for _ in range(5):
            t = threading.Thread(target=log_queries)
            t.start()
            threads.append(t)
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Should have 50 queries total
        queries = logger.get_queries()
        assert len(queries) == 50
        
        # Stats should be consistent
        stats = logger.get_stats()
        assert stats['total_queries'] == 50
