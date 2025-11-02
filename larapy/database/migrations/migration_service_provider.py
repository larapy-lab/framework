from larapy.support.service_provider import ServiceProvider
from larapy.database.migrations.migrator import Migrator
from larapy.database.migrations.migration_repository import MigrationRepository
from larapy.database.migrations.migration_creator import MigrationCreator


class MigrationServiceProvider(ServiceProvider):

    def register(self):
        self.container.singleton(
            "migration.repository", lambda app: MigrationRepository(app.make("db").connection())
        )

        self.container.singleton(
            "migrator",
            lambda app: Migrator(
                app.make("migration.repository"),
                app.make("db").connection(),
                app.make("config").get("database.migrations.paths", ["database/migrations"]),
            ),
        )

        self.container.singleton(
            "migration.creator",
            lambda app: MigrationCreator(
                app.make("config").get("database.migrations.path", "database/migrations")
            ),
        )
