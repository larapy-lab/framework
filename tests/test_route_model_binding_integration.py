"""
Integration Tests for Route Model Binding

Tests the full request lifecycle with route model binding,
including router registration, middleware execution, and controller injection.
"""

import pytest
from typing import Optional
from larapy.routing.router import Router
from larapy.routing.route_collection import RouteCollection
from larapy.routing.model_binder import ModelBinder
from larapy.http.middleware.substitute_bindings import SubstituteBindings
from larapy.http.request import Request
from larapy.container.container import Container
from larapy.database.orm.model import Model


class User(Model):
    """Test User model."""
    
    _table = 'users'
    _fillable = ['name', 'email', 'username']
    _hidden = ['password']
    
    def __init__(self, **attributes):
        super().__init__()
        self._attributes = attributes
        
    def getRouteKeyName(self) -> str:
        return 'id'
        
    @classmethod
    def findOrFail(cls, id: int):
        if id == 1:
            return cls(id=1, name='John Doe', email='john@example.com', username='john')
        elif id == 2:
            return cls(id=2, name='Jane Smith', email='jane@example.com', username='jane')
        raise Exception(f"User {id} not found")
    
    @classmethod
    def where(cls, field: str, value):
        class Query:
            def first(self):
                if field == 'id' and value == '1':
                    return User(id=1, name='John Doe', email='john@example.com', username='john')
                elif field == 'id' and value == 1:
                    return User(id=1, name='John Doe', email='john@example.com', username='john')
                elif field == 'id' and value == '2':
                    return User(id=2, name='Jane Smith', email='jane@example.com', username='jane')
                elif field == 'id' and value == 2:
                    return User(id=2, name='Jane Smith', email='jane@example.com', username='jane')
                elif field == 'username' and value == 'john':
                    return User(id=1, name='John Doe', email='john@example.com', username='john')
                elif field == 'username' and value == 'jane':
                    return User(id=2, name='Jane Smith', email='jane@example.com', username='jane')
                return None
        return Query()


class Post(Model):
    """Test Post model."""
    
    _table = 'posts'
    _fillable = ['title', 'slug', 'content', 'user_id']
    
    def __init__(self, **attributes):
        super().__init__()
        self._attributes = attributes
        
    def getRouteKeyName(self) -> str:
        return 'id'
        
    @classmethod
    def findOrFail(cls, id: int):
        if id == 1:
            return cls(id=1, title='First Post', slug='first-post', content='Content 1', user_id=1)
        elif id == 2:
            return cls(id=2, title='Second Post', slug='second-post', content='Content 2', user_id=1)
        raise Exception(f"Post {id} not found")
    
    @classmethod
    def where(cls, field: str, value):
        class Query:
            def first(self):
                if field == 'id' and value in ('1', 1):
                    return Post(id=1, title='First Post', slug='first-post', content='Content 1', user_id=1)
                elif field == 'id' and value in ('2', 2):
                    return Post(id=2, title='Second Post', slug='second-post', content='Content 2', user_id=1)
                elif field == 'slug' and value == 'first-post':
                    return Post(id=1, title='First Post', slug='first-post', content='Content 1', user_id=1)
                elif field == 'slug' and value == 'second-post':
                    return Post(id=2, title='Second Post', slug='second-post', content='Content 2', user_id=1)
                return None
        return Query()


class Comment:
    """Test Comment model - simplified to avoid config imports."""
    
    _table = 'comments'
    _fillable = ['body', 'post_id', 'user_id']
    
    def __init__(self, **attributes):
        self._attributes = attributes
        for key, value in attributes.items():
            setattr(self, key, value)
        
    @classmethod
    def findOrFail(cls, id: int):
        if id == 1:
            return cls(id=1, body='Great post!', post_id=1, user_id=2)
        raise Exception(f"Comment {id} not found")
    
    @classmethod
    def where(cls, field: str, value):
        class Query:
            def first(self):
                if field == 'id' and value in ('1', 1):
                    return Comment(id=1, body='Great post!', post_id=1, user_id=2)
                return None
        return Query()


