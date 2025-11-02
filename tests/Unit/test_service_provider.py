"""
Unit tests for Service Providers
"""

import pytest

from larapy.container import Container
from larapy.support import ServiceProvider


class DatabaseConnection:
    """Mock database connection."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.connected = False

    def connect(self):
        self.connected = True
        return self


class CacheInterface:
    """Mock cache interface."""

    def get(self, key: str):
        raise NotImplementedError

    def set(self, key: str, value: str):
        raise NotImplementedError


class RedisCache(CacheInterface):
    """Mock Redis cache implementation."""

    def __init__(self):
        self.storage = {}

    def get(self, key: str):
        return self.storage.get(key)

    def set(self, key: str, value: str):
        self.storage[key] = value


class Logger:
    """Mock logger."""

    def __init__(self):
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)


class MailManager:
    """Mock mail manager."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def send(self, to: str, message: str):
        self.logger.log(f"Sending email to {to}: {message}")


@pytest.fixture
def container():
    """Create a fresh container for each test."""
    return Container()


class TestServiceProviderBasics:
    """Test basic service provider functionality."""

    def test_provider_creation(self, container):
        """Test that a service provider can be created."""

        class TestProvider(ServiceProvider):
            pass

        provider = TestProvider(container)
        assert provider is not None
        assert provider.app is container

    def test_provider_has_access_to_container(self, container):
        """Test that provider has access to the container."""

        class TestProvider(ServiceProvider):
            def register(self):
                assert self.app is not None
                assert isinstance(self.app, Container)

        provider = TestProvider(container)
        provider.register()

    def test_register_method_called(self, container):
        """Test that register method is called."""

        class TestProvider(ServiceProvider):
            def register(self):
                self.registered = True

        provider = TestProvider(container)
        provider.register()
        assert provider.registered

    def test_boot_method_called(self, container):
        """Test that boot method is called."""

        class TestProvider(ServiceProvider):
            def boot(self):
                self.booted = True

        provider = TestProvider(container)
        provider.boot()
        assert provider.booted


class TestServiceRegistration:
    """Test service registration in providers."""

    def test_register_simple_binding(self, container):
        """Test registering a simple binding."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.bind(DatabaseConnection, DatabaseConnection)

        provider = TestProvider(container)
        provider.register()

        db = container.make(DatabaseConnection)
        assert isinstance(db, DatabaseConnection)

    def test_register_singleton(self, container):
        """Test registering a singleton."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(DatabaseConnection, DatabaseConnection)

        provider = TestProvider(container)
        provider.register()

        db1 = container.make(DatabaseConnection)
        db2 = container.make(DatabaseConnection)
        assert db1 is db2

    def test_register_with_factory(self, container):
        """Test registering with a factory function."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(
                    DatabaseConnection,
                    lambda c: DatabaseConnection({"host": "localhost"}),
                )

        provider = TestProvider(container)
        provider.register()

        db = container.make(DatabaseConnection)
        assert db.config["host"] == "localhost"

    def test_register_interface_binding(self, container):
        """Test registering an interface to implementation binding."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.bind(CacheInterface, RedisCache)

        provider = TestProvider(container)
        provider.register()

        cache = container.make(CacheInterface)
        assert isinstance(cache, RedisCache)


class TestBindingsProperty:
    """Test the bindings property."""

    def test_bindings_property_registered(self, container):
        """Test that bindings property is automatically registered."""

        class TestProvider(ServiceProvider):
            @property
            def bindings(self):
                return {CacheInterface: RedisCache}

        provider = TestProvider(container)
        provider.register()

        cache = container.make(CacheInterface)
        assert isinstance(cache, RedisCache)

    def test_multiple_bindings(self, container):
        """Test multiple bindings in property."""

        class TestProvider(ServiceProvider):
            @property
            def bindings(self):
                return {
                    CacheInterface: RedisCache,
                    DatabaseConnection: DatabaseConnection,
                }

        provider = TestProvider(container)
        provider.register()

        cache = container.make(CacheInterface)
        db = container.make(DatabaseConnection)

        assert isinstance(cache, RedisCache)
        assert isinstance(db, DatabaseConnection)


class TestSingletonsProperty:
    """Test the singletons property."""

    def test_singletons_property_registered(self, container):
        """Test that singletons property is automatically registered."""

        class TestProvider(ServiceProvider):
            @property
            def singletons(self):
                return {DatabaseConnection: DatabaseConnection}

        provider = TestProvider(container)
        provider.register()

        db1 = container.make(DatabaseConnection)
        db2 = container.make(DatabaseConnection)

        assert db1 is db2

    def test_multiple_singletons(self, container):
        """Test multiple singletons in property."""

        class TestProvider(ServiceProvider):
            @property
            def singletons(self):
                return {
                    CacheInterface: RedisCache,
                    Logger: Logger,
                }

        provider = TestProvider(container)
        provider.register()

        cache1 = container.make(CacheInterface)
        cache2 = container.make(CacheInterface)
        logger1 = container.make(Logger)
        logger2 = container.make(Logger)

        assert cache1 is cache2
        assert logger1 is logger2


