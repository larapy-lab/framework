"""
Unit tests for Application
"""

import os
import tempfile
from pathlib import Path

import pytest

from larapy.container import Container
from larapy.foundation import Application
from larapy.support import ServiceProvider


class CacheService:
    """Mock cache service."""

    def __init__(self):
        self.data = {}


class LogService:
    """Mock log service."""

    def __init__(self):
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)


@pytest.fixture
def app():
    """Create a fresh application for each test."""
    return Application()


@pytest.fixture
def temp_app(tmp_path):
    """Create an application with a temporary base path."""
    return Application(str(tmp_path))


class TestApplicationBasics:
    """Test basic application functionality."""

    def test_application_creation(self, app):
        """Test that an application can be created."""
        assert app is not None
        assert isinstance(app, Application)
        assert isinstance(app, Container)

    def test_application_version(self, app):
        """Test getting the application version."""
        version = app.version()
        assert version is not None
        assert isinstance(version, str)

    def test_application_is_container(self, app):
        """Test that application extends Container."""
        app.bind("test", CacheService)
        service = app.make("test")
        assert isinstance(service, CacheService)

    def test_application_self_binding(self, app):
        """Test that application binds itself to container."""
        resolved_app = app.make("app")
        assert resolved_app is app

        resolved_container = app.make(Container)
        assert resolved_container is app


class TestApplicationPaths:
    """Test application path methods."""

    def test_base_path(self, temp_app):
        """Test getting base path."""
        base = temp_app.base_path()
        assert base is not None
        assert os.path.isabs(base)

    def test_base_path_with_suffix(self, temp_app):
        """Test base path with additional path."""
        path = temp_app.base_path("test")
        assert path.endswith("test")

    def test_app_path(self, temp_app):
        """Test getting app directory path."""
        path = temp_app.path()
        assert "app" in path

    def test_config_path(self, temp_app):
        """Test getting config directory path."""
        path = temp_app.config_path()
        assert "config" in path

    def test_storage_path(self, temp_app):
        """Test getting storage directory path."""
        path = temp_app.storage_path()
        assert "storage" in path

    def test_bootstrap_path(self, temp_app):
        """Test getting bootstrap directory path."""
        path = temp_app.bootstrap_path()
        assert "bootstrap" in path

    def test_database_path(self, temp_app):
        """Test getting database directory path."""
        path = temp_app.database_path()
        assert "database" in path

    def test_resources_path(self, temp_app):
        """Test getting resources directory path."""
        path = temp_app.resources_path()
        assert "resources" in path

    def test_set_base_path(self, app, tmp_path):
        """Test setting base path."""
        new_path = str(tmp_path)
        result = app.set_base_path(new_path)
        
        assert result is app
        assert app.base_path() == str(Path(new_path).resolve())


class TestApplicationEnvironment:
    """Test environment detection methods."""

    def test_environment_default(self, app):
        """Test default environment."""
        env = app.environment()
        assert env in ["production", "local", "testing", "development"]

    def test_is_production(self, app):
        """Test production environment check."""
        os.environ["APP_ENV"] = "production"
        assert app.is_production()
        
        os.environ["APP_ENV"] = "local"
        assert not app.is_production()

    def test_is_local(self, app):
        """Test local environment check."""
        os.environ["APP_ENV"] = "local"
        assert app.is_local()
        
        os.environ["APP_ENV"] = "production"
        assert not app.is_local()

    def test_is_testing(self, app):
        """Test testing environment check."""
        os.environ["APP_ENV"] = "testing"
        assert app.is_testing()
        
        os.environ["APP_ENV"] = "production"
        assert not app.is_testing()


class TestServiceProviderRegistration:
    """Test service provider registration."""

    def test_register_provider_class(self, app):
        """Test registering a provider class."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton("test", CacheService)

        provider = app.register(TestProvider)
        
        assert provider is not None
        assert isinstance(provider, TestProvider)
        assert app.bound("test")

    def test_register_provider_instance(self, app):
        """Test registering a provider instance."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton("test", CacheService)

        provider_instance = TestProvider(app)
        provider = app.register(provider_instance)
        
        assert provider is provider_instance
        assert app.bound("test")

    def test_provider_not_registered_twice(self, app):
        """Test that providers are not registered twice by default."""

        call_count = []

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                call_count.append(1)

        app.register(TestProvider)
        app.register(TestProvider)
        
        assert len(call_count) == 1

    def test_force_provider_registration(self, app):
        """Test forcing provider registration."""

        call_count = []

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                call_count.append(1)

        app.register(TestProvider)
        app.register(TestProvider, force=True)
        
        assert len(call_count) == 2

    def test_multiple_providers(self, app):
        """Test registering multiple providers."""

        class CacheProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton("cache", CacheService)

        class LogProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton("log", LogService)

        app.register(CacheProvider)
        app.register(LogProvider)
        
        assert app.bound("cache")
        assert app.bound("log")