class TestRouterIntegration:
    """Test Router.bind() and Router.model() methods."""
    
    def test_router_model_registration(self):
        """Test Router.model() registers implicit binding."""
        router = Router(RouteCollection())
        
        router.model('user', User)
        route = router.get('/users/{user}', lambda user: user)
        
        binder = router.getBinder()
        assert 'user' in binder.scoped_bindings
        assert binder.scoped_bindings['user']['model_class'] == User
        assert binder.scoped_bindings['user']['field'] == 'id'
    
    def test_router_bind_registration(self):
        """Test Router.bind() registers explicit binding."""
        router = Router(RouteCollection())
        
        def find_user(value):
            return User.findOrFail(int(value))
        
        router.bind('user', find_user)
        route = router.get('/users/{user}', lambda user: user)
        
        bindings = router.getBindings()
        assert 'user' in bindings
        assert bindings['user'] == find_user
    
    def test_router_applies_bindings_to_routes(self):
        """Test Router applies global bindings to routes."""
        router = Router(RouteCollection())
        
        router.model('user', User)
        route = router.get('/users/{user}', lambda user: user)
        
        route_bindings = route.getBindings()
        assert 'user' in route_bindings
        assert route_bindings['user']['model_class'] == User
    
    def test_uri_syntax_overrides_global_binding(self):
        """Test {param:field} syntax takes precedence over Router.model()."""
        router = Router(RouteCollection())
        
        router.model('user', User)
        route = router.get('/users/{user:username}', lambda user: user)
        
        route_bindings = route.getBindings()
        assert 'user' in route_bindings
        assert route_bindings['user'].get('field') == 'username'


class TestURISyntaxParsing:
    """Test URI parameter binding syntax parsing."""
    
    def test_parse_field_from_uri(self):
        """Test parsing {param:field} syntax."""
        router = Router(RouteCollection())
        router.model('post', Post)
        
        route = router.get('/posts/{post:slug}', lambda post: post)
        
        bindings = route.getBindings()
        assert 'post' in bindings
        assert bindings['post']['field'] == 'slug'
    
    def test_parse_optional_with_field(self):
        """Test parsing {param:field?} syntax."""
        router = Router(RouteCollection())
        router.model('post', Post)
        
        route = router.get('/posts/{post:slug?}', lambda post=None: post)
        
        bindings = route.getBindings()
        assert 'post' in bindings
        assert bindings['post']['field'] == 'slug'
    
    def test_multiple_parameters_with_fields(self):
        """Test multiple parameters with custom fields."""
        router = Router(RouteCollection())
        
        route = router.get('/users/{user:username}/posts/{post:slug}', 
                          lambda user, post: (user, post))
        
        bindings = route.getBindings()
        assert bindings['user']['field'] == 'username'
        assert bindings['post']['field'] == 'slug'


class TestMiddlewareIntegration:
    """Test SubstituteBindings middleware with full request lifecycle."""
    
    def create_request(self, uri: str, method: str = 'GET'):
        """Create a test request."""
        request = Request()
        request.uri = uri
        request.method = method
        return request
    
    def test_middleware_substitutes_parameter(self):
        """Test middleware substitutes route parameter with model."""
        binder = ModelBinder()
        binder.model('user', User)
        
        middleware = SubstituteBindings(binder)
        request = self.create_request('/users/1', 'GET')
        
        class MockRoute:
            _parameters = {'user': '1'}
            _parameter_names = ['user']
            _bindings = {'user': {'model_class': User, 'field': 'id'}}
            _with_trashed = False
            
            @property
            def parameters(self):
                return self._parameters
            
            @property
            def parameter_names(self):
                return self._parameter_names
            
            @property
            def bindings(self):
                return self._bindings
            
            @property
            def with_trashed(self):
                return self._with_trashed
        
        request.route = MockRoute()
        
        def next_handler(req):
            assert isinstance(req.route.parameters['user'], User), f"Expected User, got {type(req.route.parameters['user'])}"
            assert req.route.parameters['user'].id == 1
            return 'response'
        
        result = middleware.handle(request, next_handler)
        
        # If we got JsonResponse, check what error it contains
        if hasattr(result, 'data'):
            print(f"Error response: {result.data}")
        
        assert result == 'response', f"Expected 'response', got {result}"
    
    def test_middleware_handles_not_found(self):
        """Test middleware converts ModelNotFoundException to 404."""
        binder = ModelBinder()
        binder.model('user', User)
        
        middleware = SubstituteBindings(binder)
        request = self.create_request('/users/999', 'GET')
        
        class MockRoute:
            _parameters = {'user': '999'}
            _parameter_names = ['user']
            _bindings = {'user': {'model_class': User, 'field': 'id'}}
            _with_trashed = False
            
            @property
            def parameters(self):
                return self._parameters
            
            @property
            def parameter_names(self):
                return self._parameter_names
            
            @property
            def bindings(self):
                return self._bindings
            
            @property
            def with_trashed(self):
                return self._with_trashed
        
        request.route = MockRoute()
        
        def next_handler(req):
            return 'response'
        
        response = middleware.handle(request, next_handler)
        data = response._data
        assert 'User' in str(data)
    
    def test_middleware_with_custom_field(self):
        """Test middleware with custom field binding."""
        binder = ModelBinder()
        binder.model('user', User)
        
        middleware = SubstituteBindings(binder)
        request = self.create_request('/users/john', 'GET')
        
        class MockRoute:
            _parameters = {'user': 'john'}
            _parameter_names = ['user']
            _bindings = {'user': {'model_class': User, 'field': 'username'}}
            _with_trashed = False
            
            @property
            def parameters(self):
                return self._parameters
            
            @property
            def parameter_names(self):
                return self._parameter_names
            
            @property
            def bindings(self):
                return self._bindings
            
            @property
            def with_trashed(self):
                return self._with_trashed
        
        request.route = MockRoute()
        
        def next_handler(req):
            user = req.route.parameters['user']
            assert isinstance(user, User)
            assert user.username == 'john'
            assert user.name == 'John Doe'
            return 'response'
        
        result = middleware.handle(request, next_handler)
        assert result == 'response'


