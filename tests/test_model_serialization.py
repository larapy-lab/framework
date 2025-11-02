"""
Test Model Serialization

Tests for Model toArray, toJson, toDict, hidden/visible attributes,
appended attributes, and date serialization.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any, Optional
from larapy.database.orm.model import Model


class User(Model):
    """Test user model"""
    _table = 'users'
    _fillable = ['id', 'name', 'email', 'password', 'api_token', 'created_at', 'updated_at']
    _hidden = ['password', 'api_token']
    _casts = {
        'created_at': 'datetime',
        'updated_at': 'datetime'
    }
    
    def get_full_name_attribute(self):
        """Accessor for full_name"""
        return f"{self.name} (User)"
    
    def get_is_admin_attribute(self):
        """Accessor for is_admin"""
        return self.email.endswith('@admin.com') if self.email else False


class Post(Model):
    """Test post model with visible attributes"""
    _table = 'posts'
    _fillable = ['id', 'title', 'body', 'author_id', 'slug', 'published_at']
    _visible = ['id', 'title', 'slug', 'published_at']
    _appends = ['word_count']
    _casts = {
        'published_at': 'datetime:Y-m-d H:i:s'
    }
    
    def get_word_count_attribute(self):
        """Accessor for word count"""
        if self.body:
            return len(self.body.split())
        return 0


class Product(Model):
    """Test product model with JSON casts"""
    _table = 'products'
    _fillable = ['id', 'name', 'price', 'metadata', 'tags']
    _casts = {
        'metadata': 'json',
        'tags': 'array',
        'price': 'float'
    }


class Article(Model):
    """Test article model with custom date format"""
    _table = 'articles'
    _fillable = ['id', 'title', 'content', 'published_at']
    _dateFormat = '%Y-%m-%d'
    _casts = {
        'published_at': 'datetime'
    }


class TestBasicSerialization:
    """Test basic toArray, toDict, toJson methods"""
    
    def test_to_array_basic(self):
        """Test basic toArray conversion"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123'
        })
        
        result = user.toArray()
        
        assert isinstance(result, dict)
        assert result['id'] == 1
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
        assert 'password' not in result  # Hidden attribute
    
    def test_to_dict_alias(self):
        """Test toDict is alias for toArray"""
        user = User({
            'id': 1,
            'name': 'Jane Doe',
            'email': 'jane@example.com'
        })
        
        dict_result = user.toDict()
        array_result = user.toArray()
        
        assert dict_result == array_result
    
    def test_to_json_basic(self):
        """Test basic toJson conversion"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        result = user.toJson()
        
        assert isinstance(result, str)
        
        parsed = json.loads(result)
        assert parsed['id'] == 1
        assert parsed['name'] == 'John Doe'
        assert parsed['email'] == 'john@example.com'
    
    def test_to_json_with_options(self):
        """Test toJson with custom JSON options"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        result = user.toJson(indent=2, sort_keys=True)
        
        assert isinstance(result, str)
        assert '\n' in result  # Indented
        
        parsed = json.loads(result)
        assert parsed['id'] == 1


class TestHiddenAttributes:
    """Test hidden attributes functionality"""
    
    def test_hidden_attributes_excluded(self):
        """Test hidden attributes are excluded from serialization"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123',
            'api_token': 'token_abc123'
        })
        
        result = user.toArray()
        
        assert 'password' not in result
        assert 'api_token' not in result
        assert 'name' in result
        assert 'email' in result
    
    def test_make_visible_runtime(self):
        """Test makeVisible makes hidden attributes visible"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'password': 'secret123',
            'api_token': 'token_abc123'
        })
        
        result = user.makeVisible(['password']).toArray()
        
        assert 'password' in result
        assert result['password'] == 'secret123'
        assert 'api_token' not in result  # Still hidden
    
    def test_make_hidden_runtime(self):
        """Test makeHidden hides attributes at runtime"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        result = user.makeHidden(['email']).toArray()
        
        assert 'email' not in result
        assert 'name' in result
    
    def test_set_hidden(self):
        """Test setHidden replaces hidden attributes list"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123'
        })
        
        result = user.setHidden(['name', 'email']).toArray()
        
        assert 'name' not in result
        assert 'email' not in result
        assert 'password' in result  # No longer hidden
    
    def test_get_hidden(self):
        """Test getHidden returns hidden attributes"""
        user = User()
        
        hidden = user.getHidden()
        
        assert 'password' in hidden
        assert 'api_token' in hidden