class TestBootMethod:
    """Test the boot method and lifecycle."""

    def test_boot_has_access_to_registered_services(self, container):
        """Test that boot method has access to registered services."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(Logger, Logger)

            def boot(self):
                logger = self.app.make(Logger)
                logger.log("Provider booted")
                self.logger = logger

        provider = TestProvider(container)
        provider.register()
        provider.boot()

        assert hasattr(provider, "logger")
        assert "Provider booted" in provider.logger.logs

    def test_boot_with_dependency_injection(self, container):
        """Test boot method with dependency injection."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(Logger, Logger)

            def boot(self):
                logger = self.app.make(Logger)
                logger.log("Booting")

        provider = TestProvider(container)
        provider.register()
        provider.boot()

        logger = container.make(Logger)
        assert "Booting" in logger.logs


class TestBootingCallbacks:
    """Test booting and booted callbacks."""

    def test_booting_callback(self, container):
        """Test registering and calling booting callback."""

        class TestProvider(ServiceProvider):
            pass

        provider = TestProvider(container)
        called = []

        provider.booting(lambda app: called.append("booting"))
        provider.call_booting_callbacks()

        assert "booting" in called

    def test_booted_callback(self, container):
        """Test registering and calling booted callback."""

        class TestProvider(ServiceProvider):
            pass

        provider = TestProvider(container)
        called = []

        provider.booted(lambda app: called.append("booted"))
        provider.call_booted_callbacks()

        assert "booted" in called

    def test_multiple_callbacks(self, container):
        """Test multiple booting/booted callbacks."""

        class TestProvider(ServiceProvider):
            pass

        provider = TestProvider(container)
        order = []

        provider.booting(lambda app: order.append(1))
        provider.booting(lambda app: order.append(2))
        provider.booted(lambda app: order.append(3))
        provider.booted(lambda app: order.append(4))

        provider.call_booting_callbacks()
        provider.call_booted_callbacks()

        assert order == [1, 2, 3, 4]


class TestDeferredProvider:
    """Test deferred provider functionality."""

    def test_is_deferred_default_false(self, container):
        """Test that providers are not deferred by default."""

        class TestProvider(ServiceProvider):
            pass

        provider = TestProvider(container)
        assert not provider.is_deferred()

    def test_provides_method(self, container):
        """Test the provides method."""

        class TestProvider(ServiceProvider):
            def provides(self):
                return ["cache", "redis"]

        provider = TestProvider(container)
        assert "cache" in provider.provides()
        assert "redis" in provider.provides()

    def test_when_method(self, container):
        """Test the when method."""

        class TestProvider(ServiceProvider):
            def when(self):
                return ["cache.requested", "redis.needed"]

        provider = TestProvider(container)
        assert "cache.requested" in provider.when()


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_multiple_providers_working_together(self, container):
        """Test multiple providers registering different services."""

        class CacheProvider(ServiceProvider):
            @property
            def singletons(self):
                return {CacheInterface: RedisCache}

        class LoggerProvider(ServiceProvider):
            @property
            def singletons(self):
                return {Logger: Logger}

        class MailProvider(ServiceProvider):
            @property
            def singletons(self):
                return {MailManager: MailManager}

        cache_provider = CacheProvider(container)
        logger_provider = LoggerProvider(container)
        mail_provider = MailProvider(container)

        cache_provider.register()
        logger_provider.register()
        mail_provider.register()

        cache = container.make(CacheInterface)
        logger = container.make(Logger)
        mailer = container.make(MailManager)

        assert isinstance(cache, RedisCache)
        assert isinstance(logger, Logger)
        assert isinstance(mailer, MailManager)

    def test_provider_with_complex_registration(self, container):
        """Test provider with complex service registration logic."""

        class AppServiceProvider(ServiceProvider):
            def register(self):
                super().register()
                
                self.app.singleton(Logger, Logger)
                
                self.app.singleton(
                    DatabaseConnection,
                    lambda c: DatabaseConnection({"host": "localhost", "port": 5432}),
                )
                
                self.app.bind(CacheInterface, RedisCache)

            def boot(self):
                db = self.app.make(DatabaseConnection)
                db.connect()
                
                logger = self.app.make(Logger)
                logger.log("Application services registered")

        provider = AppServiceProvider(container)
        provider.register()
        provider.boot()

        db = container.make(DatabaseConnection)
        logger = container.make(Logger)

        assert db.connected
        assert "Application services registered" in logger.logs

    def test_provider_lifecycle(self, container):
        """Test the complete provider lifecycle."""

        lifecycle = []

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                lifecycle.append("register")
                self.app.singleton(Logger, Logger)

            def boot(self):
                lifecycle.append("boot")
                logger = self.app.make(Logger)
                logger.log("Booted")

        provider = TestProvider(container)
        
        provider.booting(lambda app: lifecycle.append("booting"))
        provider.booted(lambda app: lifecycle.append("booted"))
        
        provider.register()
        provider.call_booting_callbacks()
        provider.boot()
        provider.call_booted_callbacks()

        assert lifecycle == ["register", "booting", "boot", "booted"]


class TestProviderIntegration:
    """Test provider integration with container features."""

    def test_provider_with_tagged_services(self, container):
        """Test provider registering tagged services."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.bind("cache.redis", RedisCache)
                self.app.bind("logger", Logger)
                self.app.tag(["cache.redis", "logger"], ["core"])

        provider = TestProvider(container)
        provider.register()

        core_services = container.tagged("core")
        assert len(core_services) == 2

    def test_provider_with_aliases(self, container):
        """Test provider registering service aliases."""

        class TestProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.bind("app.cache", RedisCache)
                self.app.alias("app.cache", "cache")

        provider = TestProvider(container)
        provider.register()

        cache = container.make("cache")
        assert isinstance(cache, RedisCache)
