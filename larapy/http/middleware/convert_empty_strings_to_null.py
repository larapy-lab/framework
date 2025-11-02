"""
Convert Empty Strings to Null Middleware

Converts empty string inputs to None (null) values.
"""

from typing import Any, Callable, List
from larapy.http.middleware.middleware import Middleware


class ConvertEmptyStringsToNull(Middleware):
    """
    Convert empty string inputs to None (null).

    This middleware processes all input data and converts empty strings
    to None values. This is useful for database operations where empty
    strings should be stored as NULL. Certain attributes can be excluded.
    """

    # Attributes that should not be converted
    _except: List[str] = []

    def __init__(self):
        """Initialize convert empty strings middleware."""
        super().__init__()

    def handle(self, request: Any, next_handler: Callable) -> Any:
        """
        Handle incoming request and convert empty strings to None.

        Args:
            request: The incoming HTTP request
            next_handler: The next middleware/handler in the pipeline

        Returns:
            Response from next handler
        """
        # Get all input data
        data = self._get_input_data(request)

        # Convert empty strings
        converted = self._convert_data(data)

        # Replace request data with converted version
        self._set_input_data(request, converted)

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

    def _convert_data(self, data: Any) -> Any:
        """
        Recursively convert empty strings in the data structure.

        Args:
            data: The data to process (dict, list, or scalar)

        Returns:
            Processed data with empty strings converted to None
        """
        if isinstance(data, dict):
            return {key: self._convert_value(key, value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_data(item) for item in data]
        else:
            return data

    def _convert_value(self, key: str, value: Any) -> Any:
        """
        Convert a single value if it's an empty string and not in except list.

        Args:
            key: The key name (to check against except list)
            value: The value to potentially convert

        Returns:
            None if empty string, otherwise original value
        """
        # Skip if key is in except list
        if key in self._except:
            return value

        # Convert empty strings to None
        if isinstance(value, str) and value == "":
            return None

        # Recursively process nested structures
        if isinstance(value, dict):
            return {k: self._convert_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [None if isinstance(item, str) and item == "" else item for item in value]

        return value

    def except_keys(self, keys: List[str]) -> "ConvertEmptyStringsToNull":
        """
        Add keys to exclude from conversion.

        Args:
            keys: List of keys to exclude

        Returns:
            Self for method chaining
        """
        self._except.extend(keys)
        return self
