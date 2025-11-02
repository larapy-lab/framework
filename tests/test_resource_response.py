import pytest
import json
from unittest.mock import Mock
from larapy.http.resources import JsonResource, ResourceResponse


class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class UserResource(JsonResource):
    def to_array(self, request=None):
        return {
            'id': self.resource.id,
            'name': self.resource.name
        }


class TestResourceResponse:
    def test_to_response_returns_dict(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource)
        
        result = response.to_response()
        
        assert isinstance(result, dict)
        assert 'body' in result
        assert 'status' in result
        assert 'headers' in result
    
    def test_json_body_generated(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource)
        
        result = response.to_response()
        body = json.loads(result['body'])
        
        assert 'data' in body
        assert body['data']['id'] == 1
        assert body['data']['name'] == 'John Doe'
    
    def test_status_code_set(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource, status=201)
        
        result = response.to_response()
        
        assert result['status'] == 201
    
    def test_headers_included(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource, headers={'X-Custom-Header': 'value'})
        
        result = response.to_response()
        
        assert 'X-Custom-Header' in result['headers']
        assert result['headers']['X-Custom-Header'] == 'value'
    
    def test_content_type_header(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource)
        
        result = response.to_response()
        
        assert result['headers']['Content-Type'] == 'application/json'
    
    def test_custom_status_codes(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        
        response_404 = ResourceResponse(resource, status=404)
        assert response_404.to_response()['status'] == 404
        
        response_500 = ResourceResponse(resource, status=500)
        assert response_500.to_response()['status'] == 500
    
    def test_with_status_method(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource)
        
        response.with_status(204)
        result = response.to_response()
        
        assert result['status'] == 204
    
    def test_with_headers_method(self):
        user = User(1, 'John Doe')
        resource = UserResource(user)
        response = ResourceResponse(resource)
        
        response.with_headers({'X-RateLimit-Limit': '100', 'X-RateLimit-Remaining': '99'})
        result = response.to_response()
        
        assert result['headers']['X-RateLimit-Limit'] == '100'
        assert result['headers']['X-RateLimit-Remaining'] == '99'
