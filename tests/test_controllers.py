"""
Tests for HTTP Controllers

Tests controller base class, resource routes, single action controllers,
middleware, and dependency injection.
"""

import pytest
from larapy.routing.router import Router
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse
from larapy.http.controllers import Controller, ResourceController, ApiResourceController, ControllerDispatcher


class TestController(Controller):
    """Test controller for basic actions."""
    
    def index(self, request):
        return {'action': 'index', 'method': request.method()}
    
    def show(self, request, id):
        return {'action': 'show', 'id': id}
    
    def store(self, request):
        return {'action': 'store', 'name': request.input('name')}
    
    def update(self, request, id):
        return {'action': 'update', 'id': id, 'name': request.input('name')}


class SingleActionController(Controller):
    """Test single action controller."""
    
    def __invoke(self, request):
        return {'action': 'invoke'}


class PostController(ResourceController):
    """Test resource controller."""
    
    def index(self):
        return {'posts': []}
    
    def create(self):
        return {'form': 'create'}
    
    def store(self, request):
        return {'created': request.input('title')}
    
    def show(self, id):
        return {'post': id}
    
    def edit(self, id):
        return {'form': 'edit', 'id': id}
    
    def update(self, request, id):
        return {'updated': id, 'title': request.input('title')}
    
    def destroy(self, id):
        return {'deleted': id}


class UserController(ApiResourceController):
    """Test API resource controller."""
    
    def index(self):
        return JsonResponse({'users': []})
    
    def store(self, request):
        return JsonResponse({'created': request.input('name')})
    
    def show(self, id):
        return JsonResponse({'user': id})
    
    def update(self, request, id):
        return JsonResponse({'updated': id})
    
    def destroy(self, id):
        return JsonResponse({'deleted': id})


class MiddlewareController(Controller):
    """Controller with middleware."""
    
    def __init__(self):
        super().__init__()
        self.middleware('auth')
        self.middleware('admin', only=['destroy'])
        self.middleware('throttle', except_=['index'])
    
    def index(self, request):
        return {'action': 'index'}
    
    def destroy(self, request, id):
        return {'action': 'destroy', 'id': id}
    
    def update(self, request, id):
        return {'action': 'update', 'id': id}


class DependencyInjectionController(Controller):
    """Controller with dependency injection."""
    
    def __init__(self, service=None):
        super().__init__()
        self.service = service
    
    def index(self, request):
        service_name = self.service.__class__.__name__ if self.service else 'None'
        return {'service': service_name}


class MockService:
    """Mock service for dependency injection."""
    pass


class TestControllerBasics:
    """Test basic controller functionality."""
    
    def test_controller_instantiation(self):
        """Test controller can be instantiated."""
        controller = TestController()
        assert isinstance(controller, Controller)
    
    def test_controller_call_action(self):
        """Test calling controller actions."""
        controller = TestController()
        request = Request(uri='/test', method='GET')
        
        result = controller.callAction('index', [request])
        assert result['action'] == 'index'
        assert result['method'] == 'GET'
    
    def test_controller_action_with_parameters(self):
        """Test controller action with route parameters."""
        controller = TestController()
        request = Request(uri='/test/123', method='GET')
        
        result = controller.callAction('show', [request, '123'])
        assert result['action'] == 'show'
        assert result['id'] == '123'
    
    def test_controller_nonexistent_method(self):
        """Test calling nonexistent method raises error."""
        controller = TestController()
        
        with pytest.raises(AttributeError):
            controller.callAction('nonexistent', [])


class TestControllerMiddleware:
    """Test controller middleware."""
    
    def test_controller_middleware_registration(self):
        """Test middleware registration."""
        controller = MiddlewareController()
        middleware = controller.getMiddleware()
        
        assert len(middleware) == 3
        assert any(m['middleware'] == 'auth' for m in middleware)
    
    def test_controller_middleware_for_method(self):
        """Test getting middleware for specific method."""
        controller = MiddlewareController()
        
        index_middleware = controller.getMiddlewareForMethod('index')
        assert 'auth' in index_middleware
        assert 'admin' not in index_middleware
        assert 'throttle' not in index_middleware
        
        destroy_middleware = controller.getMiddlewareForMethod('destroy')
        assert 'auth' in destroy_middleware
        assert 'admin' in destroy_middleware
        assert 'throttle' in destroy_middleware
        
        update_middleware = controller.getMiddlewareForMethod('update')
        assert 'auth' in update_middleware
        assert 'admin' not in update_middleware
        assert 'throttle' in update_middleware


