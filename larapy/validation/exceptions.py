from typing import Any, Dict, Optional, Union


class AuthorizationException(Exception):
    def __init__(self, message: str = "This action is unauthorized.", status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException422(Exception):
    def __init__(self, errors, message: str = "The given data was invalid."):
        self.errors = errors
        self.message = message
        self.status_code = 422
        super().__init__(self.message)

    def get_errors(self):
        return self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "errors": self.errors.messages() if hasattr(self.errors, "messages") else {},
        }


class RedirectException(Exception):
    def __init__(
        self,
        url: str,
        with_errors: Optional[Union[Dict, Any]] = None,
        with_input: Optional[Dict] = None,
    ):
        self.url = url
        self.with_errors = with_errors
        self.with_input = with_input
        super().__init__(f"Redirect to: {url}")

    def get_url(self) -> str:
        return self.url

    def get_errors(self) -> Optional[Union[Dict, Any]]:
        return self.with_errors

    def get_input(self) -> Optional[Dict]:
        return self.with_input
