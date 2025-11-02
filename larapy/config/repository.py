"""
Configuration Repository

Manages application configuration values with dot notation access.
"""

from typing import Any, Callable, Dict, List, Optional, Union


class Repository:
    """
    Configuration repository that manages application configuration.

    Provides dot notation access to configuration values and type-safe
    retrieval methods matching Laravel's Config facade.
    """

    def __init__(self, items: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the configuration repository.

        Args:
            items: Initial configuration items
        """
        self._items: Dict[str, Any] = items or {}

    def has(self, key: str) -> bool:
        """
        Determine if the given configuration value exists.

        Args:
            key: The configuration key in dot notation

        Returns:
            True if the key exists, False otherwise
        """
        return self._has(self._items, key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get the specified configuration value.

        Args:
            key: The configuration key in dot notation
            default: The default value to return if key doesn't exist

        Returns:
            The configuration value or default
        """
        return self._get(self._items, key, default)

    def set(self, key: Union[str, Dict[str, Any]], value: Any = None) -> None:
        """
        Set a given configuration value.

        Args:
            key: The configuration key or dictionary of keys/values
            value: The value to set (ignored if key is a dictionary)
        """
        if isinstance(key, dict):
            for k, v in key.items():
                self._set(self._items, k, v)
        else:
            self._set(self._items, key, value)

    def prepend(self, key: str, value: Any) -> None:
        """
        Prepend a value onto an array configuration value.

        Args:
            key: The configuration key
            value: The value to prepend
        """
        array = self.get(key, [])
        if not isinstance(array, list):
            array = []

        array.insert(0, value)
        self.set(key, array)

    def push(self, key: str, value: Any) -> None:
        """
        Push a value onto an array configuration value.

        Args:
            key: The configuration key
            value: The value to push
        """
        array = self.get(key, [])
        if not isinstance(array, list):
            array = []

        array.append(value)
        self.set(key, array)

    def all(self) -> Dict[str, Any]:
        """
        Get all of the configuration items.

        Returns:
            All configuration items
        """
        return self._items

    def string(self, key: str, default: Optional[str] = None) -> str:
        """
        Get the specified string configuration value.

        Args:
            key: The configuration key
            default: The default value

        Returns:
            The string value

        Raises:
            ValueError: If the value is not a string
        """
        value = self.get(key, default)

        if value is None:
            if default is None:
                raise ValueError(f"Configuration value for key [{key}] is required")
            return default

        if not isinstance(value, str):
            raise ValueError(
                f"Configuration value for key [{key}] must be a string, "
                f"{type(value).__name__} given"
            )

        return value

    def integer(self, key: str, default: Optional[int] = None) -> int:
        """
        Get the specified integer configuration value.

        Args:
            key: The configuration key
            default: The default value

        Returns:
            The integer value

        Raises:
            ValueError: If the value is not an integer
        """
        value = self.get(key, default)

        if value is None:
            if default is None:
                raise ValueError(f"Configuration value for key [{key}] is required")
            return default

        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"Configuration value for key [{key}] must be an integer, "
                f"{type(value).__name__} given"
            )

        return value

    def float(self, key: str, default: Optional[float] = None) -> float:
        """
        Get the specified float configuration value.

        Args:
            key: The configuration key
            default: The default value

        Returns:
            The float value

        Raises:
            ValueError: If the value is not a float
        """
        value = self.get(key, default)

        if value is None:
            if default is None:
                raise ValueError(f"Configuration value for key [{key}] is required")
            return default

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(
                f"Configuration value for key [{key}] must be a float, "
                f"{type(value).__name__} given"
            )

        return float(value)

    def boolean(self, key: str, default: Optional[bool] = None) -> bool:
        """
        Get the specified boolean configuration value.

        Args:
            key: The configuration key
            default: The default value

        Returns:
            The boolean value

        Raises:
            ValueError: If the value is not a boolean
        """
        value = self.get(key, default)

        if value is None:
            if default is None:
                raise ValueError(f"Configuration value for key [{key}] is required")
            return default

        if not isinstance(value, bool):
            raise ValueError(
                f"Configuration value for key [{key}] must be a boolean, "
                f"{type(value).__name__} given"
            )

        return value

    def array(self, key: str, default: Optional[List[Any]] = None) -> List[Any]:
        """
        Get the specified array configuration value.

        Args:
            key: The configuration key
            default: The default value

        Returns:
            The array value

        Raises:
            ValueError: If the value is not an array
        """
        value = self.get(key, default)

        if value is None:
            if default is None:
                raise ValueError(f"Configuration value for key [{key}] is required")
            return default

        if not isinstance(value, list):
            raise ValueError(
                f"Configuration value for key [{key}] must be an array, "
                f"{type(value).__name__} given"
            )

        return value

    def _has(self, items: Dict[str, Any], key: str) -> bool:
        """
        Check if a key exists in nested dictionary using dot notation.

        Args:
            items: The dictionary to search
            key: The dot notation key

        Returns:
            True if key exists, False otherwise
        """
        if key in items:
            return True

        if "." not in key:
            return False

        parts = key.split(".")
        current = items

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        return True

    def _get(self, items: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Get a value from nested dictionary using dot notation.

        Args:
            items: The dictionary to search
            key: The dot notation key
            default: The default value

        Returns:
            The value or default
        """
        if key in items:
            return items[key]

        if "." not in key:
            return default() if callable(default) else default

        parts = key.split(".")
        current = items

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default() if callable(default) else default
            current = current[part]

        return current

    def _set(self, items: Dict[str, Any], key: str, value: Any) -> None:
        """
        Set a value in nested dictionary using dot notation.

        Args:
            items: The dictionary to modify
            key: The dot notation key
            value: The value to set
        """
        if "." not in key:
            items[key] = value
            return

        parts = key.split(".")
        current = items

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def __getitem__(self, key: str) -> Any:
        """Support array-style access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support array-style assignment."""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Repository items={len(self._items)}>"
