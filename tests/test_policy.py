import pytest
import asyncio
from larapy.auth.gate import Gate
from larapy.auth.policy import Policy
from larapy.container import Container


class MockUser:
    def __init__(self, id, is_admin=False):
        self.id = id
        self.is_admin_flag = is_admin
    
    def is_admin(self):
        return self.is_admin_flag


class MockPost:
    def __init__(self, user_id, published=True):
        self.user_id = user_id
        self.published = published


class PostPolicy(Policy):
    def view(self, user, post):
        return post.published or user.id == post.user_id
    
    def update(self, user, post):
        return user.id == post.user_id
    
    def delete(self, user, post):
        return user.id == post.user_id or user.is_admin()


class AdminPolicy(Policy):
    def before(self, user, ability):
        if user.is_admin():
            return True
        return None


class AsyncPolicy(Policy):
    async def view(self, user, post):
        await asyncio.sleep(0.001)
        return True


class PolicyWithDependencies(Policy):
    def __init__(self, dep):
        self.dep = dep
    
    def view(self, user, post):
        return self.dep == 'test'


class TestPolicy:
    def test_gate_can_register_policy(self):
        container = Container()
        gate = Gate(container)
        
        gate.policy(MockPost, PostPolicy)
        
        assert MockPost in gate.policies
        assert gate.policies[MockPost] == PostPolicy
    
    def test_gate_checks_policy_method(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
    
    def test_policy_method_receives_user_and_model(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
        
        post2 = MockPost(user_id=2)
        assert gate.allows('update', post2) is False
    
    def test_policy_before_method_can_override(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1, is_admin=True)
        post = MockPost(user_id=2)
        
        gate.policy(MockPost, AdminPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
    
    def test_policy_before_returns_none_continues_check(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1, is_admin=False)
        post = MockPost(user_id=1)
        
        class PolicyWithBefore(Policy):
            def before(self, user, ability):
                return None
            
            def view(self, user, post):
                return True
        
        gate.policy(MockPost, PolicyWithBefore)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_policy_is_resolved_from_container(self):
        container = Container()
        container.bind('test_dep', lambda c: 'test')
        
        def make_policy(c):
            return PolicyWithDependencies(c.make('test_dep'))
        
        container.bind(PolicyWithDependencies, make_policy)
        
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PolicyWithDependencies)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_gate_finds_policy_by_model_class(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_policy_allows_when_method_returns_true(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1, published=True)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_policy_denies_when_method_returns_false(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.denies('update', post) is True
    
    def test_policy_denies_when_method_missing(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.denies('nonexistent', post) is True
    
    def test_policy_supports_dependency_injection(self):
        container = Container()
        container.bind('test_dep', lambda c: 'test')
        container.bind(PolicyWithDependencies, lambda c: PolicyWithDependencies(c.make('test_dep')))
        
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PolicyWithDependencies)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_policy_handles_async_methods(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, AsyncPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('view', post) is True
    
    def test_multiple_policies_can_be_registered(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        class Comment:
            def __init__(self, user_id):
                self.user_id = user_id
        
        class CommentPolicy(Policy):
            def update(self, user, comment):
                return user.id == comment.user_id
        
        gate.policy(MockPost, PostPolicy)
        gate.policy(Comment, CommentPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
        
        comment = Comment(1)
        assert gate.allows('update', comment) is True
    
    def test_policy_checks_model_instance(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.policy(MockPost, PostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update', post) is True
    
    def test_policy_checks_model_class(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        
        class CreatePostPolicy(Policy):
            def create(self, user, post_class):
                return True
        
        gate.policy(MockPost, CreatePostPolicy)
        gate.user_resolver = lambda: user
        
        assert gate.allows('create', MockPost) is True
