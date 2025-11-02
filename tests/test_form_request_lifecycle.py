import pytest
from larapy.validation.form_request import FormRequest
from larapy.validation.validator import Validator
from larapy.validation.exceptions import AuthorizationException, ValidationException422
from larapy.validation.validation_exception import ValidationException
from larapy.http.request import Request


class TestLifecycleRequest(FormRequest):
    def __init__(self, data=None, request=None):
        # If no request provided, create a JSON request for API testing
        if request is None and data is not None:
            request = Request()
            request.set_header('Accept', 'application/json')
            request.merge(data)
        super().__init__(data, request)
        self.prepare_called = False
        self.with_validator_called = False
        self.passed_called = False
        self.failed_called = False
    
    def rules(self):
        return {
            'email': 'required|email',
            'name': 'required|string'
        }
    
    def prepareForValidation(self):
        self.prepare_called = True
        if 'username' in self._data and 'name' not in self._data:
            self._data['name'] = self._data['username']
    
    def withValidator(self, validator):
        self.with_validator_called = True
        validator.after(lambda v: None)
    
    def passedValidation(self):
        self.passed_called = True
    
    def failedValidation(self):
        self.failed_called = True


class TestFormRequestLifecycle:
    
    def test_prepare_for_validation_called(self):
        request = TestLifecycleRequest({
            'username': 'john',
            'email': 'john@example.com'
        })
        
        validated = request.validated()
        
        assert request.prepare_called is True
        assert validated['name'] == 'john'
    
    def test_with_validator_customization(self):
        request = TestLifecycleRequest({
            'name': 'John',
            'email': 'john@example.com'
        })
        
        request.validated()
        
        assert request.with_validator_called is True
    
    def test_passed_validation_hook(self):
        request = TestLifecycleRequest({
            'name': 'John',
            'email': 'john@example.com'
        })
        
        request.validated()
        
        assert request.passed_called is True
        assert request.failed_called is False
    
    def test_failed_validation_hook(self):
        request = TestLifecycleRequest({
            'name': 'John',
            'email': 'invalid-email'
        })
        
        with pytest.raises(ValidationException422):
            request.validated()
        
        assert request.failed_called is True
        assert request.passed_called is False
    
    def test_lifecycle_execution_order(self):
        order = []
        
        class OrderTrackingRequest(FormRequest):
            def rules(self):
                return {'email': 'required|email'}
            
            def prepareForValidation(self):
                order.append('prepare')
            
            def withValidator(self, validator):
                order.append('with_validator')
            
            def passedValidation(self):
                order.append('passed')
        
        request = OrderTrackingRequest({'email': 'test@example.com'})
        request.validated()
        
        assert order == ['prepare', 'with_validator', 'passed']
    
    def test_validator_stop_on_first_failure(self):
        class StopOnFirstRequest(FormRequest):
            def rules(self):
                return {
                    'email': 'required|email',
                    'name': 'required|string',
                    'age': 'required|numeric'
                }
            
            def withValidator(self, validator):
                validator.stopOnFirstFailure()
        
        # Create a JSON request
        req = Request()
        req.set_header('Accept', 'application/json')
        req.merge({
            'email': 'invalid',
            'name': '',
            'age': 'not-a-number'
        })
        
        request = StopOnFirstRequest(request=req)
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        errors = exc.value.get_errors()
        assert errors.count() == 1
    
    def test_merge_additional_data(self):
        request = TestLifecycleRequest({
            'email': 'john@example.com'
        })
        
        request.merge({'name': 'John Doe'})
        
        validated = request.validated()
        assert validated['name'] == 'John Doe'
    
    def test_replace_data(self):
        request = TestLifecycleRequest({
            'email': 'old@example.com',
            'name': 'Old Name'
        })
        
        request.replace({
            'email': 'new@example.com',
            'name': 'New Name'
        })
        
        assert request.input('email') == 'new@example.com'
        assert request.input('name') == 'New Name'
    
    def test_validated_returns_clean_data(self):
        class SelectiveRequest(FormRequest):
            def rules(self):
                return {
                    'email': 'required|email',
                    'name': 'required|string'
                }
        
        request = SelectiveRequest({
            'email': 'john@example.com',
            'name': 'John',
            'extra_field': 'should not be in validated',
            'another_extra': 'also excluded'
        })
        
        validated = request.validated()
        
        assert 'email' in validated
        assert 'name' in validated
        assert 'extra_field' not in validated
        assert 'another_extra' not in validated
    
    def test_safe_alias_for_validated(self):
        request = TestLifecycleRequest({
            'email': 'john@example.com',
            'name': 'John'
        })
        
        validated = request.validated()
        safe = request.safe()
        
        assert validated == safe
    
    def test_input_helpers(self):
        request = TestLifecycleRequest({
            'email': 'john@example.com',
            'name': 'John',
            'age': 25
        })
        
        assert request.input('email') == 'john@example.com'
        assert request.input('missing', 'default') == 'default'
        assert request.has('email') is True
        assert request.has('missing') is False
        assert request.filled('email') is True
        assert request.filled('missing') is False
    
    def test_all_returns_copy(self):
        request = TestLifecycleRequest({
            'email': 'john@example.com',
            'name': 'John'
        })
        
        data = request.all()
        data['modified'] = 'value'
        
        assert 'modified' not in request.all()


class TestCustomAttributes:
    
    def test_custom_attributes_in_messages(self):
        class AttributeRequest(FormRequest):
            def rules(self):
                return {
                    'user_email': 'required|email'
                }
            
            def attributes(self):
                return {
                    'user_email': 'email address'
                }
        
        # Create a JSON request
        req = Request()
        req.set_header('Accept', 'application/json')
        req.merge({'user_email': 'invalid'})
        
        request = AttributeRequest(request=req)
        
        with pytest.raises(ValidationException422) as exc:
            request.validated()
        
        errors = exc.value.get_errors()
        error_messages = errors.messages()
        assert 'user_email' in error_messages