class TestControllerInjection:
    """Test controller method injection with type hints."""
    
    def test_inject_model_by_type_hint(self):
        """Test injecting model instance via type hint."""
        container = Container()
        
        def controller(user: User):
            assert isinstance(user, User)
            return user.name
        
        user_instance = User(id=1, name='John Doe', email='john@example.com')
        result = container.call(controller, {'user': user_instance})
        
        assert result == 'John Doe'
    
    def test_inject_multiple_models(self):
        """Test injecting multiple model instances."""
        container = Container()
        
        def controller(user: User, post: Post):
            assert isinstance(user, User)
            assert isinstance(post, Post)
            return f"{user.name} - {post.title}"
        
        user_instance = User(id=1, name='John Doe', email='john@example.com')
        post_instance = Post(id=1, title='First Post', slug='first-post')
        
        result = container.call(controller, {
            'user': user_instance,
            'post': post_instance
        })
        
        assert result == 'John Doe - First Post'
    
    def test_inject_with_mixed_parameters(self):
        """Test injecting models mixed with regular parameters."""
        container = Container()
        
        def controller(user: User, action: str):
            assert isinstance(user, User)
            assert isinstance(action, str)
            return f"{action}: {user.name}"
        
        user_instance = User(id=1, name='John Doe', email='john@example.com')
        result = container.call(controller, {
            'user': user_instance,
            'action': 'view'
        })
        
        assert result == 'view: John Doe'
    
    def test_inject_optional_model(self):
        """Test injecting optional model parameter."""
        container = Container()
        
        def controller(user: Optional[User] = None):
            if user:
                return user.name
            return 'Guest'
        
        result = container.call(controller, {})
        assert result == 'Guest'
        
        user_instance = User(id=1, name='John Doe', email='john@example.com')
        result = container.call(controller, {'user': user_instance})
        assert result == 'John Doe'


