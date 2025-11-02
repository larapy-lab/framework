"""
Configuration Service Provider

Loads configuration files and registers the configuration repository
in the service container.
"""

import importlib.util
from pathlib import Path
from typing import Dict, Any

from larapy.support.service_provider import ServiceProvider
from larapy.config.repository import Repository
from larapy.config.environment import Environment


class ConfigServiceProvider(ServiceProvider):
    """
    Service provider for loading and registering application configuration.

    This provider:
    1. Loads environment variables from .env file
    2. Loads configuration from Python files in the config directory
    3. Registers the configuration repository in the container
    """

    def register(self) -> None:
        """Register the configuration repository in the container."""
        config = Repository(self._load_configuration())

        self.app.singleton("config", lambda app: config)

    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from the application's config directory.

        Returns:
            Dictionary of all configuration values
        """
        config_data = {}

        config_path = Path(self.app.base_path()) / "config"

        if not config_path.exists() or not config_path.is_dir():
            return config_data

        for config_file in sorted(config_path.glob("*.py")):
            if config_file.name.startswith("_"):
                continue

            config_name = config_file.stem
            config_values = self._load_config_file(config_file)

            if config_values is not None:
                config_data[config_name] = config_values

        return config_data

    def _load_config_file(self, file_path: Path) -> Any:
        """
        Load a single configuration file.

        Args:
            file_path: Path to the configuration file

        Returns:
            Configuration data from the file
        """
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "config"):
                return module.config

            config_dict = {}
            for name in dir(module):
                if not name.startswith("_"):
                    value = getattr(module, name)
                    if not callable(value) or isinstance(value, type):
                        config_dict[name] = value

            return config_dict

        except Exception:
            return None
