from larapy.support.service_provider import ServiceProvider
from larapy.database.database_manager import DatabaseManager


class DatabaseServiceProvider(ServiceProvider):
    """Service provider for the database system."""

    def register(self):
        """Register the database manager in the container."""

        def make_database_manager(app):
            config = app.make("config")
            return DatabaseManager(config.get("database", {}))

        self.app.singleton("db", make_database_manager)

    def boot(self):
        """Bootstrap the database system."""
        pass
