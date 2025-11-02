"""
Tests for Configuration Repository
"""

import pytest
from larapy.config.repository import Repository


class TestRepositoryBasicOperations:
    """Test basic repository operations."""

    def test_initialization_with_empty_items(self):
        """Test repository can be initialized with no items."""
        repo = Repository()
        assert repo.all() == {}

    def test_initialization_with_items(self):
        """Test repository can be initialized with items."""
        items = {'app': {'name': 'Larapy'}}
        repo = Repository(items)
        assert repo.all() == items

    def test_get_simple_key(self):
        """Test getting a value with a simple key."""
        repo = Repository({'name': 'Larapy'})
        assert repo.get('name') == 'Larapy'

    def test_get_nonexistent_key_returns_default(self):
        """Test getting a nonexistent key returns default."""
        repo = Repository()
        assert repo.get('missing') is None
        assert repo.get('missing', 'default') == 'default'

    def test_get_with_callable_default(self):
        """Test default value can be a callable."""
        repo = Repository()
        assert repo.get('missing', lambda: 'computed') == 'computed'

    def test_has_simple_key(self):
        """Test checking if a simple key exists."""
        repo = Repository({'name': 'Larapy'})
        assert repo.has('name') is True
        assert repo.has('missing') is False

    def test_set_simple_key(self):
        """Test setting a value with a simple key."""
        repo = Repository()
        repo.set('name', 'Larapy')
        assert repo.get('name') == 'Larapy'

    def test_set_multiple_keys_with_dict(self):
        """Test setting multiple values with a dictionary."""
        repo = Repository()
        repo.set({'name': 'Larapy', 'version': '1.0'})
        assert repo.get('name') == 'Larapy'
        assert repo.get('version') == '1.0'


class TestRepositoryDotNotation:
    """Test dot notation access."""

    def test_get_nested_value_with_dot_notation(self):
        """Test getting nested values using dot notation."""
        repo = Repository({
            'app': {
                'name': 'Larapy',
                'env': 'production'
            }
        })
        assert repo.get('app.name') == 'Larapy'
        assert repo.get('app.env') == 'production'

    def test_get_deeply_nested_value(self):
        """Test getting deeply nested values."""
        repo = Repository({
            'database': {
                'connections': {
                    'mysql': {
                        'host': 'localhost',
                        'port': 3306
                    }
                }
            }
        })
        assert repo.get('database.connections.mysql.host') == 'localhost'
        assert repo.get('database.connections.mysql.port') == 3306

    def test_has_nested_key(self):
        """Test checking if nested key exists."""
        repo = Repository({
            'app': {'name': 'Larapy'}
        })
        assert repo.has('app.name') is True
        assert repo.has('app.missing') is False
        assert repo.has('missing.key') is False

    def test_set_nested_value_creates_structure(self):
        """Test setting nested value creates intermediate structure."""
        repo = Repository()
        repo.set('app.name', 'Larapy')
        assert repo.get('app.name') == 'Larapy'
        assert isinstance(repo.get('app'), dict)

    def test_set_deeply_nested_value(self):
        """Test setting deeply nested values."""
        repo = Repository()
        repo.set('database.connections.mysql.host', 'localhost')
        assert repo.get('database.connections.mysql.host') == 'localhost'

    def test_set_nested_overwrites_non_dict_value(self):
        """Test setting nested value overwrites non-dict intermediate values."""
        repo = Repository({'app': 'string'})
        repo.set('app.name', 'Larapy')
        assert repo.get('app.name') == 'Larapy'
        assert isinstance(repo.get('app'), dict)

    def test_get_with_non_dict_intermediate_returns_default(self):
        """Test getting from non-dict intermediate value returns default."""
        repo = Repository({'app': 'string'})
        assert repo.get('app.name', 'default') == 'default'

    def test_has_with_non_dict_intermediate_returns_false(self):
        """Test checking key with non-dict intermediate returns False."""
        repo = Repository({'app': 'string'})
        assert repo.has('app.name') is False


