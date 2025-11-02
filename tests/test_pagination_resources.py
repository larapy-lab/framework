import pytest
from unittest.mock import Mock
from larapy.http.resources import JsonResource, PaginatedResourceResponse


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


class MockPaginator:
    def __init__(self, items_list, current=1, per_page=15, total=100):
        self._items = items_list
        self._current = current
        self._per_page = per_page
        self._total = total
    
    def items(self):
        return self._items
    
    def current_page(self):
        return self._current
    
    def per_page(self):
        return self._per_page
    
    def total(self):
        return self._total
    
    def last_page(self):
        return (self._total + self._per_page - 1) // self._per_page
    
    def first_item(self):
        if not self._items:
            return None
        return (self._current - 1) * self._per_page + 1
    
    def last_item(self):
        if not self._items:
            return None
        return (self._current - 1) * self._per_page + len(self._items)
    
    def url(self, page):
        return f'/users?page={page}'
    
    def previous_page_url(self):
        if self._current <= 1:
            return None
        return self.url(self._current - 1)
    
    def next_page_url(self):
        if self._current >= self.last_page():
            return None
        return self.url(self._current + 1)


class TestPaginatedResourceResponse:
    def test_paginated_response_structure(self):
        users = [User(i, f'User {i}') for i in range(1, 16)]
        paginator = MockPaginator(users, current=1, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert 'data' in data
        assert 'links' in data
        assert 'meta' in data
    
    def test_links_generated_correctly(self):
        users = [User(i, f'User {i}') for i in range(1, 16)]
        paginator = MockPaginator(users, current=2, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['links']['first'] == '/users?page=1'
        assert data['links']['last'] == '/users?page=7'
        assert data['links']['prev'] == '/users?page=1'
        assert data['links']['next'] == '/users?page=3'
    
    def test_meta_data_correct(self):
        users = [User(i, f'User {i}') for i in range(1, 16)]
        paginator = MockPaginator(users, current=2, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['meta']['current_page'] == 2
        assert data['meta']['per_page'] == 15
        assert data['meta']['total'] == 100
        assert data['meta']['last_page'] == 7
        assert data['meta']['from'] == 16
        assert data['meta']['to'] == 30
    
    def test_first_page_links(self):
        users = [User(i, f'User {i}') for i in range(1, 16)]
        paginator = MockPaginator(users, current=1, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['links']['prev'] is None
        assert data['links']['next'] == '/users?page=2'
    
    def test_last_page_links(self):
        users = [User(i, f'User {i}') for i in range(1, 11)]
        paginator = MockPaginator(users, current=7, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['links']['prev'] == '/users?page=6'
        assert data['links']['next'] is None
    
    def test_middle_page_links(self):
        users = [User(i, f'User {i}') for i in range(1, 16)]
        paginator = MockPaginator(users, current=4, per_page=15, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['links']['prev'] == '/users?page=3'
        assert data['links']['next'] == '/users?page=5'
    
    def test_empty_paginator(self):
        paginator = MockPaginator([], current=1, per_page=15, total=0)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['data'] == []
        assert data['meta']['total'] == 0
    
    def test_custom_per_page(self):
        users = [User(i, f'User {i}') for i in range(1, 26)]
        paginator = MockPaginator(users, current=1, per_page=25, total=100)
        
        response = PaginatedResourceResponse(paginator, UserResource)
        data = response.to_response()
        
        assert data['meta']['per_page'] == 25
        assert len(data['data']) == 25
