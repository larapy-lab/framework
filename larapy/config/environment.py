"""
Environment Variable Management

Provides environment variable loading and type-casting utilities
matching Laravel's environment handling.
"""

import os
from pathlib import Path
from typing import Any, Callable, Optional, Union


class EnvironmentVariablesNotLoaded(Exception):
    """Exception raised when environment variables are not loaded."""

    pass


class Environment:
    """
    Environment variable manager that loads and provides access to
    environment variables with type casting.
    """

    _loaded: bool = False
    _file_path: Optional[Path] = None

    @classmethod
    def load(cls, directory: Union[str, Path], filename: str = ".env") -> bool:
        """
        Load environment variables from a .env file.

        Args:
            directory: Directory containing the .env file
            filename: Name of the environment file

        Returns:
            True if file was loaded, False if file doesn't exist
        """
        directory = Path(directory)
        file_path = directory / filename

        if not file_path.exists():
            return False

        cls._file_path = file_path

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                value = cls._parse_value(value)

                if key and key not in os.environ:
                    os.environ[key] = str(value)

        cls._loaded = True
        return True

    @classmethod
    def _parse_value(cls, value: str) -> str:
        """
        Parse environment variable value, handling quotes and special values.

        Args:
            value: Raw value string

        Returns:
            Parsed value string
        """
        value = value.strip()

        if not value:
            return ""

        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        return value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get an environment variable with type casting.

        Args:
            key: The environment variable key
            default: Default value if key doesn't exist

        Returns:
            The environment variable value with type casting applied
        """
        value = os.environ.get(key)

        if value is None:
            return default() if callable(default) else default

        return cls._cast_value(value)

    @classmethod
    def _cast_value(cls, value: str) -> Union[str, bool, None]:
        """
        Cast string value to appropriate Python type.

        Args:
            value: String value to cast

        Returns:
            Casted value (bool, None, or str)
        """
        value_lower = value.lower()

        if value_lower == "true":
            return True
        elif value_lower == "false":
            return False
        elif value_lower == "null" or value_lower == "none":
            return None
        elif value_lower == "empty" or value == "":
            return ""

        return value

    @classmethod
    def put(cls, key: str, value: Any) -> None:
        """
        Set an environment variable.

        Args:
            key: The environment variable key
            value: The value to set
        """
        os.environ[key] = str(value)

    @classmethod
    def forget(cls, key: str) -> None:
        """
        Remove an environment variable.

        Args:
            key: The environment variable key to remove
        """
        os.environ.pop(key, None)

    @classmethod
    def has(cls, key: str) -> bool:
        """
        Determine if an environment variable exists.

        Args:
            key: The environment variable key

        Returns:
            True if the key exists, False otherwise
        """
        return key in os.environ

    @classmethod
    def file_path(cls) -> Optional[Path]:
        """
        Get the path to the loaded environment file.

        Returns:
            Path to the .env file or None if not loaded
        """
        return cls._file_path


def env(key: str, default: Any = None) -> Any:
    """
    Get the value of an environment variable.

    This function provides a convenient interface matching Laravel's env() helper.

    Args:
        key: The environment variable key
        default: Default value if key doesn't exist

    Returns:
        The environment variable value with type casting

    Examples:
        >>> env('APP_DEBUG', False)
        True
        >>> env('APP_NAME', 'Larapy')
        'MyApp'
    """
    return Environment.get(key, default)
