from typing import Any, Dict, List, Optional, Union
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection, Result
from sqlalchemy.pool import NullPool, QueuePool


class Connection:
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._engine = None
        self._connection = None
        self._transactions = []
        self._in_transaction = False
        self._metadata = MetaData()

    def connect(self) -> "Connection":
        if self._engine is None:
            self._engine = self._create_engine()
        return self

    def _create_engine(self) -> Engine:
        driver = self._config.get("driver", "sqlite")

        if driver == "sqlite":
            database = self._config.get("database", ":memory:")
            url = f"sqlite:///{database}"
            return create_engine(url, poolclass=NullPool)

        elif driver == "mysql":
            host = self._config.get("host", "localhost")
            port = self._config.get("port", 3306)
            database = self._config.get("database")
            username = self._config.get("username")
            password = self._config.get("password")
            charset = self._config.get("charset", "utf8mb4")

            url = (
                f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset={charset}"
            )
            return create_engine(url, poolclass=QueuePool, pool_size=5, max_overflow=10)

        elif driver in ["postgresql", "pgsql"]:
            host = self._config.get("host", "localhost")
            port = self._config.get("port", 5432)
            database = self._config.get("database")
            username = self._config.get("username")
            password = self._config.get("password")

            url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
            return create_engine(url, poolclass=QueuePool, pool_size=5, max_overflow=10)

        else:
            raise ValueError(f"Unsupported database driver: {driver}")

    def get_connection(self):
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = self._engine.connect()
        return self._connection

    def _prepare_bindings(self, query: str, bindings: List) -> tuple[str, Dict]:
        """Convert positional bindings (?) to named parameters (:param_N)."""
        if not bindings:
            return query, {}

        params = {}
        result_query = query

        for i, value in enumerate(bindings):
            param_name = f"param_{i}"
            params[param_name] = value
            result_query = result_query.replace("?", f":{param_name}", 1)

        return result_query, params

    def table(self, table_name: str):
        from larapy.database.query.builder import QueryBuilder

        return QueryBuilder(self, table_name)

    def select(self, query: str, bindings: Optional[List] = None) -> List[Dict]:
        conn = self.get_connection()

        if bindings:
            query, params = self._prepare_bindings(query, bindings)
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))

        rows = result.fetchall()

        if rows and hasattr(rows[0], "_mapping"):
            return [dict(row._mapping) for row in rows]
        return [dict(row) for row in rows]

    def insert(self, query: str, bindings: Optional[List] = None) -> int:
        conn = self.get_connection()

        if bindings:
            query, params = self._prepare_bindings(query, bindings)
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))

        if not self._in_transaction:
            conn.commit()
        return result.lastrowid if hasattr(result, "lastrowid") else 0

    def update(self, query: str, bindings: Optional[List] = None) -> int:
        conn = self.get_connection()

        if bindings:
            query, params = self._prepare_bindings(query, bindings)
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))

        if not self._in_transaction:
            conn.commit()
        return result.rowcount

    def delete(self, query: str, bindings: Optional[List] = None) -> int:
        conn = self.get_connection()

        if bindings:
            query, params = self._prepare_bindings(query, bindings)
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))

        if not self._in_transaction:
            conn.commit()
        return result.rowcount

    def statement(self, query: str, bindings: Optional[List] = None) -> bool:
        conn = self.get_connection()

        if bindings:
            query, params = self._prepare_bindings(query, bindings)
            conn.execute(text(query), params)
        else:
            conn.execute(text(query))

        if not self._in_transaction:
            conn.commit()
        return True

    def raw(self, query: str):
        return text(query)

    def begin_transaction(self):
        conn = self.get_connection()
        trans = conn.begin()
        self._transactions.append(trans)
        return trans

    def commit(self):
        if self._transactions:
            trans = self._transactions.pop()
            trans.commit()

    def rollback(self):
        if self._transactions:
            trans = self._transactions.pop()
            trans.rollback()

    def transaction(self, callback):
        self._in_transaction = True
        self.begin_transaction()

        try:
            result = callback()
            self.commit()
            return result
        except Exception as e:
            self.rollback()
            raise e
        finally:
            self._in_transaction = False

    def get_table_metadata(self, table_name: str) -> Table:
        return Table(table_name, self._metadata, autoload_with=self._engine)

    def disconnect(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_driver_name(self) -> str:
        """Get the database driver name."""
        return self._config.get("driver", "sqlite")

    def schema(self):
        """Get a schema builder instance."""
        from larapy.database.schema.schema import Schema

        return Schema(self)

    def get_config(self, key: str = None):
        if key:
            return self._config.get(key)
        return self._config

    def get_driver_name(self) -> str:
        return self._config.get("driver", "sqlite")
