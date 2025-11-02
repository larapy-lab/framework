import time
import pytest
from larapy.http.middleware.throttle_requests import ThrottleRequests
from larapy.cache.rate_limiter import RateLimiter, Limit
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse


class MockCache:
    
    def __init__(self):
        self.store = {}
    
    def add(self, key: str, value, seconds: int) -> bool:
        if key not in self.store:
            self.store[key] = {'value': value, 'expires': time.time() + seconds}
            return True
        return False
    
    def get(self, key: str, default=None):
        if key in self.store:
            item = self.store[key]
            if item['expires'] > time.time():
                return item['value']
            del self.store[key]
        return default
    
    def put(self, key: str, value, seconds: int):
        self.store[key] = {'value': value, 'expires': time.time() + seconds}
    
    def increment(self, key: str, amount: int = 1):
        current = self.get(key, 0)
        current_value = 0 if current is None else int(current)
        new_value = current_value + amount
        
        if key in self.store:
            self.store[key]['value'] = new_value
        
        return new_value
    
    def forget(self, key: str):
        if key in self.store:
            del self.store[key]
    
    def has(self, key: str) -> bool:
        if key in self.store:
            item = self.store[key]
            if item['expires'] > time.time():
                return True
            del self.store[key]
        return False
    
    def flush(self):
        self.store = {}


class TestThrottleRequests:
    
    def setup_method(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
        self.middleware = ThrottleRequests(self.limiter)
    
    def test_allows_requests_under_limit(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(5):
            response = self.middleware.handle(request, next_handler, 10, 1)
            assert response.status() == 200
    
    def test_blocks_requests_over_limit(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            response = self.middleware.handle(request, next_handler, 3, 1)
        
        response = self.middleware.handle(request, next_handler, 3, 1)
        assert response.status() == 429
    
    def test_adds_rate_limit_headers(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        response = self.middleware.handle(request, next_handler, 10, 1)
        
        headers = response.getHeaders()
        assert 'X-RateLimit-Limit' in headers
        assert headers['X-RateLimit-Limit'] == '10'
        assert 'X-RateLimit-Remaining' in headers
        assert headers['X-RateLimit-Remaining'] == '9'
    
    def test_429_response_includes_retry_after(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(2):
            self.middleware.handle(request, next_handler, 2, 1)
        
        response = self.middleware.handle(request, next_handler, 2, 1)
        
        headers = response.getHeaders()
        assert response.status() == 429
        assert 'Retry-After' in headers
        assert int(headers['Retry-After']) > 0
    
    def test_per_user_signature(self):
        request1 = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        request1.user = lambda: {'id': 1}
        
        request2 = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        request2.user = lambda: {'id': 2}
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            response1 = self.middleware.handle(request1, next_handler, 3, 1)
            assert response1.status() == 200
        
        response1_blocked = self.middleware.handle(request1, next_handler, 3, 1)
        assert response1_blocked.status() == 429
        
        response2 = self.middleware.handle(request2, next_handler, 3, 1)
        assert response2.status() == 200
    
    def test_per_ip_signature_for_guests(self):
        request1 = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '192.168.1.1'})
        request2 = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '192.168.1.2'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            self.middleware.handle(request1, next_handler, 3, 1)
        
        response1 = self.middleware.handle(request1, next_handler, 3, 1)
        assert response1.status() == 429
        
        response2 = self.middleware.handle(request2, next_handler, 3, 1)
        assert response2.status() == 200
    
    def test_json_response_for_api_requests(self):
        request = Request(uri='/api/users', method='GET', headers={'Accept': 'application/json'}, server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(5):
            self.middleware.handle(request, next_handler, 5, 1)
        
        response = self.middleware.handle(request, next_handler, 5, 1)
        
        assert response.status() == 429
        assert isinstance(response, JsonResponse)
    
    def test_html_response_for_web_requests(self):
        request = Request(uri='/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            self.middleware.handle(request, next_handler, 3, 1)
        
        response = self.middleware.handle(request, next_handler, 3, 1)
        
        assert response.status() == 429
        assert not isinstance(response, JsonResponse)
        assert response.content() == 'Too Many Attempts.'
    
    def test_custom_decay_minutes(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(2):
            self.middleware.handle(request, next_handler, 2, 2)
        
        response = self.middleware.handle(request, next_handler, 2, 2)
        
        headers = response.getHeaders()
        retry_after = int(headers['Retry-After'])
        
        assert retry_after > 60
        assert retry_after <= 120
    
    def test_named_limiter(self):
        def api_limiter(request):
            return Limit.per_minute(5)
        
        self.limiter.for_rate('api', api_limiter)
        
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(5):
            response = self.middleware.handle(request, next_handler, 'api')
            assert response.status() == 200
        
        response = self.middleware.handle(request, next_handler, 'api')
        assert response.status() == 429
    
    def test_named_limiter_with_custom_key(self):
        def user_limiter(request):
            user = request.user() if hasattr(request, 'user') else None
            user_id = user.get('id') if user else 'guest'
            return Limit.per_minute(10).by(user_id)
        
        self.limiter.for_rate('user_api', user_limiter)
        
        request = Request(uri='/api/profile', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        request.user = lambda: {'id': 42}
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(10):
            response = self.middleware.handle(request, next_handler, 'user_api')
            assert response.status() == 200
        
        response = self.middleware.handle(request, next_handler, 'user_api')
        assert response.status() == 429
    
    def test_reset_after_decay(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(2):
            self.middleware.handle(request, next_handler, 2, 0.016667)
        
        response1 = self.middleware.handle(request, next_handler, 2, 0.016667)
        assert response1.status() == 429
        
        time.sleep(1.1)
        
        response2 = self.middleware.handle(request, next_handler, 2, 0.016667)
        assert response2.status() == 200
    
    def test_concurrent_different_routes(self):
        request1 = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        request2 = Request(uri='/api/posts', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            self.middleware.handle(request1, next_handler, 3, 1)
        
        response1 = self.middleware.handle(request1, next_handler, 3, 1)
        assert response1.status() == 429
        
        response2 = self.middleware.handle(request2, next_handler, 3, 1)
        assert response2.status() == 200