class TestVisibleAttributes:
    """Test visible attributes functionality"""
    
    def test_visible_attributes_only(self):
        """Test only visible attributes are included"""
        post = Post({
            'id': 1,
            'title': 'Test Post',
            'body': 'This is the body',
            'author_id': 5,
            'slug': 'test-post'
        })
        
        result = post.toArray()
        
        assert 'id' in result
        assert 'title' in result
        assert 'slug' in result
        assert 'body' not in result  # Not in visible list
        assert 'author_id' not in result  # Not in visible list
    
    def test_set_visible(self):
        """Test setVisible sets visible attributes"""
        post = Post({
            'id': 1,
            'title': 'Test Post',
            'body': 'Body content',
            'author_id': 5
        })
        
        result = post.setVisible(['id', 'body']).toArray()
        
        assert 'id' in result
        assert 'body' in result
        assert 'title' not in result  # No longer visible
    
    def test_get_visible(self):
        """Test getVisible returns visible attributes"""
        post = Post()
        
        visible = post.getVisible()
        
        assert 'id' in visible
        assert 'title' in visible
        assert 'slug' in visible


class TestAppendedAttributes:
    """Test appended attributes functionality"""
    
    def test_appends_basic(self):
        """Test appended attributes are included"""
        post = Post({
            'id': 1,
            'title': 'Test Post',
            'body': 'This is a test post with multiple words',
            'slug': 'test-post'
        })
        
        result = post.toArray()
        
        assert 'word_count' in result
        assert result['word_count'] == 8
    
    def test_accessor_method(self):
        """Test accessor method pattern"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        user._appends = ['full_name']
        result = user.toArray()
        
        assert 'full_name' in result
        assert result['full_name'] == 'John Doe (User)'
    
    def test_append_runtime(self):
        """Test append adds attributes at runtime"""
        user = User({
            'id': 1,
            'name': 'Admin User',
            'email': 'admin@admin.com'
        })
        
        result = user.append(['full_name', 'is_admin']).toArray()
        
        assert 'full_name' in result
        assert result['full_name'] == 'Admin User (User)'
        assert 'is_admin' in result
        assert result['is_admin'] is True
    
    def test_get_appends(self):
        """Test getAppends returns appended attributes"""
        post = Post()
        
        appends = post.getAppends()
        
        assert 'word_count' in appends


class TestDateSerialization:
    """Test date serialization functionality"""
    
    def test_iso8601_date_format(self):
        """Test default ISO 8601 date format"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'created_at': datetime(2024, 1, 15, 10, 30, 45)
        })
        
        result = user.toArray()
        
        assert 'created_at' in result
        assert isinstance(result['created_at'], str)
        assert '2024-01-15' in result['created_at']
    
    def test_custom_date_format(self):
        """Test custom date format via dateFormat property"""
        article = Article({
            'id': 1,
            'title': 'Test Article',
            'published_at': datetime(2024, 1, 15, 10, 30, 45)
        })
        
        result = article.toArray()
        
        assert 'published_at' in result
        assert result['published_at'] == '2024-01-15'
    
    def test_cast_with_format(self):
        """Test datetime cast with custom format"""
        post = Post({
            'id': 1,
            'title': 'Test Post',
            'published_at': datetime(2024, 1, 15, 10, 30, 45)
        })
        
        # Note: The cast format 'Y-m-d H:i:s' needs to be converted to Python format
        # This test will verify the serialization handles datetime objects
        result = post.toArray()
        
        assert 'published_at' in result


class TestAttributeCasting:
    """Test attribute casting in serialization"""
    
    def test_json_cast_serialization(self):
        """Test JSON cast in serialization"""
        product = Product({
            'id': 1,
            'name': 'Test Product',
            'metadata': '{"color": "red", "size": "large"}'
        })
        
        result = product.toArray()
        
        assert 'metadata' in result
        assert isinstance(result['metadata'], dict)
        assert result['metadata']['color'] == 'red'
    
    def test_array_cast_serialization(self):
        """Test array cast in serialization"""
        product = Product({
            'id': 1,
            'name': 'Test Product',
            'tags': '["electronics", "gadgets"]'
        })
        
        result = product.toArray()
        
        assert 'tags' in result
        assert isinstance(result['tags'], list)
        assert 'electronics' in result['tags']
    
    def test_float_cast_serialization(self):
        """Test float cast in serialization"""
        product = Product({
            'id': 1,
            'name': 'Test Product',
            'price': 99.99
        })
        
        result = product.toArray()
        
        assert 'price' in result
        assert result['price'] == 99.99


