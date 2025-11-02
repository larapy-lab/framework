"""
Cache Manager for Larapy

Provides simple in-memory caching with TTL support for query results.
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
from threading import Lock


class CacheManager:
    """
    Simple in-memory cache with TTL (Time To Live) support.
    
    Thread-safe cache implementation for storing query results and other data.
    """
    
    def __init__(self):
        """Initialize the cache manager."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if entry has expired
            if entry['expires_at'] and time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            return entry['value']
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self._lock:
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists and is valid, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            
            # Check if entry has expired
            if entry['expires_at'] and time.time() > entry['expires_at']:
                del self._cache[key]
                return False
            
            return True
    
    def forget(self, key: str) -> bool:
        """
        Remove a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was removed, False if it didn't exist
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def flush(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            self._cache.clear()
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            The number of expired entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry['expires_at'] and current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            The number of items in the cache
        """
        with self._lock:
            return len(self._cache)
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments to include in the key
            **kwargs: Keyword arguments to include in the key
            
        Returns:
            A hash string suitable for use as a cache key
        """
        # Create a string representation of all arguments
        key_parts = []
        
        for arg in args:
            if isinstance(arg, (list, dict)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (list, dict)):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")
        
        # Generate MD5 hash of the combined string
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def cache() -> CacheManager:
    """
    Get the global cache instance.
    
    Returns:
        The global CacheManager instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


def reset_cache() -> None:
    """Reset the global cache instance (useful for testing)."""
    global _cache_instance
    if _cache_instance is not None:
        _cache_instance.flush()
    _cache_instance = None