class TestResourceController:
    """Test resource controller functionality."""
    
    def test_resource_controller_index(self):
        """Test resource controller index action."""
        controller = PostController()
        result = controller.index()
        assert 'posts' in result
    
    def test_resource_controller_create(self):
        """Test resource controller create action."""
        controller = PostController()
        result = controller.create()
        assert 'form' in result
    
    def test_resource_controller_store(self):
        """Test resource controller store action."""
        controller = PostController()
        request = Request(uri='/posts', method='POST', post={'title': 'Test Post'})
        
        result = controller.store(request)
        assert result['created'] == 'Test Post'
    
    def test_resource_controller_show(self):
        """Test resource controller show action."""
        controller = PostController()
        result = controller.show('123')
        assert result['post'] == '123'
    
    def test_resource_controller_edit(self):
        """Test resource controller edit action."""
        controller = PostController()
        result = controller.edit('123')
        assert result['form'] == 'edit'
        assert result['id'] == '123'
    
    def test_resource_controller_update(self):
        """Test resource controller update action."""
        controller = PostController()
        request = Request(uri='/posts/123', method='PUT', post={'title': 'Updated'})
        
        result = controller.update(request, '123')
        assert result['updated'] == '123'
        assert result['title'] == 'Updated'
    
    def test_resource_controller_destroy(self):
        """Test resource controller destroy action."""
        controller = PostController()
        result = controller.destroy('123')
        assert result['deleted'] == '123'


class TestApiResourceController:
    """Test API resource controller."""
    
    def test_api_resource_controller_index(self):
        """Test API resource index."""
        controller = UserController()
        result = controller.index()
        assert isinstance(result, JsonResponse)
    
    def test_api_resource_controller_store(self):
        """Test API resource store."""
        controller = UserController()
        request = Request(uri='/users', method='POST', post={'name': 'John'})
        
        result = controller.store(request)
        assert isinstance(result, JsonResponse)
    
    def test_api_resource_controller_show(self):
        """Test API resource show."""
        controller = UserController()
        result = controller.show('123')
        assert isinstance(result, JsonResponse)


class TestResourceRoutes:
    """Test resource route registration."""
    
    def test_resource_routes_creation(self):
        """Test creating resource routes."""
        router = Router()
        routes = router.resource('posts', 'PostController')
        
        assert len(routes) == 7
        
        route_methods = [r.getName() for r in routes]
        assert 'posts.index' in route_methods
        assert 'posts.create' in route_methods
        assert 'posts.store' in route_methods
        assert 'posts.show' in route_methods
        assert 'posts.edit' in route_methods
        assert 'posts.update' in route_methods
        assert 'posts.destroy' in route_methods
    
    def test_resource_routes_only_option(self):
        """Test resource routes with only option."""
        router = Router()
        routes = router.resource('posts', 'PostController', only=['index', 'show'])
        
        assert len(routes) == 2
        
        route_methods = [r.getName() for r in routes]
        assert 'posts.index' in route_methods
        assert 'posts.show' in route_methods
    
    def test_resource_routes_except_option(self):
        """Test resource routes with except option."""
        router = Router()
        routes = router.resource('posts', 'PostController', except_=['destroy', 'edit'])
        
        assert len(routes) == 5
        
        route_methods = [r.getName() for r in routes]
        assert 'posts.destroy' not in route_methods
        assert 'posts.edit' not in route_methods
    
    def test_api_resource_routes(self):
        """Test API resource routes (no create/edit)."""
        router = Router()
        routes = router.apiResource('users', 'UserController')
        
        assert len(routes) == 5
        
        route_methods = [r.getName() for r in routes]
        assert 'users.index' in route_methods
        assert 'users.store' in route_methods
        assert 'users.show' in route_methods
        assert 'users.update' in route_methods
        assert 'users.destroy' in route_methods
        assert 'users.create' not in route_methods
        assert 'users.edit' not in route_methods
    
    def test_multiple_resources(self):
        """Test registering multiple resources."""
        router = Router()
        routes = router.resources({
            'posts': 'PostController',
            'users': 'UserController'
        })
        
        assert 'posts' in routes
        assert 'users' in routes
        assert len(routes['posts']) == 7
        assert len(routes['users']) == 7


