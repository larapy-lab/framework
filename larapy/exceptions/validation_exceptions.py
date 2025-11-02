"""
Validation Exception Hierarchy

Provides consistent exception classes for validation errors with
improved error messages and formatting options.
"""

from typing import Dict, List, Any, Optional
import json


class ValidationException(Exception):
    """
    Base exception for validation errors.
    
    Attributes:
        errors: Dictionary of validation errors by field
        validator: Optional validator instance that raised the exception
        
    Example:
        ```python
        try:
            validator.validate(data)
        except ValidationException as e:
            return {"errors": e.errors}, 422
        ```
    """
    
    def __init__(
        self,
        errors: Dict[str, List[str]],
        message: str = "The given data was invalid.",
        validator: Optional[Any] = None
    ):
        self.errors = errors
        self.message = message
        self.validator = validator
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message"""
        if not self.errors:
            return self.message
        
        error_lines = [self.message]
        for field, messages in self.errors.items():
            for msg in messages:
                error_lines.append(f"  - {field}: {msg}")
        
        return "\n".join(error_lines)
    
    def get_errors(self) -> Dict[str, List[str]]:
        """Get all validation errors"""
        return self.errors
    
    def get_first_error(self, field: Optional[str] = None) -> Optional[str]:
        """
        Get the first error message.
        
        Args:
            field: Optional field name to get error for
            
        Returns:
            First error message or None
        """
        if field:
            return self.errors.get(field, [None])[0]
        
        # Return first error from any field
        for messages in self.errors.values():
            if messages:
                return messages[0]
        return None
    
    def has_error(self, field: str) -> bool:
        """Check if a specific field has errors"""
        return field in self.errors and len(self.errors[field]) > 0
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 422
    
    def format_errors_for_json(self) -> Dict[str, Any]:
        """
        Format errors for JSON response.
        
        Returns:
            Dictionary suitable for JSON API response
            
        Example:
            ```python
            {
                "message": "The given data was invalid.",
                "errors": {
                    "email": ["The email field is required."],
                    "password": ["The password must be at least 8 characters."]
                }
            }
            ```
        """
        return {
            "message": self.message,
            "errors": self.errors
        }
    
    def format_errors_for_html(self) -> str:
        """
        Format errors for HTML display.
        
        Returns:
            HTML string with formatted errors
            
        Example:
            ```python
            <div class="alert alert-danger">
                <p><strong>The given data was invalid.</strong></p>
                <ul>
                    <li>The email field is required.</li>
                    <li>The password must be at least 8 characters.</li>
                </ul>
            </div>
            ```
        """
        lines = ['<div class="alert alert-danger">']
        lines.append(f'    <p><strong>{self.message}</strong></p>')
        
        if self.errors:
            lines.append('    <ul>')
            for field, messages in self.errors.items():
                for msg in messages:
                    lines.append(f'        <li>{msg}</li>')
            lines.append('    </ul>')
        
        lines.append('</div>')
        return '\n'.join(lines)
    
    def format_errors_as_list(self) -> List[str]:
        """
        Format errors as a flat list of messages.
        
        Returns:
            List of all error messages
            
        Example:
            ```python
            [
                "The email field is required.",
                "The password must be at least 8 characters."
            ]
            ```
        """
        messages = []
        for field_errors in self.errors.values():
            messages.extend(field_errors)
        return messages
    
    def format_errors_with_fields(self) -> List[Dict[str, str]]:
        """
        Format errors with field names for detailed display.
        
        Returns:
            List of dictionaries with field and message
            
        Example:
            ```python
            [
                {"field": "email", "message": "The email field is required."},
                {"field": "password", "message": "The password must be at least 8 characters."}
            ]
            ```
        """
        formatted = []
        for field, messages in self.errors.items():
            for msg in messages:
                formatted.append({"field": field, "message": msg})
        return formatted
    
    def to_json(self) -> str:
        """Convert errors to JSON string"""
        return json.dumps(self.format_errors_for_json(), indent=2)


class InvalidRuleException(ValidationException):
    """
    Exception raised when a validation rule is invalid or not found.
    
    Example:
        ```python
        try:
            validator.validate({'email': 'test'}, {'email': 'unknown_rule'})
        except InvalidRuleException as e:
            print(f"Invalid rule: {e.rule_name}")
        ```
    """
    
    def __init__(
        self,
        rule_name: str,
        message: Optional[str] = None
    ):
        self.rule_name = rule_name
        error_message = message or f"Validation rule '{rule_name}' does not exist."
        super().__init__(
            errors={'_validation': [error_message]},
            message=error_message
        )


class RuleParseException(ValidationException):
    """
    Exception raised when a validation rule cannot be parsed.
    
    Example:
        ```python
        try:
            validator.validate(data, {'field': 'max:invalid'})
        except RuleParseException as e:
            print(f"Failed to parse rule: {e.rule}")
        ```
    """
    
    def __init__(
        self,
        rule: str,
        message: Optional[str] = None
    ):
        self.rule = rule
        error_message = message or f"Failed to parse validation rule: {rule}"
        super().__init__(
            errors={'_validation': [error_message]},
            message=error_message
        )


class ValidatorException(Exception):
    """
    Base exception for validator-related errors.
    
    Used for configuration and setup errors, not validation failures.
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AuthorizationException(Exception):
    """
    Exception raised when authorization fails.
    
    Example:
        ```python
        try:
            if not user.can('edit', post):
                raise AuthorizationException("Unauthorized to edit this post")
        except AuthorizationException as e:
            return {"error": e.message}, 403
        ```
    """
    
    def __init__(
        self,
        message: str = "This action is unauthorized.",
        ability: Optional[str] = None,
        resource: Optional[str] = None
    ):
        self.message = message
        self.ability = ability
        self.resource = resource
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format with authorization details"""
        if self.ability and self.resource:
            return f"{self.message} (Ability: {self.ability}, Resource: {self.resource})"
        return self.message
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 403
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "message": self.message,
            "ability": self.ability,
            "resource": self.resource,
        }


class AuthenticationException(Exception):
    """
    Exception raised when authentication fails.
    
    Example:
        ```python
        try:
            user = User.authenticate(credentials)
            if not user:
                raise AuthenticationException("Invalid credentials")
        except AuthenticationException as e:
            return {"error": e.message}, 401
        ```
    """
    
    def __init__(
        self,
        message: str = "Unauthenticated.",
        redirect_to: Optional[str] = None
    ):
        self.message = message
        self.redirect_to = redirect_to
        super().__init__(message)
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 401
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "message": self.message,
            "redirect_to": self.redirect_to,
        }


class TokenMismatchException(Exception):
    """
    Exception raised when CSRF token validation fails.
    
    Example:
        ```python
        try:
            if not csrf_token_valid(token):
                raise TokenMismatchException()
        except TokenMismatchException as e:
            return {"error": "Token mismatch"}, 419
        ```
    """
    
    def __init__(self, message: str = "CSRF token mismatch."):
        self.message = message
        super().__init__(message)
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 419


class ThrottleException(Exception):
    """
    Exception raised when rate limiting is triggered.
    
    Example:
        ```python
        try:
            if rate_limiter.too_many_attempts(key):
                raise ThrottleException(retry_after=60)
        except ThrottleException as e:
            return {"error": "Too many attempts"}, 429
        ```
    """
    
    def __init__(
        self,
        message: str = "Too many attempts.",
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.retry_after = retry_after  # Seconds until retry allowed
        super().__init__(message)
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 429
    
    def get_retry_after(self) -> Optional[int]:
        """Get retry-after value in seconds"""
        return self.retry_after
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "message": self.message,
            "retry_after": self.retry_after,
        }
