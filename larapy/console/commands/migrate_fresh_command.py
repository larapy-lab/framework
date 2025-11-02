from larapy.console.commands.base_migration_command import BaseMigrationCommand
from larapy.database.connection import Connection


class MigrateFreshCommand(BaseMigrationCommand):
    signature = "migrate:fresh {--seed}"
    description = "Drop all tables and re-run all migrations"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__(connection, config)

    def handle(self) -> int:
        if not self.ensure_connection():
            return 1

        self.info("Dropping all tables...")

        schema = self._connection.schema()
        tables = schema.get_tables()

        for table in tables:
            self.comment(f"Dropping table: {table}")
            schema.drop(table)

        self.info(f"Dropped {len(tables)} table(s)")

        repository = self.create_repository()
        migrator = self.create_migrator(repository)

        self.info("Running migrations...")
        migrator.run(self.get_migration_paths(), {})

        self.output_migration_notes(migrator.get_notes())

        self.info("Database created successfully")

        if self.option("seed", False):
            self.info("Seeding database...")
            from larapy.console.commands.db_seed_command import DbSeedCommand

            seed_command = DbSeedCommand(self._connection, self._config)
            seed_command.set_arguments([])
            seed_command.set_options({})
            seed_command.handle()

        return 0
