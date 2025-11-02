"""
Configuration Helper

Provides convenient access to application configuration.
"""

from typing import Any, Optional

_config_instance: Optional["Repository"] = None


def config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration value.

    This function provides convenient access to configuration values,
    matching Laravel's config() helper function.

    Args:
        key: The configuration key in dot notation (e.g., 'app.name')
        default: Default value if key doesn't exist

    Returns:
        Configuration value or entire repository if no key provided

    Examples:
        >>> config('app.name')
        'Larapy'
        >>> config('app.debug', False)
        True
        >>> config('cache.default', 'file')
        'redis'
    """
    from larapy.config.repository import Repository

    global _config_instance

    if _config_instance is None:
        _config_instance = Repository()

    if key is None:
        return _config_instance

    return _config_instance.get(key, default)


def set_config_instance(repository: "Repository") -> None:
    """
    Set the global configuration instance.

    This is used internally by the framework to inject the
    application's configuration repository.

    Args:
        repository: The configuration repository instance
    """
    global _config_instance
    _config_instance = repository
