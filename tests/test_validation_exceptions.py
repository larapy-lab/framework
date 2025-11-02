"""
Tests for Validation Exception Hierarchy
"""

import pytest
import json
from larapy.exceptions import (
    ValidationException,
    InvalidRuleException,
    RuleParseException,
    ValidatorException,
    AuthorizationException,
    AuthenticationException,
    TokenMismatchException,
    ThrottleException,
)


class TestValidationException:
    """Test ValidationException"""
    
    def test_basic_validation_exception(self):
        """Test basic validation exception"""
        errors = {
            "email": ["The email field is required."],
            "password": ["The password must be at least 8 characters."]
        }
        exc = ValidationException(errors)
        
        assert exc.errors == errors
        assert "email" in str(exc)
        assert "password" in str(exc)
    
    def test_get_errors(self):
        """Test getting all errors"""
        errors = {"field": ["Error message"]}
        exc = ValidationException(errors)
        assert exc.get_errors() == errors
    
    def test_get_first_error_no_field(self):
        """Test getting first error without specifying field"""
        errors = {
            "email": ["Email required", "Email invalid"],
            "password": ["Password required"]
        }
        exc = ValidationException(errors)
        first = exc.get_first_error()
        assert first in ["Email required", "Password required"]
    
    def test_get_first_error_with_field(self):
        """Test getting first error for specific field"""
        errors = {
            "email": ["Email required", "Email invalid"],
        }
        exc = ValidationException(errors)
        assert exc.get_first_error("email") == "Email required"
        assert exc.get_first_error("nonexistent") is None
    
    def test_has_error(self):
        """Test checking if field has errors"""
        errors = {"email": ["Error"]}
        exc = ValidationException(errors)
        assert exc.has_error("email") is True
        assert exc.has_error("password") is False
    
    def test_status_code(self):
        """Test HTTP status code"""
        exc = ValidationException({})
        assert exc.get_status_code() == 422
    
    def test_format_errors_for_json(self):
        """Test JSON formatting"""
        errors = {
            "email": ["The email field is required."],
            "password": ["The password must be at least 8 characters."]
        }
        exc = ValidationException(errors)
        result = exc.format_errors_for_json()
        
        assert "message" in result
        assert "errors" in result
        assert result["errors"] == errors
    
    def test_format_errors_for_html(self):
        """Test HTML formatting"""
        errors = {
            "email": ["Email required"],
            "password": ["Password required"]
        }
        exc = ValidationException(errors)
        html = exc.format_errors_for_html()
        
        assert '<div class="alert alert-danger">' in html
        assert "Email required" in html
        assert "Password required" in html
        assert "<ul>" in html
        assert "</ul>" in html
    
    def test_format_errors_as_list(self):
        """Test flat list formatting"""
        errors = {
            "email": ["Email required", "Email invalid"],
            "password": ["Password required"]
        }
        exc = ValidationException(errors)
        result = exc.format_errors_as_list()
        
        assert len(result) == 3
        assert "Email required" in result
        assert "Email invalid" in result
        assert "Password required" in result
    
    def test_format_errors_with_fields(self):
        """Test formatting with field names"""
        errors = {
            "email": ["Email required"],
            "password": ["Password required"]
        }
        exc = ValidationException(errors)
        result = exc.format_errors_with_fields()
        
        assert len(result) == 2
        assert {"field": "email", "message": "Email required"} in result
        assert {"field": "password", "message": "Password required"} in result
    
    def test_to_json(self):
        """Test JSON string conversion"""
        errors = {"email": ["Required"]}
        exc = ValidationException(errors)
        json_str = exc.to_json()
        
        data = json.loads(json_str)
        assert "message" in data
        assert "errors" in data


class TestInvalidRuleException:
    """Test InvalidRuleException"""
    
    def test_invalid_rule(self):
        """Test invalid rule exception"""
        exc = InvalidRuleException("unknown_rule")
        assert "unknown_rule" in str(exc)
        assert exc.rule_name == "unknown_rule"
    
    def test_custom_message(self):
        """Test with custom message"""
        exc = InvalidRuleException("bad_rule", "Custom error message")
        assert "Custom error message" in str(exc)


class TestRuleParseException:
    """Test RuleParseException"""
    
    def test_rule_parse(self):
        """Test rule parse exception"""
        exc = RuleParseException("max:invalid")
        assert "max:invalid" in str(exc)
        assert exc.rule == "max:invalid"
    
    def test_custom_message(self):
        """Test with custom message"""
        exc = RuleParseException("rule", "Failed to parse")
        assert "Failed to parse" in str(exc)


class TestValidatorException:
    """Test ValidatorException"""
    
    def test_validator_exception(self):
        """Test validator exception"""
        exc = ValidatorException("Validator configuration error")
        assert exc.message == "Validator configuration error"


