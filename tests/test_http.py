"""
Tests for HTTP Foundation.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime
from larapy.http.request import Request
from larapy.http.response import (
    Response, JsonResponse, RedirectResponse,
    StreamedResponse, BinaryFileResponse,
    response, redirect, back
)
from larapy.http.uploaded_file import UploadedFile


class TestRequest:
    def test_request_initialization(self):
        req = Request('/users', 'GET')
        assert req.method() == 'GET'
        assert req.path() == 'users'

    def test_path_extraction(self):
        req = Request('/users/123/posts')
        assert req.path() == 'users/123/posts'

    def test_root_path(self):
        req = Request('/')
        assert req.path() == '/'

    def test_url_without_query(self):
        req = Request('/users?page=1', headers={'Host': 'example.com'})
        url = req.url()
        assert '/users' in url

    def test_full_url_with_query(self):
        req = Request('/users?page=1')
        assert '?page=1' in req.fullUrl()

    def test_full_url_with_added_query(self):
        req = Request('/users?page=1')
        url = req.fullUrlWithQuery({'sort': 'name'})
        assert 'page=1' in url
        assert 'sort=name' in url

    def test_full_url_without_query_params(self):
        req = Request('/users?page=1&sort=name')
        url = req.fullUrlWithoutQuery(['sort'])
        assert 'page=1' in url
        assert 'sort' not in url

    def test_is_path_matching(self):
        req = Request('/admin/users')
        assert req.is_('admin/*') is True
        assert req.is_('user/*') is False

    def test_route_is_matching(self):
        req = Request('/admin/users')
        req.setRouteParameters({'_route_name': 'admin.users.index'})
        assert req.routeIs('admin.*') is True
        assert req.routeIs('user.*') is False

    def test_host_retrieval(self):
        req = Request('/', headers={'Host': 'example.com'})
        assert req.host() == 'example.com'

    def test_http_host(self):
        req = Request('/', headers={'Host': 'example.com:8080'})
        assert req.httpHost() == 'example.com:8080'

    def test_scheme_and_http_host(self):
        req = Request('/', server={'HTTP_SCHEME': 'https'}, headers={'Host': 'example.com'})
        result = req.schemeAndHttpHost()
        assert 'https' in result
        assert 'example.com' in result

    def test_is_method(self):
        req = Request('/', 'POST')
        assert req.isMethod('post') is True
        assert req.isMethod('get') is False

    def test_header_access(self):
        req = Request('/', headers={'Content-Type': 'application/json'})
        assert req.header('Content-Type') == 'application/json'
        assert req.header('Missing', 'default') == 'default'

    def test_has_header(self):
        req = Request('/', headers={'Authorization': 'Bearer token'})
        assert req.hasHeader('Authorization') is True
        assert req.hasHeader('Missing') is False

    def test_bearer_token(self):
        req = Request('/', headers={'Authorization': 'Bearer abc123'})
        assert req.bearerToken() == 'abc123'

    def test_ip_address(self):
        req = Request('/', server={'REMOTE_ADDR': '192.168.1.1'})
        assert req.ip() == '192.168.1.1'

    def test_ips_with_forwarded(self):
        req = Request('/', 
                     server={'REMOTE_ADDR': '192.168.1.1'},
                     headers={'X-Forwarded-For': '10.0.0.1, 10.0.0.2'})
        ips = req.ips()
        assert '10.0.0.1' in ips
        assert '10.0.0.2' in ips
        assert '192.168.1.1' in ips

    def test_acceptable_content_types(self):
        req = Request('/', headers={'Accept': 'application/json, text/html'})
        types = req.getAcceptableContentTypes()
        assert 'application/json' in types
        assert 'text/html' in types

    def test_accepts_content_type(self):
        req = Request('/', headers={'Accept': 'application/json'})
        assert req.accepts(['application/json']) is True
        assert req.accepts(['text/html']) is False

    def test_prefers_content_type(self):
        req = Request('/', headers={'Accept': 'application/json, text/html'})
        assert req.prefers(['application/json', 'text/html']) == 'application/json'

    def test_expects_json(self):
        req = Request('/api/users', headers={'Accept': 'application/json'})
        assert req.expectsJson() is True

    def test_all_input(self):
        req = Request('/', query={'name': 'John'}, post={'email': 'john@example.com'})
        data = req.all()
        assert data['name'] == 'John'
        assert data['email'] == 'john@example.com'

    def test_input_retrieval(self):
        req = Request('/', query={'name': 'John', 'age': '30'})
        assert req.input('name') == 'John'
        assert req.input('missing', 'default') == 'default'

    def test_nested_input_with_dot_notation(self):
        req = Request('/', post={'user': {'name': 'John', 'email': 'john@example.com'}})
        assert req.input('user.name') == 'John'
        assert req.input('user.email') == 'john@example.com'

    def test_query_string_input(self):
        req = Request('/?page=1&sort=name', query={'page': '1', 'sort': 'name'})
        assert req.query('page') == '1'
        assert req.query('sort') == 'name'

    def test_string_input(self):
        req = Request('/', post={'name': 123})
        assert req.string('name') == '123'

    def test_integer_input(self):
        req = Request('/', post={'age': '30'})
        assert req.integer('age') == 30

    def test_boolean_input(self):
        req = Request('/', post={'active': '1', 'enabled': 'true'})
        assert req.boolean('active') is True
        assert req.boolean('enabled') is True
        assert req.boolean('missing', False) is False

    def test_array_input(self):
        req = Request('/', post={'tags': ['python', 'laravel']})
        assert req.array('tags') == ['python', 'laravel']

    def test_date_input(self):
        req = Request('/', post={'birthday': '1990-01-15'})
        date = req.date('birthday')
        assert isinstance(date, datetime)
        assert date.year == 1990

    def test_only_input(self):
        req = Request('/', post={'name': 'John', 'email': 'john@example.com', 'password': 'secret'})
        data = req.only('name', 'email')
        assert 'name' in data
        assert 'email' in data
        assert 'password' not in data

    def test_except_input(self):
        req = Request('/', post={'name': 'John', 'email': 'john@example.com', 'password': 'secret'})
        data = req.except_('password')
        assert 'name' in data
        assert 'email' in data
        assert 'password' not in data

    def test_has_input(self):
        req = Request('/', post={'name': 'John', 'email': 'john@example.com'})
        assert req.has('name') is True
        assert req.has(['name', 'email']) is True
        assert req.has('missing') is False

    def test_has_any(self):
        req = Request('/', post={'name': 'John'})
        assert req.hasAny(['name', 'email']) is True
        assert req.hasAny(['missing1', 'missing2']) is False

    def test_filled_input(self):
        req = Request('/', post={'name': 'John', 'empty': ''})
        assert req.filled('name') is True
        assert req.filled('empty') is False

    def test_is_not_filled(self):
        req = Request('/', post={'name': '', 'email': 'john@example.com'})
        assert req.isNotFilled('name') is True
        assert req.isNotFilled('email') is False

    def test_any_filled(self):
        req = Request('/', post={'name': '', 'email': 'john@example.com'})
        assert req.anyFilled(['name', 'email']) is True

    def test_missing_input(self):
        req = Request('/', post={'name': 'John'})
        assert req.missing('name') is False
        assert req.missing('email') is True

    def test_merge_input(self):
        req = Request('/', post={'name': 'John'})
        req.merge({'email': 'john@example.com'})
        assert req.input('email') == 'john@example.com'

    def test_merge_if_missing(self):
        req = Request('/', post={'name': 'John'})
        req.mergeIfMissing({'name': 'Jane', 'email': 'jane@example.com'})
        assert req.input('name') == 'John'
        assert req.input('email') == 'jane@example.com'

    def test_cookie_retrieval(self):
        req = Request('/', cookies={'session': 'abc123'})
        assert req.cookie('session') == 'abc123'
        assert req.hasCookie('session') is True

    def test_file_retrieval(self):
        req = Request('/', files={'photo': 'file_object'})
        assert req.file('photo') == 'file_object'
        assert req.hasFile('photo') is True

    def test_route_parameters(self):
        req = Request('/users/123')
        req.setRouteParameters({'id': '123', 'action': 'show'})
        assert req.route('id') == '123'
        assert req.route('action') == 'show'

    def test_session_access(self):
        req = Request('/')
        req.setSession({'user_id': 1, 'name': 'John'})
        assert req.session('user_id') == 1
        assert req.session('name') == 'John'

    def test_old_input(self):
        req = Request('/')
        req.setSession({'_old_input': {'name': 'John', 'email': 'john@example.com'}})
        assert req.old('name') == 'John'
        assert req.old('email') == 'john@example.com'

    def test_flash_input(self):
        req = Request('/', post={'name': 'John', 'email': 'john@example.com'})
        req.setSession({})
        req.flash()
        assert req.session('_old_input')['name'] == 'John'

    def test_flash_only(self):
        req = Request('/', post={'name': 'John', 'email': 'john@example.com', 'password': 'secret'})
        req.setSession({})
        req.flashOnly(['name', 'email'])
        old = req.session('_old_input')
        assert 'name' in old
        assert 'email' in old
        assert 'password' not in old

    def test_dynamic_property_access(self):
        req = Request('/', post={'name': 'John'})
        assert req.name == 'John'


class TestResponse:
    def test_response_initialization(self):
        res = Response('Hello World', 200)
        assert res.content() == 'Hello World'
        assert res.status() == 200

    def test_set_content(self):
        res = Response()
        res.setContent('Updated')
        assert res.content() == 'Updated'

    def test_set_status_code(self):
        res = Response()
        res.setStatusCode(404)
        assert res.status() == 404

    def test_add_header(self):
        res = Response()
        res.header('Content-Type', 'text/plain')
        assert res.getHeaders()['Content-Type'] == 'text/plain'

    def test_add_multiple_headers(self):
        res = Response()
        res.withHeaders({'Content-Type': 'text/plain', 'X-Custom': 'value'})
        headers = res.getHeaders()
        assert headers['Content-Type'] == 'text/plain'
        assert headers['X-Custom'] == 'value'

    def test_add_cookie(self):
        res = Response()
        res.cookie('session', 'abc123', 60)
        cookies = res.getCookies()
        assert len(cookies) == 1
        assert cookies[0]['name'] == 'session'
        assert cookies[0]['value'] == 'abc123'

    def test_remove_cookie(self):
        res = Response()
        res.cookie('session', 'abc123')
        res.withoutCookie('session')
        cookies = res.getCookies()
        expired = [c for c in cookies if c['name'] == 'session' and c['minutes'] == -1]
        assert len(expired) > 0

    def test_response_string_representation(self):
        res = Response('Test')
        assert str(res) == 'Test'


class TestJsonResponse:
    def test_json_response_creation(self):
        res = JsonResponse({'name': 'John', 'age': 30})
        assert res.status() == 200
        assert res.getHeaders()['Content-Type'] == 'application/json'

    def test_json_response_data(self):
        data = {'users': [{'id': 1, 'name': 'John'}]}
        res = JsonResponse(data)
        assert res.getData() == data

    def test_json_response_set_data(self):
        res = JsonResponse({'old': 'data'})
        res.setData({'new': 'data'})
        assert res.getData() == {'new': 'data'}

    def test_json_response_content(self):
        res = JsonResponse({'name': 'John'})
        content = str(res)
        assert 'name' in content
        assert 'John' in content


class TestRedirectResponse:
    def test_redirect_creation(self):
        res = RedirectResponse('/home')
        assert res.status() == 302
        assert res.getHeaders()['Location'] == '/home'

    def test_redirect_with_custom_status(self):
        res = RedirectResponse('/home', 301)
        assert res.status() == 301

    def test_redirect_target_url(self):
        res = RedirectResponse('/dashboard')
        assert res.getTargetUrl() == '/dashboard'

    def test_redirect_with_flash_data(self):
        res = RedirectResponse('/home')
        res.with_('status', 'Profile updated!')
        assert res.getSessionData()['status'] == 'Profile updated!'

    def test_redirect_with_input(self):
        res = RedirectResponse('/form')
        res.withInput({'name': 'John', 'email': 'john@example.com'})
        assert res.getSessionData()['_old_input']['name'] == 'John'


class TestResponseHelpers:
    def test_response_helper_with_string(self):
        res = response('Hello')
        assert isinstance(res, Response)
        assert res.content() == 'Hello'

    def test_response_helper_with_dict(self):
        res = response({'data': 'value'})
        assert isinstance(res, JsonResponse)

    def test_redirect_helper(self):
        res = redirect('/home')
        assert isinstance(res, RedirectResponse)
        assert res.getTargetUrl() == '/home'

    def test_back_helper(self):
        res = back()
        assert isinstance(res, RedirectResponse)


class TestUploadedFile:
    def test_uploaded_file_creation(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'test content')
            temp_path = f.name
        
        try:
            file = UploadedFile(temp_path, 'test.txt', 'text/plain', 12)
            assert file.getClientOriginalName() == 'test.txt'
            assert file.extension() == 'txt'
            assert file.getSize() == 12
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_is_valid(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            file = UploadedFile(temp_path, 'test.txt')
            assert file.isValid() is True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_move(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            temp_path = f.name
        
        try:
            file = UploadedFile(temp_path, 'test.txt')
            target_dir = tempfile.mkdtemp()
            new_path = file.move(target_dir, 'moved.txt')
            
            assert os.path.exists(new_path)
            assert 'moved.txt' in new_path
            
            if os.path.exists(new_path):
                os.unlink(new_path)
            if os.path.exists(target_dir):
                os.rmdir(target_dir)
        except:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_store(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            temp_path = f.name
        
        try:
            file = UploadedFile(temp_path, 'test.txt')
            target_dir = tempfile.mkdtemp()
            stored_path = file.store(target_dir)
            
            assert os.path.exists(stored_path)
            
            if os.path.exists(stored_path):
                os.unlink(stored_path)
            if os.path.exists(target_dir):
                os.rmdir(target_dir)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_store_as(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'content')
            temp_path = f.name
        
        try:
            file = UploadedFile(temp_path, 'test.txt')
            target_dir = tempfile.mkdtemp()
            stored_path = file.storeAs(target_dir, 'custom.txt')
            
            assert os.path.exists(stored_path)
            assert 'custom.txt' in stored_path
            
            if os.path.exists(stored_path):
                os.unlink(stored_path)
            if os.path.exists(target_dir):
                os.rmdir(target_dir)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestComplexScenarios:
    def test_api_request_with_json(self):
        req = Request(
            '/api/users',
            'POST',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            content='{"name": "John", "email": "john@example.com"}'
        )
        
        assert req.expectsJson() is True
        assert req.input('name') == 'John'
        assert req.input('email') == 'john@example.com'

    def test_form_submission_with_validation(self):
        req = Request(
            '/users',
            'POST',
            post={
                'name': 'John Doe',
                'email': 'john@example.com',
                'age': '30',
                'active': '1',
                'roles': ['admin', 'user']
            }
        )
        
        assert req.filled('name') is True
        assert req.string('name') == 'John Doe'
        assert req.integer('age') == 30
        assert req.boolean('active') is True
        assert req.array('roles') == ['admin', 'user']

    def test_paginated_api_request(self):
        req = Request(
            '/api/users?page=2&per_page=20&sort=name&filter[status]=active',
            'GET',
            query={
                'page': '2',
                'per_page': '20',
                'sort': 'name',
                'filter': {'status': 'active'}
            }
        )
        
        assert req.integer('page') == 2
        assert req.integer('per_page') == 20
        assert req.query('sort') == 'name'
        assert req.input('filter.status') == 'active'

    def test_file_upload_request(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b'fake image data')
            temp_path = f.name
        
        try:
            uploaded_file = UploadedFile(temp_path, 'photo.jpg', 'image/jpeg')
            
            req = Request(
                '/users/profile',
                'POST',
                post={'name': 'John Doe'},
                files={'photo': uploaded_file}
            )
            
            assert req.filled('name') is True
            assert req.hasFile('photo') is True
            
            file = req.file('photo')
            assert file.getClientOriginalName() == 'photo.jpg'
            assert file.isValid() is True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_redirect_with_validation_errors(self):
        res = RedirectResponse('/form')
        res.with_('errors', {
            'name': ['The name field is required.'],
            'email': ['The email must be a valid email address.']
        })
        res.withInput({'name': '', 'email': 'invalid'})
        
        session_data = res.getSessionData()
        assert 'errors' in session_data
        assert '_old_input' in session_data
        assert session_data['_old_input']['email'] == 'invalid'

    def test_json_api_response_with_nested_data(self):
        data = {
            'user': {
                'id': 1,
                'name': 'John Doe',
                'email': 'john@example.com',
                'profile': {
                    'bio': 'Software developer',
                    'location': 'San Francisco'
                }
            },
            'meta': {
                'timestamp': '2025-10-24T12:00:00Z'
            }
        }
        
        res = JsonResponse(data)
        res.header('X-API-Version', '1.0')
        
        assert res.status() == 200
        assert res.getData()['user']['name'] == 'John Doe'
        assert res.getHeaders()['Content-Type'] == 'application/json'
        assert res.getHeaders()['X-API-Version'] == '1.0'

    def test_authenticated_request_with_bearer_token(self):
        req = Request(
            '/api/profile',
            'GET',
            headers={
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
                'Accept': 'application/json'
            }
        )
        
        assert req.bearerToken() == 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        assert req.expectsJson() is True

    def test_complex_nested_input_access(self):
        req = Request(
            '/api/orders',
            'POST',
            content=json.dumps({
                'order': {
                    'items': [
                        {'product_id': 1, 'quantity': 2},
                        {'product_id': 2, 'quantity': 1}
                    ],
                    'shipping': {
                        'address': {
                            'street': '123 Main St',
                            'city': 'San Francisco',
                            'zip': '94102'
                        }
                    }
                }
            }),
            headers={'Content-Type': 'application/json'}
        )
        
        assert req.input('order.shipping.address.city') == 'San Francisco'
        assert req.input('order.shipping.address.zip') == '94102'
