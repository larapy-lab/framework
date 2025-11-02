"""
Test Route Model Binding

Tests for implicit binding, explicit binding, custom fields,
soft-deleted models, scoped bindings, and error handling.
"""

import pytest
from typing import Dict, Any, Optional
from larapy.database.orm.model import Model
from larapy.routing.model_binder import ModelBinder, ModelNotFoundException


# Test Models

class User(Model):
    """Test user model"""
    _table = 'users'
    _primary_key = 'id'
    _fillable = ['id', 'name', 'email', 'username']
    
    # Store test data in class
    _test_data = {}
    
    @classmethod
    def where(cls, field: str, value: Any):
        """Mock where query"""
        class MockQuery:
            def __init__(self, model_class, field, value):
                self.model_class = model_class
                self.field = field
                self.value = value
            
            def first(self):
                """Find matching model"""
                for item_id, data in self.model_class._test_data.items():
                    field_value = data.get(self.field)
                    # Handle type coercion for IDs
                    if self.field == 'id':
                        # Try to compare as both string and int
                        if str(field_value) == str(self.value) or field_value == self.value:
                            model = self.model_class(data)
                            model._exists = True
                            return model
                    elif field_value == self.value:
                        model = self.model_class(data)
                        model._exists = True
                        return model
                return None
        
        return MockQuery(cls, field, value)


class Post(Model):
    """Test post model with custom route key"""
    _table = 'posts'
    _primary_key = 'id'
    _fillable = ['id', 'title', 'slug', 'user_id', 'body']
    
    # Store test data
    _test_data = {}
    
    def getRouteKeyName(self) -> str:
        """Use slug as route key"""
        return 'slug'
    
    @classmethod
    def where(cls, field: str, value: Any):
        """Mock where query"""
        class MockQuery:
            def __init__(self, model_class, field, value):
                self.model_class = model_class
                self.field = field
                self.value = value
            
            def first(self):
                for item_id, data in self.model_class._test_data.items():
                    if data.get(self.field) == self.value:
                        model = self.model_class(data)
                        model._exists = True
                        return model
                return None
        
        return MockQuery(cls, field, value)


class Product(Model):
    """Test product model with custom resolution"""
    _table = 'products'
    _primary_key = 'id'
    _fillable = ['id', 'name', 'sku', 'price']
    
    # Store test data
    _test_data = {}
    
    def resolveRouteBinding(self, value: Any, field: Optional[str] = None):
        """Custom route binding resolution"""
        if field == 'sku':
            # Search by SKU
            for item_id, data in self._test_data.items():
                if data.get('sku') == value:
                    model = Product(data)
                    model._exists = True
                    return model
        else:
            # Default to ID
            if int(value) in self._test_data:
                data = self._test_data[int(value)]
                model = Product(data)
                model._exists = True
                return model
        return None
    
    @classmethod
    def where(cls, field: str, value: Any):
        """Mock where query"""
        class MockQuery:
            def __init__(self, model_class, field, value):
                self.model_class = model_class
                self.field = field
                self.value = value
            
            def first(self):
                for item_id, data in self.model_class._test_data.items():
                    if data.get(self.field) == self.value:
                        model = self.model_class(data)
                        model._exists = True
                        return model
                return None
        
        return MockQuery(cls, field, value)


# Test Fixtures

@pytest.fixture(autouse=True)
def setup_test_data():
    """Setup test data before each test"""
    User._test_data = {
        1: {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'username': 'johndoe'},
        2: {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'username': 'janesmith'},
        3: {'id': 3, 'name': 'Bob Wilson', 'email': 'bob@example.com', 'username': 'bobwilson'}
    }
    
    Post._test_data = {
        1: {'id': 1, 'title': 'First Post', 'slug': 'first-post', 'user_id': 1, 'body': 'Content'},
        2: {'id': 2, 'title': 'Second Post', 'slug': 'second-post', 'user_id': 1, 'body': 'More content'},
        3: {'id': 3, 'title': 'Third Post', 'slug': 'third-post', 'user_id': 2, 'body': 'Even more'}
    }
    
    Product._test_data = {
        1: {'id': 1, 'name': 'Laptop', 'sku': 'LAP-001', 'price': 999.99},
        2: {'id': 2, 'name': 'Mouse', 'sku': 'MOU-001', 'price': 29.99},
        3: {'id': 3, 'name': 'Keyboard', 'sku': 'KEY-001', 'price': 79.99}
    }
    
    yield
    
    # Cleanup
    User._test_data = {}
    Post._test_data = {}
    Product._test_data = {}


