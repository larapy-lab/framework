"""
Application Class

The central component of the Larapy framework. Manages the service container,
bootstraps service providers, and coordinates the application lifecycle.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from larapy.container import Container
from larapy.support import ServiceProvider


class Application(Container):
    """
    The Larapy Application.

    This class extends the IoC Container and adds application-level functionality
    including service provider registration and bootstrapping.
    """

    VERSION = "0.1.0"

    def __init__(self, base_path: Optional[str] = None) -> None:
        """
        Initialize the application.

        Args:
            base_path: The base path of the application
        """
        super().__init__()

        self._base_path = base_path or os.getcwd()
        self._bootstrapped = False
        self._booted = False

        self._service_providers: List[ServiceProvider] = []
        self._loaded_providers: Dict[str, bool] = {}
        self._deferred_services: Dict[str, str] = {}

        self._register_base_bindings()
        self._register_base_service_providers()

    def version(self) -> str:
        """
        Get the version number of the application.

        Returns:
            The version string
        """
        return self.VERSION

    def base_path(self, path: str = "") -> str:
        """
        Get the base path of the application.

        Args:
            path: Optional path to append to base path

        Returns:
            The full path
        """
        if path:
            return os.path.join(self._base_path, path)
        return self._base_path

    def path(self, path: str = "") -> str:
        """
        Get the path to the application directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("app", path))

    def config_path(self, path: str = "") -> str:
        """
        Get the path to the configuration directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("config", path))

    def storage_path(self, path: str = "") -> str:
        """
        Get the path to the storage directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("storage", path))

    def bootstrap_path(self, path: str = "") -> str:
        """
        Get the path to the bootstrap directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("bootstrap", path))

    def database_path(self, path: str = "") -> str:
        """
        Get the path to the database directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("database", path))

    def resources_path(self, path: str = "") -> str:
        """
        Get the path to the resources directory.

        Args:
            path: Optional path to append

        Returns:
            The full path
        """
        return self.base_path(os.path.join("resources", path))

    def environment(self) -> str:
        """
        Get the current application environment.

        Returns:
            The environment name (production, development, testing, etc.)
        """
        return os.getenv("APP_ENV", "production")

    def is_local(self) -> bool:
        """Check if the application is in local environment."""
        return self.environment() == "local"

    def is_production(self) -> bool:
        """Check if the application is in production environment."""
        return self.environment() == "production"

    def is_testing(self) -> bool:
        """Check if the application is in testing environment."""
        return self.environment() == "testing"

    def _register_base_bindings(self) -> None:
        """Register the base bindings in the container."""
        self.instance("app", self)
        self.instance(Application, self)
        self.instance(Container, self)

    def _register_base_service_providers(self) -> None:
        """Register the base service providers."""
        pass

    def register(
        self, provider: Type[ServiceProvider] | ServiceProvider, force: bool = False
    ) -> ServiceProvider:
        """
        Register a service provider with the application.

        Args:
            provider: The service provider class or instance
            force: Force registration even if already registered

        Returns:
            The registered service provider instance
        """
        if isinstance(provider, type):
            provider = provider(self)

        provider_class = provider.__class__.__name__

        if provider_class in self._loaded_providers and not force:
            return provider

        provider.register()

        self._mark_as_registered(provider)

        if self._booted:
            self._boot_provider(provider)

        return provider

    def register_configured_providers(self) -> None:
        """Register all configured providers from bootstrap/providers.py."""
        providers_file = self.bootstrap_path("providers.py")

        if os.path.exists(providers_file):
            import importlib.util

            spec = importlib.util.spec_from_file_location("providers", providers_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "providers"):
                    for provider_class in module.providers:
                        self.register(provider_class)

    def _mark_as_registered(self, provider: ServiceProvider) -> None:
        """
        Mark the given provider as registered.

        Args:
            provider: The service provider to mark
        """
        self._service_providers.append(provider)
        self._loaded_providers[provider.__class__.__name__] = True

    def boot(self) -> None:
        """
        Boot the application's service providers.
        """
        if self._booted:
            return

        for provider in self._service_providers:
            self._boot_provider(provider)

        self._booted = True

    def _boot_provider(self, provider: ServiceProvider) -> None:
        """
        Boot the given service provider.

        Args:
            provider: The service provider to boot
        """
        provider.call_booting_callbacks()

        provider.boot()

        provider.call_booted_callbacks()

    def booting(self, callback) -> None:
        """
        Register a new boot listener.

        Args:
            callback: The callback to execute during boot
        """
        for provider in self._service_providers:
            provider.booting(callback)

    def booted(self, callback) -> None:
        """
        Register a new booted listener.

        Args:
            callback: The callback to execute after boot
        """
        for provider in self._service_providers:
            provider.booted(callback)

    def bootstrapped(self) -> bool:
        """
        Determine if the application has been bootstrapped before.

        Returns:
            True if bootstrapped, False otherwise
        """
        return self._bootstrapped

    def has_been_bootstrapped(self) -> bool:
        """
        Determine if the application has been bootstrapped before.

        Returns:
            True if bootstrapped, False otherwise
        """
        return self._bootstrapped

    def set_base_path(self, base_path: str) -> "Application":
        """
        Set the base path for the application.

        Args:
            base_path: The new base path

        Returns:
            The application instance for chaining
        """
        self._base_path = str(Path(base_path).resolve())
        return self

    def get_providers(self, provider_class: Type[ServiceProvider]) -> List[ServiceProvider]:
        """
        Get all registered providers of a certain type.

        Args:
            provider_class: The provider class to search for

        Returns:
            List of matching providers
        """
        return [p for p in self._service_providers if isinstance(p, provider_class)]

    def get_provider(self, provider_class: Type[ServiceProvider]) -> Optional[ServiceProvider]:
        """
        Get a registered provider instance.

        Args:
            provider_class: The provider class to find

        Returns:
            The provider instance or None
        """
        providers = self.get_providers(provider_class)
        return providers[0] if providers else None

    def provider_is_loaded(self, provider: str) -> bool:
        """
        Determine if the given provider is loaded.

        Args:
            provider: The provider class name

        Returns:
            True if loaded, False otherwise
        """
        return provider in self._loaded_providers

    def terminate(self) -> None:
        """
        Terminate the application.

        Performs any cleanup needed when the application shuts down.
        """
        pass

    def __repr__(self) -> str:
        """String representation of the application."""
        return (
            f"<Application version={self.VERSION} "
            f"env={self.environment()} "
            f"providers={len(self._service_providers)}>"
        )
