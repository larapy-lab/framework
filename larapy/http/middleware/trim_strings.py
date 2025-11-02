"""
Trim Strings Middleware

Automatically trims whitespace from all string inputs in the request.
"""

from typing import Any, Callable, List
from larapy.http.middleware.middleware import Middleware


class TrimStrings(Middleware):
    """
    Trim whitespace from all string inputs in the request.

    This middleware processes all input data and removes leading and
    trailing whitespace from string values. Certain attributes can be
    excluded from trimming.
    """

    # Attributes that should not be trimmed
    _except: List[str] = [
        "password",
        "password_confirmation",
        "current_password",
    ]

    def __init__(self):
        """Initialize trim strings middleware."""
        super().__init__()

    def handle(self, request: Any, next_handler: Callable) -> Any:
        """
        Handle incoming request and trim string inputs.

        Args:
            request: The incoming HTTP request
            next_handler: The next middleware/handler in the pipeline

        Returns:
            Response from next handler
        """
        # Get all input data
        data = self._get_input_data(request)

        # Trim strings in the data
        trimmed = self._trim_data(data)

        # Replace request data with trimmed version
        self._set_input_data(request, trimmed)

        return next_handler(request)

    def _get_input_data(self, request: Any) -> dict:
        """
        Get all input data from the request.

        Args:
            request: The HTTP request

        Returns:
            Dictionary of all input data
        """
        if hasattr(request, "all"):
            return request.all()
        return {}

    def _set_input_data(self, request: Any, data: dict) -> None:
        """
        Set the input data on the request.

        Args:
            request: The HTTP request
            data: The data to set
        """
        if hasattr(request, "replace"):
            request.replace(data)
        elif hasattr(request, "merge"):
            # Clear existing and merge new
            if hasattr(request, "_input"):
                request._input.clear()
            request.merge(data)

    def _trim_data(self, data: Any) -> Any:
        """
        Recursively trim strings in the data structure.

        Args:
            data: The data to trim (dict, list, or scalar)

        Returns:
            Trimmed data maintaining the same structure
        """
        if isinstance(data, dict):
            return {key: self._trim_value(key, value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._trim_data(item) for item in data]
        else:
            return data

    def _trim_value(self, key: str, value: Any) -> Any:
        """
        Trim a single value if it's a string and not in except list.

        Args:
            key: The key name (to check against except list)
            value: The value to potentially trim

        Returns:
            Trimmed value or original value
        """
        # Skip if key is in except list
        if key in self._except:
            return value

        # Trim strings
        if isinstance(value, str):
            return value.strip()

        # Recursively process nested structures
        if isinstance(value, dict):
            return {k: self._trim_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [item.strip() if isinstance(item, str) else item for item in value]

        return value

    def except_keys(self, keys: List[str]) -> "TrimStrings":
        """
        Add keys to exclude from trimming.

        Args:
            keys: List of keys to exclude

        Returns:
            Self for method chaining
        """
        self._except.extend(keys)
        return self
