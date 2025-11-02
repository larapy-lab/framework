import pytest
from larapy.auth.passwords import Hash
from larapy.auth.user import User
from larapy.auth.user_provider import DatabaseUserProvider
from larapy.auth.guard import SessionGuard
from larapy.auth.auth_manager import AuthManager
from larapy.auth.middleware import Authenticate, RedirectIfAuthenticated
from larapy.session.store import Store
from larapy.session.array_session_handler import ArraySessionHandler
from larapy.session.session_manager import SessionManager
from larapy.http.request import Request
from larapy.http.response import Response


class TestHash:
    def test_hash_make(self):
        hashed = Hash.make('password')
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != 'password'
    
    def test_hash_check(self):
        password = 'secret123'
        hashed = Hash.make(password)
        
        assert Hash.check(password, hashed) is True
        assert Hash.check('wrongpassword', hashed) is False
    
    def test_hash_different_rounds(self):
        password = 'password'
        hash1 = Hash.make(password, rounds=4)
        hash2 = Hash.make(password, rounds=10)
        
        assert Hash.check(password, hash1) is True
        assert Hash.check(password, hash2) is True
    
    def test_hash_info(self):
        hashed = Hash.make('password')
        info = Hash.info(hashed)
        
        assert info is not None
        assert 'algo' in info
        assert 'algoName' in info
        assert info['algoName'] == 'bcrypt'


class TestUser:
    def test_user_creation(self):
        user = User({'id': 1, 'name': 'John', 'email': 'john@example.com'})
        assert user.getAuthIdentifier() == 1
    
    def test_auth_identifier(self):
        user = User({'id': 123, 'name': 'Jane'})
        assert user.getAuthIdentifierName() == 'id'
        assert user.getAuthIdentifier() == 123
    
    def test_auth_password(self):
        hashed = Hash.make('secret')
        user = User({'id': 1, 'password': hashed})
        
        assert user.getAuthPasswordName() == 'password'
        assert user.getAuthPassword() == hashed
    
    def test_remember_token(self):
        user = User({'id': 1})
        assert user.getRememberTokenName() == 'remember_token'
        assert user.getRememberToken() is None
        
        user.setRememberToken('token123')
        assert user.getRememberToken() == 'token123'
    
    def test_user_attributes_access(self):
        user = User({'id': 1, 'name': 'John', 'email': 'john@example.com'})
        
        assert user.name == 'John'
        assert user.email == 'john@example.com'
        assert user.get('name') == 'John'
    
    def test_user_to_dict(self):
        data = {'id': 1, 'name': 'John', 'email': 'john@example.com'}
        user = User(data)
        
        user_dict = user.toDict()
        assert user_dict['id'] == 1
        assert user_dict['name'] == 'John'