class TestAuthorizationException:
    """Test AuthorizationException"""
    
    def test_basic_authorization(self):
        """Test basic authorization exception"""
        exc = AuthorizationException()
        assert "unauthorized" in str(exc).lower()
        assert exc.get_status_code() == 403
    
    def test_with_ability_and_resource(self):
        """Test with ability and resource"""
        exc = AuthorizationException(
            "Cannot edit post",
            ability="edit",
            resource="Post"
        )
        assert "edit" in str(exc)
        assert "Post" in str(exc)
        assert exc.ability == "edit"
        assert exc.resource == "Post"
    
    def test_to_json(self):
        """Test JSON conversion"""
        exc = AuthorizationException("Forbidden", ability="delete", resource="User")
        data = exc.to_json()
        
        assert data["message"] == "Forbidden"
        assert data["ability"] == "delete"
        assert data["resource"] == "User"


class TestAuthenticationException:
    """Test AuthenticationException"""
    
    def test_basic_authentication(self):
        """Test basic authentication exception"""
        exc = AuthenticationException()
        assert "unauthenticated" in str(exc).lower()
        assert exc.get_status_code() == 401
    
    def test_with_redirect(self):
        """Test with redirect URL"""
        exc = AuthenticationException(
            "Login required",
            redirect_to="/login"
        )
        assert exc.redirect_to == "/login"
    
    def test_to_json(self):
        """Test JSON conversion"""
        exc = AuthenticationException("Auth failed", redirect_to="/login")
        data = exc.to_json()
        
        assert data["message"] == "Auth failed"
        assert data["redirect_to"] == "/login"


class TestTokenMismatchException:
    """Test TokenMismatchException"""
    
    def test_token_mismatch(self):
        """Test token mismatch exception"""
        exc = TokenMismatchException()
        assert "csrf" in str(exc).lower() or "token" in str(exc).lower()
        assert exc.get_status_code() == 419
    
    def test_custom_message(self):
        """Test with custom message"""
        exc = TokenMismatchException("Invalid CSRF token")
        assert "Invalid CSRF token" in str(exc)


class TestThrottleException:
    """Test ThrottleException"""
    
    def test_throttle(self):
        """Test throttle exception"""
        exc = ThrottleException()
        assert "too many" in str(exc).lower()
        assert exc.get_status_code() == 429
    
    def test_with_retry_after(self):
        """Test with retry-after value"""
        exc = ThrottleException("Rate limited", retry_after=60)
        assert exc.retry_after == 60
        assert exc.get_retry_after() == 60
    
    def test_to_json(self):
        """Test JSON conversion"""
        exc = ThrottleException("Too many requests", retry_after=120)
        data = exc.to_json()
        
        assert data["message"] == "Too many requests"
        assert data["retry_after"] == 120


class TestValidatorFormattingMethods:
    """Test Validator formatting methods"""
    
    def test_format_errors_for_json(self):
        """Test JSON formatting in Validator"""
        from larapy.validation.validator import Validator
        
        validator = Validator(
            data={},
            rules={"email": "required", "password": "required|min:8"}
        )
        validator.fails()
        
        result = validator.format_errors_for_json()
        assert "message" in result
        assert "errors" in result
        assert isinstance(result["errors"], dict)
    
    def test_format_errors_for_html(self):
        """Test HTML formatting in Validator"""
        from larapy.validation.validator import Validator
        
        validator = Validator(
            data={},
            rules={"email": "required"}
        )
        validator.fails()
        
        html = validator.format_errors_for_html()
        assert '<div class="alert alert-danger">' in html
        assert "</div>" in html
    
    def test_format_errors_as_list(self):
        """Test list formatting in Validator"""
        from larapy.validation.validator import Validator
        
        validator = Validator(
            data={},
            rules={"email": "required", "name": "required"}
        )
        validator.fails()
        
        result = validator.format_errors_as_list()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_format_errors_with_fields(self):
        """Test field formatting in Validator"""
        from larapy.validation.validator import Validator
        
        validator = Validator(
            data={},
            rules={"email": "required"}
        )
        validator.fails()
        
        result = validator.format_errors_with_fields()
        assert isinstance(result, list)
        if result:
            assert "field" in result[0]
            assert "message" in result[0]
    
    def test_first_error(self):
        """Test first_error method in Validator"""
        from larapy.validation.validator import Validator
        
        validator = Validator(
            data={},
            rules={"email": "required", "password": "required"}
        )
        validator.fails()
        
        first = validator.first_error()
        assert first is not None
        assert isinstance(first, str)
        
        email_error = validator.first_error("email")
        assert email_error is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
