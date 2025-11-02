"""
Tests for CSRF Token Verification Middleware

Comprehensive test suite covering CSRF token generation, validation,
and exception handling.
"""

import pytest
from larapy.http.middleware.verify_csrf_token import VerifyCsrfToken
from larapy.http.middleware.trim_strings import TrimStrings
from larapy.http.middleware.convert_empty_strings_to_null import ConvertEmptyStringsToNull
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse
from larapy.http.kernel import Kernel
from larapy.session.store import Store


class MockSession:
    """Mock session for testing."""
    
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def put(self, key, value):
        self.data[key] = value
    
    def has(self, key):
        return key in self.data


class TestCsrfTokenGeneration:
    """Test CSRF token generation."""
    
    def test_token_generation_creates_unique_tokens(self):
        middleware = VerifyCsrfToken()
        
        token1 = middleware._generate_token()
        token2 = middleware._generate_token()
        
        assert token1 != token2
        assert len(token1) > 32
        assert len(token2) > 32
    
    def test_token_added_to_request_without_session(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'GET')
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert hasattr(request, '_csrf_token')
        assert request._csrf_token is not None
    
    def test_token_stored_in_session(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'GET')
        session = MockSession()
        request.setSession(session)
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert session.has('_token')
        assert request._csrf_token == session.get('_token')
    
    def test_existing_token_loaded_from_session(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'GET')
        session = MockSession()
        session.put('_token', 'existing-token-12345')
        request.setSession(session)
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request._csrf_token == 'existing-token-12345'