@pytest.fixture
def binder():
    """Create model binder instance"""
    return ModelBinder()


# Tests

class TestImplicitBinding:
    """Test implicit route model binding"""
    
    def test_bind_by_primary_key(self, binder):
        """Test implicit binding by primary key"""
        result = binder.resolveImplicit(User, 1)
        
        assert isinstance(result, User)
        assert result.id == 1
        assert result.name == 'John Doe'
    
    def test_bind_by_custom_field(self, binder):
        """Test implicit binding by custom field"""
        result = binder.resolveImplicit(User, 'johndoe', field='username')
        
        assert isinstance(result, User)
        assert result.id == 1
        assert result.username == 'johndoe'
    
    def test_bind_uses_route_key_name(self, binder):
        """Test binding uses model's route key name"""
        result = binder.resolveImplicit(Post, 'first-post')
        
        assert isinstance(result, Post)
        assert result.slug == 'first-post'
        assert result.title == 'First Post'
    
    def test_bind_not_found_raises_exception(self, binder):
        """Test binding raises exception when model not found"""
        with pytest.raises(ModelNotFoundException) as exc_info:
            binder.resolveImplicit(User, 999)
        
        assert 'User' in str(exc_info.value)
        assert '999' in str(exc_info.value)
    
    def test_bind_different_model_types(self, binder):
        """Test binding works with different model types"""
        user = binder.resolveImplicit(User, 2)
        post = binder.resolveImplicit(Post, 'second-post')
        
        assert isinstance(user, User)
        assert isinstance(post, Post)
        assert user.id == 2
        assert post.slug == 'second-post'


class TestExplicitBinding:
    """Test explicit route model binding with callbacks"""
    
    def test_bind_with_custom_callback(self, binder):
        """Test explicit binding with custom callback"""
        def custom_resolver(value):
            # Find user by username
            return User.where('username', value).first()
        
        binder.bind('user', custom_resolver)
        
        result = binder.resolve('user', 'janesmith')
        
        assert isinstance(result, User)
        assert result.username == 'janesmith'
    
    def test_bind_with_model_method(self, binder):
        """Test explicit binding using model() method"""
        binder.model('user', User)
        
        result = binder.resolve('user', 1)
        
        assert isinstance(result, User)
        assert result.id == 1
    
    def test_bind_callback_not_found(self, binder):
        """Test explicit binding raises exception when callback returns None"""
        def always_none(value):
            return None
        
        binder.bind('user', always_none)
        
        with pytest.raises(ModelNotFoundException):
            binder.resolve('user', 1)
    
    def test_explicit_overrides_implicit(self, binder):
        """Test explicit binding takes precedence over implicit"""
        def custom_resolver(value):
            # Always return user 3 regardless of value
            return User.where('id', 3).first()
        
        binder.bind('user', custom_resolver)
        
        result = binder.resolve('user', 1, model_class=User)
        
        assert result.id == 3  # Custom resolver overrides


class TestCustomResolution:
    """Test custom resolution via resolveRouteBinding"""
    
    def test_model_custom_resolution(self, binder):
        """Test model's custom resolveRouteBinding method"""
        result = binder.resolveImplicit(Product, 'LAP-001', field='sku')
        
        assert isinstance(result, Product)
        assert result.sku == 'LAP-001'
        assert result.name == 'Laptop'
    
    def test_fallback_to_default_resolution(self, binder):
        """Test fallback to default resolution when field not specified"""
        result = binder.resolveImplicit(Product, 2)
        
        assert isinstance(result, Product)
        assert result.id == 2
        assert result.name == 'Mouse'


