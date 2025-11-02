import pytest
from larapy.validation.form_request import FormRequest
from larapy.validation.exceptions import ValidationException422, RedirectException


class MockRequest:
    def __init__(self, accepts_json=False, url='/test'):
        self.accepts_json = accepts_json
        self._url = url
        self._session = {}
    
    def header(self, key, default=''):
        if key == 'Accept' and self.accepts_json:
            return 'application/json'
        return default
    
    def url(self):
        return self._url
    
    def session(self):
        return MockSession(self._session)
    
    def expectsJson(self):
        return self.accepts_json


class MockSession:
    def __init__(self, data):
        self._data = data
    
    def flash(self, key, value):
        self._data[key] = value


class SimpleRequest(FormRequest):
    def rules(self):
        return {
            'email': 'required|email',
            'password': 'required|min:8'
        }


class TestFormRequestErrors:
    
    def test_validation_fails_json_response(self):
        mock_request = MockRequest(accepts_json=True)
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'short'},
            mock_request
        )
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        assert exc.value.status_code == 422
        errors = exc.value.get_errors()
        assert errors.has('email')
    
    def test_validation_fails_redirect_response(self):
        mock_request = MockRequest(accepts_json=False, url='/register')
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'short'},
            mock_request
        )
        
        with pytest.raises(RedirectException) as exc:
            request.validated()
        
        assert exc.value.get_url() == '/register'
        assert exc.value.get_input() is not None
    
    def test_errors_flashed_to_session(self):
        mock_request = MockRequest(accepts_json=False)
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'short'},
            mock_request
        )
        
        with pytest.raises(RedirectException):
            request.validated()
        
        assert 'errors' in mock_request._session
        assert 'old' in mock_request._session
    
    def test_old_input_flashed_to_session(self):
        mock_request = MockRequest(accepts_json=False)
        data = {'email': 'test@example.com', 'password': 'short'}
        request = SimpleRequest(data, mock_request)
        
        with pytest.raises(RedirectException):
            request.validated()
        
        assert mock_request._session['old'] == data
    
    def test_custom_redirect_url(self):
        mock_request = MockRequest(accepts_json=False)
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'short'},
            mock_request
        )
        request.redirect('/custom-url')
        
        with pytest.raises(RedirectException) as exc:
            request.validated()
        
        assert exc.value.get_url() == '/custom-url'
    
    def test_custom_redirect_route(self):
        mock_request = MockRequest(accepts_json=False)
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'short'},
            mock_request
        )
        request.setRouteResolver(lambda route: f'/routes/{route}')
        request.redirectToRoute('register')
        
        with pytest.raises(RedirectException) as exc:
            request.validated()
        
        assert exc.value.get_url() == '/routes/register'
    
    def test_422_status_code_for_json(self):
        mock_request = MockRequest(accepts_json=True)
        request = SimpleRequest(
            {'email': 'invalid'},
            mock_request
        )
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        assert exc.value.status_code == 422
    
    def test_error_messages_in_json(self):
        mock_request = MockRequest(accepts_json=True)
        request = SimpleRequest(
            {'email': 'invalid', 'password': 'sh'},
            mock_request
        )
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        error_dict = exc.value.to_dict()
        assert 'message' in error_dict
        assert 'errors' in error_dict
        assert error_dict['message'] == 'The given data was invalid.'
    
    def test_multiple_validation_errors(self):
        class MultiFieldRequest(FormRequest):
            def rules(self):
                return {
                    'name': 'required|string',
                    'email': 'required|email',
                    'age': 'required|numeric|min:18',
                    'website': 'required|url'
                }
        
        mock_request = MockRequest(accepts_json=True)
        request = MultiFieldRequest(
            {
                'name': '',
                'email': 'invalid',
                'age': '10',
                'website': 'not-a-url'
            },
            mock_request
        )
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        errors = exc.value.get_errors()
        assert errors.has('name')
        assert errors.has('email')
        assert errors.has('age')
        assert errors.has('website')
    
    def test_custom_error_messages(self):
        class CustomMessageRequest(FormRequest):
            def rules(self):
                return {'email': 'required|email'}
            
            def messages(self):
                return {'email.email': 'Please provide a valid email address.'}
        
        mock_request = MockRequest(accepts_json=True)
        request = CustomMessageRequest({'email': 'invalid'}, mock_request)
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        errors = exc.value.get_errors()
        assert 'Please provide a valid email address.' in str(errors.first('email'))
