from larapy.console.commands.base_migration_command import BaseMigrationCommand
from larapy.database.connection import Connection


class MigrateResetCommand(BaseMigrationCommand):
    signature = "migrate:reset {--pretend}"
    description = "Rollback all database migrations"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__(connection, config)

    def handle(self) -> int:
        if not self.ensure_connection():
            return 1

        repository = self.create_repository()

        if not self.ensure_repository_exists(repository):
            self.error("No migrations to reset")
            return 1

        migrator = self.create_migrator(repository)

        pretend = self.option("pretend", False)

        migrations = migrator.reset(self.get_migration_paths(), pretend)

        self.output_migration_notes(migrator.get_notes())

        if migrations:
            self.info(f"Reset {len(migrations)} migration(s)")

        return 0