class TestRepositoryArrayOperations:
    """Test array manipulation operations."""

    def test_push_to_existing_array(self):
        """Test pushing value to existing array."""
        repo = Repository({'items': [1, 2, 3]})
        repo.push('items', 4)
        assert repo.get('items') == [1, 2, 3, 4]

    def test_push_creates_array_if_missing(self):
        """Test push creates array if key doesn't exist."""
        repo = Repository()
        repo.push('items', 1)
        assert repo.get('items') == [1]

    def test_push_creates_array_if_not_list(self):
        """Test push creates array if value is not a list."""
        repo = Repository({'items': 'string'})
        repo.push('items', 1)
        assert repo.get('items') == [1]

    def test_prepend_to_existing_array(self):
        """Test prepending value to existing array."""
        repo = Repository({'items': [2, 3, 4]})
        repo.prepend('items', 1)
        assert repo.get('items') == [1, 2, 3, 4]

    def test_prepend_creates_array_if_missing(self):
        """Test prepend creates array if key doesn't exist."""
        repo = Repository()
        repo.prepend('items', 1)
        assert repo.get('items') == [1]

    def test_prepend_creates_array_if_not_list(self):
        """Test prepend creates array if value is not a list."""
        repo = Repository({'items': 'string'})
        repo.prepend('items', 1)
        assert repo.get('items') == [1]

    def test_push_with_dot_notation(self):
        """Test push with nested key."""
        repo = Repository({'app': {'providers': ['ServiceProvider']}})
        repo.push('app.providers', 'DatabaseProvider')
        assert repo.get('app.providers') == ['ServiceProvider', 'DatabaseProvider']

    def test_prepend_with_dot_notation(self):
        """Test prepend with nested key."""
        repo = Repository({'app': {'providers': ['ServiceProvider']}})
        repo.prepend('app.providers', 'BootstrapProvider')
        assert repo.get('app.providers') == ['BootstrapProvider', 'ServiceProvider']


