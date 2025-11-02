from typing import Dict, Optional
from larapy.database.connection import Connection


class DatabaseManager:
    def __init__(self, config: Dict):
        self._config = config
        self._connections: Dict[str, Connection] = {}
        self._default_connection = config.get("default", "sqlite")

    def connection(self, name: Optional[str] = None) -> Connection:
        name = name or self._default_connection

        if name not in self._connections:
            self._connections[name] = self._make_connection(name)

        return self._connections[name]

    def _make_connection(self, name: str) -> Connection:
        config = self._get_connection_config(name)
        connection = Connection(config)
        connection.connect()
        return connection

    def _get_connection_config(self, name: str) -> Dict:
        connections = self._config.get("connections", {})

        if name not in connections:
            raise ValueError(f"Database connection '{name}' not configured")

        return connections[name]

    def table(self, table_name: str, connection_name: Optional[str] = None):
        return self.connection(connection_name).table(table_name)

    def select(self, query: str, bindings=None, connection_name: Optional[str] = None):
        return self.connection(connection_name).select(query, bindings)

    def insert(self, query: str, bindings=None, connection_name: Optional[str] = None):
        return self.connection(connection_name).insert(query, bindings)

    def update(self, query: str, bindings=None, connection_name: Optional[str] = None):
        return self.connection(connection_name).update(query, bindings)

    def delete(self, query: str, bindings=None, connection_name: Optional[str] = None):
        return self.connection(connection_name).delete(query, bindings)

    def statement(self, query: str, bindings=None, connection_name: Optional[str] = None):
        return self.connection(connection_name).statement(query, bindings)

    def transaction(self, callback, connection_name: Optional[str] = None):
        return self.connection(connection_name).transaction(callback)

    def begin_transaction(self, connection_name: Optional[str] = None):
        return self.connection(connection_name).begin_transaction()

    def commit(self, connection_name: Optional[str] = None):
        return self.connection(connection_name).commit()

    def rollback(self, connection_name: Optional[str] = None):
        return self.connection(connection_name).rollback()

    def disconnect(self, name: Optional[str] = None):
        if name:
            if name in self._connections:
                self._connections[name].disconnect()
                del self._connections[name]
        else:
            for connection in self._connections.values():
                connection.disconnect()
            self._connections.clear()

    def get_default_connection(self) -> str:
        return self._default_connection

    def set_default_connection(self, name: str):
        self._default_connection = name

    def get_connections(self) -> Dict[str, Connection]:
        return self._connections
