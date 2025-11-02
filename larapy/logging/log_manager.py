from typing import Dict, Any, List, Optional
from .logger import Logger
from .log_level import LogLevel
from .handlers import (
    Handler,
    FileHandler,
    StreamHandler,
    NullHandler,
    DailyFileHandler,
    StackHandler,
)
from .formatters import LineFormatter, JsonFormatter


class LogManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channels: Dict[str, Logger] = {}

    def channel(self, name: Optional[str] = None) -> Logger:
        resolved_name = name or self.config.get("default", "stack")

        if resolved_name not in self.channels:
            self.channels[resolved_name] = self._create_channel(resolved_name)

        return self.channels[resolved_name]

    def stack(self, channels: List[str]) -> Logger:
        handlers = []
        for channel_name in channels:
            channel = self.channel(channel_name)
            handlers.extend(channel.handlers)

        logger = Logger("stack", handlers)
        return logger

    def build(self, config: Dict[str, Any]) -> Logger:
        handler = self._create_handler(config)
        return Logger("custom", [handler])

    def _create_channel(self, name: str) -> Logger:
        channel_config = self.config.get("channels", {}).get(name, {})

        if not channel_config:
            return Logger(name, [NullHandler()])

        driver = channel_config.get("driver")

        if driver == "stack":
            return self._create_stack_channel(name, channel_config)

        handler = self._create_handler(channel_config)
        return Logger(name, [handler])

    def _create_stack_channel(self, name: str, config: Dict[str, Any]) -> Logger:
        channel_names = config.get("channels", [])
        ignore_exceptions = config.get("ignore_exceptions", False)

        handlers = []
        for channel_name in channel_names:
            channel = self.channel(channel_name)
            handlers.extend(channel.handlers)

        stack_handler = StackHandler(handlers, ignore_exceptions)
        return Logger(name, [stack_handler])

    def _create_handler(self, config: Dict[str, Any]) -> Handler:
        driver = config.get("driver")
        level = self._parse_level(config.get("level", "debug"))
        formatter = self._create_formatter(config.get("formatter"))

        if driver == "file":
            return FileHandler(
                path=config.get("path", "storage/logs/larapy.log"), level=level, formatter=formatter
            )
        elif driver == "daily":
            return DailyFileHandler(
                path=config.get("path", "storage/logs/larapy.log"),
                days=config.get("days", 7),
                level=level,
                formatter=formatter,
            )
        elif driver == "stream":
            return StreamHandler(
                stream=config.get("stream", "stderr"), level=level, formatter=formatter
            )
        elif driver == "null":
            return NullHandler(level, formatter)
        else:
            return NullHandler(level, formatter)

    def _create_formatter(self, formatter_type: Optional[str]):
        if formatter_type == "json":
            return JsonFormatter()
        return LineFormatter()

    def _parse_level(self, level: str) -> LogLevel:
        return LogLevel.from_name(level)

    def get_default_driver(self) -> str:
        return self.config.get("default", "stack")
