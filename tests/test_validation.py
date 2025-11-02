import pytest
from larapy.validation.message_bag import MessageBag
from larapy.validation.validator import Validator
from larapy.validation.factory import Factory
from larapy.validation.form_request import FormRequest
from larapy.validation.validation_exception import ValidationException
from larapy.validation.rules import *


class TestMessageBag:
    def test_add_message(self):
        bag = MessageBag()
        bag.add('email', 'Email is invalid')
        assert bag.has('email')
        assert 'Email is invalid' in bag.get('email')

    def test_get_messages(self):
        bag = MessageBag()
        bag.add('email', 'First error')
        bag.add('email', 'Second error')
        messages = bag.get('email')
        assert len(messages) == 2
        assert 'First error' in messages
        assert 'Second error' in messages

    def test_first_message(self):
        bag = MessageBag()
        bag.add('email', 'First error')
        bag.add('email', 'Second error')
        assert bag.first('email') == 'First error'

    def test_all_messages(self):
        bag = MessageBag()
        bag.add('email', 'Email error')
        bag.add('password', 'Password error')
        all_messages = bag.all()
        assert len(all_messages) == 2
        assert 'Email error' in all_messages
        assert 'Password error' in all_messages

    def test_has_messages(self):
        bag = MessageBag()
        assert not bag.has('email')
        bag.add('email', 'Error')
        assert bag.has('email')

    def test_any_messages(self):
        bag = MessageBag()
        assert not bag.any()
        bag.add('email', 'Error')
        assert bag.any()

    def test_count_messages(self):
        bag = MessageBag()
        bag.add('email', 'Error 1')
        bag.add('email', 'Error 2')
        bag.add('password', 'Error 3')
        assert bag.count() == 3
        assert len(bag) == 3


