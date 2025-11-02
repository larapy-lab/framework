from larapy.console.commands.base_migration_command import BaseMigrationCommand
from larapy.database.connection import Connection


class MigrateRollbackCommand(BaseMigrationCommand):
    signature = "migrate:rollback {--step=} {--pretend}"
    description = "Rollback the last database migration"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__(connection, config)

    def handle(self) -> int:
        if not self.ensure_connection():
            return 1

        repository = self.create_repository()

        if not self.ensure_repository_exists(repository):
            self.error("No migrations to rollback")
            return 1

        migrator = self.create_migrator(repository)

        options = {"pretend": self.option("pretend", False), "step": self.option("step", False)}

        migrations = migrator.rollback(self.get_migration_paths(), options)

        self.output_migration_notes(migrator.get_notes())

        if migrations:
            self.info(f"Rolled back {len(migrations)} migration(s)")

        return 0
