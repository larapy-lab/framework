from larapy.console.command import Command
import os
from datetime import datetime


class MakeMigrationCommand(Command):

    signature = "make:migration {name} {--create=} {--table=}"
    description = "Create a new migration file"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Migration name is required")
            return 1

        migration_path = self._config.get("migrations", {}).get("path", "database/migrations")

        os.makedirs(migration_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"{timestamp}_{name}.py"
        filepath = os.path.join(migration_path, filename)

        create_table = self.option("create", None)
        table_name = self.option("table", None)

        if create_table:
            stub = self._get_create_stub(create_table)
        elif table_name:
            stub = self._get_update_stub(table_name)
        else:
            stub = self._get_blank_stub()

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Created Migration: {filename}")

        return 0

    def _get_create_stub(self, table_name: str) -> str:
        return f"""class CreateTable:

    def __init__(self, connection):
        self._connection = connection

    def up(self):
        schema = self._connection.schema()

        schema.create('{table_name}', lambda table: (
            table.increments('id'),
            table.timestamps()
        ))

    def down(self):
        schema = self._connection.schema()
        schema.drop_if_exists('{table_name}')
"""

    def _get_update_stub(self, table_name: str) -> str:
        return f"""class UpdateTable:

    def __init__(self, connection):
        self._connection = connection

    def up(self):
        schema = self._connection.schema()

        schema.table('{table_name}', lambda table: (

        ))

    def down(self):
        schema = self._connection.schema()

        schema.table('{table_name}', lambda table: (

        ))
"""

    def _get_blank_stub(self) -> str:
        return """class Migration:

    def __init__(self, connection):
        self._connection = connection

    def up(self):
        pass

    def down(self):
        pass
"""
