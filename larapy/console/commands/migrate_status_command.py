from larapy.console.command import Command
from larapy.database.connection import Connection
from larapy.database.migrations.migration_repository import MigrationRepository


class MigrateStatusCommand(Command):

    signature = "migrate:status"
    description = "Show the status of each migration"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__()
        self._connection = connection
        self._config = config or {}

    def handle(self) -> int:
        if not self._connection:
            self.error("Database connection not configured")
            return 1

        migration_paths = self._config.get("migrations", {}).get("paths", ["database/migrations"])
        migration_table = self._config.get("migrations", {}).get("table", "migrations")

        repository = MigrationRepository(self._connection, migration_table)

        if not repository.repository_exists():
            self.warn("No migrations table found")
            return 0

        import os

        all_migrations = []
        for path in migration_paths:
            if not os.path.exists(path):
                continue

            for file in sorted(os.listdir(path)):
                if file.endswith(".py") and not file.startswith("__"):
                    all_migrations.append(file[:-3])

        ran_migrations = repository.get_migrations_batches()

        if not all_migrations:
            self.info("No migrations found")
            return 0

        rows = []
        for migration in all_migrations:
            if migration in ran_migrations:
                status = "Ran"
                batch = str(ran_migrations[migration])
            else:
                status = "Pending"
                batch = "-"

            rows.append([status, migration, batch])

        self.table(["Status", "Migration", "Batch"], rows)

        return 0
