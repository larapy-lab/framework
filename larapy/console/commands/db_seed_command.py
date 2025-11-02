from larapy.console.command import Command
from larapy.database.connection import Connection
from larapy.database.seeding.seeder_runner import SeederRunner


class DbSeedCommand(Command):

    signature = "db:seed {--class=}"
    description = "Seed the database with records"

    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__()
        self._connection = connection
        self._config = config or {}

    def handle(self) -> int:
        if not self._connection:
            self.error("Database connection not configured")
            return 1

        seeder_paths = self._config.get("seeders", {}).get("paths", ["database/seeders"])

        runner = SeederRunner(self._connection, seeder_paths)

        seeder_class = self.option("class", None)

        if seeder_class:
            self.info(f"Seeding: {seeder_class}")
            try:
                runner.call(seeder_class, silent=False)
                self.info(f"Seeded: {seeder_class}")
            except Exception as e:
                self.error(f"Seeding failed: {str(e)}")
                return 1
        else:
            self.info("Seeding: DatabaseSeeder")
            try:
                runner.call("DatabaseSeeder", silent=False)
                self.info("Database seeded successfully")
            except Exception as e:
                self.error(f"Seeding failed: {str(e)}")
                return 1

        return 0
