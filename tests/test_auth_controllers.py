import pytest
from unittest.mock import Mock, MagicMock, patch
from larapy.auth.controllers import (
    LoginController,
    RegisterController,
    ForgotPasswordController,
    ResetPasswordController,
    VerificationController
)
from larapy.auth.passwords.password_broker import PasswordBroker
from larapy.http.response import RedirectResponse, JsonResponse
from larapy.validation.validation_exception import ValidationException


class TestLoginController:
    @pytest.fixture
    def auth_manager(self):
        auth = Mock()
        guard = Mock()
        guard.attempt = Mock(return_value=True)
        guard.user = Mock(return_value=Mock(id=1, email='test@example.com'))
        guard.logout = Mock()
        auth.guard = Mock(return_value=guard)
        return auth
    
    @pytest.fixture
    def controller(self, auth_manager):
        return LoginController(auth_manager)
    
    def test_show_login_form(self, controller):
        request = Mock()
        response = controller.showLoginForm(request)
        assert isinstance(response, type(response))
        assert 'Login' in response.content()
    
    def test_login_success(self, controller, auth_manager):
        request = Mock()
        request.all = Mock(return_value={'email': 'test@example.com', 'password': 'password123'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'test@example.com', 'password': 'password123'}.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.regenerate = Mock()
        
        response = controller.login(request)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/dashboard'
        auth_manager.guard().attempt.assert_called_once()
    
    def test_login_failure(self, controller, auth_manager):
        auth_manager.guard().attempt = Mock(return_value=False)
        
        request = Mock()
        request.all = Mock(return_value={'email': 'test@example.com', 'password': 'wrongpassword'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'test@example.com', 'password': 'wrongpassword'}.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.login(request)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/login'
        request._session.flash.assert_called_with('error', 'These credentials do not match our records.')
    
    def test_login_json_success(self, controller):
        request = Mock()
        request.all = Mock(return_value={'email': 'test@example.com', 'password': 'password123'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'test@example.com', 'password': 'password123'}.get(k, d))
        request.expectsJson = Mock(return_value=True)
        request._session = Mock()
        request._session.regenerate = Mock()
        
        response = controller.login(request)
        assert isinstance(response, JsonResponse)
        assert response.getData()['message'] == 'Logged in successfully.'
    
    def test_logout(self, controller, auth_manager):
        request = Mock()
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.invalidate = Mock()
        request._session.regenerateToken = Mock()
        
        response = controller.logout(request)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/login'
        auth_manager.guard().logout.assert_called_once()
    
    def test_login_validation_failure(self, controller):
        request = Mock()
        request.all = Mock(return_value={'email': 'invalid', 'password': ''})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'invalid', 'password': ''}.get(k, d))
        
        with pytest.raises(ValidationException):
            controller.login(request)