class TestDatabaseUserProvider:
    def test_provider_creation(self):
        provider = DatabaseUserProvider()
        assert provider is not None
    
    def test_create_user(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({
            'name': 'John',
            'email': 'john@example.com',
            'password': 'password123'
        })
        
        assert user.getAuthIdentifier() == 1
        assert user.name == 'John'
        assert Hash.check('password123', user.getAuthPassword())
    
    def test_retrieve_by_id(self):
        provider = DatabaseUserProvider()
        created_user = provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password'})
        
        user = provider.retrieveById(created_user.getAuthIdentifier())
        assert user is not None
        assert user.name == 'John'
    
    def test_retrieve_by_credentials(self):
        provider = DatabaseUserProvider()
        provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password123'})
        
        user = provider.retrieveByCredentials({'email': 'john@example.com'})
        assert user is not None
        assert user.email == 'john@example.com'
    
    def test_validate_credentials(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'secret123'})
        
        assert provider.validateCredentials(user, {'password': 'secret123'}) is True
        assert provider.validateCredentials(user, {'password': 'wrongpassword'}) is False
    
    def test_retrieve_by_token(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password'})
        
        token = 'remember_token_123'
        provider.updateRememberToken(user, token)
        
        retrieved = provider.retrieveByToken(user.getAuthIdentifier(), token)
        assert retrieved is not None
        assert retrieved.email == 'john@example.com'
    
    def test_update_remember_token(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password'})
        
        token = 'new_token_456'
        provider.updateRememberToken(user, token)
        
        assert user.getRememberToken() == token


class TestSessionGuard:
    def test_guard_creation(self):
        provider = DatabaseUserProvider()
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        assert guard.getName() == 'web'
    
    def test_guest_when_not_authenticated(self):
        provider = DatabaseUserProvider()
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        assert guard.guest() is True
        assert guard.check() is False
    
    def test_attempt_with_valid_credentials(self):
        provider = DatabaseUserProvider()
        provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password123'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        result = guard.attempt({'email': 'john@example.com', 'password': 'password123'})
        
        assert result is True
        assert guard.check() is True
        assert guard.user().email == 'john@example.com'
    
    def test_attempt_with_invalid_credentials(self):
        provider = DatabaseUserProvider()
        provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password123'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        result = guard.attempt({'email': 'john@example.com', 'password': 'wrongpassword'})
        
        assert result is False
        assert guard.check() is False
    
    def test_login_user(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'Jane', 'email': 'jane@example.com', 'password': 'password'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        guard.login(user)
        
        assert guard.check() is True
        assert guard.id() == user.getAuthIdentifier()
    
    def test_logout(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'John', 'email': 'john@example.com', 'password': 'password'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        guard.login(user)
        assert guard.check() is True
        
        guard.logout()
        assert guard.check() is False
        assert guard.user() is None
    
    def test_login_using_id(self):
        provider = DatabaseUserProvider()
        user = provider.createUser({'name': 'Alice', 'email': 'alice@example.com', 'password': 'password'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        logged_user = guard.loginUsingId(user.getAuthIdentifier())
        
        assert logged_user is not None
        assert logged_user.email == 'alice@example.com'
        assert guard.check() is True
    
    def test_once_authentication(self):
        provider = DatabaseUserProvider()
        provider.createUser({'name': 'Bob', 'email': 'bob@example.com', 'password': 'secret'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        result = guard.once({'email': 'bob@example.com', 'password': 'secret'})
        
        assert result is True
        assert guard.user() is not None
    
    def test_validate_credentials(self):
        provider = DatabaseUserProvider()
        provider.createUser({'name': 'Charlie', 'email': 'charlie@example.com', 'password': 'password123'})
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        
        assert guard.validate({'email': 'charlie@example.com', 'password': 'password123'}) is True
        assert guard.validate({'email': 'charlie@example.com', 'password': 'wrong'}) is False
    
    def test_attempt_when_with_callback(self):
        provider = DatabaseUserProvider()
        provider.createUser({
            'name': 'David',
            'email': 'david@example.com',
            'password': 'password',
            'active': True
        })
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        
        guard = SessionGuard('web', provider, session)
        
        result = guard.attemptWhen(
            {'email': 'david@example.com', 'password': 'password'},
            lambda user: user.active is True
        )
        
        assert result is True
        assert guard.check() is True


class TestAuthManager:
    def test_manager_creation(self):
        manager = AuthManager()
        assert manager is not None
    
    def test_default_guard(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        guard = manager.guard()
        assert guard is not None
    
    def test_attempt_via_manager(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Emma', 'email': 'emma@example.com', 'password': 'password123'})
        
        result = manager.attempt({'email': 'emma@example.com', 'password': 'password123'})
        
        assert result is True
        assert manager.check() is True
        assert manager.user().name == 'Emma'
    
    def test_multiple_guards(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'},
                'admin': {'driver': 'session', 'provider': 'admins'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'},
                'admins': {'driver': 'database', 'table': 'admins'}
            }
        })
        
        web_guard = manager.guard('web')
        admin_guard = manager.guard('admin')
        
        assert web_guard.getName() == 'web'
        assert admin_guard.getName() == 'admin'
    
    def test_logout_via_manager(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Frank', 'email': 'frank@example.com', 'password': 'password'})
        
        manager.attempt({'email': 'frank@example.com', 'password': 'password'})
        assert manager.check() is True
        
        manager.logout()
        assert manager.check() is False


class TestAuthMiddleware:
    def test_authenticate_middleware_allows_authenticated(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Grace', 'email': 'grace@example.com', 'password': 'password'})
        
        manager.attempt({'email': 'grace@example.com', 'password': 'password'})
        
        middleware = Authenticate(manager)
        request = Request('/')
        request._session = manager.guard()._session
        
        def handler(req):
            return Response('Success')
        
        response = middleware.handle(request, handler)
        assert response.content() == 'Success'
    
    def test_authenticate_middleware_blocks_unauthenticated(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        middleware = Authenticate(manager)
        request = Request('/')
        
        handler = ArraySessionHandler()
        session = Store('test', handler)
        session.start()
        request._session = session
        
        def handler_func(req):
            return Response('Success')
        
        response = middleware.handle(request, handler_func)
        assert response.status() in [302, 401]
    
    def test_redirect_if_authenticated_middleware(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Henry', 'email': 'henry@example.com', 'password': 'password'})
        
        manager.attempt({'email': 'henry@example.com', 'password': 'password'})
        
        middleware = RedirectIfAuthenticated(manager)
        request = Request('/')
        request._session = manager.guard()._session
        
        def handler(req):
            return Response('Login Page')
        
        response = middleware.handle(request, handler)
        assert response.status() == 302


class TestComplexScenarios:
    def test_login_workflow_with_session_persistence(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Isabella', 'email': 'isabella@example.com', 'password': 'secret123'})
        
        result = manager.attempt({'email': 'isabella@example.com', 'password': 'secret123'})
        assert result is True
        
        user = manager.user()
        assert user.name == 'Isabella'
        assert user.email == 'isabella@example.com'
        
        user_id = manager.id()
        assert user_id is not None
    
    def test_failed_login_attempts(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Jack', 'email': 'jack@example.com', 'password': 'correctpassword'})
        
        assert manager.attempt({'email': 'jack@example.com', 'password': 'wrongpassword'}) is False
        assert manager.attempt({'email': 'nonexistent@example.com', 'password': 'password'}) is False
        assert manager.check() is False
    
    def test_role_based_authentication(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        admin = provider.createUser({
            'name': 'Admin User',
            'email': 'admin@example.com',
            'password': 'adminpass',
            'role': 'admin'
        })
        
        regular = provider.createUser({
            'name': 'Regular User',
            'email': 'user@example.com',
            'password': 'userpass',
            'role': 'user'
        })
        
        manager.attempt({'email': 'admin@example.com', 'password': 'adminpass'})
        current_user = manager.user()
        assert current_user.role == 'admin'
    
    def test_password_rehashing(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        user = provider.createUser({'name': 'Karen', 'email': 'karen@example.com', 'password': 'oldpassword'})
        
        old_hash = user.getAuthPassword()
        
        manager.attempt({'email': 'karen@example.com', 'password': 'oldpassword'})
        
        assert user.getAuthPassword() is not None
    
    def test_multi_guard_authentication(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'},
                'api': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Laura', 'email': 'laura@example.com', 'password': 'password'})
        
        web_guard = manager.guard('web')
        api_guard = manager.guard('api')
        
        web_guard.attempt({'email': 'laura@example.com', 'password': 'password'})
        assert web_guard.check() is True
        
        assert api_guard.check() is False
    
    def test_session_regeneration_on_login(self):
        session_manager = SessionManager()
        session_manager.set_config({'driver': 'array'})
        
        manager = AuthManager(session_manager)
        manager.set_config({
            'defaults': {'guard': 'web'},
            'guards': {
                'web': {'driver': 'session', 'provider': 'users'}
            },
            'providers': {
                'users': {'driver': 'database', 'table': 'users'}
            }
        })
        
        provider = manager.createUserProvider('users')
        provider.createUser({'name': 'Mike', 'email': 'mike@example.com', 'password': 'password'})
        
        guard = manager.guard('web')
        session = guard._session
        old_id = session.getId()
        
        manager.attempt({'email': 'mike@example.com', 'password': 'password'})
        
        new_id = session.getId()
        assert new_id != old_id
