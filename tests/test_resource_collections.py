import pytest
from unittest.mock import Mock
from larapy.http.resources import JsonResource, ResourceCollection


class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


class UserResource(JsonResource):
    def to_array(self, request=None):
        return {
            'id': self.resource.id,
            'name': self.resource.name,
            'email': self.resource.email
        }


class TestResourceCollection:
    def test_to_dict_transforms_all_items(self):
        users = [
            User(1, 'John Doe', 'john@example.com'),
            User(2, 'Jane Smith', 'jane@example.com'),
            User(3, 'Bob Johnson', 'bob@example.com')
        ]
        
        collection = ResourceCollection(users, UserResource)
        data = collection.to_dict()
        
        assert len(data) == 3
        assert data[0]['id'] == 1
        assert data[0]['name'] == 'John Doe'
        assert data[1]['id'] == 2
        assert data[2]['id'] == 3
    
    def test_empty_collection_returns_empty_array(self):
        collection = ResourceCollection([], UserResource)
        data = collection.to_dict()
        
        assert data == []
        assert collection.is_empty()
    
    def test_with_adds_metadata_to_collection(self):
        users = [User(1, 'John Doe', 'john@example.com')]
        collection = ResourceCollection(users, UserResource)
        
        collection.with_info('meta', {'total': 100, 'page': 1})
        response = collection.to_response()
        
        assert 'meta' in response
        assert response['meta']['total'] == 100
        assert response['meta']['page'] == 1
    
    def test_additional_adds_extra_data(self):
        users = [User(1, 'John Doe', 'john@example.com')]
        collection = ResourceCollection(users, UserResource)
        
        collection.additional({'status': 'success', 'version': '1.0.0'})
        response = collection.to_response()
        
        assert response['status'] == 'success'
        assert response['version'] == '1.0.0'
    
    def test_custom_resource_class_in_collection(self):
        class CustomUserResource(JsonResource):
            def to_array(self, request=None):
                return {
                    'user_id': self.resource.id,
                    'full_name': self.resource.name
                }
        
        users = [User(1, 'John Doe', 'john@example.com')]
        collection = ResourceCollection(users, CustomUserResource)
        data = collection.to_dict()
        
        assert data[0]['user_id'] == 1
        assert data[0]['full_name'] == 'John Doe'
        assert 'id' not in data[0]
    
    def test_collection_to_response(self):
        users = [
            User(1, 'John Doe', 'john@example.com'),
            User(2, 'Jane Smith', 'jane@example.com')
        ]
        
        collection = ResourceCollection(users, UserResource)
        response = collection.to_response()
        
        assert 'data' in response
        assert len(response['data']) == 2
    
    def test_collection_without_wrapping(self):
        users = [User(1, 'John Doe', 'john@example.com')]
        
        ResourceCollection.without_wrapping()
        collection = ResourceCollection(users, UserResource)
        response = collection.to_response()
        
        assert 'data' in response
        
        ResourceCollection.wrap_with('data')
    
    def test_collection_count(self):
        users = [
            User(1, 'John', 'john@example.com'),
            User(2, 'Jane', 'jane@example.com'),
            User(3, 'Bob', 'bob@example.com')
        ]
        
        collection = ResourceCollection(users, UserResource)
        
        assert collection.count() == 3
    
    def test_none_resources_handled(self):
        collection = ResourceCollection(None, UserResource)
        
        assert collection.count() == 0
        assert collection.is_empty()
        assert collection.to_dict() == []
    
    def test_collection_without_resource_class(self):
        users = [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
        
        collection = ResourceCollection(users)
        data = collection.to_dict()
        
        assert len(data) == 2
        assert data[0]['id'] == 1
    
    def test_large_collection_handling(self):
        users = [User(i, f'User {i}', f'user{i}@example.com') for i in range(100)]
        
        collection = ResourceCollection(users, UserResource)
        data = collection.to_dict()
        
        assert len(data) == 100
        assert data[0]['id'] == 0
        assert data[99]['id'] == 99
    
    def test_collection_chaining_methods(self):
        users = [User(1, 'John Doe', 'john@example.com')]
        
        collection = (ResourceCollection(users, UserResource)
            .with_info('meta', {'page': 1})
            .additional({'status': 'success'}))
        
        response = collection.to_response()
        
        assert response['meta']['page'] == 1
        assert response['status'] == 'success'
