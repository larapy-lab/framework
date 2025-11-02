import pytest
from larapy.validation.form_request import FormRequest
from larapy.validation.exceptions import AuthorizationException


class UnauthorizedRequest(FormRequest):
    def rules(self):
        return {'email': 'required|email'}
    
    def authorize(self):
        return False


class UserBasedRequest(FormRequest):
    def rules(self):
        return {'title': 'required|string'}
    
    def authorize(self):
        user = self.user()
        return user is not None and user.get('is_admin', False)


class TestFormRequestAuthorization:
    
    def test_unauthorized_throws_exception(self):
        request = UnauthorizedRequest({'email': 'test@example.com'})
        
        with pytest.raises(AuthorizationException) as exc:
            request.validated()
        
        assert exc.value.message == 'This action is unauthorized.'
        assert exc.value.status_code == 403
    
    def test_authorized_allows_validation(self):
        class AuthorizedRequest(FormRequest):
            def rules(self):
                return {'email': 'required|email'}
            
            def authorize(self):
                return True
        
        request = AuthorizedRequest({'email': 'test@example.com'})
        validated = request.validated()
        
        assert validated['email'] == 'test@example.com'
    
    def test_authorization_with_user(self):
        admin_user = {'id': 1, 'name': 'Admin', 'is_admin': True}
        request = UserBasedRequest({'title': 'Test Post'})
        request.setUserResolver(lambda: admin_user)
        
        validated = request.validated()
        assert validated['title'] == 'Test Post'
    
    def test_authorization_with_guest(self):
        request = UserBasedRequest({'title': 'Test Post'})
        request.setUserResolver(lambda: None)
        
        with pytest.raises(AuthorizationException):
            request.validated()
    
    def test_authorization_with_non_admin_user(self):
        regular_user = {'id': 2, 'name': 'User', 'is_admin': False}
        request = UserBasedRequest({'title': 'Test Post'})
        request.setUserResolver(lambda: regular_user)
        
        with pytest.raises(AuthorizationException):
            request.validated()
    
    def test_authorization_called_before_validation(self):
        order = []
        
        class OrderRequest(FormRequest):
            def rules(self):
                return {'email': 'required|email'}
            
            def authorize(self):
                order.append('authorize')
                return True
            
            def prepareForValidation(self):
                order.append('prepare')
        
        request = OrderRequest({'email': 'test@example.com'})
        request.validated()
        
        assert order[0] == 'authorize'
        assert 'prepare' in order
    
    def test_custom_authorization_message(self):
        class CustomMessageRequest(FormRequest):
            def rules(self):
                return {'email': 'required|email'}
            
            def authorize(self):
                raise AuthorizationException('You must be an admin to perform this action.')
        
        request = CustomMessageRequest({'email': 'test@example.com'})
        
        with pytest.raises(AuthorizationException) as exc:
            request.validated()
        
        assert exc.value.message == 'You must be an admin to perform this action.'