class TestBinderManagement:
    """Test binder configuration and management"""
    
    def test_has_binding(self, binder):
        """Test hasBinding checks for custom bindings"""
        assert not binder.hasBinding('user')
        
        binder.bind('user', lambda v: None)
        
        assert binder.hasBinding('user')
    
    def test_get_binding_callback(self, binder):
        """Test getBindingCallback retrieves callback"""
        callback = lambda v: User.where('id', v).first()
        binder.bind('user', callback)
        
        retrieved = binder.getBindingCallback('user')
        
        assert retrieved is callback
    
    def test_clear_bindings(self, binder):
        """Test clear removes all bindings"""
        binder.bind('user', lambda v: None)
        binder.bind('post', lambda v: None)
        
        assert binder.hasBinding('user')
        assert binder.hasBinding('post')
        
        binder.clear()
        
        assert not binder.hasBinding('user')
        assert not binder.hasBinding('post')
    
    def test_multiple_bindings(self, binder):
        """Test multiple parameter bindings"""
        binder.bind('user', lambda v: User.where('id', v).first())
        binder.bind('post', lambda v: Post.where('slug', v).first())
        
        user = binder.resolve('user', 1)
        post = binder.resolve('post', 'first-post')
        
        assert isinstance(user, User)
        assert isinstance(post, Post)


class TestResolveMethod:
    """Test the main resolve method"""
    
    def test_resolve_with_explicit_binding(self, binder):
        """Test resolve uses explicit binding when available"""
        binder.bind('user', lambda v: User.where('username', v).first())
        
        result = binder.resolve('user', 'johndoe')
        
        assert result.username == 'johndoe'
    
    def test_resolve_with_implicit_binding(self, binder):
        """Test resolve uses implicit binding"""
        result = binder.resolve('user', 1, model_class=User)
        
        assert result.id == 1
    
    def test_resolve_with_custom_field(self, binder):
        """Test resolve with custom field parameter"""
        result = binder.resolve('user', 'jane@example.com', model_class=User, field='email')
        
        assert result.email == 'jane@example.com'
    
    def test_resolve_without_binding_returns_none(self, binder):
        """Test resolve returns None when no binding configured"""
        result = binder.resolve('unknown', 'value')
        
        assert result is None


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_exception_contains_model_info(self, binder):
        """Test ModelNotFoundException contains useful info"""
        with pytest.raises(ModelNotFoundException) as exc_info:
            binder.resolveImplicit(User, 999)
        
        exc = exc_info.value
        assert exc.model_class == User
        assert exc.value == 999
        assert exc.field == 'id'
    
    def test_exception_with_custom_field(self, binder):
        """Test exception with custom field"""
        with pytest.raises(ModelNotFoundException) as exc_info:
            binder.resolveImplicit(User, 'nonexistent', field='username')
        
        exc = exc_info.value
        assert exc.field == 'username'
        assert exc.value == 'nonexistent'
    
    def test_string_id_coercion(self, binder):
        """Test binding works with string ID values"""
        result = binder.resolveImplicit(User, '1')
        
        assert result.id == 1


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_multiple_parameters_same_route(self, binder):
        """Test resolving multiple parameters from same route"""
        user = binder.resolve('user', 1, model_class=User)
        post = binder.resolve('post', 'first-post', model_class=Post)
        
        assert user.id == 1
        assert post.slug == 'first-post'
    
    def test_bind_with_validation_logic(self, binder):
        """Test binding with custom validation"""
        def validate_and_resolve(value):
            # Only allow admin users
            user = User.where('id', value).first()
            if user and user.email.endswith('@admin.com'):
                return user
            return None
        
        binder.bind('admin', validate_and_resolve)
        
        # Add admin user
        User._test_data[4] = {'id': 4, 'name': 'Admin', 'email': 'admin@admin.com', 'username': 'admin'}
        
        result = binder.resolve('admin', 4)
        assert result.email == 'admin@admin.com'
        
        with pytest.raises(ModelNotFoundException):
            binder.resolve('admin', 1)  # Not admin
    
    def test_case_insensitive_slug(self, binder):
        """Test binding with case-insensitive slug"""
        def case_insensitive(value):
            value_lower = value.lower()
            for post_id, data in Post._test_data.items():
                if data['slug'].lower() == value_lower:
                    model = Post(data)
                    model._exists = True
                    return model
            return None
        
        binder.bind('post', case_insensitive)
        
        result = binder.resolve('post', 'FIRST-POST')
        assert result.slug == 'first-post'
