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


class TestRateLimitingIntegration:
    
    def setup_method(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
        self.middleware = ThrottleRequests(self.limiter)
    
    def test_rate_limiting_with_authentication(self):
        admin_request = Request(uri='/api/posts', method='POST', server={'REMOTE_ADDR': '127.0.0.1'})
        admin_request.user = lambda: {'id': 1, 'role': 'admin'}
        
        regular_request = Request(uri='/api/posts', method='POST', server={'REMOTE_ADDR': '127.0.0.1'})
        regular_request.user = lambda: {'id': 2, 'role': 'user'}
        
        def next_handler(req):
            return JsonResponse({'success': True}, 200)
        
        for i in range(5):
            admin_response = self.middleware.handle(admin_request, next_handler, 5, 1)
            assert admin_response.status() == 200
        
        admin_blocked = self.middleware.handle(admin_request, next_handler, 5, 1)
        assert admin_blocked.status() == 429
        
        regular_response = self.middleware.handle(regular_request, next_handler, 5, 1)
        assert regular_response.status() == 200
    
    def test_rate_limiting_with_api_routes(self):
        def api_routes_limiter(request):
            if '/api/public' in request.path():
                return Limit.per_minute(100)
            elif '/api/private' in request.path():
                return Limit.per_minute(10)
            return Limit.per_minute(60)
        
        self.limiter.for_rate('api_routes', api_routes_limiter)
        
        public_request = Request(uri='/api/public/data', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        private_request = Request(uri='/api/private/data', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return JsonResponse({'data': []}, 200)
        
        public_response = self.middleware.handle(public_request, next_handler, 'api_routes')
        assert public_response.status() == 200
        
        private_response = self.middleware.handle(private_request, next_handler, 'api_routes')
        assert private_response.status() == 200
    
    def test_rate_limiting_with_multiple_users(self):
        users = [{'id': i} for i in range(1, 6)]
        
        def next_handler(req):
            return Response('Success', 200)
        
        for user in users:
            request = Request(uri='/api/data', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
            request.user = lambda u=user: u
            
            for i in range(3):
                response = self.middleware.handle(request, next_handler, 3, 1)
                assert response.status() == 200
            
            blocked = self.middleware.handle(request, next_handler, 3, 1)
            assert blocked.status() == 429
    
    def test_rate_limiting_cascade(self):
        global_limiter = RateLimiter(self.cache)
        per_route_limiter = RateLimiter(self.cache)
        
        global_middleware = ThrottleRequests(global_limiter)
        route_middleware = ThrottleRequests(per_route_limiter)
        
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def final_handler(req):
            return Response('Success', 200)
        
        def route_handler(req):
            return route_middleware.handle(req, final_handler, 10, 1)
        
        response = global_middleware.handle(request, route_handler, 10, 1)
        assert response.status() == 200
    
    def test_rate_limiting_with_middleware_chain(self):
        def auth_middleware(request, next_handler):
            request.user = lambda: {'id': 123, 'authenticated': True}
            return next_handler(request)
        
        def logging_middleware(request, next_handler):
            response = next_handler(request)
            response.header('X-Request-Id', '12345')
            return response
        
        request = Request(uri='/api/create', method='POST', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def final_handler(req):
            return Response('Created', 201)
        
        def chain(req):
            return auth_middleware(req, lambda r: self.middleware.handle(r, lambda r2: logging_middleware(r2, final_handler), 3, 1))
        
        for i in range(3):
            response = chain(request)
            assert response.status() == 201
            assert 'X-Request-Id' in response.getHeaders()
        
        blocked_response = chain(request)
        assert blocked_response.status() == 429
    
    def test_rate_limiting_headers_in_response(self):
        request = Request(uri='/api/users', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            response = JsonResponse({'users': []}, 200)
            response.header('X-Custom', 'Value')
            return response
        
        response1 = self.middleware.handle(request, next_handler, 10, 1)
        
        headers = response1.getHeaders()
        assert headers['X-RateLimit-Limit'] == '10'
        assert headers['X-RateLimit-Remaining'] == '9'
        assert headers['X-Custom'] == 'Value'
        
        for i in range(9):
            self.middleware.handle(request, next_handler, 10, 1)
        
        response2 = self.middleware.handle(request, next_handler, 10, 1)
        headers2 = response2.getHeaders()
        
        assert response2.status() == 429
        assert 'Retry-After' in headers2
        assert 'X-RateLimit-Remaining' in headers2
        assert headers2['X-RateLimit-Remaining'] == '0'
    
    def test_rate_limiting_expires_correctly(self):
        request = Request(uri='/api/data', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        
        def next_handler(req):
            return Response('Success', 200)
        
        for i in range(3):
            response = self.middleware.handle(request, next_handler, 3, 0.016667)
            assert response.status() == 200
        
        blocked = self.middleware.handle(request, next_handler, 3, 0.016667)
        assert blocked.status() == 429
        
        retry_after = int(blocked.getHeaders()['Retry-After'])
        assert retry_after > 0
        
        time.sleep(1.1)
        
        response_after_wait = self.middleware.handle(request, next_handler, 3, 0.016667)
        assert response_after_wait.status() == 200
    
    def test_premium_vs_free_users(self):
        def tiered_limiter(request):
            user = None
            if hasattr(request, 'user') and callable(request.user):
                user = request.user()
            
            if user and isinstance(user, dict) and user.get('tier') == 'premium':
                return Limit.per_minute(1000).by(user['id'])
            
            user_id = user.get('id') if user and isinstance(user, dict) else 'guest'
            return Limit.per_minute(10).by(user_id)
        
        self.limiter.for_rate('tiered_api', tiered_limiter)
        
        premium_request = Request(uri='/api/data', method='GET', server={'REMOTE_ADDR': '127.0.0.1'})
        premium_request.user = lambda: {'id': 1, 'tier': 'premium'}
        
        free_request = Request(uri='/api/data', method='GET', server={'REMOTE_ADDR': '127.0.0.2'})
        free_request.user = lambda: {'id': 2, 'tier': 'free'}
        
        def next_handler(req):
            return JsonResponse({'data': []}, 200)
        
        for i in range(10):
            free_response = self.middleware.handle(free_request, next_handler, 'tiered_api')
            assert free_response.status() == 200
        
        free_blocked = self.middleware.handle(free_request, next_handler, 'tiered_api')
        assert free_blocked.status() == 429
        
        for i in range(50):
            premium_response = self.middleware.handle(premium_request, next_handler, 'tiered_api')
            assert premium_response.status() == 200
