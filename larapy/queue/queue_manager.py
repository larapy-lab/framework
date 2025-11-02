from typing import Optional, Dict, Any

from larapy.queue.sync_queue import SyncQueue
from larapy.queue.database_queue import DatabaseQueue


class QueueManager:

    def __init__(self, config: Dict[str, Any], container=None):
        self.config = config
        self.container = container
        self.connections = {}

    def connection(self, name: Optional[str] = None):
        name = name or self.get_default_connection()

        if name not in self.connections:
            self.connections[name] = self.resolve(name)

        return self.connections[name]

    def resolve(self, name: str):
        if name not in self.config["connections"]:
            raise ValueError(f"Queue connection '{name}' is not configured")

        config = self.config["connections"][name]
        driver = config["driver"]

        if driver == "sync":
            return self.create_sync_driver()
        elif driver == "database":
            return self.create_database_driver(config)
        elif driver == "redis":
            return self.create_redis_driver(config)
        else:
            raise ValueError(f"Unsupported queue driver: {driver}")

    def create_sync_driver(self) -> SyncQueue:
        queue = SyncQueue()
        queue.set_connection_name("sync")
        return queue

    def create_database_driver(self, config: Dict[str, Any]) -> DatabaseQueue:
        database = self.container.make("db") if self.container else None

        queue = DatabaseQueue(
            database,
            config.get("table", "jobs"),
            config.get("queue", "default"),
            config.get("retry_after", 90),
        )

        queue.set_connection_name("database")
        return queue

    def create_redis_driver(self, config: Dict[str, Any]):
        from larapy.queue.redis_queue import RedisQueue

        redis = self.container.make("redis") if self.container else None

        queue = RedisQueue(
            redis,
            config.get("queue", "default"),
            config.get("retry_after", 90),
            config.get("block_for"),
        )

        queue.set_connection_name(config.get("connection", "default"))
        return queue

    def get_default_connection(self) -> str:
        return self.config.get("default", "sync")

    def set_default_connection(self, name: str) -> None:
        self.config["default"] = name

    def get_name(self, connection: Optional[str] = None) -> str:
        return connection or self.get_default_connection()

    def get_connections(self) -> Dict[str, Any]:
        return self.connections

    def add_connector(self, driver: str, resolver) -> None:
        pass
