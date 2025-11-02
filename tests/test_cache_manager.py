"""
Tests for Cache Manager

Tests the cache manager's functionality including:
- Basic put/get operations
- TTL (Time To Live) expiration
- Cache key generation
- Cache clearing and flushing
"""

import pytest
import time
from larapy.cache import CacheManager, cache, reset_cache


class TestCacheManager:
    """Test the CacheManager class."""
    
    def setup_method(self):
        """Reset cache before each test."""
        reset_cache()
    
    def teardown_method(self):
        """Reset cache after each test."""
        reset_cache()
    
    def test_basic_put_and_get(self):
        """Test basic cache put and get operations."""
        cache_mgr = cache()
        
        # Store a value
        cache_mgr.put('test_key', 'test_value')
        
        # Retrieve the value
        assert cache_mgr.get('test_key') == 'test_value'
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist returns None."""
        cache_mgr = cache()
        
        assert cache_mgr.get('nonexistent') is None
    
    def test_has_method(self):
        """Test the has() method to check if key exists."""
        cache_mgr = cache()
        
        cache_mgr.put('existing_key', 'value')
        
        assert cache_mgr.has('existing_key') is True
        assert cache_mgr.has('nonexistent_key') is False
    
    def test_ttl_expiration(self):
        """Test that cached values expire after TTL."""
        cache_mgr = cache()
        
        # Store with 1 second TTL
        cache_mgr.put('short_lived', 'value', ttl=1)
        
        # Should exist immediately
        assert cache_mgr.get('short_lived') == 'value'
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache_mgr.get('short_lived') is None
    
    def test_no_ttl(self):
        """Test that values without TTL don't expire."""
        cache_mgr = cache()
        
        # Store without TTL
        cache_mgr.put('permanent', 'value', ttl=None)
        
        # Should still exist after some time
        time.sleep(0.5)
        assert cache_mgr.get('permanent') == 'value'
    
    def test_forget(self):
        """Test removing a value from cache."""
        cache_mgr = cache()
        
        cache_mgr.put('test_key', 'test_value')
        
        # Remove the key
        result = cache_mgr.forget('test_key')
        
        assert result is True
        assert cache_mgr.get('test_key') is None
    
    def test_forget_nonexistent(self):
        """Test forgetting a key that doesn't exist."""
        cache_mgr = cache()
        
        result = cache_mgr.forget('nonexistent')
        
        assert result is False
    
    def test_flush(self):
        """Test clearing all cache entries."""
        cache_mgr = cache()
        
        # Add multiple entries
        cache_mgr.put('key1', 'value1')
        cache_mgr.put('key2', 'value2')
        cache_mgr.put('key3', 'value3')
        
        # Flush all
        cache_mgr.flush()
        
        # All should be gone
        assert cache_mgr.get('key1') is None
        assert cache_mgr.get('key2') is None
        assert cache_mgr.get('key3') is None
        assert cache_mgr.size() == 0
    
    def test_clear_expired(self):
        """Test clearing only expired entries."""
        cache_mgr = cache()
        
        # Add entries with different TTLs
        cache_mgr.put('short', 'value1', ttl=1)
        cache_mgr.put('long', 'value2', ttl=10)
        cache_mgr.put('permanent', 'value3', ttl=None)
        
        # Wait for short TTL to expire
        time.sleep(1.1)
        
        # Clear expired entries
        cleared = cache_mgr.clear_expired()
        
        assert cleared == 1
        assert cache_mgr.get('short') is None
        assert cache_mgr.get('long') == 'value2'
        assert cache_mgr.get('permanent') == 'value3'
    
    def test_size(self):
        """Test getting the cache size."""
        cache_mgr = cache()
        
        assert cache_mgr.size() == 0
        
        cache_mgr.put('key1', 'value1')
        assert cache_mgr.size() == 1
        
        cache_mgr.put('key2', 'value2')
        assert cache_mgr.size() == 2
        
        cache_mgr.forget('key1')
        assert cache_mgr.size() == 1
    
    def test_generate_key_simple(self):
        """Test generating cache keys from simple arguments."""
        key1 = CacheManager.generate_key('arg1', 'arg2', 'arg3')
        key2 = CacheManager.generate_key('arg1', 'arg2', 'arg3')
        key3 = CacheManager.generate_key('arg1', 'arg2', 'different')
        
        # Same arguments should generate same key
        assert key1 == key2
        
        # Different arguments should generate different key
        assert key1 != key3
    
    def test_generate_key_with_kwargs(self):
        """Test generating cache keys with keyword arguments."""
        key1 = CacheManager.generate_key('arg1', foo='bar', baz='qux')
        key2 = CacheManager.generate_key('arg1', foo='bar', baz='qux')
        key3 = CacheManager.generate_key('arg1', foo='different', baz='qux')
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_lists(self):
        """Test generating cache keys with list arguments."""
        key1 = CacheManager.generate_key(['a', 'b', 'c'])
        key2 = CacheManager.generate_key(['a', 'b', 'c'])
        key3 = CacheManager.generate_key(['a', 'b', 'd'])
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_dicts(self):
        """Test generating cache keys with dict arguments."""
        key1 = CacheManager.generate_key({'x': 1, 'y': 2})
        key2 = CacheManager.generate_key({'y': 2, 'x': 1})  # Different order
        key3 = CacheManager.generate_key({'x': 1, 'y': 3})
        
        # Same content, different order should generate same key
        assert key1 == key2
        
        # Different content should generate different key
        assert key1 != key3
    
    def test_cache_different_types(self):
        """Test caching different data types."""
        cache_mgr = cache()
        
        # String
        cache_mgr.put('string', 'test')
        assert cache_mgr.get('string') == 'test'
        
        # Integer
        cache_mgr.put('int', 42)
        assert cache_mgr.get('int') == 42
        
        # List
        cache_mgr.put('list', [1, 2, 3])
        assert cache_mgr.get('list') == [1, 2, 3]
        
        # Dict
        cache_mgr.put('dict', {'key': 'value'})
        assert cache_mgr.get('dict') == {'key': 'value'}
        
        # Boolean
        cache_mgr.put('bool', True)
        assert cache_mgr.get('bool') is True
        
        # None
        cache_mgr.put('none', None)
        # Note: get() returns None for both missing and None values
        # Use has() to distinguish
        assert cache_mgr.has('none') is True
    
    def test_global_cache_instance(self):
        """Test that cache() returns a singleton instance."""
        cache1 = cache()
        cache2 = cache()
        
        assert cache1 is cache2
        
        # Changes in one should reflect in the other
        cache1.put('test', 'value')
        assert cache2.get('test') == 'value'
    
    def test_thread_safety_basic(self):
        """Basic test for thread safety (put/get operations)."""
        import threading
        
        cache_mgr = cache()
        results = []
        
        def worker(n):
            cache_mgr.put(f'key{n}', f'value{n}')
            results.append(cache_mgr.get(f'key{n}'))
        
        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all to complete
        for t in threads:
            t.join()
        
        # Check that all operations completed successfully
        assert len(results) == 10
        assert all(r is not None for r in results)