class TestCsrfTokenValidation:
    """Test CSRF token validation."""
    
    def test_get_request_not_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'GET')
        
        # No token should be required for GET
        assert not middleware._should_verify(request)
    
    def test_post_request_should_be_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        
        assert middleware._should_verify(request)
    
    def test_put_request_should_be_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'PUT')
        
        assert middleware._should_verify(request)
    
    def test_patch_request_should_be_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'PATCH')
        
        assert middleware._should_verify(request)
    
    def test_delete_request_should_be_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'DELETE')
        
        assert middleware._should_verify(request)
    
    def test_valid_token_passes_verification(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token-123')
        request.setSession(session)
        request.merge({'_token': 'valid-token-123'})
        
        assert middleware._tokens_match(request)
    
    def test_invalid_token_fails_verification(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token-123')
        request.setSession(session)
        request.merge({'_token': 'invalid-token-456'})
        
        assert not middleware._tokens_match(request)
    
    def test_missing_token_fails_verification(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token-123')
        request.setSession(session)
        
        assert not middleware._tokens_match(request)
    
    def test_token_in_header_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token-123')
        request.setSession(session)
        request.set_header('X-CSRF-TOKEN', 'valid-token-123')
        
        assert middleware._tokens_match(request)
    
    def test_token_in_xsrf_header_verified(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token-123')
        request.setSession(session)
        request.set_header('X-XSRF-TOKEN', 'valid-token-123')
        
        assert middleware._tokens_match(request)


class TestCsrfExclusions:
    """Test CSRF exclusion rules."""
    
    def test_excluded_uri_not_verified(self):
        middleware = VerifyCsrfToken()
        middleware._except = ['/api/webhook']
        
        request = Request('/api/webhook', 'POST')
        
        assert not middleware._should_verify(request)
    
    def test_wildcard_exclusion(self):
        middleware = VerifyCsrfToken()
        middleware._except = ['/api/*']
        
        request1 = Request('/api/users', 'POST')
        request2 = Request('/api/posts/create', 'POST')
        
        assert not middleware._should_verify(request1)
        assert not middleware._should_verify(request2)
    
    def test_dynamic_exclusion(self):
        middleware = VerifyCsrfToken()
        middleware.except_uris(['/webhook/stripe', '/webhook/paypal'])
        
        request1 = Request('/webhook/stripe', 'POST')
        request2 = Request('/webhook/paypal', 'POST')
        request3 = Request('/checkout', 'POST')
        
        assert not middleware._should_verify(request1)
        assert not middleware._should_verify(request2)
        assert middleware._should_verify(request3)


class TestCsrfErrorHandling:
    """Test CSRF error responses."""
    
    def test_token_mismatch_returns_419(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token')
        request.setSession(session)
        request.merge({'_token': 'invalid-token'})
        
        def next_handler(req):
            return Response('Should not reach here')
        
        response = middleware.handle(request, next_handler)
        
        assert response.status() == 419
    
    def test_ajax_token_mismatch_returns_json(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token')
        request.setSession(session)
        request.merge({'_token': 'invalid-token'})
        request.set_header('X-Requested-With', 'XMLHttpRequest')
        
        def next_handler(req):
            return Response('Should not reach here')
        
        response = middleware.handle(request, next_handler)
        
        assert isinstance(response, JsonResponse)
        assert response.status() == 419
        assert 'CSRF token mismatch' in response.getData()['message']
    
    def test_valid_token_continues_to_handler(self):
        middleware = VerifyCsrfToken()
        request = Request('/', 'POST')
        session = MockSession()
        session.put('_token', 'valid-token')
        request.setSession(session)
        request.merge({'_token': 'valid-token'})
        
        called = False
        
        def next_handler(req):
            nonlocal called
            called = True
            return Response('Success')
        
        response = middleware.handle(request, next_handler)
        
        assert called
        assert response.status() == 200


class TestTrimStringsMiddleware:
    """Test TrimStrings middleware."""
    
    def test_trims_string_inputs(self):
        middleware = TrimStrings()
        request = Request('/')
        request.merge({
            'name': '  John Doe  ',
            'email': 'john@example.com  ',
            'bio': '  Developer  '
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('name') == 'John Doe'
        assert request.input('email') == 'john@example.com'
        assert request.input('bio') == 'Developer'
    
    def test_excludes_password_fields(self):
        middleware = TrimStrings()
        request = Request('/')
        request.merge({
            'username': '  john  ',
            'password': '  secret  ',
            'password_confirmation': '  secret  '
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('username') == 'john'
        assert request.input('password') == '  secret  '
        assert request.input('password_confirmation') == '  secret  '
    
    def test_custom_exclusions(self):
        middleware = TrimStrings()
        middleware.except_keys(['api_key', 'secret'])
        
        request = Request('/')
        request.merge({
            'name': '  John  ',
            'api_key': '  secret-key  ',
            'secret': '  token  '
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('name') == 'John'
        assert request.input('api_key') == '  secret-key  '
        assert request.input('secret') == '  token  '
    
    def test_trims_nested_strings(self):
        middleware = TrimStrings()
        request = Request('/')
        request.merge({
            'user': {
                'name': '  John  ',
                'email': '  john@example.com  '
            },
            'tags': ['  python  ', '  web  ', '  framework  ']
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('user')['name'] == 'John'
        assert request.input('user')['email'] == 'john@example.com'
        assert request.input('tags') == ['python', 'web', 'framework']


class TestConvertEmptyStringsMiddleware:
    """Test ConvertEmptyStringsToNull middleware."""
    
    def test_converts_empty_strings_to_none(self):
        middleware = ConvertEmptyStringsToNull()
        request = Request('/')
        request.merge({
            'name': 'John',
            'bio': '',
            'company': '',
            'email': 'john@example.com'
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('name') == 'John'
        assert request.input('bio') is None
        assert request.input('company') is None
        assert request.input('email') == 'john@example.com'
    
    def test_custom_exclusions(self):
        middleware = ConvertEmptyStringsToNull()
        middleware.except_keys(['notes', 'description'])
        
        request = Request('/')
        request.merge({
            'title': 'Post',
            'notes': '',
            'description': '',
            'content': ''
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('title') == 'Post'
        assert request.input('notes') == ''
        assert request.input('description') == ''
        assert request.input('content') is None
    
    def test_converts_nested_empty_strings(self):
        middleware = ConvertEmptyStringsToNull()
        request = Request('/')
        request.merge({
            'user': {
                'name': 'John',
                'bio': '',
                'company': ''
            },
            'tags': ['python', '', 'web']
        })
        
        def next_handler(req):
            return Response('OK')
        
        middleware.handle(request, next_handler)
        
        assert request.input('user')['name'] == 'John'
        assert request.input('user')['bio'] is None
        assert request.input('user')['company'] is None
        assert request.input('tags') == ['python', None, 'web']


class TestMiddlewareIntegration:
    """Test middleware integration with Kernel."""
    
    def test_csrf_with_trim_strings_pipeline(self):
        kernel = Kernel()
        csrf = VerifyCsrfToken()
        trim = TrimStrings()
        
        kernel.use([trim, csrf])
        
        request = Request('/', 'POST')
        session = MockSession()
        request.setSession(session)
        
        # First request establishes token
        def handler1(req):
            return Response('OK')
        
        response1 = kernel.handle(request, handler1)
        token = request._csrf_token
        
        # Second request with trimmed token
        request2 = Request('/', 'POST')
        request2.setSession(session)
        request2.merge({'_token': f'  {token}  ', 'name': '  John  '})
        
        def handler2(req):
            assert req.input('name') == 'John'
            return Response('Success')
        
        response2 = kernel.handle(request2, handler2)
        assert response2.status() == 200
    
    def test_full_middleware_stack(self):
        kernel = Kernel()
        trim = TrimStrings()
        convert = ConvertEmptyStringsToNull()
        csrf = VerifyCsrfToken()
        
        kernel.use([trim, convert, csrf])
        
        request = Request('/', 'POST')
        session = MockSession()
        request.setSession(session)
        
        # Establish token
        def handler1(req):
            return Response('OK')
        
        kernel.handle(request, handler1)
        token = request._csrf_token
        
        # Submit with trimming and empty string conversion
        request2 = Request('/', 'POST')
        request2.setSession(session)
        request2.merge({
            '_token': token,
            'name': '  John Doe  ',
            'bio': '',
            'email': '  john@example.com  '
        })
        
        def handler2(req):
            assert req.input('name') == 'John Doe'
            assert req.input('bio') is None
            assert req.input('email') == 'john@example.com'
            return Response('Success')
        
        response = kernel.handle(request2, handler2)
        assert response.status() == 200


class TestRequestCsrfMethods:
    """Test CSRF token methods on Request class."""
    
    def test_csrf_token_getter(self):
        request = Request('/')
        request._csrf_token = 'test-token-123'
        
        assert request.csrf_token() == 'test-token-123'
    
    def test_csrf_token_from_session(self):
        request = Request('/')
        session = MockSession()
        session.put('_token', 'session-token-456')
        request.setSession(session)
        
        assert request.csrf_token() == 'session-token-456'
    
    def test_set_csrf_token(self):
        request = Request('/')
        session = MockSession()
        request.setSession(session)
        
        request.set_csrf_token('new-token-789')
        
        assert request._csrf_token == 'new-token-789'
        assert session.get('_token') == 'new-token-789'
    
    def test_csrf_token_returns_none_when_missing(self):
        request = Request('/')
        
        assert request.csrf_token() is None


class TestPerformance:
    """Test middleware performance."""
    
    def test_middleware_overhead_minimal(self):
        import time
        
        kernel = Kernel()
        csrf = VerifyCsrfToken()
        trim = TrimStrings()
        convert = ConvertEmptyStringsToNull()
        
        kernel.use([trim, convert, csrf])
        
        request = Request('/', 'GET')
        session = MockSession()
        request.setSession(session)
        request.merge({
            'name': '  John  ',
            'bio': '',
            'tags': ['  python  ', '  web  ']
        })
        
        def handler(req):
            return Response('OK')
        
        # Warm up
        kernel.handle(request, handler)
        
        # Measure 100 requests
        start = time.time()
        for _ in range(100):
            kernel.handle(request, handler)
        duration = time.time() - start
        
        # Should be under 5ms per request on average
        avg_per_request = (duration / 100) * 1000
        assert avg_per_request < 5.0, f"Average {avg_per_request:.2f}ms exceeds 5ms target"
