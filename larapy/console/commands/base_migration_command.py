from larapy.console.command import Command
from larapy.database.connection import Connection
from larapy.database.migrations.migration_repository import MigrationRepository
from larapy.database.migrations.migrator import Migrator


class BaseMigrationCommand(Command):
    def __init__(self, connection: Connection = None, config: dict = None):
        super().__init__()
        self._connection = connection
        self._config = config or {}

    def get_migration_paths(self):
        return self._config.get("migrations", {}).get("paths", ["database/migrations"])

    def get_migration_table(self):
        return self._config.get("migrations", {}).get("table", "migrations")

    def create_repository(self) -> MigrationRepository:
        return MigrationRepository(self._connection, self.get_migration_table())

    def create_migrator(self, repository: MigrationRepository) -> Migrator:
        return Migrator(repository, self._connection, self.get_migration_paths())

    def output_migration_notes(self, notes):
        for note in notes:
            if "Migrating:" in note or "Rolling back:" in note or "Pretending" in note:
                self.comment(note)
            elif "Migrated:" in note or "Rolled back:" in note:
                self.info(note)
            elif "Nothing to" in note or "Migration not found" in note:
                self.warn(note)
            else:
                self.line(note)

    def ensure_connection(self) -> bool:
        if not self._connection:
            self.error("Database connection not configured")
            return False
        return True

    def ensure_repository_exists(self, repository: MigrationRepository) -> bool:
        if not repository.repository_exists():
            return False
        return True