class TestFullLifecycle:
    """Test complete request lifecycle from routing to response."""
    
    def test_implicit_binding_full_lifecycle(self):
        """Test full lifecycle with implicit model binding."""
        router = Router(RouteCollection())
        container = Container()
        binder = ModelBinder()
        
        binder.model('user', User)
        
        def show_user(user: User):
            return {'name': user.name, 'email': user.email}
        
        route = router.get('/users/{user}', show_user)
        route.bind(container)
        
        route._parameters = {'user': '1'}
        route_bindings = {'user': {'model_class': User, 'field': 'id'}}
        route._bindings = route_bindings
        
        middleware = SubstituteBindings(binder)
        request = Request()
        request.uri = '/users/1'
        request.method = 'GET'
        request.route = route
        
        def next_handler(req):
            return req.route.run()
        
        result = middleware.handle(request, next_handler)
        
        assert isinstance(result, dict)
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
    
    def test_explicit_binding_full_lifecycle(self):
        """Test full lifecycle with explicit callback binding."""
        router = Router(RouteCollection())
        container = Container()
        binder = ModelBinder()
        
        def find_user_by_username(value: str) -> User:
            return User.where('username', value).first()
        
        binder.bind('user', find_user_by_username)
        
        def show_user(user: User):
            return {'username': user.username, 'name': user.name}
        
        route = router.get('/users/{user}', show_user)
        route.bind(container)
        
        route._parameters = {'user': 'john'}
        route_bindings = {'user': {'callback': find_user_by_username}}
        route._bindings = route_bindings
        
        middleware = SubstituteBindings(binder)
        request = Request()
        request.uri = '/users/john'
        request.method = 'GET'
        request.route = route
        
        def next_handler(req):
            return req.route.run()
        
        result = middleware.handle(request, next_handler)
        
        assert isinstance(result, dict)
        assert result['username'] == 'john'
        assert result['name'] == 'John Doe'
    
    def test_nested_resource_binding(self):
        """Test binding multiple nested resources."""
        router = Router(RouteCollection())
        container = Container()
        binder = ModelBinder()
        
        binder.model('user', User)
        binder.model('post', Post)
        binder.model('comment', Comment)
        
        def show_comment(user: User, post: Post, comment: Comment):
            return {
                'user': user.name,
                'post': post.title,
                'comment': comment.body
            }
        
        route = router.get('/users/{user}/posts/{post}/comments/{comment}', show_comment)
        route.bind(container)
        
        route._parameters = {'user': '1', 'post': '1', 'comment': '1'}
        route._bindings = {
            'user': {'model_class': User, 'field': 'id'},
            'post': {'model_class': Post, 'field': 'id'},
            'comment': {'model_class': Comment, 'field': 'id'}
        }
        
        middleware = SubstituteBindings(binder)
        request = Request()
        request.uri = '/users/1/posts/1/comments/1'
        request.method = 'GET'
        request.route = route
        
        def next_handler(req):
            return req.route.run()
        
        result = middleware.handle(request, next_handler)
        
        assert result['user'] == 'John Doe'
        assert result['post'] == 'First Post'
        assert result['comment'] == 'Great post!'


class TestRouteWithTrashed:
    """Test Route.withTrashed() for soft-delete support."""
    
    def test_with_trashed_flag_set(self):
        """Test Route.withTrashed() sets flag."""
        router = Router(RouteCollection())
        route = router.get('/posts/{post}', lambda post: post)
        
        assert route.shouldIncludeTrashed() is False
        
        route.withTrashed()
        assert route.shouldIncludeTrashed() is True
    
    def test_with_trashed_chaining(self):
        """Test withTrashed() returns route for chaining."""
        router = Router(RouteCollection())
        route = router.get('/posts/{post}', lambda post: post)
        
        result = route.withTrashed().name('posts.show')
        assert result == route
        assert route.getName() == 'posts.show'
        assert route.shouldIncludeTrashed() is True


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_blog_post_by_slug(self):
        """Test blog post retrieval by slug."""
        router = Router(RouteCollection())
        container = Container()
        
        # Use router.model() to set up binding
        router.model('post', Post)
        
        def show_post(post: Post):
            return {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content': post.content
            }
        
        route = router.get('/blog/{post:slug}', show_post)
        route.bind(container)
        
        route._parameters = {'post': 'first-post'}
        
        # Use router's binder for middleware
        binder = router.getBinder()
        middleware = SubstituteBindings(binder)
        request = Request()
        request.uri = '/blog/first-post'
        request.route = route
        
        def next_handler(req):
            return req.route.run()
        
        result = middleware.handle(request, next_handler)
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result['slug'] == 'first-post'
        assert result['title'] == 'First Post'
    
    def test_user_profile_by_username(self):
        """Test user profile by username."""
        router = Router(RouteCollection())
        container = Container()
        
        # Use router.model() to set up binding
        router.model('user', User)
        
        def show_profile(user: User):
            return {
                'username': user.username,
                'name': user.name,
                'email': user.email
            }
        
        route = router.get('/@{user:username}', show_profile)
        route.bind(container)
        
        route._parameters = {'user': 'jane'}
        
        # Use router's binder for middleware
        binder = router.getBinder()
        middleware = SubstituteBindings(binder)
        request = Request()
        request.uri = '/@jane'
        request.route = route
        
        def next_handler(req):
            return req.route.run()
        
        result = middleware.handle(request, next_handler)
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result['username'] == 'jane'
        assert result['name'] == 'Jane Smith'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