class TestRegisterController:
    @pytest.fixture
    def auth_manager(self):
        auth = Mock()
        guard = Mock()
        guard.login = Mock()
        auth.guard = Mock(return_value=guard)
        return auth
    
    @pytest.fixture
    def user_provider(self):
        provider = Mock()
        provider.create = Mock(return_value=1)
        return provider
    
    @pytest.fixture
    def controller(self, auth_manager, user_provider):
        return RegisterController(auth_manager, user_provider)
    
    def test_show_registration_form(self, controller):
        request = Mock()
        response = controller.showRegistrationForm(request)
        assert 'Register' in response.content()
    
    def test_register_success(self, controller, auth_manager, user_provider):
        request = Mock()
        request.all = Mock(return_value={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'password_confirmation': 'password123'
        })
        request.input = Mock(side_effect=lambda k, d=None: {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'password_confirmation': 'password123'
        }.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.regenerate = Mock()
        
        response = controller.register(request)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/dashboard'
        user_provider.create.assert_called_once()
        auth_manager.guard().login.assert_called_once()
    
    def test_register_json_success(self, controller):
        request = Mock()
        request.all = Mock(return_value={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'password_confirmation': 'password123'
        })
        request.input = Mock(side_effect=lambda k, d=None: {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'password_confirmation': 'password123'
        }.get(k, d))
        request.expectsJson = Mock(return_value=True)
        request._session = Mock()
        request._session.regenerate = Mock()
        
        response = controller.register(request)
        assert isinstance(response, JsonResponse)
        assert response.getData()['message'] == 'Registration successful.'
    
    def test_register_validation_failure(self, controller):
        request = Mock()
        request.all = Mock(return_value={
            'name': 'John Doe',
            'email': 'invalid-email',
            'password': 'short',
            'password_confirmation': 'different'
        })
        request.input = Mock(side_effect=lambda k, d=None: {
            'name': 'John Doe',
            'email': 'invalid-email',
            'password': 'short',
            'password_confirmation': 'different'
        }.get(k, d))
        
        with pytest.raises(ValidationException):
            controller.register(request)


class TestForgotPasswordController:
    @pytest.fixture
    def password_broker(self):
        broker = Mock(spec=PasswordBroker)
        broker.RESET_LINK_SENT = PasswordBroker.RESET_LINK_SENT
        broker.INVALID_USER = PasswordBroker.INVALID_USER
        broker.THROTTLED = PasswordBroker.THROTTLED
        broker.send_reset_link_sync = Mock(return_value=PasswordBroker.RESET_LINK_SENT)
        return broker
    
    @pytest.fixture
    def controller(self, password_broker):
        return ForgotPasswordController(password_broker)
    
    def test_show_link_request_form(self, controller):
        request = Mock()
        response = controller.showLinkRequestForm(request)
        assert 'Reset Password' in response.content()
    
    def test_send_reset_link_success(self, controller, password_broker):
        request = Mock()
        request.all = Mock(return_value={'email': 'test@example.com'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'test@example.com'}.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.sendResetLinkEmail(request)
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('status', 'We have emailed your password reset link!')
        password_broker.send_reset_link_sync.assert_called_once()
    
    def test_send_reset_link_invalid_user(self, controller, password_broker):
        password_broker.send_reset_link_sync = Mock(return_value=PasswordBroker.INVALID_USER)
        
        request = Mock()
        request.all = Mock(return_value={'email': 'notfound@example.com'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'notfound@example.com'}.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.sendResetLinkEmail(request)
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('error', 'We cannot find a user with that email address.')
    
    def test_send_reset_link_json_success(self, controller):
        request = Mock()
        request.all = Mock(return_value={'email': 'test@example.com'})
        request.input = Mock(side_effect=lambda k, d=None: {'email': 'test@example.com'}.get(k, d))
        request.expectsJson = Mock(return_value=True)
        
        response = controller.sendResetLinkEmail(request)
        assert isinstance(response, JsonResponse)
        assert response.getData()['message'] == 'We have emailed your password reset link!'


class TestResetPasswordController:
    @pytest.fixture
    def password_broker(self):
        broker = Mock(spec=PasswordBroker)
        broker.PASSWORD_RESET = PasswordBroker.PASSWORD_RESET
        broker.INVALID_USER = PasswordBroker.INVALID_USER
        broker.INVALID_TOKEN = PasswordBroker.INVALID_TOKEN
        broker.THROTTLED = PasswordBroker.THROTTLED
        broker.reset_sync = Mock(return_value=PasswordBroker.PASSWORD_RESET)
        return broker
    
    @pytest.fixture
    def auth_manager(self):
        return Mock()
    
    @pytest.fixture
    def controller(self, password_broker, auth_manager):
        return ResetPasswordController(password_broker, auth_manager)
    
    def test_show_reset_form(self, controller):
        request = Mock()
        request.input = Mock(return_value='test@example.com')
        
        response = controller.showResetForm(request, 'test-token')
        assert 'Reset Password' in response.content()
        assert 'test-token' in response.content()
    
    def test_reset_password_success(self, controller, password_broker):
        request = Mock()
        request.all = Mock(return_value={
            'token': 'test-token',
            'email': 'test@example.com',
            'password': 'newpassword123',
            'password_confirmation': 'newpassword123'
        })
        request.input = Mock(side_effect=lambda k, d=None: {
            'token': 'test-token',
            'email': 'test@example.com',
            'password': 'newpassword123',
            'password_confirmation': 'newpassword123'
        }.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.reset(request)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/login'
        request._session.flash.assert_called_with('status', 'Your password has been reset!')
        password_broker.reset_sync.assert_called_once()
    
    def test_reset_password_invalid_token(self, controller, password_broker):
        password_broker.reset_sync = Mock(return_value=PasswordBroker.INVALID_TOKEN)
        
        request = Mock()
        request.all = Mock(return_value={
            'token': 'invalid-token',
            'email': 'test@example.com',
            'password': 'newpassword123',
            'password_confirmation': 'newpassword123'
        })
        request.input = Mock(side_effect=lambda k, d=None: {
            'token': 'invalid-token',
            'email': 'test@example.com',
            'password': 'newpassword123',
            'password_confirmation': 'newpassword123'
        }.get(k, d))
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.reset(request)
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('error', 'This password reset token is invalid.')


class TestVerificationController:
    @pytest.fixture
    def auth_manager(self):
        auth = Mock()
        guard = Mock()
        user = Mock()
        user.get = Mock(side_effect=lambda k, d=None: {'id': 1, 'email': 'test@example.com', 'email_verified_at': None}.get(k, d))
        guard.user = Mock(return_value=user)
        auth.guard = Mock(return_value=guard)
        return auth
    
    @pytest.fixture
    def user_provider(self):
        provider = Mock()
        user = Mock()
        user.get = Mock(side_effect=lambda k, d=None: {'id': 1, 'email': 'test@example.com', 'email_verified_at': None}.get(k, d))
        user._attributes = {'email_verified_at': None}
        provider.retrieveById = Mock(return_value=user)
        return provider
    
    @pytest.fixture
    def controller(self, auth_manager, user_provider):
        return VerificationController(auth_manager, user_provider)
    
    def test_show_verification_notice(self, controller):
        request = Mock()
        response = controller.show(request)
        assert 'Verify' in response.content()
    
    def test_verify_email_success(self, controller, user_provider):
        import hashlib
        request = Mock()
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        email = 'test@example.com'
        hash_value = hashlib.sha1(email.encode()).hexdigest()
        
        response = controller.verify(request, '1', hash_value)
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('status', 'Your email has been verified!')
    
    def test_verify_email_invalid_hash(self, controller):
        request = Mock()
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.verify(request, '1', 'invalid-hash')
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('error', 'Invalid verification link.')
    
    def test_resend_verification_email(self, controller):
        request = Mock()
        request.expectsJson = Mock(return_value=False)
        request._session = Mock()
        request._session.flash = Mock()
        
        response = controller.resend(request)
        assert isinstance(response, RedirectResponse)
        request._session.flash.assert_called_with('status', 'A fresh verification link has been sent to your email address.')


class TestMiddleware:
    def test_ensure_email_is_verified_verified_user(self):
        from larapy.auth.middleware import EnsureEmailIsVerified
        
        auth_manager = Mock()
        guard = Mock()
        user = Mock()
        user.get = Mock(side_effect=lambda k, d=None: {'email_verified_at': '2024-01-01'}.get(k, d))
        guard.user = Mock(return_value=user)
        guard.setRequest = Mock()
        guard.setSession = Mock()
        auth_manager.guard = Mock(return_value=guard)
        
        middleware = EnsureEmailIsVerified(auth_manager)
        request = Mock()
        request._session = Mock()
        next_handler = Mock(return_value=Mock())
        
        response = middleware.handle(request, next_handler)
        next_handler.assert_called_once()
    
    def test_ensure_email_is_verified_unverified_user(self):
        from larapy.auth.middleware import EnsureEmailIsVerified
        
        auth_manager = Mock()
        guard = Mock()
        user = Mock()
        user.get = Mock(return_value=None)
        guard.user = Mock(return_value=user)
        guard.setRequest = Mock()
        guard.setSession = Mock()
        auth_manager.guard = Mock(return_value=guard)
        
        middleware = EnsureEmailIsVerified(auth_manager)
        request = Mock()
        request._session = Mock()
        request.expectsJson = Mock(return_value=False)
        next_handler = Mock()
        
        response = middleware.handle(request, next_handler)
        assert isinstance(response, RedirectResponse)
        assert response.getTargetUrl() == '/email/verify'