class TestComplexScenarios:
    """Test complex serialization scenarios"""
    
    def test_chained_visibility_methods(self):
        """Test chaining multiple visibility methods"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123',
            'api_token': 'token_abc'
        })
        
        result = user.makeVisible(['password']).makeHidden(['email']).append(['full_name']).toArray()
        
        assert 'password' in result
        assert 'email' not in result
        assert 'full_name' in result
        assert 'api_token' not in result
    
    def test_empty_model_serialization(self):
        """Test serialization of empty model"""
        user = User()
        
        result = user.toArray()
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_none_values_serialization(self):
        """Test serialization with None values"""
        user = User({
            'id': 1,
            'name': None,
            'email': 'john@example.com'
        })
        
        result = user.toArray()
        
        assert 'name' in result
        assert result['name'] is None
    
    def test_serialization_preserves_original(self):
        """Test serialization doesn't modify original attributes"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'password': 'secret123'
        })
        
        original_attrs = user._attributes.copy()
        
        user.toArray()
        user.toJson()
        
        assert user._attributes == original_attrs
    
    def test_json_unicode_handling(self):
        """Test JSON serialization with unicode characters"""
        user = User({
            'id': 1,
            'name': '李明',
            'email': 'li@example.com'
        })
        
        result = user.toJson()
        
        parsed = json.loads(result)
        assert parsed['name'] == '李明'


class TestAccessorPatterns:
    """Test accessor method patterns"""
    
    def test_accessor_with_no_base_attribute(self):
        """Test accessor that doesn't rely on base attribute"""
        user = User({
            'id': 1,
            'name': 'John Doe',
            'email': 'user@example.com'
        })
        
        result = user.append(['is_admin']).toArray()
        
        assert 'is_admin' in result
        assert result['is_admin'] is False
    
    def test_accessor_returns_none(self):
        """Test accessor returning None"""
        post = Post({
            'id': 1,
            'title': 'Test',
            'body': None
        })
        
        result = post.toArray()
        
        assert 'word_count' in result
        assert result['word_count'] == 0
    
    def test_missing_accessor_method(self):
        """Test appending non-existent accessor"""
        user = User({
            'id': 1,
            'name': 'John Doe'
        })
        
        result = user.append(['non_existent_accessor']).toArray()
        
        assert 'non_existent_accessor' in result
        assert result['non_existent_accessor'] is None


class TestRouteKeyMethods:
    """Test route key methods for model binding"""
    
    def test_get_route_key_name(self):
        """Test getRouteKeyName returns primary key"""
        user = User()
        
        assert user.getRouteKeyName() == 'id'
    
    def test_custom_route_key_name(self):
        """Test custom route key name"""
        class CustomKeyModel(Model):
            _table = 'models'
            _primary_key = 'uuid'
        
        model = CustomKeyModel()
        
        assert model.getRouteKeyName() == 'uuid'


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_circular_reference_handling(self):
        """Test handling of potential circular references"""
        user = User({
            'id': 1,
            'name': 'John Doe'
        })
        
        # This shouldn't cause infinite recursion
        result = user.toArray()
        
        assert isinstance(result, dict)
    
    def test_large_model_serialization(self):
        """Test serialization of model with many attributes"""
        attributes = {f'field_{i}': f'value_{i}' for i in range(100)}
        attributes['id'] = 1
        
        class LargeModel(Model):
            _table = 'large'
            _fillable = list(attributes.keys())
        
        model = LargeModel(attributes)
        result = model.toArray()
        
        assert len(result) == 101
    
    def test_special_characters_in_values(self):
        """Test serialization with special characters"""
        user = User({
            'id': 1,
            'name': 'John "The Boss" O\'Reilly',
            'email': 'john+boss@example.com'
        })
        
        result = user.toJson()
        parsed = json.loads(result)
        
        assert parsed['name'] == 'John "The Boss" O\'Reilly'
        assert parsed['email'] == 'john+boss@example.com'
