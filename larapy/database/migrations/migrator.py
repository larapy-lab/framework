import os
import importlib.util
from typing import List, Dict, Callable, Optional
from pathlib import Path


class Migrator:

    def __init__(self, repository, connection, migration_paths: List[str] = None):
        self._repository = repository
        self._connection = connection
        self._migration_paths = migration_paths or []
        self._notes = []

    def run(self, paths: List[str] = None, options: Dict = None) -> List[str]:
        options = options or {}
        self._notes = []

        if not self._repository.repository_exists():
            self._repository.create_repository()

        paths = paths or self._migration_paths

        files = self.get_migration_files(paths)

        ran = self._repository.get_ran()

        migrations = [f for f in files if f not in ran]

        return self.run_pending(migrations, options)

    def run_pending(self, migrations: List[str], options: Dict = None) -> List[str]:
        options = options or {}

        if len(migrations) == 0:
            self._note("Nothing to migrate")
            return []

        batch = self._repository.get_next_batch_number()

        pretend = options.get("pretend", False)
        step = options.get("step", False)

        if step:
            migrations = migrations[:1]

        for migration in migrations:
            self.run_up(migration, batch, pretend)

        return migrations

    def run_up(self, migration: str, batch: int, pretend: bool = False):
        migration_instance = self._resolve(migration)

        if pretend:
            self._note(f"Pretending to run: {migration}")
            return

        self._note(f"Migrating: {migration}")

        self._run_migration(migration_instance, "up")

        self._repository.log(migration, batch)

        self._note(f"Migrated: {migration}")

    def rollback(self, paths: List[str] = None, options: Dict = None) -> List[str]:
        options = options or {}
        self._notes = []

        paths = paths or self._migration_paths

        migrations = self._repository.get_last()

        if len(migrations) == 0:
            self._note("Nothing to rollback")
            return []

        return self.rollback_migrations(migrations, paths, options)

    def rollback_migrations(
        self, migrations: List[Dict], paths: List[str], options: Dict
    ) -> List[str]:
        rolled_back = []

        pretend = options.get("pretend", False)
        step = options.get("step", False)

        if step:
            migrations = migrations[:1]

        for migration_data in migrations:
            migration = migration_data["migration"]

            if not self._migration_exists(migration, paths):
                self._note(f"Migration not found: {migration}")
                continue

            rolled_back.append(migration)

            self.run_down(migration, pretend)

        return rolled_back

    def run_down(self, migration: str, pretend: bool = False):
        migration_instance = self._resolve(migration)

        if pretend:
            self._note(f"Pretending to rollback: {migration}")
            return

        self._note(f"Rolling back: {migration}")

        self._run_migration(migration_instance, "down")

        self._repository.delete(migration)

        self._note(f"Rolled back: {migration}")

    def reset(self, paths: List[str] = None, pretend: bool = False) -> List[str]:
        self._notes = []
        paths = paths or self._migration_paths

        migrations = self._repository.get_migrations_batches()

        if len(migrations) == 0:
            self._note("Nothing to reset")
            return []

        rolled_back = []

        for migration in reversed(list(migrations.keys())):
            if not self._migration_exists(migration, paths):
                self._note(f"Migration not found: {migration}")
                continue

            rolled_back.append(migration)
            self.run_down(migration, pretend)

        return rolled_back

    def refresh(self, paths: List[str] = None, options: Dict = None):
        options = options or {}

        self.reset(paths, options.get("pretend", False))

        return self.run(paths, options)

    def get_migration_files(self, paths: List[str]) -> List[str]:
        files = []

        for path in paths:
            if not os.path.exists(path):
                continue

            for file in sorted(os.listdir(path)):
                if file.endswith(".py") and not file.startswith("__"):
                    files.append(file[:-3])

        return files

    def _migration_exists(self, migration: str, paths: List[str]) -> bool:
        for path in paths:
            file_path = os.path.join(path, f"{migration}.py")
            if os.path.exists(file_path):
                return True
        return False

    def _resolve(self, migration: str):
        for path in self._migration_paths:
            file_path = os.path.join(path, f"{migration}.py")

            if os.path.exists(file_path):
                spec = importlib.util.spec_from_file_location(migration, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, "up") and hasattr(attr, "down"):
                        if attr_name != "Migration":
                            return attr(self._connection)

        raise Exception(f"Migration not found: {migration}")

    def _run_migration(self, migration, method: str):
        getattr(migration, method)()

    def _note(self, message: str):
        self._notes.append(message)

    def get_notes(self) -> List[str]:
        return self._notes

    def repository_exists(self) -> bool:
        return self._repository.repository_exists()

    def has_ran_migrations(self) -> bool:
        return len(self._repository.get_ran()) > 0
