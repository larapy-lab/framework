"""
Tests for QueryBuilder Caching

Tests the query result caching functionality including:
- Basic remember() usage
- Cache hits and misses
- TTL behavior
- Custom cache keys
- Cache key generation
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, call
from larapy.database.query.builder import QueryBuilder
from larapy.cache import cache, reset_cache


class TestQueryBuilderCaching:
    """Test caching functionality in QueryBuilder."""
    
    def setup_method(self):
        """Setup test fixtures before each test."""
        reset_cache()
        
        # Create a mock connection
        self.mock_connection = Mock()
        self.mock_connection.select = Mock(return_value=[
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ])
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_cache()
    
    def test_remember_enables_caching(self):
        """Test that remember() enables caching."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        assert builder._cache_enabled is False
        
        builder.remember()
        
        assert builder._cache_enabled is True
        assert builder._cache_ttl == 3600  # Default TTL
    
    def test_remember_custom_ttl(self):
        """Test remember() with custom TTL."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        builder.remember(ttl=300)
        
        assert builder._cache_enabled is True
        assert builder._cache_ttl == 300
    
    def test_remember_custom_key(self):
        """Test remember() with custom cache key."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        builder.remember(key='my_custom_key')
        
        assert builder._cache_enabled is True
        assert builder._cache_key == 'my_custom_key'
    
    def test_remember_returns_self(self):
        """Test that remember() returns self for method chaining."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        result = builder.remember()
        
        assert result is builder
    
    def test_remember_method_chaining(self):
        """Test remember() can be chained with other query methods."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        # This should not raise an error
        result = (builder
                  .where('active', True)
                  .remember(300)
                  .order_by('name')
                  .limit(10))
        
        assert result is builder
    
    def test_get_without_cache(self):
        """Test get() without caching executes query normally."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        results = builder.get()
        
        # Should call connection.select once
        assert self.mock_connection.select.call_count == 1
        assert results == [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
    
    def test_get_with_cache_first_call(self):
        """Test get() with caching on first call (cache miss)."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        results = builder.remember().get()
        
        # Should execute query once
        assert self.mock_connection.select.call_count == 1
        assert results == [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
    
    def test_get_with_cache_second_call(self):
        """Test get() with caching on second call (cache hit)."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # First call - cache miss
        results1 = builder1.remember().get()
        
        # Second call with identical query - cache hit
        results2 = builder2.remember().get()
        
        # Should only execute query once (first call)
        assert self.mock_connection.select.call_count == 1
        
        # Both results should be identical
        assert results1 == results2
        assert results2 == [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
    
    def test_cache_different_queries(self):
        """Test that different queries have different cache keys."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # Execute two different queries
        results1 = builder1.where('id', 1).remember().get()
        results2 = builder2.where('id', 2).remember().get()
        
        # Both queries should be executed (different cache keys)
        assert self.mock_connection.select.call_count == 2
    
    def test_cache_key_generation_consistency(self):
        """Test that identical queries generate the same cache key."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # Build identical queries
        builder1.where('active', True).order_by('name').limit(10)
        builder2.where('active', True).order_by('name').limit(10)
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 == key2
    
    def test_cache_key_generation_different_wheres(self):
        """Test that different WHERE clauses generate different keys."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        builder1.where('active', True)
        builder2.where('active', False)
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 != key2
    
    def test_cache_key_generation_different_selects(self):
        """Test that different SELECT columns generate different keys."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        builder1.select('id', 'name')
        builder2.select('id', 'email')
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 != key2
    
    def test_cache_key_generation_different_orders(self):
        """Test that different ORDER BY clauses generate different keys."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        builder1.order_by('name', 'asc')
        builder2.order_by('name', 'desc')
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 != key2
    
    def test_cache_key_generation_different_limits(self):
        """Test that different LIMIT values generate different keys."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        builder1.limit(10)
        builder2.limit(20)
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 != key2
    
    def test_custom_cache_key_override(self):
        """Test that custom cache key overrides auto-generated key."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # Different queries but same custom key
        builder1.where('id', 1).remember(key='shared_key')
        builder2.where('id', 2).remember(key='shared_key')
        
        key1 = builder1._generate_cache_key()
        key2 = builder2._generate_cache_key()
        
        assert key1 == key2 == 'shared_key'
    
    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # First call with 1 second TTL
        results1 = builder1.remember(ttl=1).get()
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second call should execute query again
        results2 = builder2.remember(ttl=1).get()
        
        # Should execute query twice (cache expired)
        assert self.mock_connection.select.call_count == 2
    
    def test_cache_with_first_method(self):
        """Test that first() method doesn't use caching."""
        builder = QueryBuilder(self.mock_connection, 'users')
        
        # first() calls limit(1) then get()
        # The caching should still work through get()
        result = builder.remember().first()
        
        # Should execute query
        assert self.mock_connection.select.call_count == 1
    
    def test_cache_performance_improvement(self):
        """Test that caching improves query performance."""
        # Mock a slow database query
        call_count = [0]
        
        def slow_select(query, bindings):
            call_count[0] += 1
            time.sleep(0.1)  # Simulate slow query
            return [{'id': 1, 'name': 'Test'}]
        
        self.mock_connection.select = slow_select
        
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # First call (cache miss) - should be slow
        start1 = time.time()
        results1 = builder1.remember().get()
        duration1 = time.time() - start1
        
        # Second call (cache hit) - should be fast
        start2 = time.time()
        results2 = builder2.remember().get()
        duration2 = time.time() - start2
        
        # Cache hit should be much faster than cache miss
        assert duration2 < duration1 * 0.5  # At least 2x faster
        
        # Should only execute query once
        assert call_count[0] == 1
        
        # Results should match
        assert results1 == results2
    
    def test_cache_with_complex_query(self):
        """Test caching with a complex query."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # Build complex query
        query = (builder1
                 .select('id', 'name', 'email')
                 .where('active', True)
                 .where('age', '>', 18)
                 .order_by('name', 'asc')
                 .limit(10)
                 .offset(5)
                 .remember(300))
        
        results1 = query.get()
        
        # Same complex query
        query2 = (builder2
                  .select('id', 'name', 'email')
                  .where('active', True)
                  .where('age', '>', 18)
                  .order_by('name', 'asc')
                  .limit(10)
                  .offset(5)
                  .remember(300))
        
        results2 = query2.get()
        
        # Should only execute once (cache hit on second call)
        assert self.mock_connection.select.call_count == 1
        assert results1 == results2
    
    def test_cache_clears_between_different_tables(self):
        """Test that different tables don't share cache."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'posts')
        
        results1 = builder1.remember().get()
        results2 = builder2.remember().get()
        
        # Should execute both queries (different tables)
        assert self.mock_connection.select.call_count == 2
    
    def test_manual_cache_clear(self):
        """Test manually clearing the cache."""
        builder1 = QueryBuilder(self.mock_connection, 'users')
        builder2 = QueryBuilder(self.mock_connection, 'users')
        
        # First call
        results1 = builder1.remember().get()
        
        # Clear cache manually
        cache().flush()
        
        # Second call should execute query again
        results2 = builder2.remember().get()
        
        # Should execute twice (cache was cleared)
        assert self.mock_connection.select.call_count == 2
