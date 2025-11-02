import pytest
import asyncio
from larapy.auth.gate import Gate
from larapy.auth.policy import Policy
from larapy.auth.exceptions import AuthorizationException
from larapy.container import Container


class MockUser:
    def __init__(self, id, is_admin=False, is_super_admin=False):
        self.id = id
        self.is_admin_flag = is_admin
        self.is_super_admin_flag = is_super_admin
    
    def is_admin(self):
        return self.is_admin_flag
    
    def is_super_admin(self):
        return self.is_super_admin_flag


class MockPost:
    def __init__(self, user_id, published=True):
        self.user_id = user_id
        self.published = published


class MockRequest:
    def __init__(self, user=None):
        self._user = user
    
    def user(self):
        return self._user


class TestGate:
    def test_gate_can_define_ability(self):
        container = Container()
        gate = Gate(container)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        
        assert 'update-post' in gate.abilities
    
    def test_gate_checks_ability_with_callback(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_denies_undefined_ability(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.user_resolver = lambda: user
        
        assert gate.allows('undefined-ability', post) is False
    
    def test_gate_allows_returns_true_when_authorized(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_denies_returns_true_when_not_authorized(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        assert gate.denies('update-post', post) is True
    
    def test_gate_authorize_throws_exception_when_denied(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        with pytest.raises(AuthorizationException):
            gate.authorize('update-post', post)
    
    def test_gate_authorize_passes_when_allowed(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        gate.authorize('update-post', post)
    
    def test_gate_any_returns_true_if_any_ability_allowed(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.define('delete-post', lambda user, post: False)
        gate.user_resolver = lambda: user
        
        assert gate.any(['update-post', 'delete-post'], post) is True
    
    def test_gate_none_returns_true_if_no_ability_allowed(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.define('delete-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user
        
        assert gate.none(['update-post', 'delete-post'], post) is True
    
    def test_gate_for_user_creates_new_gate_for_user(self):
        container = Container()
        gate = Gate(container)
        user1 = MockUser(1)
        user2 = MockUser(2)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: user1
        
        user2_gate = gate.for_user(user2)
        
        assert gate.allows('update-post', post) is True
        assert user2_gate.allows('update-post', post) is False
    
    def test_gate_before_callback_can_allow_all(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1, is_admin=True)
        post = MockPost(user_id=2)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.before(lambda user, ability: True if user.is_admin() else None)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_before_callback_can_deny_all(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.before(lambda user, ability: False)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is False
    
    def test_gate_before_callback_can_pass_through(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.before(lambda user, ability: None)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_after_callback_is_executed(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        executed = []
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.after(lambda user, ability, result: executed.append((ability, result)))
        gate.user_resolver = lambda: user
        
        gate.allows('update-post', post)
        
        assert len(executed) == 1
        assert executed[0] == ('update-post', True)
    
    def test_gate_checks_with_multiple_arguments(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        def check_update(user, post):
            return user.id == post.user_id
        
        gate.define('update-post', check_update)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_handles_guest_users(self):
        container = Container()
        gate = Gate(container)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        gate.user_resolver = lambda: None
        
        assert gate.allows('update-post', post) is False
    
    def test_gate_resolves_user_from_request(self):
        container = Container()
        user = MockUser(1)
        request = MockRequest(user)
        container.bind('request', lambda c: request)
        
        gate = Gate(container)
        post = MockPost(user_id=1)
        
        gate.define('update-post', lambda user, post: user.id == post.user_id)
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_handles_async_callbacks(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        async def async_check(user, post):
            await asyncio.sleep(0.001)
            return user.id == post.user_id
        
        gate.define('update-post', async_check)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
    
    def test_gate_passes_ability_to_callback(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        captured = []
        
        def capture_before(user, ability):
            captured.append(ability)
            return None
        
        gate.define('update-post', lambda user, post: True)
        gate.before(capture_before)
        gate.user_resolver = lambda: user
        
        gate.allows('update-post', post)
        
        assert 'update-post' in captured
    
    def test_gate_passes_arguments_to_callback(self):
        container = Container()
        gate = Gate(container)
        user = MockUser(1)
        post = MockPost(user_id=1)
        
        def check_with_args(user, post):
            return post.user_id == 1
        
        gate.define('update-post', check_with_args)
        gate.user_resolver = lambda: user
        
        assert gate.allows('update-post', post) is True
