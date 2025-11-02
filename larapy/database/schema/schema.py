from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    MetaData,
    Index,
    ForeignKey,
)
from sqlalchemy import create_engine


class Blueprint:
    def __init__(self, table_name: str, callback: Optional[Callable] = None):
        self.table_name = table_name
        self._columns = []
        self._indexes = []
        self._foreign_keys = []
        self._primary_key = None

        if callback:
            callback(self)

    def id(self, column_name: str = "id"):
        return self.increments(column_name)

    def increments(self, column_name: str = "id"):
        self._columns.append(
            {
                "name": column_name,
                "type": "integer",
                "autoincrement": True,
                "primary_key": True,
                "nullable": False,
            }
        )
        self._primary_key = column_name
        return self

    def morph(self, name: str):
        self.string(f"{name}_type")
        self.big_integer(f"{name}_id")
        self.index([f"{name}_type", f"{name}_id"])
        return self

    def integer(self, column_name: str, autoincrement: bool = False, unsigned: bool = False):
        self._columns.append(
            {
                "name": column_name,
                "type": "integer",
                "autoincrement": autoincrement,
                "nullable": True,
            }
        )
        return self

    def big_integer(self, column_name: str, autoincrement: bool = False):
        return self.integer(column_name, autoincrement)

    def string(self, column_name: str, length: int = 255):
        self._columns.append(
            {"name": column_name, "type": "string", "length": length, "nullable": True}
        )
        return self

    def text(self, column_name: str):
        self._columns.append({"name": column_name, "type": "text", "nullable": True})
        return self

    def boolean(self, column_name: str):
        self._columns.append({"name": column_name, "type": "boolean", "nullable": True})
        return self

    def float(self, column_name: str, precision: int = 10, scale: int = 2):
        self._columns.append({"name": column_name, "type": "float", "nullable": True})
        return self

    def decimal(self, column_name: str, precision: int = 8, scale: int = 2):
        return self.float(column_name, precision, scale)

    def datetime(self, column_name: str):
        self._columns.append({"name": column_name, "type": "datetime", "nullable": True})
        return self

    def timestamp(self, column_name: str):
        return self.datetime(column_name)

    def timestamps(self):
        self.timestamp("created_at").nullable()
        self.timestamp("updated_at").nullable()
        return self

    def nullable(self):
        if self._columns:
            self._columns[-1]["nullable"] = True
        return self

    def default(self, value: Any):
        if self._columns:
            self._columns[-1]["default"] = value
        return self

    def unique(self):
        if self._columns:
            self._columns[-1]["unique"] = True
        return self

    def index(self, columns: List[str], name: Optional[str] = None):
        if not name:
            name = f"{self.table_name}_{'_'.join(columns)}_index"

        self._indexes.append({"name": name, "columns": columns})
        return self

    def foreign(self, column: str):
        return ForeignKeyBuilder(self, column)

    def add_foreign_key(self, column: str, references: str, on: str):
        self._foreign_keys.append({"column": column, "references": references, "on": on})

    def get_columns(self) -> List[Dict]:
        return self._columns

    def get_indexes(self) -> List[Dict]:
        return self._indexes

    def get_foreign_keys(self) -> List[Dict]:
        return self._foreign_keys


class ForeignKeyBuilder:
    def __init__(self, blueprint: Blueprint, column: str):
        self._blueprint = blueprint
        self._column = column
        self._references = None
        self._on = None

    def references(self, column: str):
        self._references = column
        return self

    def on(self, table: str):
        self._on = table
        self._blueprint.add_foreign_key(self._column, self._references, self._on)
        return self._blueprint


