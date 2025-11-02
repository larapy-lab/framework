"""
Tests for Connection Pool Implementation
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock
from larapy.database.connection_pool import (
    ConnectionPool,
    PooledConnection,
    set_global_pool,
    get_global_pool,
    close_global_pool
)


class MockConnection:
    """Mock database connection for testing"""
    
    def __init__(self):
        self.closed = False
        
    def execute(self, query):
        if self.closed:
            raise RuntimeError("Connection is closed")
        return f"Result: {query}"
    
    def close(self):
        self.closed = True


def create_mock_connection():
    """Factory for creating mock connections"""
    return MockConnection()


class TestPooledConnection:
    """Test PooledConnection wrapper"""
    
    def test_creation(self):
        """Test creating a pooled connection"""
        conn = MockConnection()
        pool = Mock()
        pooled = PooledConnection(conn, pool)
        
        assert pooled.connection == conn
        assert pooled.pool == pool
        assert not pooled.in_use
        assert pooled.created_at <= time.time()
        assert pooled.last_used_at <= time.time()
    
    def test_mark_in_use(self):
        """Test marking connection as in use"""
        pooled = PooledConnection(MockConnection(), Mock())
        initial_time = pooled.last_used_at
        
        time.sleep(0.01)
        pooled.mark_in_use()
        
        assert pooled.in_use
        assert pooled.last_used_at > initial_time
    
    def test_mark_returned(self):
        """Test marking connection as returned"""
        pooled = PooledConnection(MockConnection(), Mock())
        pooled.mark_in_use()
        
        time.sleep(0.01)
        pooled.mark_returned()
        
        assert not pooled.in_use
    
    def test_is_expired(self):
        """Test expiration check"""
        pooled = PooledConnection(MockConnection(), Mock())
        
        # Not expired yet
        assert not pooled.is_expired(max_idle_time=10)
        
        # Simulate old connection
        pooled.last_used_at = time.time() - 20
        assert pooled.is_expired(max_idle_time=10)
        
        # In-use connections don't expire
        pooled.mark_in_use()
        assert not pooled.is_expired(max_idle_time=10)
    
    def test_close(self):
        """Test closing connection"""
        conn = MockConnection()
        pooled = PooledConnection(conn, Mock())
        
        pooled.close()
        assert conn.closed


class TestConnectionPool:
    """Test ConnectionPool class"""
    
    def test_initialization(self):
        """Test pool initialization"""
        pool = ConnectionPool(
            connection_factory=create_mock_connection,
            min_size=2,
            max_size=5,
            enable_cleanup=False  # Disable for faster testing
        )
        
        assert pool.min_size == 2
        assert pool.max_size == 5
        assert pool.size() == 2  # Initial connections created
        
        pool.close()
    
    def test_invalid_parameters(self):
        """Test validation of pool parameters"""
        with pytest.raises(ValueError, match="min_size must be >= 0"):
            ConnectionPool(create_mock_connection, min_size=-1)
        
        with pytest.raises(ValueError, match="max_size must be >= min_size"):
            ConnectionPool(create_mock_connection, min_size=5, max_size=3)
        
        with pytest.raises(ValueError, match="max_idle_time must be >= 0"):
            ConnectionPool(create_mock_connection, max_idle_time=-1)
        
        with pytest.raises(ValueError, match="timeout must be > 0"):
            ConnectionPool(create_mock_connection, timeout=0)
    
    def test_get_connection(self):
        """Test getting a connection from the pool"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        conn = pool.get_connection()
        assert isinstance(conn, PooledConnection)
        assert conn.in_use
        assert pool.in_use() == 1
        
        pool.return_connection(conn)
        pool.close()
    
    def test_return_connection(self):
        """Test returning a connection to the pool"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        conn = pool.get_connection()
        assert pool.in_use() == 1
        
        pool.return_connection(conn)
        assert pool.in_use() == 0
        assert not conn.in_use
        
        pool.close()
    
    def test_connection_context_manager(self):
        """Test using connection as context manager"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        with pool.connection() as conn:
            assert isinstance(conn, MockConnection)
            result = conn.execute("SELECT * FROM users")
            assert result == "Result: SELECT * FROM users"
        
        # Connection should be returned to pool
        assert pool.in_use() == 0
        
        pool.close()
    
    def test_pool_expansion(self):
        """Test pool expanding up to max_size"""
        pool = ConnectionPool(create_mock_connection, min_size=1, max_size=3, timeout=2.0, enable_cleanup=False)
        
        assert pool.size() == 1
        
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        conn3 = pool.get_connection()
        
        assert pool.size() == 3
        assert pool.in_use() == 3
        
        pool.return_connection(conn1)
        pool.return_connection(conn2)
        pool.return_connection(conn3)
        pool.close()
    
    def test_max_size_limit(self):
        """Test that pool respects max_size"""
        pool = ConnectionPool(
            create_mock_connection,
            min_size=1,
            max_size=2,
            timeout=0.5,
            enable_cleanup=False
        )
        
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        
        # Pool is at max capacity
        assert pool.size() == 2
        
        # Trying to get another should timeout
        with pytest.raises(TimeoutError):
            pool.get_connection(timeout=0.3)
        
        pool.return_connection(conn1)
        pool.return_connection(conn2)
        pool.close()
    
    def test_concurrent_access(self):
        """Test thread-safe concurrent access"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=10, timeout=2.0, enable_cleanup=False)
        results = []
        errors = []
        
        def worker():
            try:
                with pool.connection() as conn:
                    result = conn.execute("SELECT 1")
                    results.append(result)
                    time.sleep(0.005)  # Reduced sleep time
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 20
        assert len(errors) == 0
        assert pool.in_use() == 0  # All returned
        
        pool.close()
    
    def test_expired_connection_handling(self):
        """Test that expired connections are discarded"""
        pool = ConnectionPool(
            create_mock_connection,
            min_size=2,
            max_size=5,
            max_idle_time=1,  # Very short for testing
            timeout=2.0,
            enable_cleanup=False
        )
        
        conn = pool.get_connection()
        pool.return_connection(conn)
        
        # Wait for connection to expire
        time.sleep(1.2)
        
        # Getting a new connection should discard the expired one
        new_conn = pool.get_connection()
        assert new_conn != conn
        
        pool.return_connection(new_conn)
        pool.close()
    
    def test_stats(self):
        """Test pool statistics"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        stats = pool.stats()
        assert stats['total'] == 2
        assert stats['available'] == 2
        assert stats['in_use'] == 0
        assert stats['min_size'] == 2
        assert stats['max_size'] == 5
        
        conn = pool.get_connection()
        stats = pool.stats()
        assert stats['in_use'] == 1
        assert stats['available'] == 1
        
        pool.return_connection(conn)
        pool.close()
    
    def test_close_pool(self):
        """Test closing the pool"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        conn = pool.get_connection()
        pool.close()
        
        # Pool should be closed
        with pytest.raises(RuntimeError, match="Connection pool is closed"):
            pool.get_connection()
        
        # Size should be 0
        assert pool.size() == 0
    
    def test_pool_as_context_manager(self):
        """Test using pool as context manager"""
        with ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False) as pool:
            with pool.connection() as conn:
                result = conn.execute("SELECT 1")
                assert result == "Result: SELECT 1"
        
        # Pool should be closed after context
        with pytest.raises(RuntimeError):
            pool.get_connection()
    
    def test_connection_reuse(self):
        """Test that connections are properly reused"""
        pool = ConnectionPool(create_mock_connection, min_size=1, max_size=3, enable_cleanup=False)
        
        # Get and return a connection
        conn1 = pool.get_connection()
        original_conn = conn1.connection
        pool.return_connection(conn1)
        
        # Get another connection - should reuse the same one
        conn2 = pool.get_connection()
        assert conn2.connection == original_conn
        
        pool.return_connection(conn2)
        pool.close()


class TestGlobalPool:
    """Test global pool functions"""
    
    def test_set_and_get_global_pool(self):
        """Test setting and getting global pool"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        
        set_global_pool(pool)
        global_pool = get_global_pool()
        
        assert global_pool == pool
        
        close_global_pool()
        assert get_global_pool() is None
    
    def test_close_global_pool(self):
        """Test closing global pool"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=5, enable_cleanup=False)
        set_global_pool(pool)
        
        close_global_pool()
        
        # Pool should be closed
        with pytest.raises(RuntimeError):
            pool.get_connection()
        
        # Global pool should be None
        assert get_global_pool() is None


class TestConnectionPoolPerformance:
    """Test connection pool performance characteristics"""
    
    def test_connection_acquisition_speed(self):
        """Test that getting connections from pool is fast"""
        pool = ConnectionPool(create_mock_connection, min_size=5, max_size=10, enable_cleanup=False)
        
        start_time = time.time()
        for _ in range(100):
            with pool.connection() as conn:
                conn.execute("SELECT 1")
        elapsed = time.time() - start_time
        
        # Should complete quickly (under 1 second for 100 operations)
        assert elapsed < 1.0
        
        pool.close()
    
    def test_pool_under_load(self):
        """Test pool behavior under concurrent load"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=10, enable_cleanup=False)
        success_count = [0]
        lock = threading.Lock()
        
        def worker():
            for _ in range(10):
                try:
                    with pool.connection() as conn:
                        conn.execute("SELECT 1")
                        with lock:
                            success_count[0] += 1
                except Exception:
                    pass
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        start_time = time.time()
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.time() - start_time
        
        # All operations should succeed
        assert success_count[0] == 100
        
        # Should complete reasonably quickly
        assert elapsed < 5.0
        
        pool.close()
    
    def test_memory_efficiency(self):
        """Test that pool doesn't leak connections"""
        pool = ConnectionPool(create_mock_connection, min_size=2, max_size=10, enable_cleanup=False)
        
        # Use connections multiple times
        for _ in range(50):
            with pool.connection():
                pass
        
        # Pool should not have grown excessively
        assert pool.size() <= 10
        
        # All connections should be available
        assert pool.in_use() == 0
        
        pool.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
