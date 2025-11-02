"""
Integration tests demonstrating real-world usage scenarios
"""

import pytest

from larapy.foundation import Application
from larapy.support import ServiceProvider


class Database:
    """Simulates a real database connection."""

    def __init__(self, config: dict):
        self.config = config
        self.connected = False
        self.queries = []

    def connect(self):
        self.connected = True

    def query(self, sql: str):
        if not self.connected:
            raise RuntimeError("Database not connected")
        self.queries.append(sql)
        return f"Result: {sql}"


class Cache:
    """Simulates a real cache system."""

    def __init__(self, driver: str = "redis"):
        self.driver = driver
        self.store = {}

    def get(self, key: str, default=None):
        return self.store.get(key, default)

    def put(self, key: str, value, ttl: int = 3600):
        self.store[key] = value

    def forget(self, key: str):
        self.store.pop(key, None)


class Logger:
    """Simulates a logging system."""

    def __init__(self):
        self.logs = []

    def info(self, message: str):
        self.logs.append(("info", message))

    def error(self, message: str):
        self.logs.append(("error", message))


class UserRepository:
    """Repository for user data access."""

    def __init__(self, database: Database, cache: Cache, logger: Logger):
        self.database = database
        self.cache = cache
        self.logger = logger

    def find(self, user_id: int):
        cache_key = f"user:{user_id}"
        
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"User {user_id} loaded from cache")
            return cached
        
        user_data = self.database.query(f"SELECT * FROM users WHERE id = {user_id}")
        self.cache.put(cache_key, user_data)
        self.logger.info(f"User {user_id} loaded from database")
        
        return user_data


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, logger: Logger):
        self.logger = logger
        self.sent = []

    def send(self, user_id: int, message: str):
        self.sent.append((user_id, message))
        self.logger.info(f"Notification sent to user {user_id}")


@pytest.fixture
def app():
    """Create application for integration tests."""
    return Application()


class TestDatabaseIntegration:
    """Test database provider and repository integration."""

    def test_database_provider_lifecycle(self, app):
        """Test complete database provider lifecycle."""

        class DatabaseServiceProvider(ServiceProvider):
            def register(self):
                super().register()
                self.app.singleton(
                    Database,
                    lambda c: Database({"host": "localhost", "port": 5432}),
                )

            def boot(self):
                db = self.app.make(Database)
                db.connect()

        app.register(DatabaseServiceProvider)
        app.boot()
        
        db = app.make(Database)
        assert db.connected
        assert db.config["host"] == "localhost"

    def test_multiple_services_with_dependencies(self, app):
        """Test multiple services with interdependencies."""

        class InfrastructureProvider(ServiceProvider):
            @property
            def singletons(self):
                return {
                    Database: lambda c: Database({"host": "localhost"}),
                    Cache: Cache,
                    Logger: Logger,
                }

            def boot(self):
                db = self.app.make(Database)
                db.connect()

        class RepositoryProvider(ServiceProvider):
            @property
            def singletons(self):
                return {UserRepository: UserRepository}

        app.register(InfrastructureProvider)
        app.register(RepositoryProvider)
        app.boot()
        
        repo = app.make(UserRepository)
        
        user = repo.find(1)
        assert "SELECT * FROM users WHERE id = 1" in user
        
        cached_user = repo.find(1)
        assert cached_user == user
        
        logger = app.make(Logger)
        assert len(logger.logs) == 2
        assert logger.logs[0][1] == "User 1 loaded from database"
        assert logger.logs[1][1] == "User 1 loaded from cache"


class TestCompleteApplicationStack:
    """Test complete application stack like a real application."""

    def test_full_application_with_multiple_layers(self, app):
        """Test a complete application with multiple service layers."""

        class CoreServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {Logger: Logger}

        class DatabaseServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {Database: lambda c: Database({"host": "localhost"})}

            def boot(self):
                db = self.app.make(Database)
                db.connect()
                
                logger = self.app.make(Logger)
                logger.info("Database connected")

        class CacheServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {Cache: lambda c: Cache("redis")}

            def boot(self):
                logger = self.app.make(Logger)
                logger.info("Cache initialized")

        class RepositoryServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {UserRepository: UserRepository}

        class NotificationServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {NotificationService: NotificationService}

        app.register(CoreServiceProvider)
        app.register(DatabaseServiceProvider)
        app.register(CacheServiceProvider)
        app.register(RepositoryServiceProvider)
        app.register(NotificationServiceProvider)
        app.boot()
        
        repo = app.make(UserRepository)
        notifier = app.make(NotificationService)
        
        user = repo.find(100)
        notifier.send(100, "Welcome!")
        
        logger = app.make(Logger)
        
        assert ("info", "Database connected") in logger.logs
        assert ("info", "Cache initialized") in logger.logs
        assert ("info", "User 100 loaded from database") in logger.logs
        assert ("info", "Notification sent to user 100") in logger.logs