class Schema:
    def __init__(self, connection):
        self._connection = connection
        self._metadata = MetaData()

    def create(self, table_name: str, callback: Callable):
        blueprint = Blueprint(table_name, callback)

        driver = self._connection.get_driver_name()

        if driver == "sqlite":
            query = self._build_sqlite_create(blueprint)
        elif driver == "mysql":
            query = self._build_mysql_create(blueprint)
        else:
            query = self._build_postgresql_create(blueprint)

        self._connection.statement(query)

        for index in blueprint.get_indexes():
            self._create_index(blueprint.table_name, index)

    def _build_sqlite_create(self, blueprint: Blueprint) -> str:
        columns_sql = []

        for col in blueprint.get_columns():
            col_def = f"{col['name']} "

            if col.get("primary_key"):
                col_def += "INTEGER PRIMARY KEY AUTOINCREMENT"
            elif col["type"] == "integer":
                col_def += "INTEGER"
            elif col["type"] == "string":
                col_def += f"VARCHAR({col.get('length', 255)})"
            elif col["type"] == "text":
                col_def += "TEXT"
            elif col["type"] == "boolean":
                col_def += "INTEGER"
            elif col["type"] == "float":
                col_def += "REAL"
            elif col["type"] == "datetime":
                col_def += "DATETIME"

            if not col.get("primary_key"):
                if not col.get("nullable", True):
                    col_def += " NOT NULL"

                if "default" in col:
                    default_val = col["default"]
                    if isinstance(default_val, str):
                        col_def += f" DEFAULT '{default_val}'"
                    else:
                        col_def += f" DEFAULT {default_val}"

                if col.get("unique"):
                    col_def += " UNIQUE"

            columns_sql.append(col_def)

        for fk in blueprint.get_foreign_keys():
            columns_sql.append(
                f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['on']}({fk['references']})"
            )

        query = f"CREATE TABLE {blueprint.table_name} (\n  "
        query += ",\n  ".join(columns_sql)
        query += "\n)"

        return query

    def _build_mysql_create(self, blueprint: Blueprint) -> str:
        columns_sql = []

        for col in blueprint.get_columns():
            col_def = f"`{col['name']}` "

            if col["type"] == "integer":
                col_def += "INT"
                if col.get("autoincrement"):
                    col_def += " AUTO_INCREMENT"
            elif col["type"] == "string":
                col_def += f"VARCHAR({col.get('length', 255)})"
            elif col["type"] == "text":
                col_def += "TEXT"
            elif col["type"] == "boolean":
                col_def += "TINYINT(1)"
            elif col["type"] == "float":
                col_def += "DOUBLE"
            elif col["type"] == "datetime":
                col_def += "DATETIME"

            if not col.get("nullable", True):
                col_def += " NOT NULL"

            if "default" in col:
                default_val = col["default"]
                if isinstance(default_val, str):
                    col_def += f" DEFAULT '{default_val}'"
                else:
                    col_def += f" DEFAULT {default_val}"

            if col.get("unique"):
                col_def += " UNIQUE"

            if col.get("primary_key"):
                col_def += " PRIMARY KEY"

            columns_sql.append(col_def)

        query = f"CREATE TABLE `{blueprint.table_name}` (\n  "
        query += ",\n  ".join(columns_sql)
        query += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"

        return query

    def _build_postgresql_create(self, blueprint: Blueprint) -> str:
        columns_sql = []

        for col in blueprint.get_columns():
            col_def = f'"{col["name"]}" '

            if col.get("primary_key"):
                col_def += "SERIAL PRIMARY KEY"
            elif col["type"] == "integer":
                col_def += "INTEGER"
            elif col["type"] == "string":
                col_def += f"VARCHAR({col.get('length', 255)})"
            elif col["type"] == "text":
                col_def += "TEXT"
            elif col["type"] == "boolean":
                col_def += "BOOLEAN"
            elif col["type"] == "float":
                col_def += "DOUBLE PRECISION"
            elif col["type"] == "datetime":
                col_def += "TIMESTAMP"

            if not col.get("primary_key"):
                if not col.get("nullable", True):
                    col_def += " NOT NULL"

                if "default" in col:
                    default_val = col["default"]
                    if isinstance(default_val, str):
                        col_def += f" DEFAULT '{default_val}'"
                    else:
                        col_def += f" DEFAULT {default_val}"

                if col.get("unique"):
                    col_def += " UNIQUE"

            columns_sql.append(col_def)

        query = f'CREATE TABLE "{blueprint.table_name}" (\n  '
        query += ",\n  ".join(columns_sql)
        query += "\n)"

        return query

    def _create_index(self, table_name: str, index: Dict):
        columns = ", ".join(index["columns"])
        query = f"CREATE INDEX {index['name']} ON {table_name} ({columns})"
        self._connection.statement(query)

    def drop(self, table_name: str):
        query = f"DROP TABLE {table_name}"
        self._connection.statement(query)

    def drop_if_exists(self, table_name: str):
        driver = self._connection.get_driver_name()

        if driver == "sqlite":
            query = f"DROP TABLE IF EXISTS {table_name}"
        elif driver == "mysql":
            query = f"DROP TABLE IF EXISTS `{table_name}`"
        else:
            query = f'DROP TABLE IF EXISTS "{table_name}"'

        self._connection.statement(query)

    def has_table(self, table_name: str) -> bool:
        driver = self._connection.get_driver_name()

        if driver == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            results = self._connection.select(query, [table_name])
        elif driver == "mysql":
            query = "SHOW TABLES LIKE ?"
            results = self._connection.select(query, [table_name])
        else:
            query = "SELECT tablename FROM pg_tables WHERE tablename = ?"
            results = self._connection.select(query, [table_name])

        return len(results) > 0

    def has_column(self, table_name: str, column_name: str) -> bool:
        driver = self._connection.get_driver_name()

        if driver == "sqlite":
            query = f"PRAGMA table_info({table_name})"
            results = self._connection.select(query)
            return any(row["name"] == column_name for row in results)
        elif driver == "mysql":
            query = f"SHOW COLUMNS FROM `{table_name}` LIKE ?"
            results = self._connection.select(query, [column_name])
        else:
            query = "SELECT column_name FROM information_schema.columns WHERE table_name = ? AND column_name = ?"
            results = self._connection.select(query, [table_name, column_name])

        return len(results) > 0

    def get_tables(self) -> List[str]:
        driver = self._connection.get_driver_name()

        if driver == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            results = self._connection.select(query)
            return [row["name"] for row in results]
        elif driver == "mysql":
            query = "SHOW TABLES"
            results = self._connection.select(query)
            key = list(results[0].keys())[0] if results else None
            return [row[key] for row in results] if key else []
        else:
            query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            results = self._connection.select(query)
            return [row["tablename"] for row in results]
