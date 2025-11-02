from abc import ABC, abstractmethod
from typing import Dict, List, Any, Union, Optional, Callable
from larapy.validation.validator import Validator
from larapy.validation.exceptions import (
    AuthorizationException,
    ValidationException422,
    RedirectException,
)
from larapy.validation.validation_exception import ValidationException


class FormRequest(ABC):
    def __init__(self, data: Optional[Dict[str, Any]] = None, request=None):
        self._data = data or {}
        self._request = request
        self._validator: Optional[Validator] = None
        self._redirect_route: Optional[str] = None
        self._redirect_to: Optional[str] = None
        self._user_resolver: Optional[Callable] = None
        self._route_resolver: Optional[Callable] = None

    @abstractmethod
    def rules(self) -> Dict[str, Union[str, List]]:
        pass

    def authorize(self) -> bool:
        return True

    def messages(self) -> Dict[str, str]:
        return {}

    def attributes(self) -> Dict[str, str]:
        return {}

    def prepareForValidation(self) -> None:
        pass

    def withValidator(self, validator: Validator) -> None:
        pass

    def passedValidation(self) -> None:
        pass

    def failedValidation(self) -> None:
        pass

    def validated(self) -> Dict[str, Any]:
        if not self._validator:
            self._performValidation()
        if self._validator:
            return self._validator.validated()
        return {}

    def safe(self) -> Dict[str, Any]:
        return self.validated()

    def validate(self) -> Dict[str, Any]:
        return self.validated()

    def _performValidation(self) -> None:
        if not self.authorize():
            raise AuthorizationException("This action is unauthorized.")

        self.prepareForValidation()

        self._validator = Validator(self._data, self.rules(), self.messages())

        self.withValidator(self._validator)

        try:
            self._validator.validate()
            self.passedValidation()
        except ValidationException as e:
            self.failedValidation()
            self._handleFailedValidation(e)

    def _handleFailedValidation(self, exception: ValidationException) -> None:
        if self._expectsJson():
            raise ValidationException422(exception.getErrors())
        else:
            errors = exception.getErrors()
            if self._request and hasattr(self._request, "session"):
                session = self._request.session()
                if session:
                    session.flash("errors", errors)
                    session.flash("old", self._data)

            raise RedirectException(
                self.getRedirectUrl(),
                with_errors=errors.messages() if hasattr(errors, "messages") else {},
                with_input=self._data,
            )

    def _expectsJson(self) -> bool:
        if self._request and hasattr(self._request, "expectsJson"):
            return self._request.expectsJson()
        if self._request and hasattr(self._request, "header"):
            accept = self._request.header("Accept", "")
            return "application/json" in accept
        return False

    def getRedirectUrl(self) -> str:
        if self._redirect_to:
            return self._redirect_to
        if self._redirect_route and self._route_resolver:
            return self._route_resolver(self._redirect_route)
        if self._request and hasattr(self._request, "url"):
            return self._request.url()
        return "/"

    def redirect(self, url: str) -> "FormRequest":
        self._redirect_to = url
        return self

    def redirectToRoute(self, route: str) -> "FormRequest":
        self._redirect_route = route
        return self

    def setUserResolver(self, resolver: Callable) -> "FormRequest":
        self._user_resolver = resolver
        return self

    def setRouteResolver(self, resolver: Callable) -> "FormRequest":
        self._route_resolver = resolver
        return self

    def set_request(self, request) -> "FormRequest":
        """
        Set the underlying HTTP request for this form request.

        Args:
            request: The HTTP Request object

        Returns:
            Self for method chaining
        """
        self._request = request
        return self

    def validateResolved(self) -> Dict[str, Any]:
        """
        Validate the form request (Laravel compatibility method).

        Returns:
            Validated data dictionary

        Raises:
            AuthorizationException: If authorization fails
            ValidationException422: If validation fails and JSON response expected
            RedirectException: If validation fails and redirect expected
        """
        self._performValidation()
        return self.validated()

    def user(self):
        if self._user_resolver:
            return self._user_resolver()
        if self._request and hasattr(self._request, "user"):
            return self._request.user()
        return None

    def all(self) -> Dict[str, Any]:
        return self._data.copy()

    def input(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def filled(self, key: str) -> bool:
        value = self._data.get(key)
        return value is not None and value != ""

    def merge(self, data: Dict[str, Any]) -> None:
        self._data.update(data)

    def replace(self, data: Dict[str, Any]) -> None:
        self._data = data.copy()

    def fails(self) -> bool:
        self._validator = Validator(self._data, self.rules(), self.messages())
        return self._validator.fails()

    def passes(self) -> bool:
        return not self.fails()

    def errors(self):
        if self._validator:
            return self._validator.errors()
        from larapy.validation.message_bag import MessageBag

        return MessageBag()
