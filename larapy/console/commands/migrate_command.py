from larapy.console.commands.base_migration_command import BaseMigrationCommand
from larapy.database.connection import Connection


class MigrateCommand(BaseMigrationCommand):
    signature = "migrate {--force} {--pretend} {--step}"
    description = "Run database migrations"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__(connection, config)

    def handle(self) -> int:
        if not self.ensure_connection():
            return 1

        repository = self.create_repository()
        migrator = self.create_migrator(repository)

        if not repository.repository_exists():
            self.info("Creating migrations table...")
            repository.create_repository()

        options = {"pretend": self.option("pretend", False), "step": self.option("step", False)}

        migrations = migrator.run(self.get_migration_paths(), options)

        self.output_migration_notes(migrator.get_notes())

        if migrations:
            self.info(f"Migrated {len(migrations)} migration(s)")

        return 0