class TestRepositoryTypedGetters:
    """Test typed getter methods."""

    def test_string_returns_string_value(self):
        """Test string() returns string values."""
        repo = Repository({'name': 'Larapy'})
        assert repo.string('name') == 'Larapy'

    def test_string_with_default(self):
        """Test string() returns default for missing key."""
        repo = Repository()
        assert repo.string('name', 'default') == 'default'

    def test_string_raises_for_none_without_default(self):
        """Test string() raises ValueError for None without default."""
        repo = Repository({'name': None})
        with pytest.raises(ValueError, match="required"):
            repo.string('name')

    def test_string_raises_for_non_string(self):
        """Test string() raises ValueError for non-string values."""
        repo = Repository({'name': 123})
        with pytest.raises(ValueError, match="must be a string"):
            repo.string('name')

    def test_integer_returns_integer_value(self):
        """Test integer() returns integer values."""
        repo = Repository({'port': 8000})
        assert repo.integer('port') == 8000

    def test_integer_with_default(self):
        """Test integer() returns default for missing key."""
        repo = Repository()
        assert repo.integer('port', 3000) == 3000

    def test_integer_raises_for_none_without_default(self):
        """Test integer() raises ValueError for None without default."""
        repo = Repository({'port': None})
        with pytest.raises(ValueError, match="required"):
            repo.integer('port')

    def test_integer_raises_for_non_integer(self):
        """Test integer() raises ValueError for non-integer values."""
        repo = Repository({'port': '8000'})
        with pytest.raises(ValueError, match="must be an integer"):
            repo.integer('port')

    def test_integer_raises_for_boolean(self):
        """Test integer() raises ValueError for boolean values."""
        repo = Repository({'port': True})
        with pytest.raises(ValueError, match="must be an integer"):
            repo.integer('port')

    def test_float_returns_float_value(self):
        """Test float() returns float values."""
        repo = Repository({'rate': 1.5})
        assert repo.float('rate') == 1.5

    def test_float_accepts_integer(self):
        """Test float() accepts integer values."""
        repo = Repository({'rate': 2})
        assert repo.float('rate') == 2.0

    def test_float_with_default(self):
        """Test float() returns default for missing key."""
        repo = Repository()
        assert repo.float('rate', 0.5) == 0.5

    def test_float_raises_for_none_without_default(self):
        """Test float() raises ValueError for None without default."""
        repo = Repository({'rate': None})
        with pytest.raises(ValueError, match="required"):
            repo.float('rate')

    def test_float_raises_for_non_numeric(self):
        """Test float() raises ValueError for non-numeric values."""
        repo = Repository({'rate': '1.5'})
        with pytest.raises(ValueError, match="must be a float"):
            repo.float('rate')

    def test_float_raises_for_boolean(self):
        """Test float() raises ValueError for boolean values."""
        repo = Repository({'rate': False})
        with pytest.raises(ValueError, match="must be a float"):
            repo.float('rate')

    def test_boolean_returns_boolean_value(self):
        """Test boolean() returns boolean values."""
        repo = Repository({'debug': True})
        assert repo.boolean('debug') is True

    def test_boolean_with_default(self):
        """Test boolean() returns default for missing key."""
        repo = Repository()
        assert repo.boolean('debug', False) is False

    def test_boolean_raises_for_none_without_default(self):
        """Test boolean() raises ValueError for None without default."""
        repo = Repository({'debug': None})
        with pytest.raises(ValueError, match="required"):
            repo.boolean('debug')

    def test_boolean_raises_for_non_boolean(self):
        """Test boolean() raises ValueError for non-boolean values."""
        repo = Repository({'debug': 1})
        with pytest.raises(ValueError, match="must be a boolean"):
            repo.boolean('debug')

    def test_array_returns_list_value(self):
        """Test array() returns list values."""
        repo = Repository({'items': [1, 2, 3]})
        assert repo.array('items') == [1, 2, 3]

    def test_array_with_default(self):
        """Test array() returns default for missing key."""
        repo = Repository()
        assert repo.array('items', []) == []

    def test_array_raises_for_none_without_default(self):
        """Test array() raises ValueError for None without default."""
        repo = Repository({'items': None})
        with pytest.raises(ValueError, match="required"):
            repo.array('items')

    def test_array_raises_for_non_list(self):
        """Test array() raises ValueError for non-list values."""
        repo = Repository({'items': 'string'})
        with pytest.raises(ValueError, match="must be an array"):
            repo.array('items')


class TestRepositoryArrayAccess:
    """Test array-style access interface."""

    def test_getitem_returns_value(self):
        """Test array-style get returns value."""
        repo = Repository({'name': 'Larapy'})
        assert repo['name'] == 'Larapy'

    def test_getitem_with_dot_notation(self):
        """Test array-style get with dot notation."""
        repo = Repository({'app': {'name': 'Larapy'}})
        assert repo['app.name'] == 'Larapy'

    def test_setitem_sets_value(self):
        """Test array-style set stores value."""
        repo = Repository()
        repo['name'] = 'Larapy'
        assert repo.get('name') == 'Larapy'

    def test_setitem_with_dot_notation(self):
        """Test array-style set with dot notation."""
        repo = Repository()
        repo['app.name'] = 'Larapy'
        assert repo.get('app.name') == 'Larapy'

    def test_contains_returns_true_for_existing_key(self):
        """Test 'in' operator returns True for existing keys."""
        repo = Repository({'name': 'Larapy'})
        assert 'name' in repo

    def test_contains_returns_false_for_missing_key(self):
        """Test 'in' operator returns False for missing keys."""
        repo = Repository()
        assert 'name' not in repo

    def test_contains_with_dot_notation(self):
        """Test 'in' operator with dot notation."""
        repo = Repository({'app': {'name': 'Larapy'}})
        assert 'app.name' in repo
        assert 'app.missing' not in repo


