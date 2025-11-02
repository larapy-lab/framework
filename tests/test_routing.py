"""
Tests for routing system.
"""

import pytest
from larapy.routing.route import Route
from larapy.routing.route_collection import RouteCollection
from larapy.routing.router import Router, RouteGroup
from larapy.container.container import Container


class TestRoute:
    def test_route_initialization(self):
        route = Route(['GET'], '/users', lambda: 'response')
        assert route.methods() == ['GET', 'HEAD']
        assert route.uri() == '/users'

    def test_route_matches_uri(self):
        route = Route(['GET'], '/users', lambda: 'response')
        assert route.matches('/users', 'GET') is True
        assert route.matches('/posts', 'GET') is False

    def test_route_matches_method(self):
        route = Route(['GET'], '/users', lambda: 'response')
        assert route.matches('/users', 'GET') is True
        assert route.matches('/users', 'POST') is False

    def test_route_with_required_parameters(self):
        route = Route(['GET'], '/users/{id}', lambda: 'response')
        assert route.matches('/users/123', 'GET') is True
        assert route.matches('/users/', 'GET') is False
        params = route.parameters()
        assert params['id'] == '123'

    def test_route_with_multiple_parameters(self):
        route = Route(['GET'], '/users/{user}/posts/{post}', lambda: 'response')
        assert route.matches('/users/42/posts/99', 'GET') is True
        params = route.parameters()
        assert params['user'] == '42'
        assert params['post'] == '99'

    def test_route_with_optional_parameters(self):
        route = Route(['GET'], '/users/{id?}', lambda: 'response')
        assert route.matches('/users/123', 'GET') is True
        assert route.matches('/users', 'GET') is True
        
        route.matches('/users/123', 'GET')
        params = route.parameters()
        assert params['id'] == '123'

    def test_route_where_constraint(self):
        route = Route(['GET'], '/users/{id}', lambda: 'response')
        route.where('id', r'\d+')
        assert route.matches('/users/123', 'GET') is True
        assert route.matches('/users/abc', 'GET') is False

    def test_route_where_dict_constraint(self):
        route = Route(['GET'], '/users/{user}/posts/{post}', lambda: 'response')
        route.where({'user': r'\d+', 'post': r'\d+'})
        assert route.matches('/users/123/posts/456', 'GET') is True
        assert route.matches('/users/abc/posts/456', 'GET') is False

    def test_route_where_number(self):
        route = Route(['GET'], '/users/{id}', lambda: 'response')
        route.whereNumber('id')
        assert route.matches('/users/123', 'GET') is True
        assert route.matches('/users/abc', 'GET') is False

    def test_route_where_alpha(self):
        route = Route(['GET'], '/users/{name}', lambda: 'response')
        route.whereAlpha('name')
        assert route.matches('/users/john', 'GET') is True
        assert route.matches('/users/john123', 'GET') is False

    def test_route_where_alpha_numeric(self):
        route = Route(['GET'], '/users/{username}', lambda: 'response')
        route.whereAlphaNumeric('username')
        assert route.matches('/users/john123', 'GET') is True
        assert route.matches('/users/john_123', 'GET') is False

    def test_route_where_uuid(self):
        route = Route(['GET'], '/users/{id}', lambda: 'response')
        route.whereUuid('id')
        uuid = '550e8400-e29b-41d4-a716-446655440000'
        assert route.matches(f'/users/{uuid}', 'GET') is True
        assert route.matches('/users/123', 'GET') is False

    def test_route_where_in(self):
        route = Route(['GET'], '/{locale}/posts', lambda: 'response')
        route.whereIn('locale', ['en', 'fr', 'es'])
        assert route.matches('/en/posts', 'GET') is True
        assert route.matches('/fr/posts', 'GET') is True
        assert route.matches('/de/posts', 'GET') is False

    def test_route_naming(self):
        route = Route(['GET'], '/users', lambda: 'response')
        route.name('users.index')
        assert route.getName() == 'users.index'
        assert route.named('users.index') is True

    def test_route_middleware(self):
        route = Route(['GET'], '/admin', lambda: 'response')
        route.middleware('auth', 'admin')
        middleware = route.getMiddleware()
        assert 'auth' in middleware
        assert 'admin' in middleware

    def test_route_parameter_accessors(self):
        route = Route(['GET'], '/users/{id}', lambda: 'response')
        route.matches('/users/123', 'GET')
        assert route.parameter('id') == '123'
        route.setParameter('id', '456')
        assert route.parameter('id') == '456'

    def test_route_run_with_callable(self):
        def action():
            return 'test response'
        
        route = Route(['GET'], '/test', action)
        result = route.run()
        assert result == 'test response'

    def test_route_run_with_parameters(self):
        def action(id: str):
            return f'user {id}'
        
        route = Route(['GET'], '/users/{id}', action)
        route.matches('/users/123', 'GET')
        result = route.run()
        assert result == 'user 123'

    def test_route_run_with_container(self):
        container = Container()
        
        class Service:
            def get_value(self):
                return 'injected service'
        
        container.bind('Service', lambda c: Service())
        
        def action(service: Service):
            return service.get_value()
        
        route = Route(['GET'], '/test', action)
        route.bind(container)
        result = route.run()
        assert result == 'injected service'


