import os
from datetime import datetime
from pathlib import Path


class MigrationCreator:

    def __init__(self, migration_path: str):
        self._migration_path = migration_path

    def create(self, name: str, table: str = None, create: bool = False) -> str:
        migration_name = self._get_migration_name(name)

        path = self._get_path(migration_name)

        stub = self._get_stub(table, create)

        content = self._populate_stub(stub, table)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        return path

    def _get_migration_name(self, name: str) -> str:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        return f"{timestamp}_{name}"

    def _get_path(self, name: str) -> str:
        return os.path.join(self._migration_path, f"{name}.py")

    def _get_stub(self, table: str = None, create: bool = False) -> str:
        if create:
            return self._get_create_stub()
        elif table:
            return self._get_update_stub()
        else:
            return self._get_blank_stub()

    def _get_blank_stub(self) -> str:
        return """from larapy.database.migrations.migration import Migration


class {{class_name}}(Migration):

    def up(self):
        pass

    def down(self):
        pass
"""

    def _get_create_stub(self) -> str:
        return """from larapy.database.migrations.migration import Migration


class {{class_name}}(Migration):

    def up(self):
        schema = self._connection.schema()

        def define_table(table):
            table.increments('id')
            table.timestamps()

        schema.create('{{table}}', define_table)

    def down(self):
        self._connection.schema().drop_if_exists('{{table}}')
"""

    def _get_update_stub(self) -> str:
        return """from larapy.database.migrations.migration import Migration


class {{class_name}}(Migration):

    def up(self):
        schema = self._connection.schema()

        def modify_table(table):
            pass

        schema.table('{{table}}', modify_table)

    def down(self):
        schema = self._connection.schema()

        def modify_table(table):
            pass

        schema.table('{{table}}', modify_table)
"""

    def _populate_stub(self, stub: str, table: str = None) -> str:
        class_name = self._get_class_name(table)

        stub = stub.replace("{{class_name}}", class_name)

        if table:
            stub = stub.replace("{{table}}", table)

        return stub

    def _get_class_name(self, table: str = None) -> str:
        if table:
            parts = table.split("_")
            return "".join(word.capitalize() for word in parts) + "Migration"
        return "Migration"