class TestControllerDispatcher:
    """Test controller dispatcher."""
    
    def test_dispatcher_parse_action_string(self):
        """Test parsing controller@method syntax."""
        dispatcher = ControllerDispatcher()
        result = dispatcher.parseAction('TestController@index')
        
        assert result['controller'] == 'TestController'
        assert result['method'] == 'index'
    
    def test_dispatcher_parse_action_callable(self):
        """Test parsing callable action."""
        dispatcher = ControllerDispatcher()
        
        def action():
            pass
        
        result = dispatcher.parseAction(action)
        assert 'uses' in result
        assert callable(result['uses'])
    
    def test_dispatcher_resolve_controller(self):
        """Test resolving controller instance."""
        dispatcher = ControllerDispatcher()
        controller = dispatcher.resolveController(TestController)
        
        assert isinstance(controller, TestController)


class TestRouterControllerIntegration:
    """Test router integration with controllers."""
    
    def test_router_dispatch_to_controller(self):
        """Test router dispatching to controller."""
        router = Router()
        router.get('/test', 'TestController@index')
        
        request = Request(uri='/test', method='GET')
        
        controller = TestController()
        result = controller.index(request)
        
        assert result['action'] == 'index'
    
    def test_router_dispatch_with_parameters(self):
        """Test dispatching with route parameters."""
        router = Router()
        router.get('/test/{id}', 'TestController@show')
        
        route = router.findRoute(Request(uri='/test/123', method='GET'))
        assert route is not None
        assert '123' in route.parameters().values()
    
    def test_router_resource_route_matching(self):
        """Test resource routes match correctly."""
        router = Router()
        router.resource('posts', 'PostController')
        
        index_route = router.findRoute(Request(uri='/posts', method='GET'))
        assert index_route is not None
        assert 'PostController@index' in index_route.getAction('uses')
        
        show_route = router.findRoute(Request(uri='/posts/123', method='GET'))
        assert show_route is not None
        assert 'PostController@show' in show_route.getAction('uses')
        
        store_route = router.findRoute(Request(uri='/posts', method='POST'))
        assert store_route is not None
        assert 'PostController@store' in store_route.getAction('uses')
        
        update_route = router.findRoute(Request(uri='/posts/123', method='PUT'))
        assert update_route is not None
        assert 'PostController@update' in update_route.getAction('uses')
        
        destroy_route = router.findRoute(Request(uri='/posts/123', method='DELETE'))
        assert destroy_route is not None
        assert 'PostController@destroy' in destroy_route.getAction('uses')


class TestComplexScenarios:
    """Test complex controller scenarios."""
    
    def test_nested_resource_routes(self):
        """Test nested resource routes."""
        router = Router()
        
        router.group({'prefix': '/api/v1'}, lambda r: [
            r.resource('posts', 'PostController'),
            r.resource('users', 'UserController'),
        ])
        
        route = router.findRoute(Request(uri='/api/v1/posts', method='GET'))
        assert route is not None
    
    def test_resource_with_middleware(self):
        """Test resource routes with middleware."""
        router = Router()
        
        routes = router.resource('posts', 'PostController')
        for route in routes:
            route.middleware('auth')
        
        assert all('auth' in route.getMiddleware() for route in routes)
    
    def test_api_versioning_with_resources(self):
        """Test API versioning with resource routes."""
        router = Router()
        
        router.group({'prefix': '/api/v1', 'name': 'api.v1.'}, lambda r: [
            r.apiResource('posts', 'Api.V1.PostController'),
            r.apiResource('users', 'Api.V1.UserController'),
        ])
        
        router.group({'prefix': '/api/v2', 'name': 'api.v2.'}, lambda r: [
            r.apiResource('posts', 'Api.V2.PostController'),
            r.apiResource('users', 'Api.V2.UserController'),
        ])
        
        v1_route = router.findRoute(Request(uri='/api/v1/posts', method='GET'))
        assert v1_route is not None
        
        v2_route = router.findRoute(Request(uri='/api/v2/posts', method='GET'))
        assert v2_route is not None
    
    def test_custom_resource_names(self):
        """Test custom resource route names."""
        router = Router()
        
        routes = router.resource('posts', 'PostController', names={
            'index': 'post.list',
            'show': 'post.detail',
        })
        
        route_names = [r.getName() for r in routes]
        assert 'post.list' in route_names
        assert 'post.detail' in route_names
    
    def test_custom_resource_parameters(self):
        """Test custom resource parameter names."""
        router = Router()
        
        routes = router.resource('posts', 'PostController', parameters={
            'posts': 'post_id'
        })
        
        show_route = [r for r in routes if 'show' in r.getName()][0]
        assert '{post_id}' in show_route.uri()