class TestRouteCollection:
    def test_add_route(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        collection.add(route)
        assert collection.count() == 1

    def test_match_route_by_uri(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        collection.add(route)
        matched = collection.match('/users', 'GET')
        assert matched == route

    def test_match_route_not_found(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        collection.add(route)
        matched = collection.match('/posts', 'GET')
        assert matched is None

    def test_match_route_wrong_method(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        collection.add(route)
        matched = collection.match('/users', 'POST')
        assert matched is None

    def test_get_by_name(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        route.name('users.index')
        collection.add(route)
        found = collection.getByName('users.index')
        assert found == route

    def test_get_by_method(self):
        collection = RouteCollection()
        route1 = Route(['GET'], '/users', lambda: 'response')
        route2 = Route(['POST'], '/users', lambda: 'response')
        collection.add(route1)
        collection.add(route2)
        get_routes = collection.getByMethod('GET')
        assert len(get_routes) == 1
        assert route1 in get_routes

    def test_has_named_route(self):
        collection = RouteCollection()
        route = Route(['GET'], '/users', lambda: 'response')
        route.name('users.index')
        collection.add(route)
        assert collection.hasNamedRoute('users.index') is True
        assert collection.hasNamedRoute('posts.index') is False

    def test_collection_iteration(self):
        collection = RouteCollection()
        routes = [
            Route(['GET'], '/users', lambda: 'response'),
            Route(['POST'], '/users', lambda: 'response'),
        ]
        for route in routes:
            collection.add(route)
        
        collected = list(collection)
        assert len(collected) == 2
        assert all(r in collected for r in routes)


class TestRouter:
    def test_router_initialization(self):
        router = Router()
        assert router.routes.count() == 0

    def test_get_route_registration(self):
        router = Router()
        route = router.get('/users', lambda: 'response')
        assert route.methods() == ['GET', 'HEAD']
        assert router.routes.count() == 1

    def test_post_route_registration(self):
        router = Router()
        route = router.post('/users', lambda: 'response')
        assert route.methods() == ['POST']
        assert router.routes.count() == 1

    def test_put_route_registration(self):
        router = Router()
        route = router.put('/users/1', lambda: 'response')
        assert route.methods() == ['PUT']

    def test_patch_route_registration(self):
        router = Router()
        route = router.patch('/users/1', lambda: 'response')
        assert route.methods() == ['PATCH']

    def test_delete_route_registration(self):
        router = Router()
        route = router.delete('/users/1', lambda: 'response')
        assert route.methods() == ['DELETE']

    def test_options_route_registration(self):
        router = Router()
        route = router.options('/users', lambda: 'response')
        assert route.methods() == ['OPTIONS']

    def test_any_route_registration(self):
        router = Router()
        route = router.any('/users', lambda: 'response')
        methods = route.methods()
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods

    def test_match_route_registration(self):
        router = Router()
        route = router.match(['GET', 'POST'], '/users', lambda: 'response')
        methods = route.methods()
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' not in methods

    def test_route_group_with_prefix(self):
        router = Router()
        
        def register_routes(r):
            r.get('/users', lambda: 'users')
            r.get('/posts', lambda: 'posts')
        
        router.group({'prefix': 'api'}, register_routes)
        
        assert router.routes.count() == 2
        route1 = router.routes.match('api/users', 'GET')
        route2 = router.routes.match('api/posts', 'GET')
        assert route1 is not None
        assert route2 is not None

    def test_route_group_with_middleware(self):
        router = Router()
        
        def register_routes(r):
            r.get('/admin', lambda: 'admin')
        
        router.group({'middleware': ['auth', 'admin']}, register_routes)
        
        route = router.routes.match('admin', 'GET')
        middleware = route.getMiddleware()
        assert 'auth' in middleware
        assert 'admin' in middleware

    def test_route_group_with_name_prefix(self):
        router = Router()
        
        def register_routes(r):
            r.get('/users', lambda: 'users').name('index')
        
        router.group({'name': 'admin'}, register_routes)
        
        route = router.routes.getByName('admin.index')
        assert route is not None

    def test_nested_route_groups(self):
        router = Router()
        
        def admin_routes(r):
            def user_routes(r2):
                r2.get('/', lambda: 'users')
            
            r.group({'prefix': 'users'}, user_routes)
        
        router.group({'prefix': 'admin'}, admin_routes)
        
        route = router.routes.match('admin/users', 'GET')
        assert route is not None

    def test_route_group_fluent_api(self):
        router = Router()
        
        def register_routes(r):
            r.get('/dashboard', lambda: 'dashboard')
        
        router.prefix('admin').middleware('auth').group(register_routes)
        
        route = router.routes.match('admin/dashboard', 'GET')
        assert route is not None
        assert 'auth' in route.getMiddleware()

    def test_global_parameter_pattern(self):
        router = Router()
        router.pattern('id', r'\d+')
        route = router.get('/users/{id}', lambda: 'response')
        assert route.matches('/users/123', 'GET') is True
        assert route.matches('/users/abc', 'GET') is False

    def test_global_parameter_patterns(self):
        router = Router()
        router.patterns({'id': r'\d+', 'slug': r'[a-z\-]+'})
        route = router.get('/posts/{slug}', lambda: 'response')
        assert route.matches('/posts/hello-world', 'GET') is True
        assert route.matches('/posts/HELLO', 'GET') is False

    def test_middleware_alias(self):
        router = Router()
        router.aliasMiddleware('auth', 'App\\Http\\Middleware\\Authenticate')
        assert router._middleware['auth'] == 'App\\Http\\Middleware\\Authenticate'

    def test_middleware_group(self):
        router = Router()
        router.middlewareGroup('web', ['session', 'csrf'])
        assert 'web' in router._middleware_groups
        assert router._middleware_groups['web'] == ['session', 'csrf']


class TestRouterComplexScenarios:
    def test_api_routes_with_versioning(self):
        router = Router()
        
        def v1_routes(r):
            r.get('/users', lambda: 'v1 users')
            r.get('/users/{id}', lambda id: f'v1 user {id}').whereNumber('id')
            r.post('/users', lambda: 'v1 create user')
        
        def v2_routes(r):
            r.get('/users', lambda: 'v2 users')
            r.get('/users/{id}', lambda id: f'v2 user {id}').whereNumber('id')
        
        router.group({'prefix': 'api/v1', 'middleware': ['api']}, v1_routes)
        router.group({'prefix': 'api/v2', 'middleware': ['api']}, v2_routes)
        
        v1_user = router.routes.match('api/v1/users/123', 'GET')
        v2_user = router.routes.match('api/v2/users/456', 'GET')
        v1_create = router.routes.match('api/v1/users', 'POST')
        
        assert v1_user is not None
        assert v2_user is not None
        assert v1_create is not None
        assert 'api' in v1_user.getMiddleware()

    def test_admin_panel_routes(self):
        router = Router()
        router.patterns({'id': r'\d+', 'slug': r'[a-z0-9\-]+'})
        
        def admin_routes(r):
            def user_routes(r2):
                r2.get('/', lambda: 'users list').name('index')
                r2.get('/create', lambda: 'create user').name('create')
                r2.post('/', lambda: 'store user').name('store')
                r2.get('/{id}', lambda id: f'show user {id}').name('show')
                r2.get('/{id}/edit', lambda id: f'edit user {id}').name('edit')
                r2.put('/{id}', lambda id: f'update user {id}').name('update')
                r2.delete('/{id}', lambda id: f'delete user {id}').name('destroy')
            
            def post_routes(r2):
                r2.get('/', lambda: 'posts list').name('index')
                r2.get('/{slug}', lambda slug: f'show post {slug}').name('show')
            
            r.group({'prefix': 'users', 'name': 'users.'}, user_routes)
            r.group({'prefix': 'posts', 'name': 'posts.'}, post_routes)
        
        router.prefix('admin').name('admin.').middleware('auth', 'admin').group(admin_routes)
        
        assert router.routes.count() == 9
        
        user_index = router.routes.getByName('admin.users.index')
        user_show = router.routes.getByName('admin.users.show')
        post_show = router.routes.getByName('admin.posts.show')
        
        assert user_index is not None
        assert user_show is not None
        assert post_show is not None
        
        assert user_index.matches('admin/users', 'GET')
        assert user_show.matches('admin/users/123', 'GET')
        assert post_show.matches('admin/posts/hello-world', 'GET')

    def test_multilingual_routes(self):
        router = Router()
        
        def localized_routes(r):
            r.get('/about', lambda: 'about page').name('about')
            r.get('/contact', lambda: 'contact page').name('contact')
            r.get('/products/{id}', lambda id: f'product {id}').name('products.show')
        
        for locale in ['en', 'fr', 'es', 'de']:
            router.prefix(locale).name(f'{locale}.').group(localized_routes)
        
        assert router.routes.count() == 12
        
        en_about = router.routes.getByName('en.about')
        fr_contact = router.routes.getByName('fr.contact')
        es_product = router.routes.getByName('es.products.show')
        
        assert en_about.matches('en/about', 'GET')
        assert fr_contact.matches('fr/contact', 'GET')
        assert es_product.matches('es/products/123', 'GET')

    def test_restful_resource_routes(self):
        router = Router()
        
        def resource_routes(r):
            r.get('/', lambda: 'index').name('index')
            r.get('/create', lambda: 'create').name('create')
            r.post('/', lambda: 'store').name('store')
            r.get('/{id}', lambda id: f'show {id}').name('show').whereNumber('id')
            r.get('/{id}/edit', lambda id: f'edit {id}').name('edit').whereNumber('id')
            r.put('/{id}', lambda id: f'update {id}').name('update').whereNumber('id')
            r.delete('/{id}', lambda id: f'destroy {id}').name('destroy').whereNumber('id')
        
        router.prefix('posts').name('posts.').group(resource_routes)
        
        assert router.routes.count() == 7
        
        index = router.routes.getByName('posts.index')
        show = router.routes.getByName('posts.show')
        update = router.routes.getByName('posts.update')
        
        assert index.matches('posts', 'GET')
        assert show.matches('posts/42', 'GET')
        assert not show.matches('posts/abc', 'GET')
        assert update.matches('posts/42', 'PUT')

    def test_complex_nested_groups_with_all_attributes(self):
        router = Router()
        router.patterns({'id': r'\d+', 'uuid': r'[0-9a-f\-]{36}'})
        
        def api_routes(r):
            def v1_routes(r2):
                def auth_routes(r3):
                    def user_routes(r4):
                        r4.get('/profile', lambda: 'profile').name('profile')
                        r4.put('/profile', lambda: 'update profile').name('profile.update')
                        r4.get('/settings', lambda: 'settings').name('settings')
                    
                    def admin_routes(r4):
                        r4.get('/dashboard', lambda: 'dashboard').name('dashboard')
                        r4.get('/users', lambda: 'manage users').name('users')
                        r4.get('/users/{id}', lambda id: f'user {id}').name('users.show')
                    
                    r3.group({'prefix': 'user', 'name': 'user.', 'middleware': ['verified']}, user_routes)
                    r3.group({'prefix': 'admin', 'name': 'admin.', 'middleware': ['admin']}, admin_routes)
                
                r2.group({'middleware': ['auth']}, auth_routes)
            
            r.group({'prefix': 'v1', 'name': 'v1.'}, v1_routes)
        
        router.prefix('api').name('api.').middleware('throttle:60,1').group(api_routes)
        
        profile = router.routes.getByName('api.v1.user.profile')
        dashboard = router.routes.getByName('api.v1.admin.dashboard')
        user_show = router.routes.getByName('api.v1.admin.users.show')
        
        assert profile is not None
        assert dashboard is not None
        assert user_show is not None
        
        assert profile.matches('api/v1/user/profile', 'GET')
        assert dashboard.matches('api/v1/admin/dashboard', 'GET')
        assert user_show.matches('api/v1/admin/users/123', 'GET')
        
        profile_middleware = profile.getMiddleware()
        assert 'throttle:60,1' in profile_middleware
        assert 'auth' in profile_middleware
        assert 'verified' in profile_middleware
        
        dashboard_middleware = dashboard.getMiddleware()
        assert 'throttle:60,1' in dashboard_middleware
        assert 'auth' in dashboard_middleware
        assert 'admin' in dashboard_middleware