class TestRepositoryComplexScenarios:
    """Test complex real-world scenarios."""

    def test_database_configuration_scenario(self):
        """Test managing database configuration."""
        repo = Repository()
        
        repo.set('database.default', 'mysql')
        repo.set('database.connections.mysql', {
            'driver': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'larapy',
            'username': 'root',
            'password': 'secret'
        })
        
        assert repo.string('database.default') == 'mysql'
        assert repo.string('database.connections.mysql.driver') == 'mysql'
        assert repo.integer('database.connections.mysql.port') == 3306
        assert repo.has('database.connections.mysql.password') is True

    def test_service_providers_configuration(self):
        """Test managing service providers configuration."""
        repo = Repository({
            'app': {
                'providers': [
                    'DatabaseServiceProvider',
                    'CacheServiceProvider'
                ]
            }
        })
        
        repo.push('app.providers', 'QueueServiceProvider')
        repo.prepend('app.providers', 'BootstrapProvider')
        
        providers = repo.array('app.providers')
        assert providers[0] == 'BootstrapProvider'
        assert providers[-1] == 'QueueServiceProvider'
        assert len(providers) == 4

    def test_environment_specific_configuration(self):
        """Test managing environment-specific settings."""
        base_config = {
            'app': {
                'name': 'Larapy',
                'debug': False,
                'url': 'https://production.example.com'
            }
        }
        
        repo = Repository(base_config)
        
        repo.set('app.debug', True)
        repo.set('app.url', 'http://localhost:8000')
        
        assert repo.boolean('app.debug') is True
        assert repo.string('app.url') == 'http://localhost:8000'
        assert repo.string('app.name') == 'Larapy'

    def test_nested_configuration_merging(self):
        """Test merging nested configuration values."""
        repo = Repository({
            'cache': {
                'default': 'redis',
                'stores': {
                    'redis': {
                        'driver': 'redis',
                        'connection': 'default'
                    }
                }
            }
        })
        
        repo.set('cache.stores.file', {
            'driver': 'file',
            'path': '/tmp/cache'
        })
        
        assert repo.has('cache.stores.redis') is True
        assert repo.has('cache.stores.file') is True
        assert repo.string('cache.stores.file.driver') == 'file'

    def test_configuration_with_callable_defaults(self):
        """Test using callable defaults for lazy evaluation."""
        repo = Repository({'computed': {'enabled': True}})
        
        call_count = 0
        
        def expensive_default():
            nonlocal call_count
            call_count += 1
            return 'expensive-value'
        
        result1 = repo.get('existing.key', expensive_default)
        assert result1 == 'expensive-value'
        assert call_count == 1
        
        result2 = repo.get('computed.enabled', expensive_default)
        assert result2 is True
        assert call_count == 1

    def test_overwriting_simple_value_with_nested(self):
        """Test overwriting simple values with nested structures."""
        repo = Repository({'setting': 'simple'})
        
        assert repo.get('setting') == 'simple'
        
        repo.set('setting.nested', 'value')
        
        assert isinstance(repo.get('setting'), dict)
        assert repo.get('setting.nested') == 'value'

    def test_multiple_configuration_sources(self):
        """Test combining configuration from multiple sources."""
        defaults = {
            'app': {'name': 'Larapy', 'env': 'production'},
            'database': {'default': 'mysql'}
        }
        
        repo = Repository(defaults)
        
        repo.set({
            'app.debug': True,
            'cache.default': 'redis',
            'queue.connection': 'database'
        })
        
        assert repo.string('app.name') == 'Larapy'
        assert repo.boolean('app.debug') is True
        assert repo.string('cache.default') == 'redis'
        assert repo.string('database.default') == 'mysql'
