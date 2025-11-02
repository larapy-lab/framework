import pytest
from larapy.auth.gate import Gate
from larapy.auth.policy import Policy
from larapy.auth.exceptions import AuthorizationException
from larapy.auth.middleware.authorize import AuthorizeMiddleware
from larapy.auth.authorizes_requests import AuthorizesRequests
from larapy.container import Container


class MockUser:
    def __init__(self, id):
        self.id = id


class MockPost:
    def __init__(self, user_id):
        self.user_id = user_id


class MockRequest:
    def __init__(self, user, container, route_params=None):
        self._user = user
        self.container = container
        self.route_params = route_params or {}
    
    def user(self):
        return self._user


class MockController(AuthorizesRequests):
    def __init__(self, container):
        self.container = container


class PostPolicy(Policy):
    def update(self, user, post):
        return user.id == post.user_id


class TestAuthorizeMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_authorizes_request(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {'post': post})
        middleware = AuthorizeMiddleware('update-post', 'post')
        
        called = []
        async def next_handler(req):
            called.append(True)
            return 'response'
        
        result = await middleware.handle(request, next_handler)
        
        assert called == [True]
        assert result == 'response'
    
    @pytest.mark.asyncio
    async def test_middleware_throws_exception_when_denied(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {'post': post})
        middleware = AuthorizeMiddleware('update-post', 'post')
        
        async def next_handler(req):
            return 'response'
        
        with pytest.raises(AuthorizationException):
            await middleware.handle(request, next_handler)
    
    @pytest.mark.asyncio
    async def test_middleware_passes_when_authorized(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {'post': post})
        middleware = AuthorizeMiddleware('update-post', 'post')
        
        result_called = []
        async def next_handler(req):
            result_called.append(True)
            return 'success'
        
        result = await middleware.handle(request, next_handler)
        
        assert result == 'success'
        assert result_called == [True]
    
    @pytest.mark.asyncio
    async def test_middleware_can_check_route_parameter(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('delete-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {'post': post})
        middleware = AuthorizeMiddleware('delete-post', 'post')
        
        async def next_handler(req):
            return 'deleted'
        
        result = await middleware.handle(request, next_handler)
        assert result == 'deleted'
    
    @pytest.mark.asyncio
    async def test_middleware_resolves_model_from_route(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post1 = MockPost(user_id=1)
        post2 = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request1 = MockRequest(user, container, {'post': post1})
        middleware = AuthorizeMiddleware('update-post', 'post')
        
        async def next_handler(req):
            return 'ok'
        
        result = await middleware.handle(request1, next_handler)
        assert result == 'ok'
        
        request2 = MockRequest(user, container, {'post': post2})
        with pytest.raises(AuthorizationException):
            await middleware.handle(request2, next_handler)
    
    @pytest.mark.asyncio
    async def test_middleware_works_with_policy(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {'post': post})
        middleware = AuthorizeMiddleware('update', 'post')
        
        async def next_handler(req):
            return 'updated'
        
        result = await middleware.handle(request, next_handler)
        assert result == 'updated'
    
    @pytest.mark.asyncio
    async def test_middleware_handles_missing_model(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        
        gate.define('view-dashboard', lambda user: True)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        request = MockRequest(user, container, {})
        middleware = AuthorizeMiddleware('view-dashboard')
        
        async def next_handler(req):
            return 'dashboard'
        
        result = await middleware.handle(request, next_handler)
        assert result == 'dashboard'


class TestAuthorizesRequests:
    def test_controller_can_authorize(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        controller.authorize('update-post', post)
    
    def test_controller_authorize_throws_exception(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        with pytest.raises(AuthorizationException):
            controller.authorize('update-post', post)
    
    def test_controller_authorize_for_user_works(self):
        container = Container()
        gate = Gate(container)
        user1 = MockUser(1)
        user2 = MockUser(2)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        with pytest.raises(AuthorizationException):
            controller.authorize_for_user(user1, 'update-post', post)
        
        controller.authorize_for_user(user2, 'update-post', post)
    
    def test_controller_can_method_returns_true_when_authorized(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        assert controller.can('update-post', post) is True
    
    def test_controller_can_method_returns_false_when_denied(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        assert controller.can('update-post', post) is False
    
    def test_controller_cannot_method_returns_true_when_denied(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        assert controller.cannot('update-post', post) is True
    
    def test_controller_cannot_method_returns_false_when_authorized(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        assert controller.cannot('update-post', post) is False
    
    def test_controller_works_with_policy(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        controller.authorize('update', post)
        assert controller.can('update', post) is True
    
    def test_controller_checks_multiple_abilities(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.define('delete-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        container.bind('gate', lambda c: gate)
        
        controller = MockController(container)
        
        assert controller.can('update-post', post) is True
        assert controller.can('delete-post', post) is True
    
    def test_controller_handles_missing_gate(self):
        container = Container()
        controller = MockController(container)
        
        with pytest.raises(Exception):
            controller.authorize('update-post', None)