class TestLaravelLikeUsage:
    """Test usage patterns that mirror Laravel."""

    def test_laravel_style_service_provider(self, app):
        """Test Laravel-style service provider pattern."""

        class AppServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {
                    Logger: Logger,
                    Cache: Cache,
                }

            def register(self):
                super().register()
                
                self.app.singleton(
                    Database,
                    lambda c: Database({"host": "localhost", "database": "myapp"}),
                )

            def boot(self):
                db = self.app.make(Database)
                db.connect()
                
                cache = self.app.make(Cache)
                cache.put("app.booted", True)
                
                logger = self.app.make(Logger)
                logger.info("Application ready")

        provider = app.register(AppServiceProvider)
        app.boot()
        
        assert provider is not None
        assert app.make(Database).connected
        assert app.make(Cache).get("app.booted") is True
        assert app.make(Logger).logs[0] == ("info", "Application ready")

    def test_service_resolution_like_laravel(self, app):
        """Test service resolution similar to Laravel's app() helper."""

        class TestProvider(ServiceProvider):
            @property
            def singletons(self):
                return {
                    Database: lambda c: Database({"host": "localhost"}),
                    Logger: Logger,
                }

        app.register(TestProvider)
        app.boot()
        
        db1 = app.make(Database)
        db2 = app.make(Database)
        assert db1 is db2
        
        logger = app.make(Logger)
        assert isinstance(logger, Logger)


class TestProviderBootstrapOrdering:
    """Test that providers boot in correct order."""

    def test_providers_boot_after_all_registered(self, app):
        """Test that all providers are registered before any boot."""

        order = []

        class Provider1(ServiceProvider):
            def register(self):
                super().register()
                order.append("p1_register")

            def boot(self):
                order.append("p1_boot")

        class Provider2(ServiceProvider):
            def register(self):
                super().register()
                order.append("p2_register")

            def boot(self):
                order.append("p2_boot")

        class Provider3(ServiceProvider):
            def register(self):
                super().register()
                order.append("p3_register")

            def boot(self):
                order.append("p3_boot")

        app.register(Provider1)
        app.register(Provider2)
        app.register(Provider3)
        app.boot()
        
        assert order == [
            "p1_register",
            "p2_register",
            "p3_register",
            "p1_boot",
            "p2_boot",
            "p3_boot",
        ]

    def test_late_registered_provider_boots_immediately(self, app):
        """Test provider registered after boot is booted immediately."""

        order = []

        class EarlyProvider(ServiceProvider):
            def boot(self):
                order.append("early_boot")

        class LateProvider(ServiceProvider):
            def boot(self):
                order.append("late_boot")

        app.register(EarlyProvider)
        app.boot()
        app.register(LateProvider)
        
        assert order == ["early_boot", "late_boot"]


class TestRealWorldScenario:
    """Test a complete real-world scenario."""

    def test_web_application_bootstrap(self, app):
        """Simulate a complete web application bootstrap process."""

        class ConfigServiceProvider(ServiceProvider):
            def register(self):
                super().register()
                config = {
                    "app": {"name": "My App", "env": "production"},
                    "database": {"host": "localhost", "port": 5432},
                    "cache": {"driver": "redis"},
                }
                self.app.instance("config", config)

        class DatabaseServiceProvider(ServiceProvider):
            def register(self):
                super().register()
                config = self.app.make("config")
                self.app.singleton(
                    Database,
                    lambda c: Database(config["database"]),
                )

            def boot(self):
                db = self.app.make(Database)
                db.connect()

        class CacheServiceProvider(ServiceProvider):
            def register(self):
                super().register()
                config = self.app.make("config")
                self.app.singleton(
                    Cache,
                    lambda c: Cache(config["cache"]["driver"]),
                )

        class LogServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {Logger: Logger}

            def boot(self):
                logger = self.app.make(Logger)
                config = self.app.make("config")
                logger.info(f"Application {config['app']['name']} starting")

        class AppServiceProvider(ServiceProvider):
            @property
            def singletons(self):
                return {
                    UserRepository: UserRepository,
                    NotificationService: NotificationService,
                }

            def boot(self):
                logger = self.app.make(Logger)
                logger.info("Application services registered")

        app.register(ConfigServiceProvider)
        app.register(LogServiceProvider)
        app.register(DatabaseServiceProvider)
        app.register(CacheServiceProvider)
        app.register(AppServiceProvider)
        
        app.boot()
        
        db = app.make(Database)
        cache = app.make(Cache)
        logger = app.make(Logger)
        repo = app.make(UserRepository)
        
        assert db.connected
        assert cache.driver == "redis"
        assert len(logger.logs) >= 2
        assert isinstance(repo, UserRepository)
        
        user = repo.find(42)
        assert "SELECT * FROM users WHERE id = 42" in user
