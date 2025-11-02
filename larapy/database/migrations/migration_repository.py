from typing import List, Dict, Optional


class MigrationRepository:

    def __init__(self, connection, table: str = "migrations"):
        self._connection = connection
        self._table = table

    def create_repository(self):
        schema = self._connection.schema()

        if not schema.has_table(self._table):
            schema.create(
                self._table,
                lambda table: (
                    table.increments("id"),
                    table.string("migration"),
                    table.integer("batch"),
                ),
            )

    def repository_exists(self) -> bool:
        schema = self._connection.schema()
        return schema.has_table(self._table)

    def get_ran(self) -> List[str]:
        if not self.repository_exists():
            return []

        results = (
            self._connection.table(self._table).order_by("migration", "asc").pluck("migration")
        )

        return results

    def get_migrations(self, steps: int = None) -> List[Dict]:
        query = self._connection.table(self._table)

        if steps is not None:
            query = query.where("batch", ">=", 1).order_by("migration", "desc").limit(steps)

        return query.order_by("migration", "asc").get()

    def get_last(self) -> List[Dict]:
        batch = self.get_last_batch_number()

        if batch == 0:
            return []

        return (
            self._connection.table(self._table)
            .where("batch", "=", batch)
            .order_by("migration", "desc")
            .get()
        )

    def get_migrations_batches(self) -> Dict[str, int]:
        results = self._connection.table(self._table).order_by("migration", "asc").get()

        return {row["migration"]: row["batch"] for row in results}

    def log(self, migration: str, batch: int):
        self._connection.table(self._table).insert({"migration": migration, "batch": batch})

    def delete(self, migration: str):
        self._connection.table(self._table).where("migration", "=", migration).delete()

    def get_next_batch_number(self) -> int:
        return self.get_last_batch_number() + 1

    def get_last_batch_number(self) -> int:
        result = self._connection.table(self._table).max("batch")
        return result if result is not None else 0