class TestValidationRules:
    def test_required_rule(self):
        rule = RequiredRule()
        assert rule.passes('name', 'John', {})
        assert not rule.passes('name', '', {})
        assert not rule.passes('name', None, {})
        assert not rule.passes('name', [], {})

    def test_email_rule(self):
        rule = EmailRule()
        assert rule.passes('email', 'john@example.com', {})
        assert not rule.passes('email', 'invalid-email', {})
        assert not rule.passes('email', 'test@', {})

    def test_min_rule(self):
        rule = MinRule(5)
        assert rule.passes('name', 'abcdef', {})
        assert not rule.passes('name', 'abc', {})
        assert rule.passes('age', 10, {})
        assert not rule.passes('age', 3, {})

    def test_max_rule(self):
        rule = MaxRule(10)
        assert rule.passes('name', 'short', {})
        assert not rule.passes('name', 'this is too long', {})
        assert rule.passes('age', 5, {})
        assert not rule.passes('age', 15, {})

    def test_numeric_rule(self):
        rule = NumericRule()
        assert rule.passes('age', 25, {})
        assert rule.passes('price', 19.99, {})
        assert rule.passes('count', '42', {})
        assert not rule.passes('age', 'abc', {})

    def test_string_rule(self):
        rule = StringRule()
        assert rule.passes('name', 'John Doe', {})
        assert not rule.passes('name', 123, {})
        assert not rule.passes('name', [], {})

    def test_array_rule(self):
        rule = ArrayRule()
        assert rule.passes('items', [1, 2, 3], {})
        assert rule.passes('data', {'key': 'value'}, {})
        assert not rule.passes('items', 'string', {})

    def test_boolean_rule(self):
        rule = BooleanRule()
        assert rule.passes('active', True, {})
        assert rule.passes('active', False, {})
        assert rule.passes('active', 1, {})
        assert rule.passes('active', 0, {})
        assert rule.passes('active', 'true', {})
        assert not rule.passes('active', 'yes', {})

    def test_integer_rule(self):
        rule = IntegerRule()
        assert rule.passes('age', 25, {})
        assert rule.passes('count', '10', {})
        assert not rule.passes('age', 25.5, {})
        assert not rule.passes('age', '25.5', {})
        assert not rule.passes('age', True, {})

    def test_alpha_rule(self):
        rule = AlphaRule()
        assert rule.passes('name', 'John', {})
        assert not rule.passes('name', 'John123', {})
        assert not rule.passes('name', 'John Doe', {})

    def test_alpha_num_rule(self):
        rule = AlphaNumRule()
        assert rule.passes('username', 'john123', {})
        assert not rule.passes('username', 'john_123', {})
        assert not rule.passes('username', 'john 123', {})

    def test_alpha_dash_rule(self):
        rule = AlphaDashRule()
        assert rule.passes('slug', 'my-slug_123', {})
        assert not rule.passes('slug', 'my slug', {})
        assert not rule.passes('slug', 'my@slug', {})

    def test_url_rule(self):
        rule = UrlRule()
        assert rule.passes('website', 'https://example.com', {})
        assert rule.passes('website', 'http://test.org', {})
        assert not rule.passes('website', 'not-a-url', {})

    def test_ip_rule(self):
        rule = IpRule()
        assert rule.passes('ip', '192.168.1.1', {})
        assert rule.passes('ip', '2001:db8::1', {})
        assert not rule.passes('ip', '999.999.999.999', {})

    def test_confirmed_rule(self):
        rule = ConfirmedRule()
        data = {'password': 'secret123', 'password_confirmation': 'secret123'}
        assert rule.passes('password', 'secret123', data)
        
        data_mismatch = {'password': 'secret123', 'password_confirmation': 'different'}
        assert not rule.passes('password', 'secret123', data_mismatch)

    def test_same_rule(self):
        rule = SameRule('password')
        data = {'password': 'secret', 'password_confirm': 'secret'}
        assert rule.passes('password_confirm', 'secret', data)
        
        data_different = {'password': 'secret', 'password_confirm': 'different'}
        assert not rule.passes('password_confirm', 'different', data_different)

    def test_different_rule(self):
        rule = DifferentRule('email')
        data = {'email': 'john@example.com', 'alt_email': 'jane@example.com'}
        assert rule.passes('alt_email', 'jane@example.com', data)
        
        data_same = {'email': 'john@example.com', 'alt_email': 'john@example.com'}
        assert not rule.passes('alt_email', 'john@example.com', data_same)

    def test_in_rule(self):
        rule = InRule(['admin', 'user', 'guest'])
        assert rule.passes('role', 'admin', {})
        assert rule.passes('role', 'user', {})
        assert not rule.passes('role', 'superadmin', {})

    def test_not_in_rule(self):
        rule = NotInRule(['banned', 'suspended'])
        assert rule.passes('status', 'active', {})
        assert not rule.passes('status', 'banned', {})

    def test_nullable_rule(self):
        rule = NullableRule()
        assert rule.passes('optional', None, {})
        assert rule.passes('optional', '', {})
        assert rule.passes('optional', 'value', {})

    def test_regex_rule(self):
        rule = RegexRule(r'^[A-Z]{3}$')
        assert rule.passes('code', 'ABC', {})
        assert not rule.passes('code', 'abc', {})
        assert not rule.passes('code', 'ABCD', {})

    def test_required_if_rule(self):
        rule = RequiredIfRule('country', 'US')
        data = {'country': 'US', 'state': 'CA'}
        assert rule.passes('state', 'CA', data)
        
        data_missing = {'country': 'US', 'state': ''}
        assert not rule.passes('state', '', data_missing)
        
        data_other_country = {'country': 'UK', 'state': ''}
        assert rule.passes('state', '', data_other_country)

    def test_required_unless_rule(self):
        rule = RequiredUnlessRule('type', 'guest')
        data = {'type': 'admin', 'password': 'secret'}
        assert rule.passes('password', 'secret', data)
        
        data_missing = {'type': 'admin', 'password': ''}
        assert not rule.passes('password', '', data_missing)
        
        data_guest = {'type': 'guest', 'password': ''}
        assert rule.passes('password', '', data_guest)

    def test_required_with_rule(self):
        rule = RequiredWithRule(['email'])
        data = {'email': 'john@example.com', 'name': 'John'}
        assert rule.passes('name', 'John', data)
        
        data_missing = {'email': 'john@example.com', 'name': ''}
        assert not rule.passes('name', '', data_missing)
        
        data_no_email = {'name': ''}
        assert rule.passes('name', '', data_no_email)

    def test_required_without_rule(self):
        rule = RequiredWithoutRule(['email'])
        data = {'name': 'John'}
        assert rule.passes('name', 'John', data)
        
        data_missing = {'name': ''}
        assert not rule.passes('name', '', data_missing)
        
        data_with_email = {'email': 'john@example.com', 'name': ''}
        assert rule.passes('name', '', data_with_email)

    def test_size_rule(self):
        rule = SizeRule(5)
        assert rule.passes('code', 'ABCDE', {})
        assert not rule.passes('code', 'ABC', {})
        assert rule.passes('count', 5, {})
        assert not rule.passes('count', 3, {})

    def test_between_rule(self):
        rule = BetweenRule(5, 10)
        assert rule.passes('name', 'John Doe', {})
        assert not rule.passes('name', 'Joe', {})
        assert not rule.passes('name', 'Very Long Name Here', {})
        assert rule.passes('age', 7, {})
        assert not rule.passes('age', 3, {})

    def test_digits_rule(self):
        rule = DigitsRule(4)
        assert rule.passes('pin', '1234', {})
        assert rule.passes('pin', 1234, {})
        assert not rule.passes('pin', '123', {})
        assert not rule.passes('pin', '12345', {})

    def test_json_rule(self):
        rule = JsonRule()
        assert rule.passes('data', '{"key": "value"}', {})
        assert rule.passes('data', '[1, 2, 3]', {})
        assert not rule.passes('data', 'not json', {})
        assert not rule.passes('data', "{'invalid': json}", {})

    def test_date_rule(self):
        rule = DateRule('%Y-%m-%d')
        assert rule.passes('date', '2024-01-15', {})
        assert not rule.passes('date', '15-01-2024', {})
        assert not rule.passes('date', 'not-a-date', {})


