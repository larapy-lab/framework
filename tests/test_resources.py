import pytest
from unittest.mock import Mock
from larapy.http.resources import JsonResource, MissingValue


class User:
    def __init__(self, id, name, email, is_admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.is_admin = is_admin
        self.created_at = Mock()
        self.created_at.isoformat = Mock(return_value='2025-01-01T00:00:00')


class UserResource(JsonResource):
    def to_array(self, request=None):
        return {
            'id': self.resource.id,
            'name': self.resource.name,
            'email': self.resource.email,
            'created_at': self.resource.created_at.isoformat()
        }


class ConditionalUserResource(JsonResource):
    def to_array(self, request=None):
        return {
            'id': self.resource.id,
            'name': self.resource.name,
            'email': self.when(
                request and hasattr(request, 'user') and request.user.is_admin,
                self.resource.email
            ),
            'is_admin': self.when(
                request and hasattr(request, 'user') and request.user.is_admin,
                self.resource.is_admin
            )
        }


class TestJsonResource:
    def test_to_dict_returns_resource_data(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        data = resource.to_dict()
        
        assert data['id'] == 1
        assert data['name'] == 'John Doe'
        assert data['email'] == 'john@example.com'
        assert data['created_at'] == '2025-01-01T00:00:00'
    
    def test_to_array_custom_transformation(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        data = resource.to_array()
        
        assert 'id' in data
        assert 'name' in data
        assert 'email' in data
    
    def test_with_adds_metadata(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        resource.with_info('meta', {'version': '1.0.0'})
        response = resource.to_response()
        
        assert 'meta' in response
        assert response['meta']['version'] == '1.0.0'
    
    def test_additional_adds_extra_data(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        resource.additional({'status': 'success', 'message': 'User retrieved'})
        response = resource.to_response()
        
        assert response['status'] == 'success'
        assert response['message'] == 'User retrieved'
    
    def test_when_returns_value_if_true(self):
        user = User(1, 'John Doe', 'john@example.com', is_admin=True)
        request = Mock()
        request.user = Mock()
        request.user.is_admin = True
        
        resource = ConditionalUserResource(user)
        data = resource.to_dict(request)
        
        assert data['email'] == 'john@example.com'
        assert data['is_admin'] is True
    
    def test_when_returns_missing_value_if_false(self):
        user = User(1, 'John Doe', 'john@example.com', is_admin=True)
        request = Mock()
        request.user = Mock()
        request.user.is_admin = False
        
        resource = ConditionalUserResource(user)
        data = resource.to_dict(request)
        
        assert 'email' not in data
        assert 'is_admin' not in data
    
    def test_when_loaded_checks_relationship(self):
        user = User(1, 'John Doe', 'john@example.com')
        user.posts = [Mock(), Mock()]
        
        resource = UserResource(user)
        posts = resource.when_loaded('posts')
        
        assert posts is not None
        assert len(posts) == 2
    
    def test_when_loaded_returns_missing_if_not_loaded(self):
        user = User(1, 'John Doe', 'john@example.com')
        
        resource = UserResource(user)
        posts = resource.when_loaded('posts')
        
        assert isinstance(posts, MissingValue)
    
    def test_merge_combines_data(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        merged = resource.merge({'role': 'admin', 'status': 'active'})
        
        assert merged['id'] == 1
        assert merged['name'] == 'John Doe'
        assert merged['role'] == 'admin'
        assert merged['status'] == 'active'
    
    def test_merge_when_conditional_merge(self):
        user = User(1, 'John Doe', 'john@example.com', is_admin=True)
        resource = UserResource(user)
        
        merged = resource.merge_when(user.is_admin, {'admin_level': 5})
        
        assert 'admin_level' in merged
        assert merged['admin_level'] == 5
    
    def test_collection_creates_resource_collection(self):
        users = [
            User(1, 'John Doe', 'john@example.com'),
            User(2, 'Jane Smith', 'jane@example.com')
        ]
        
        collection = UserResource.collection(users)
        
        from larapy.http.resources import ResourceCollection
        assert isinstance(collection, ResourceCollection)
        assert collection.count() == 2
    
    def test_to_response_wraps_data(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = UserResource(user)
        
        response = resource.to_response()
        
        assert 'data' in response
        assert response['data']['id'] == 1
        assert response['data']['name'] == 'John Doe'
    
    def test_resource_without_to_array_uses_dict(self):
        user = User(1, 'John Doe', 'john@example.com')
        
        class SimpleResource(JsonResource):
            pass
        
        resource = SimpleResource(user)
        data = resource.to_dict()
        
        assert 'id' in data
        assert 'name' in data
        assert 'email' in data
    
    def test_null_resource_handling(self):
        class SimpleResource(JsonResource):
            pass
        
        resource = SimpleResource(None)
        data = resource.to_dict()
        
        assert data == {}
    
    def test_without_wrapping(self):
        user = User(1, 'John Doe', 'john@example.com')
        
        class CustomResource(JsonResource):
            def to_array(self, request=None):
                return {'id': self.resource.id, 'name': self.resource.name}
        
        CustomResource.without_wrapping()
        resource = CustomResource(user)
        response = resource.to_response()
        
        assert 'id' in response
        assert 'data' not in response
        
        CustomResource.wrap_with('data')
