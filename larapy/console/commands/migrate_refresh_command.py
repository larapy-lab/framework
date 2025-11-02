from larapy.console.commands.base_migration_command import BaseMigrationCommand
from larapy.database.connection import Connection


class MigrateRefreshCommand(BaseMigrationCommand):
    signature = "migrate:refresh {--seed} {--step=}"
    description = "Reset and re-run all migrations"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__(connection, config)

    def handle(self) -> int:
        if not self.ensure_connection():
            return 1

        repository = self.create_repository()
        migrator = self.create_migrator(repository)

        self.info("Rolling back all migrations...")
        migrator.reset(self.get_migration_paths(), False)

        self.output_migration_notes(migrator.get_notes())

        self.info("Running migrations...")
        migrator.run(self.get_migration_paths(), {})

        self.output_migration_notes(migrator.get_notes())

        self.info("Database refreshed successfully")

        if self.option("seed", False):
            self.info("Seeding database...")
            from larapy.console.commands.db_seed_command import DbSeedCommand

            seed_command = DbSeedCommand(self._connection, self._config)
            seed_command.set_arguments([])
            seed_command.set_options({})
            seed_command.handle()

        return 0
