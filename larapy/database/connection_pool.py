"""
Database Connection Pool Implementation

This module provides a thread-safe connection pool for managing database connections
efficiently. It helps reduce connection overhead and improve application performance.

Example:
    ```python
    from larapy.database.connection_pool import ConnectionPool
    
    # Create a pool
    pool = ConnectionPool(
        connection_factory=lambda: create_connection(),
        min_size=2,
        max_size=10,
        max_idle_time=300
    )
    
    # Get a connection
    with pool.get_connection() as conn:
        # Use the connection
        result = conn.execute("SELECT * FROM users")
    
    # Connection is automatically returned to the pool
    ```
"""

import threading
import time
from queue import Queue, Empty, Full
from typing import Callable, Optional, Any, Generator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class PooledConnection:
    """Wrapper for a pooled database connection"""
    
    def __init__(self, connection: Any, pool: 'ConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.in_use = False
        
    def mark_in_use(self):
        """Mark the connection as being used"""
        self.in_use = True
        self.last_used_at = time.time()
        
    def mark_returned(self):
        """Mark the connection as returned to the pool"""
        self.in_use = False
        self.last_used_at = time.time()
        
    def is_expired(self, max_idle_time: int) -> bool:
        """Check if the connection has been idle too long"""
        if self.in_use:
            return False
        return (time.time() - self.last_used_at) > max_idle_time
    
    def close(self):
        """Close the underlying connection"""
        try:
            if hasattr(self.connection, 'close'):
                self.connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


class ConnectionPool:
    """
    Thread-safe connection pool for database connections.
    
    The pool maintains a minimum number of connections and can grow up to
    a maximum size. Idle connections are automatically cleaned up.
    
    Attributes:
        min_size (int): Minimum number of connections to maintain
        max_size (int): Maximum number of connections allowed
        max_idle_time (int): Maximum idle time before closing a connection (seconds)
        timeout (int): Timeout for acquiring a connection (seconds)
    """
    
    def __init__(
        self,
        connection_factory: Callable[[], Any],
        min_size: int = 2,
        max_size: int = 10,
        max_idle_time: int = 300,
        timeout: float = 30.0,
        enable_cleanup: bool = True
    ):
        """
        Initialize the connection pool.
        
        Args:
            connection_factory: Callable that creates new connections
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed
            max_idle_time: Maximum idle time in seconds before closing a connection
            timeout: Timeout in seconds for acquiring a connection
            enable_cleanup: Whether to enable automatic cleanup of idle connections
        """
        if min_size < 0:
            raise ValueError("min_size must be >= 0")
        if max_size < min_size:
            raise ValueError("max_size must be >= min_size")
        if max_idle_time < 0:
            raise ValueError("max_idle_time must be >= 0")
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
            
        self.connection_factory = connection_factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.timeout = timeout
        
        self._pool: Queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
        self._all_connections: list[PooledConnection] = []
        self._closed = False
        self._cleanup_interval = 60  # Seconds between cleanup runs
        self._enable_cleanup = enable_cleanup
        
        # Create minimum connections
        self._initialize_pool()
        
        # Start cleanup thread
        if self._enable_cleanup:
            self._cleanup_thread = threading.Thread(target=self._cleanup_idle_connections, daemon=True)
            self._cleanup_thread.start()
        
    def _initialize_pool(self):
        """Create initial minimum connections"""
        for i in range(self.min_size):
            try:
                conn = self._create_connection_unsafe()
                self._pool.put(conn, block=False)  # Non-blocking put
                logger.debug(f"Initialized connection {i+1}/{self.min_size}")
            except Exception as e:
                logger.error(f"Error creating initial connection: {e}")
                
    def _create_connection_unsafe(self) -> PooledConnection:
        """
        Create a new pooled connection without acquiring lock.
        MUST be called while holding self._lock.
        """
        if len(self._all_connections) >= self.max_size:
            raise RuntimeError("Connection pool is at maximum capacity")
            
        raw_conn = self.connection_factory()
        pooled_conn = PooledConnection(raw_conn, self)
        self._all_connections.append(pooled_conn)
        
        logger.debug(f"Created new connection. Pool size: {len(self._all_connections)}")
        return pooled_conn
                
    def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection"""
        with self._lock:
            return self._create_connection_unsafe()
    
    def get_connection(self, timeout: Optional[float] = None) -> PooledConnection:
        """
        Get a connection from the pool.
        
        Args:
            timeout: Optional timeout in seconds (uses pool default if not specified)
            
        Returns:
            PooledConnection: A pooled database connection
            
        Raises:
            RuntimeError: If the pool is closed
            TimeoutError: If unable to acquire a connection within the timeout
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
            
        actual_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        
        while True:
            try:
                # Try to get an existing connection
                conn = self._pool.get(timeout=0.1)
                
                # Check if connection is still valid
                if conn.is_expired(self.max_idle_time):
                    logger.debug("Discarding expired connection")
                    self._remove_connection(conn)
                    conn.close()
                    continue
                    
                conn.mark_in_use()
                logger.debug(f"Acquired connection from pool. Available: {self._pool.qsize()}")
                return conn
                
            except Empty:
                # No available connections, try to create a new one
                with self._lock:
                    if len(self._all_connections) < self.max_size:
                        try:
                            conn = self._create_connection_unsafe()
                            conn.mark_in_use()
                            return conn
                        except Exception as e:
                            logger.error(f"Error creating connection: {e}")
                            
                # Check timeout
                if time.time() - start_time > actual_timeout:
                    raise TimeoutError(
                        f"Unable to acquire connection within {actual_timeout} seconds. "
                        f"Pool size: {len(self._all_connections)}/{self.max_size}"
                    )
                    
                # Wait a bit before retrying
                time.sleep(0.1)
    
    def return_connection(self, conn: PooledConnection):
        """
        Return a connection to the pool.
        
        Args:
            conn: The connection to return
        """
        if self._closed:
            conn.close()
            return
            
        conn.mark_returned()
        
        try:
            self._pool.put_nowait(conn)
            logger.debug(f"Returned connection to pool. Available: {self._pool.qsize()}")
        except Full:
            # Pool is full, close the connection
            logger.debug("Pool is full, closing connection")
            self._remove_connection(conn)
            conn.close()
    
    @contextmanager
    def connection(self, timeout: Optional[float] = None) -> Generator[Any, None, None]:
        """
        Context manager for getting a connection.
        
        Args:
            timeout: Optional timeout in seconds
            
        Yields:
            The raw database connection
            
        Example:
            ```python
            with pool.connection() as conn:
                result = conn.execute("SELECT * FROM users")
            ```
        """
        pooled_conn = self.get_connection(timeout=timeout)
        try:
            yield pooled_conn.connection
        finally:
            self.return_connection(pooled_conn)
    
    def _remove_connection(self, conn: PooledConnection):
        """Remove a connection from tracking"""
        with self._lock:
            if conn in self._all_connections:
                self._all_connections.remove(conn)
                logger.debug(f"Removed connection. Pool size: {len(self._all_connections)}")
    
    def _cleanup_idle_connections(self):
        """Background thread that cleans up idle connections"""
        while not self._closed:
            try:
                time.sleep(self._cleanup_interval)
                
                if self._closed:
                    break
                
                with self._lock:
                    if len(self._all_connections) <= self.min_size:
                        continue
                        
                    # Find expired connections
                    expired = []
                    for conn in self._all_connections:
                        if conn.is_expired(self.max_idle_time):
                            expired.append(conn)
                            
                    # Remove expired connections (but keep minimum)
                    to_remove = min(
                        len(expired),
                        len(self._all_connections) - self.min_size
                    )
                    
                    for i in range(to_remove):
                        conn = expired[i]
                        if not conn.in_use:
                            try:
                                # Try to remove from queue
                                temp_queue = Queue(maxsize=self.max_size)
                                while not self._pool.empty():
                                    c = self._pool.get_nowait()
                                    if c != conn:
                                        temp_queue.put_nowait(c)
                                        
                                # Restore queue
                                while not temp_queue.empty():
                                    self._pool.put_nowait(temp_queue.get_nowait())
                                    
                                self._all_connections.remove(conn)
                                conn.close()
                                logger.debug(f"Cleaned up idle connection. Pool size: {len(self._all_connections)}")
                            except Exception as e:
                                logger.error(f"Error cleaning up connection: {e}")
                                
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def close(self):
        """Close all connections and shut down the pool"""
        if self._closed:
            return
            
        self._closed = True
        
        with self._lock:
            # Close all connections
            for conn in self._all_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
                    
            self._all_connections.clear()
            
            # Clear the queue
            while not self._pool.empty():
                try:
                    self._pool.get_nowait()
                except Empty:
                    break
                    
        logger.info("Connection pool closed")
    
    def size(self) -> int:
        """Get the total number of connections in the pool"""
        with self._lock:
            return len(self._all_connections)
    
    def available(self) -> int:
        """Get the number of available connections"""
        return self._pool.qsize()
    
    def in_use(self) -> int:
        """Get the number of connections currently in use"""
        return self.size() - self.available()
    
    def stats(self) -> dict:
        """
        Get pool statistics.
        
        Returns:
            dict: Dictionary containing pool statistics
        """
        with self._lock:
            total = len(self._all_connections)
            available = self._pool.qsize()
            in_use = total - available
            
            return {
                'total': total,
                'available': available,
                'in_use': in_use,
                'min_size': self.min_size,
                'max_size': self.max_size,
                'max_idle_time': self.max_idle_time,
            }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor"""
        try:
            if hasattr(self, '_closed'):
                self.close()
        except Exception:
            pass  # Ignore errors during cleanup


# Global pool instance (optional convenience)
_global_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def set_global_pool(pool: ConnectionPool):
    """
    Set the global connection pool instance.
    
    Args:
        pool: The ConnectionPool instance to use globally
    """
    global _global_pool
    with _pool_lock:
        _global_pool = pool


def get_global_pool() -> Optional[ConnectionPool]:
    """
    Get the global connection pool instance.
    
    Returns:
        Optional[ConnectionPool]: The global pool or None if not set
    """
    with _pool_lock:
        return _global_pool


def close_global_pool():
    """Close the global connection pool"""
    global _global_pool
    with _pool_lock:
        if _global_pool:
            _global_pool.close()
            _global_pool = None