class TestValidator:
    def test_validator_passes(self):
        data = {'name': 'John', 'email': 'john@example.com'}
        rules = {'name': 'required|string', 'email': 'required|email'}
        validator = Validator(data, rules)
        assert validator.passes()
        assert not validator.fails()

    def test_validator_fails(self):
        data = {'name': '', 'email': 'invalid'}
        rules = {'name': 'required', 'email': 'email'}
        validator = Validator(data, rules)
        assert validator.fails()
        assert not validator.passes()

    def test_validator_errors(self):
        data = {'email': 'invalid'}
        rules = {'email': 'required|email'}
        validator = Validator(data, rules)
        validator.fails()
        errors = validator.errors()
        assert errors.has('email')
        assert 'email' in str(errors.first('email')).lower()

    def test_validator_validated_data(self):
        data = {'name': 'John', 'email': 'john@example.com', 'extra': 'field'}
        rules = {'name': 'required', 'email': 'required|email'}
        validator = Validator(data, rules)
        validated = validator.validate()
        assert 'name' in validated
        assert 'email' in validated

    def test_validator_custom_messages(self):
        data = {'email': 'invalid'}
        rules = {'email': 'email'}
        messages = {'email.email': 'Please provide a valid email address'}
        validator = Validator(data, rules, messages)
        validator.fails()
        assert validator.errors().first('email') == 'Please provide a valid email address'

    def test_validator_multiple_rules(self):
        data = {'password': 'abc'}
        rules = {'password': 'required|string|min:8'}
        validator = Validator(data, rules)
        assert validator.fails()
        assert validator.errors().has('password')

    def test_validator_array_rules(self):
        data = {'email': 'john@example.com'}
        rules = {'email': ['required', 'email', 'string']}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_object_rules(self):
        data = {'age': 25}
        rules = {'age': [RequiredRule(), NumericRule(), MinRule(18)]}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_nullable_field(self):
        data = {'optional': None}
        rules = {'optional': 'nullable|email'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_stop_on_first_failure(self):
        data = {'email': 'invalid', 'name': ''}
        rules = {'email': 'email', 'name': 'required'}
        validator = Validator(data, rules)
        validator.stopOnFirstFailure()
        validator.fails()
        assert validator.errors().count() == 1

    def test_validator_after_hook(self):
        data = {'name': 'John'}
        rules = {'name': 'required'}
        validator = Validator(data, rules)
        
        called = []
        validator.after(lambda v: called.append(True))
        validator.passes()
        assert len(called) == 1

    def test_validator_nested_data(self):
        data = {'user': {'email': 'john@example.com'}}
        rules = {'user.email': 'required|email'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validation_exception(self):
        data = {'email': 'invalid'}
        rules = {'email': 'email'}
        validator = Validator(data, rules)
        
        with pytest.raises(ValidationException) as exc_info:
            validator.validate()
        
        assert exc_info.value.getErrors().has('email')


class TestFactory:
    def test_factory_make(self):
        factory = Factory()
        data = {'name': 'John'}
        rules = {'name': 'required'}
        validator = factory.make(data, rules)
        assert isinstance(validator, Validator)
        assert validator.passes()

    def test_factory_validate(self):
        factory = Factory()
        data = {'email': 'john@example.com'}
        rules = {'email': 'required|email'}
        validated = factory.validate(data, rules)
        assert 'email' in validated

    def test_factory_validate_fails(self):
        factory = Factory()
        data = {'email': 'invalid'}
        rules = {'email': 'email'}
        
        with pytest.raises(ValidationException):
            factory.validate(data, rules)


class TestFormRequest:
    def test_form_request_basic(self):
        class LoginRequest(FormRequest):
            def rules(self):
                return {
                    'email': 'required|email',
                    'password': 'required|min:8'
                }
        
        request = LoginRequest({'email': 'john@example.com', 'password': 'secret123'})
        assert request.passes()
        validated = request.validated()
        assert 'email' in validated
        assert 'password' in validated

    def test_form_request_fails(self):
        class LoginRequest(FormRequest):
            def rules(self):
                return {
                    'email': 'required|email',
                    'password': 'required|min:8'
                }
        
        request = LoginRequest({'email': 'invalid', 'password': 'short'})
        assert request.fails()
        assert not request.passes()

    def test_form_request_custom_messages(self):
        class LoginRequest(FormRequest):
            def rules(self):
                return {'email': 'email'}
            
            def messages(self):
                return {'email.email': 'Custom email error'}
        
        request = LoginRequest({'email': 'invalid'})
        request.fails()
        assert request.errors().first('email') == 'Custom email error'

    def test_form_request_authorize(self):
        class AdminRequest(FormRequest):
            def rules(self):
                return {'action': 'required'}
            
            def authorize(self):
                return True
        
        request = AdminRequest({'action': 'delete'})
        assert request.authorize()


class TestComplexScenarios:
    def test_user_registration_validation(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123',
            'password_confirmation': 'secret123',
            'age': 25,
            'terms': True
        }
        rules = {
            'name': 'required|string|min:3|max:50',
            'email': 'required|email',
            'password': 'required|min:8|confirmed',
            'age': 'required|numeric|min:18',
            'terms': 'required|boolean'
        }
        validator = Validator(data, rules)
        assert validator.passes()
        validated = validator.validated()
        assert len(validated) == 5

    def test_conditional_validation_workflow(self):
        data = {'type': 'business', 'company_name': 'Acme Inc', 'tax_id': '123456789'}
        rules = {
            'type': 'required|in:personal,business',
            'company_name': 'required_if:type,business',
            'tax_id': 'required_if:type,business'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_array_validation(self):
        data = {
            'emails': ['john@example.com', 'jane@example.com', 'bob@example.com']
        }
        rules = {
            'emails': 'required|array'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_multiple_validation_failures(self):
        data = {
            'email': 'invalid-email',
            'password': 'short',
            'age': 'not-a-number',
            'website': 'not-a-url'
        }
        rules = {
            'email': 'required|email',
            'password': 'required|min:8',
            'age': 'required|numeric|min:18',
            'website': 'required|url'
        }
        validator = Validator(data, rules)
        assert validator.fails()
        errors = validator.errors()
        assert errors.count() >= 4

    def test_profile_update_validation(self):
        data = {
            'username': 'johndoe',
            'email': 'john@example.com',
            'bio': 'Software developer',
            'age': 30,
            'website': 'https://johndoe.com'
        }
        rules = {
            'username': 'required|alpha_dash|min:3|max:20',
            'email': 'required|email',
            'bio': 'nullable|string|max:500',
            'age': 'nullable|integer|min:18|max:120',
            'website': 'nullable|url'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_payment_validation(self):
        data = {
            'amount': '99.99',
            'currency': 'USD',
            'card_number': '1234567890123456',
            'cvv': '123',
            'expiry_month': '12',
            'expiry_year': '2025'
        }
        rules = {
            'amount': 'required|numeric|min:0.01',
            'currency': 'required|in:USD,EUR,GBP',
            'card_number': 'required|digits:16',
            'cvv': 'required|digits:3',
            'expiry_month': 'required|between:1,12',
            'expiry_year': 'required|numeric'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_complex_form_request(self):
        class ComplexFormRequest(FormRequest):
            def rules(self):
                return {
                    'title': 'required|string|min:5|max:100',
                    'content': 'required|string|min:50',
                    'status': 'required|in:draft,published',
                    'publish_at': 'nullable',
                    'tags': 'nullable|array',
                    'author_email': 'required|email'
                }
            
            def messages(self):
                return {
                    'title.required': 'The title field is mandatory',
                    'content.min': 'Content must be at least 50 characters'
                }
        
        data = {
            'title': 'My Blog Post',
            'content': 'This is a very long content that exceeds the minimum requirement of 50 characters.',
            'status': 'published',
            'tags': ['python', 'web', 'framework'],
            'author_email': 'author@example.com'
        }
        request = ComplexFormRequest(data)
        assert request.passes()

    def test_api_validation_with_nested_data(self):
        data = {
            'user': {
                'name': 'John Doe',
                'email': 'john@example.com'
            },
            'settings': {
                'notifications': True,
                'theme': 'dark'
            }
        }
        rules = {
            'user.name': 'required|string',
            'user.email': 'required|email',
            'settings.notifications': 'required|boolean',
            'settings.theme': 'required|in:light,dark'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_stop_on_first_failure_complex(self):
        data = {
            'field1': 'invalid',
            'field2': 'invalid',
            'field3': 'invalid',
            'field4': 'invalid'
        }
        rules = {
            'field1': 'email',
            'field2': 'numeric',
            'field3': 'url',
            'field4': 'boolean'
        }
        validator = Validator(data, rules)
        validator.stopOnFirstFailure()
        validator.fails()
        assert validator.errors().count() == 1

    def test_validation_with_after_hook(self):
        data = {'username': 'admin', 'role': 'user'}
        rules = {'username': 'required', 'role': 'required'}
        validator = Validator(data, rules)
        
        def check_admin_role(v):
            if v._data.get('username') == 'admin' and v._data.get('role') != 'admin':
                v.errors().add('role', 'Username admin requires admin role')
        
        validator.after(check_admin_role)
        assert validator.fails()
        assert validator.errors().has('role')


class TestNewValidationRules:
    def test_accepted_rule(self):
        assert AcceptedRule().passes('terms', 'yes', {})
        assert AcceptedRule().passes('terms', 'on', {})
        assert AcceptedRule().passes('terms', '1', {})
        assert AcceptedRule().passes('terms', 1, {})
        assert AcceptedRule().passes('terms', True, {})
        assert AcceptedRule().passes('terms', 'true', {})
        assert not AcceptedRule().passes('terms', 'no', {})
        assert not AcceptedRule().passes('terms', False, {})

    def test_accepted_if_rule(self):
        assert AcceptedIfRule('agree', 'yes').passes('terms', 'yes', {'agree': 'yes'})
        assert AcceptedIfRule('agree', 'yes').passes('terms', 'no', {'agree': 'no'})
        assert not AcceptedIfRule('agree', 'yes').passes('terms', 'no', {'agree': 'yes'})

    def test_declined_rule(self):
        assert DeclinedRule().passes('marketing', 'no', {})
        assert DeclinedRule().passes('marketing', 'off', {})
        assert DeclinedRule().passes('marketing', '0', {})
        assert DeclinedRule().passes('marketing', 0, {})
        assert DeclinedRule().passes('marketing', False, {})
        assert DeclinedRule().passes('marketing', 'false', {})
        assert not DeclinedRule().passes('marketing', 'yes', {})
        assert not DeclinedRule().passes('marketing', True, {})

    def test_declined_if_rule(self):
        assert DeclinedIfRule('tracking', 'enabled').passes('analytics', 'no', {'tracking': 'enabled'})
        assert DeclinedIfRule('tracking', 'enabled').passes('analytics', 'yes', {'tracking': 'disabled'})
        assert not DeclinedIfRule('tracking', 'enabled').passes('analytics', 'yes', {'tracking': 'enabled'})

    def test_starts_with_rule(self):
        assert StartsWithRule('http', 'https').passes('url', 'https://example.com', {})
        assert StartsWithRule('http', 'https').passes('url', 'http://example.com', {})
        assert not StartsWithRule('http', 'https').passes('url', 'ftp://example.com', {})
        assert not StartsWithRule('http').passes('url', 123, {})

    def test_ends_with_rule(self):
        assert EndsWithRule('.com', '.org').passes('domain', 'example.com', {})
        assert EndsWithRule('.com', '.org').passes('domain', 'example.org', {})
        assert not EndsWithRule('.com', '.org').passes('domain', 'example.net', {})

    def test_doesnt_start_with_rule(self):
        assert DoesntStartWithRule('temp_', 'draft_').passes('name', 'final_doc', {})
        assert not DoesntStartWithRule('temp_', 'draft_').passes('name', 'temp_file', {})
        assert not DoesntStartWithRule('temp_', 'draft_').passes('name', 'draft_post', {})

    def test_doesnt_end_with_rule(self):
        assert DoesntEndWithRule('.tmp', '.bak').passes('file', 'document.pdf', {})
        assert not DoesntEndWithRule('.tmp', '.bak').passes('file', 'file.tmp', {})
        assert not DoesntEndWithRule('.tmp', '.bak').passes('file', 'backup.bak', {})

    def test_uppercase_rule(self):
        assert UppercaseRule().passes('code', 'ABC123', {})
        assert UppercaseRule().passes('code', 'HELLO', {})
        assert not UppercaseRule().passes('code', 'Hello', {})
        assert not UppercaseRule().passes('code', 'hello', {})
        assert not UppercaseRule().passes('code', '', {})
        assert not UppercaseRule().passes('code', 123, {})

    def test_lowercase_rule(self):
        assert LowercaseRule().passes('username', 'john', {})
        assert LowercaseRule().passes('username', 'hello123', {})
        assert not LowercaseRule().passes('username', 'Hello', {})
        assert not LowercaseRule().passes('username', 'HELLO', {})
        assert not LowercaseRule().passes('username', '', {})
        assert not LowercaseRule().passes('username', 123, {})

    def test_uuid_rule(self):
        assert UuidRule().passes('id', '550e8400-e29b-41d4-a716-446655440000', {})
        assert UuidRule(4).passes('id', '550e8400-e29b-41d4-a716-446655440000', {})
        assert not UuidRule().passes('id', 'not-a-uuid', {})
        assert not UuidRule().passes('id', '123', {})
        assert not UuidRule(1).passes('id', '550e8400-e29b-41d4-a716-446655440000', {})

    def test_ulid_rule(self):
        assert UlidRule().passes('id', '01ARZ3NDEKTSV4RRFFQ69G5FAV', {})
        assert not UlidRule().passes('id', 'not-a-ulid', {})
        assert not UlidRule().passes('id', '123', {})
        assert not UlidRule().passes('id', '01ARZ3NDEKTSV4RRFFQ69G5FA', {})

    def test_gt_rule(self):
        assert GtRule('min').passes('age', 30, {'min': 18})
        assert GtRule('min').passes('name', 'abcde', {'min': 'abc'})
        assert not GtRule('min').passes('age', 10, {'min': 18})

    def test_gte_rule(self):
        assert GteRule('min').passes('age', 18, {'min': 18})
        assert GteRule('min').passes('age', 30, {'min': 18})
        assert not GteRule('min').passes('age', 10, {'min': 18})

    def test_lt_rule(self):
        assert LtRule('max').passes('age', 10, {'max': 18})
        assert not LtRule('max').passes('age', 30, {'max': 18})
        assert not LtRule('max').passes('age', 18, {'max': 18})

    def test_lte_rule(self):
        assert LteRule('max').passes('age', 18, {'max': 18})
        assert LteRule('max').passes('age', 10, {'max': 18})
        assert not LteRule('max').passes('age', 30, {'max': 18})

    def test_decimal_rule(self):
        assert DecimalRule(2, 2).passes('price', '9.99', {})
        assert DecimalRule(2, 4).passes('price', '9.999', {})
        assert DecimalRule(2, 4).passes('price', '9.99', {})
        assert not DecimalRule(2, 2).passes('price', '9.9', {})
        assert not DecimalRule(2, 2).passes('price', '9.999', {})
        assert not DecimalRule(2, 2).passes('price', '9', {})

    def test_max_digits_rule(self):
        assert MaxDigitsRule(5).passes('code', 12345, {})
        assert MaxDigitsRule(5).passes('code', 123, {})
        assert not MaxDigitsRule(5).passes('code', 123456, {})

    def test_min_digits_rule(self):
        assert MinDigitsRule(3).passes('code', 123, {})
        assert MinDigitsRule(3).passes('code', 12345, {})
        assert not MinDigitsRule(3).passes('code', 12, {})

    def test_multiple_of_rule(self):
        assert MultipleOfRule(5).passes('quantity', 10, {})
        assert MultipleOfRule(5).passes('quantity', 15, {})
        assert MultipleOfRule(5).passes('quantity', 0, {})
        assert not MultipleOfRule(5).passes('quantity', 7, {})

    def test_after_rule(self):
        assert AfterRule('2024-01-01').passes('date', '2024-01-02', {})
        assert not AfterRule('2024-01-01').passes('date', '2023-12-31', {})
        assert AfterRule('start_date').passes('end_date', '2024-01-02', {'start_date': '2024-01-01'})

    def test_after_or_equal_rule(self):
        assert AfterOrEqualRule('2024-01-01').passes('date', '2024-01-01', {})
        assert AfterOrEqualRule('2024-01-01').passes('date', '2024-01-02', {})
        assert not AfterOrEqualRule('2024-01-01').passes('date', '2023-12-31', {})

    def test_before_rule(self):
        assert BeforeRule('2024-01-01').passes('date', '2023-12-31', {})
        assert not BeforeRule('2024-01-01').passes('date', '2024-01-02', {})

    def test_before_or_equal_rule(self):
        assert BeforeOrEqualRule('2024-01-01').passes('date', '2024-01-01', {})
        assert BeforeOrEqualRule('2024-01-01').passes('date', '2023-12-31', {})
        assert not BeforeOrEqualRule('2024-01-01').passes('date', '2024-01-02', {})

    def test_date_equals_rule(self):
        assert DateEqualsRule('2024-01-01').passes('date', '2024-01-01', {})
        assert not DateEqualsRule('2024-01-01').passes('date', '2024-01-02', {})

    def test_date_format_rule(self):
        assert DateFormatRule('%Y-%m-%d').passes('date', '2024-01-01', {})
        assert DateFormatRule('%d/%m/%Y').passes('date', '01/01/2024', {})
        assert not DateFormatRule('%Y-%m-%d').passes('date', '01/01/2024', {})

    def test_timezone_rule(self):
        assert TimezoneRule().passes('timezone', 'America/New_York', {})
        assert TimezoneRule().passes('timezone', 'Europe/London', {})
        assert TimezoneRule().passes('timezone', 'Asia/Tokyo', {})
        assert not TimezoneRule().passes('timezone', 'Invalid/Timezone', {})

    def test_distinct_rule(self):
        assert DistinctRule().passes('tags', ['unique', 'values', 'only'], {})
        assert not DistinctRule().passes('tags', ['duplicate', 'duplicate', 'value'], {})
        assert DistinctRule(ignore_case=True).passes('tags', ['Tag', 'value'], {})
        assert not DistinctRule(ignore_case=True).passes('tags', ['Tag', 'tag'], {})

    def test_contains_rule(self):
        assert ContainsRule('admin', 'editor').passes('roles', ['admin', 'editor', 'viewer'], {})
        assert not ContainsRule('admin', 'editor').passes('roles', ['admin', 'viewer'], {})

    def test_doesnt_contain_rule(self):
        assert DoesntContainRule('spam', 'banned').passes('words', ['hello', 'world'], {})
        assert not DoesntContainRule('spam', 'banned').passes('words', ['hello', 'spam'], {})

    def test_in_array_rule(self):
        assert InArrayRule('allowed_values').passes('choice', 'a', {'allowed_values': ['a', 'b', 'c']})
        assert not InArrayRule('allowed_values').passes('choice', 'd', {'allowed_values': ['a', 'b', 'c']})

    def test_list_rule(self):
        assert ListRule().passes('items', ['a', 'b', 'c'], {})
        assert ListRule().passes('items', [1, 2, 3], {})
        assert not ListRule().passes('items', {'a': 1}, {})

    def test_present_rule(self):
        assert PresentRule().passes('field', 'value', {'field': 'value'})
        assert PresentRule().passes('field', '', {'field': ''})
        assert not PresentRule().passes('field', None, {})

    def test_filled_rule(self):
        assert FilledRule().passes('field', 'value', {'field': 'value'})
        assert FilledRule().passes('missing', None, {})
        assert not FilledRule().passes('field', '', {'field': ''})
        assert not FilledRule().passes('field', None, {'field': None})

    def test_ascii_rule(self):
        assert AsciiRule().passes('text', 'Hello World', {})
        assert AsciiRule().passes('text', 'ABC123', {})
        assert not AsciiRule().passes('text', 'Héllo', {})
        assert not AsciiRule().passes('text', '你好', {})

    def test_hex_color_rule(self):
        assert HexColorRule().passes('color', '#FF5733', {})
        assert HexColorRule().passes('color', '#FFF', {})
        assert HexColorRule().passes('color', '#FF5733AA', {})
        assert not HexColorRule().passes('color', 'FF5733', {})
        assert not HexColorRule().passes('color', '#GG5733', {})

    def test_mac_address_rule(self):
        assert MacAddressRule().passes('mac', '00:1B:63:84:45:E6', {})
        assert MacAddressRule().passes('mac', '00-1B-63-84-45-E6', {})
        assert not MacAddressRule().passes('mac', '00:1B:63:84:45', {})
        assert not MacAddressRule().passes('mac', 'invalid', {})

    def test_not_regex_rule(self):
        assert NotRegexRule(r'^\d+$').passes('text', 'abc', {})
        assert not NotRegexRule(r'^\d+$').passes('text', '123', {})

    def test_digits_between_rule(self):
        assert DigitsBetweenRule(3, 5).passes('code', 123, {})
        assert DigitsBetweenRule(3, 5).passes('code', 12345, {})
        assert not DigitsBetweenRule(3, 5).passes('code', 12, {})
        assert not DigitsBetweenRule(3, 5).passes('code', 123456, {})

    def test_required_if_accepted_rule(self):
        assert RequiredIfAcceptedRule('terms').passes('email', 'test@example.com', {'terms': 'yes'})
        assert RequiredIfAcceptedRule('terms').passes('email', '', {'terms': 'no'})
        assert not RequiredIfAcceptedRule('terms').passes('email', '', {'terms': 'yes'})

    def test_required_if_declined_rule(self):
        assert RequiredIfDeclinedRule('marketing').passes('reason', 'privacy', {'marketing': 'no'})
        assert RequiredIfDeclinedRule('marketing').passes('reason', '', {'marketing': 'yes'})
        assert not RequiredIfDeclinedRule('marketing').passes('reason', '', {'marketing': 'no'})

    def test_required_with_all_rule(self):
        assert RequiredWithAllRule('first', 'last').passes('middle', 'M', {'first': 'John', 'last': 'Doe'})
        assert RequiredWithAllRule('first', 'last').passes('middle', '', {'first': 'John'})
        assert not RequiredWithAllRule('first', 'last').passes('middle', '', {'first': 'John', 'last': 'Doe'})

    def test_required_without_all_rule(self):
        assert RequiredWithoutAllRule('email', 'phone').passes('address', '123 Main St', {})
        assert RequiredWithoutAllRule('email', 'phone').passes('address', '', {'email': 'test@example.com'})
        assert not RequiredWithoutAllRule('email', 'phone').passes('address', '', {})

    def test_required_array_keys_rule(self):
        assert RequiredArrayKeysRule('name', 'age').passes('user', {'name': 'John', 'age': 30}, {})
        assert not RequiredArrayKeysRule('name', 'age').passes('user', {'name': 'John'}, {})


class TestValidatorWithNewRules:
    def test_validator_with_accepted(self):
        data = {'terms': 'yes'}
        rules = {'terms': 'required|accepted'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_uuid(self):
        data = {'id': '550e8400-e29b-41d4-a716-446655440000'}
        rules = {'id': 'required|uuid'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_date_comparison(self):
        data = {'start_date': '2024-01-01', 'end_date': '2024-12-31'}
        rules = {'start_date': 'required|date', 'end_date': 'required|date|after:start_date'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_numeric_comparison(self):
        data = {'min_age': 18, 'max_age': 65, 'age': 25}
        rules = {'age': 'required|numeric|gte:min_age|lte:max_age'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_string_patterns(self):
        data = {'url': 'https://example.com', 'filename': 'document.pdf'}
        rules = {'url': 'required|starts_with:http,https', 'filename': 'required|ends_with:.pdf,.doc'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_distinct_array(self):
        data = {'tags': ['unique', 'values', 'only']}
        rules = {'tags': 'required|array|distinct'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_failed_distinct(self):
        data = {'tags': ['duplicate', 'duplicate']}
        rules = {'tags': 'required|array|distinct'}
        validator = Validator(data, rules)
        assert validator.fails()

    def test_validator_with_decimal(self):
        data = {'price': '19.99'}
        rules = {'price': 'required|decimal:2'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_timezone(self):
        data = {'timezone': 'America/New_York'}
        rules = {'timezone': 'required|timezone'}
        validator = Validator(data, rules)
        assert validator.passes()
