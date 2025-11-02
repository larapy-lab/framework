from typing import Dict, Any, Optional, List, Callable
from .log_level import LogLevel
from .log_record import LogRecord
from .handlers import Handler


class Logger:
    def __init__(self, name: str = "default", handlers: Optional[List[Handler]] = None):
        self.name = name
        self.handlers = handlers or []
        self.shared_context: Dict[str, Any] = {}
        self.listeners: List[Callable[[LogRecord], None]] = []

    def log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        context = context or {}
        merged_context = {**self.shared_context, **context}

        record = LogRecord(
            level=level,
            message=message,
            context=merged_context,
            channel=self.name,
            exception=exception,
        )

        self._notify_listeners(record)

        for handler in self.handlers:
            handler.handle(record)

    def emergency(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.EMERGENCY, message, context, exception)

    def alert(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.ALERT, message, context, exception)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.CRITICAL, message, context, exception)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.ERROR, message, context, exception)

    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.WARNING, message, context, exception)

    def notice(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.NOTICE, message, context, exception)

    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.INFO, message, context, exception)

    def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ):
        self.log(LogLevel.DEBUG, message, context, exception)

    def share_context(self, context: Dict[str, Any]):
        self.shared_context.update(context)

    def with_context(self, context: Dict[str, Any]) -> "Logger":
        logger = Logger(self.name, self.handlers)
        logger.shared_context = {**self.shared_context, **context}
        logger.listeners = self.listeners.copy()
        return logger

    def listen(self, callback: Callable[[LogRecord], None]):
        self.listeners.append(callback)

    def _notify_listeners(self, record: LogRecord):
        for listener in self.listeners:
            try:
                listener(record)
            except Exception:
                pass
