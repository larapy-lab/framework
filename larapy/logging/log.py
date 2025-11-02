from typing import Dict, Any, Optional, List, Callable
from .log_manager import LogManager
from .logger import Logger
from .log_record import LogRecord


class Log:
    _manager: Optional[LogManager] = None

    @classmethod
    def set_manager(cls, manager: LogManager):
        cls._manager = manager

    @classmethod
    def _get_manager(cls) -> LogManager:
        if cls._manager is None:
            raise RuntimeError("LogManager not initialized. Call Log.set_manager() first.")
        return cls._manager

    @classmethod
    def channel(cls, name: Optional[str] = None) -> Logger:
        return cls._get_manager().channel(name)

    @classmethod
    def stack(cls, channels: List[str]) -> Logger:
        return cls._get_manager().stack(channels)

    @classmethod
    def build(cls, config: Dict[str, Any]) -> Logger:
        return cls._get_manager().build(config)

    @classmethod
    def emergency(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().emergency(message, context, exception)

    @classmethod
    def alert(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().alert(message, context, exception)

    @classmethod
    def critical(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().critical(message, context, exception)

    @classmethod
    def error(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().error(message, context, exception)

    @classmethod
    def warning(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().warning(message, context, exception)

    @classmethod
    def notice(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().notice(message, context, exception)

    @classmethod
    def info(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().info(message, context, exception)

    @classmethod
    def debug(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        cls.channel().debug(message, context, exception)

    @classmethod
    def share_context(cls, context: Dict[str, Any]):
        cls.channel().share_context(context)

    @classmethod
    def listen(cls, callback: Callable[[LogRecord], None]):
        cls.channel().listen(callback)
