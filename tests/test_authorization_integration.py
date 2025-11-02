import pytest
from larapy.auth.gate import Gate
from larapy.auth.policy import Policy
from larapy.auth.exceptions import AuthorizationException
from larapy.auth.gate_service_provider import GateServiceProvider
from larapy.auth.authorizes_requests import AuthorizesRequests
from larapy.container import Container
from larapy.foundation import Application


class User:
    def __init__(self, id, role='user'):
        self.id = id
        self.role = role
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_super_admin(self):
        return self.role == 'super_admin'


class Post:
    def __init__(self, id, user_id, published=True):
        self.id = id
        self.user_id = user_id
        self.published = published


class Comment:
    def __init__(self, id, user_id, post_id):
        self.id = id
        self.user_id = user_id
        self.post_id = post_id


class PostPolicy(Policy):
    def before(self, user, ability):
        if user.is_super_admin():
            return True
        return None
    
    def view(self, user, post):
        return post.published or user.id == post.user_id
    
    def create(self, user, post_class):
        return True
    
    def update(self, user, post):
        return user.id == post.user_id
    
    def delete(self, user, post):
        return user.id == post.user_id or user.is_admin()


class CommentPolicy(Policy):
    def update(self, user, comment):
        return user.id == comment.user_id
    
    def delete(self, user, comment):
        return user.id == comment.user_id


class TestAuthorizationIntegration:
    @pytest.mark.asyncio
    async def test_full_authorization_flow(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        user = User(1, 'user')
        post = Post(1, user_id=1)
        
        gate.policy(Post, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
        assert gate.allows('update', post) is True
        assert gate.allows('delete', post) is True
        
        gate.authorize('update', post)
        gate.authorize('delete', post)
        
        other_post = Post(2, user_id=2)
        assert gate.denies('delete', other_post) is True
        
        with pytest.raises(AuthorizationException):
            gate.authorize('delete', other_post)
    
    @pytest.mark.asyncio
    async def test_authorization_with_policy_before(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        super_admin = User(1, 'super_admin')
        post = Post(1, user_id=2)
        
        gate.policy(Post, PostPolicy)
        gate.user_resolver = lambda: super_admin
        
        assert gate.allows('update', post) is True
        assert gate.allows('delete', post) is True
        assert gate.allows('view', post) is True
        
        gate.authorize('update', post)
        gate.authorize('delete', post)
    
    @pytest.mark.asyncio
    async def test_super_admin_pattern(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        
        regular_user = User(1, 'user')
        admin_user = User(2, 'admin')
        super_admin = User(3, 'super_admin')
        post = Post(1, user_id=99)
        
        gate.policy(Post, PostPolicy)
        
        gate.user_resolver = lambda: regular_user
        assert gate.denies('update', post) is True
        assert gate.denies('delete', post) is True
        
        gate.user_resolver = lambda: admin_user
        assert gate.denies('update', post) is True
        assert gate.allows('delete', post) is True
        
        gate.user_resolver = lambda: super_admin
        assert gate.allows('update', post) is True
        assert gate.allows('delete', post) is True
    
    @pytest.mark.asyncio
    async def test_guest_user_denied(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        post = Post(1, user_id=1)
        
        gate.policy(Post, PostPolicy)
        gate.user_resolver = lambda: None
        
        assert gate.denies('view', post) is True
        assert gate.denies('update', post) is True
        assert gate.denies('delete', post) is True
        
        with pytest.raises(AuthorizationException):
            gate.authorize('view', post)
    
    @pytest.mark.asyncio
    async def test_multiple_policies_work_together(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        user = User(1, 'user')
        post = Post(1, user_id=1)
        comment = Comment(1, user_id=1, post_id=1)
        
        gate.policy(Post, PostPolicy)
        gate.policy(Comment, CommentPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
        assert gate.allows('update', comment) is True
        
        other_comment = Comment(2, user_id=2, post_id=1)
        assert gate.denies('update', other_comment) is True
    
    @pytest.mark.asyncio
    async def test_gate_with_before_callback(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        admin = User(1, 'admin')
        post = Post(1, user_id=2)
        
        gate.before(lambda user, ability: True if user.is_admin() else None)
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: admin
        
        assert gate.allows('update-post', post) is True
        
        regular_user = User(3, 'user')
        gate.user_resolver = lambda: regular_user
        
        assert gate.allows('update-post', post) is False
        assert gate.denies('update-post', post) is True
    
    @pytest.mark.asyncio
    async def test_gate_any_and_none_methods(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        user = User(1, 'user')
        post = Post(1, user_id=1)
        
        gate.policy(Post, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.any(['update', 'delete'], post) is True
        
        post2 = Post(2, user_id=2)
        assert gate.none(['update', 'delete'], post2) is True
    
    @pytest.mark.asyncio
    async def test_controller_integration(self):
        app = Application()
        app.register(GateServiceProvider)
        app.boot()
        
        gate = app.make('gate')
        user = User(1, 'user')
        post = Post(1, user_id=1)
        
        gate.policy(Post, PostPolicy)
        gate.user_resolver = lambda: user
        app.bind('gate', lambda c: gate)
        
        class PostController(AuthorizesRequests):
            def __init__(self, container):
                self.container = container
            
            def update(self, post):
                self.authorize('update', post)
                return 'updated'
        
        controller = PostController(app)
        result = controller.update(post)
        assert result == 'updated'
        
        post2 = Post(2, user_id=2)
        with pytest.raises(AuthorizationException):
            controller.update(post2)