class TestBootingProviders:
    """Test booting service providers."""

    def test_boot_providers(self, app):
        """Test booting all registered providers."""

        booted = []

        class TestProvider(ServiceProvider):
            def boot(self):
                booted.append(True)

        app.register(TestProvider)
        app.boot()
        
        assert len(booted) == 1

    def test_boot_multiple_providers(self, app):
        """Test booting multiple providers."""

        order = []

        class Provider1(ServiceProvider):
            def boot(self):
                order.append(1)

        class Provider2(ServiceProvider):
            def boot(self):
                order.append(2)

        app.register(Provider1)
        app.register(Provider2)
        app.boot()
        
        assert order == [1, 2]

    def test_boot_only_once(self, app):
        """Test that boot only happens once."""

        boot_count = []

        class TestProvider(ServiceProvider):
            def boot(self):
                boot_count.append(1)

        app.register(TestProvider)
        app.boot()
        app.boot()
        
        assert len(boot_count) == 1

    def test_provider_registered_after_boot(self, app):
        """Test provider registered after application boot is booted immediately."""

        booted = []

        class TestProvider(ServiceProvider):
            def boot(self):
                booted.append(True)

        app.boot()
        app.register(TestProvider)
        
        assert len(booted) == 1


class TestProviderCallbacks:
    """Test provider booting and booted callbacks."""

    def test_booting_callbacks(self, app):
        """Test booting callbacks are called."""

        order = []

        class TestProvider(ServiceProvider):
            def boot(self):
                order.append("boot")

        provider = TestProvider(app)
        provider.booting(lambda a: order.append("booting"))
        
        app._service_providers.append(provider)
        app._boot_provider(provider)
        
        assert order == ["booting", "boot"]

    def test_booted_callbacks(self, app):
        """Test booted callbacks are called."""

        order = []

        class TestProvider(ServiceProvider):
            def boot(self):
                order.append("boot")

        provider = TestProvider(app)
        provider.booted(lambda a: order.append("booted"))
        
        app._service_providers.append(provider)
        app._boot_provider(provider)
        
        assert order == ["boot", "booted"]


class TestProviderQueries:
    """Test querying registered providers."""

    def test_get_providers(self, app):
        """Test getting all providers of a type."""

        class TestProvider(ServiceProvider):
            pass

        app.register(TestProvider)
        app.register(TestProvider, force=True)
        
        providers = app.get_providers(TestProvider)
        assert len(providers) == 2

    def test_get_provider(self, app):
        """Test getting first provider of a type."""

        class TestProvider(ServiceProvider):
            pass

        registered = app.register(TestProvider)
        found = app.get_provider(TestProvider)
        
        assert found is registered

    def test_provider_is_loaded(self, app):
        """Test checking if provider is loaded."""

        class TestProvider(ServiceProvider):
            pass

        assert not app.provider_is_loaded("TestProvider")
        
        app.register(TestProvider)
        
        assert app.provider_is_loaded("TestProvider")


class TestBootstrapState:
    """Test bootstrap state tracking."""

    def test_has_been_bootstrapped_default(self, app):
        """Test default bootstrap state."""
        assert not app.has_been_bootstrapped()

    def test_bootstrapped_alias(self, app):
        """Test bootstrapped is alias for has_been_bootstrapped."""
        assert app.bootstrapped() == app.has_been_bootstrapped()


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_full_application_lifecycle(self, app):
        """Test complete application lifecycle."""

        lifecycle = []

        class DatabaseProvider(ServiceProvider):
            def register(self):
                super().register()
                lifecycle.append("db_register")
                self.app.singleton("db", CacheService)

            def boot(self):
                lifecycle.append("db_boot")

        class CacheProvider(ServiceProvider):
            def register(self):
                super().register()
                lifecycle.append("cache_register")
                self.app.singleton("cache", CacheService)

            def boot(self):
                lifecycle.append("cache_boot")

        app.register(DatabaseProvider)
        app.register(CacheProvider)
        app.boot()
        
        assert lifecycle == [
            "db_register",
            "cache_register",
            "db_boot",
            "cache_boot",
        ]

    def test_provider_accessing_other_services(self, app):
        """Test provider accessing services from other providers."""

        class LogProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(LogService, LogService)

        class CacheProvider(ServiceProvider):
            def boot(self):
                logger = self.app.make(LogService)
                logger.log("Cache provider booted")

        app.register(LogProvider)
        app.register(CacheProvider)
        app.boot()
        
        logger = app.make(LogService)
        assert "Cache provider booted" in logger.logs

    def test_providers_with_dependencies(self, app):
        """Test providers with interdependent services."""

        class ServiceA:
            def __init__(self):
                self.name = "A"

        class ServiceB:
            def __init__(self, a: ServiceA):
                self.a = a
                self.name = "B"

        class ProviderA(ServiceProvider):
            @property
            def singletons(self):
                return {ServiceA: ServiceA}

        class ProviderB(ServiceProvider):
            @property
            def singletons(self):
                return {ServiceB: ServiceB}

        app.register(ProviderA)
        app.register(ProviderB)
        app.boot()
        
        service_b = app.make(ServiceB)
        assert service_b.a.name == "A"
        assert service_b.name == "B"


class TestApplicationRepr:
    """Test application string representation."""

    def test_repr(self, app):
        """Test __repr__ output."""
        repr_str = repr(app)
        assert "Application" in repr_str
        assert "version" in repr_str
        assert "env" in repr_str
