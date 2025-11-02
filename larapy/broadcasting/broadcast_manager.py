from typing import Callable, Dict, Optional, List


class BroadcastManager:
    def __init__(self, container):
        self.container = container
        self.drivers: Dict[str, object] = {}
        self.custom_creators: Dict[str, Callable] = {}

    def driver(self, name: Optional[str] = None):
        name = name or self.get_default_driver()

        if name in self.drivers:
            return self.drivers[name]

        driver = self.create_driver(name)
        self.drivers[name] = driver
        return driver

    def create_driver(self, name: str):
        if name in self.custom_creators:
            return self.custom_creators[name](self.container)

        method_name = f"create_{name}_driver"
        if hasattr(self, method_name):
            return getattr(self, method_name)()

        raise ValueError(f"Broadcast driver '{name}' is not supported.")

    def create_pusher_driver(self):
        from larapy.broadcasting.broadcasters.pusher_broadcaster import PusherBroadcaster

        config = self.container.make("config").get("broadcasting.connections.pusher", {})

        try:
            import pusher

            pusher_client = pusher.Pusher(
                app_id=config.get("app_id"),
                key=config.get("key"),
                secret=config.get("secret"),
                cluster=config.get("cluster", "us2"),
                ssl=config.get("ssl", True),
            )
        except ImportError:
            raise ImportError(
                "pusher library is required for Pusher broadcasting. Install with: pip install pusher"
            )

        return PusherBroadcaster(pusher_client, config)

    def create_redis_driver(self):
        from larapy.broadcasting.broadcasters.redis_broadcaster import RedisBroadcaster

        connection_name = self.container.make("config").get(
            "broadcasting.connections.redis.connection", "default"
        )
        redis_client = self.container.make("redis").connection(connection_name)

        return RedisBroadcaster(redis_client, connection_name)

    def create_log_driver(self):
        from larapy.broadcasting.broadcasters.log_broadcaster import LogBroadcaster

        logger = self.container.make("log") if self.container.bound("log") else None
        return LogBroadcaster(logger)

    def create_null_driver(self):
        from larapy.broadcasting.broadcasters.null_broadcaster import NullBroadcaster

        return NullBroadcaster()

    def extend(self, name: str, creator: Callable):
        self.custom_creators[name] = creator
        if name in self.drivers:
            del self.drivers[name]

    def get_default_driver(self) -> str:
        if self.container.bound("config"):
            return self.container.make("config").get("broadcasting.default", "null")
        return "null"

    def broadcast(self, channels: List[str], event: str, payload: dict):
        return self.driver().broadcast(channels, event, payload)

    def __call__(self, channels: List[str], event: str, payload: dict):
        return self.broadcast(channels, event, payload)
