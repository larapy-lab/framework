"""
Service Provider Base Class

Provides the base implementation for all service providers in the framework.
Service providers are the central place for application bootstrapping.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type

from larapy.container import Container


class ServiceProvider(ABC):
    """
    Base class for all service providers.

    Service providers are responsible for binding services into the container
    and bootstrapping application components.
    """

    def __init__(self, app: Container) -> None:
        """
        Initialize the service provider.

        Args:
            app: The application container instance
        """
        self.app = app
        self._booting_callbacks: List[Callable] = []
        self._booted_callbacks: List[Callable] = []

    @property
    def bindings(self) -> Dict[Type, Type]:
        """
        All of the container bindings that should be registered.

        Returns:
            Dictionary mapping abstract types to concrete implementations
        """
        return {}

    @property
    def singletons(self) -> Dict[Type, Type]:
        """
        All of the container singletons that should be registered.

        Returns:
            Dictionary mapping abstract types to concrete singleton implementations
        """
        return {}

    def register(self) -> None:
        """
        Register any application services.

        This method is called during the registration phase of the application
        bootstrap. You should only bind things into the service container here.
        Never attempt to register event listeners, routes, or any other functionality.
        """
        self._register_bindings()

    def boot(self) -> None:
        """
        Bootstrap any application services.

        This method is called after all service providers have been registered.
        You have access to all services registered by all other service providers.
        """
        pass

    def _register_bindings(self) -> None:
        """
        Register the provider's bindings and singletons.

        Automatically processes the bindings and singletons properties.
        """
        for abstract, concrete in self.bindings.items():
            self.app.bind(abstract, concrete)

        for abstract, concrete in self.singletons.items():
            self.app.singleton(abstract, concrete)

    def booting(self, callback: Callable) -> None:
        """
        Register a booting callback to be run before the provider is booted.

        Args:
            callback: The callback to run before booting
        """
        self._booting_callbacks.append(callback)

    def booted(self, callback: Callable) -> None:
        """
        Register a booted callback to be run after the provider is booted.

        Args:
            callback: The callback to run after booting
        """
        self._booted_callbacks.append(callback)

    def call_booting_callbacks(self) -> None:
        """Call all registered booting callbacks."""
        for callback in self._booting_callbacks:
            callback(self.app)

    def call_booted_callbacks(self) -> None:
        """Call all registered booted callbacks."""
        for callback in self._booted_callbacks:
            callback(self.app)

    def provides(self) -> List[str]:
        """
        Get the services provided by the provider.

        Used for deferred providers to determine which services they provide.

        Returns:
            List of service names provided by this provider
        """
        return []

    def when(self) -> List[str]:
        """
        Get the events that trigger this service provider to register.

        Returns:
            List of event names that trigger registration
        """
        return []

    def is_deferred(self) -> bool:
        """
        Determine if the provider is deferred.

        Returns:
            True if the provider is deferred, False otherwise
        """
        return False

    def call_after_resolving(self, name: str, callback: Callable) -> None:
        """
        Setup an after resolving listener, or fire immediately if already resolved.

        Args:
            name: The service name to listen for
            callback: The callback to execute after resolution
        """
        if hasattr(self.app, "after_resolving"):
            self.app.after_resolving(name, callback)

            if hasattr(self.app, "resolved") and self.app.resolved(name):
                callback(self.app.make(name), self.app)


class DeferrableProvider(ABC):
    """
    Interface for deferred service providers.

    Deferred providers are only loaded when the services they provide
    are actually needed, improving application performance.
    """

    @abstractmethod
    def provides(self) -> List[str]:
        """
        Get the services provided by the provider.

        Returns:
            List of service names provided by this provider
        """
        pass
