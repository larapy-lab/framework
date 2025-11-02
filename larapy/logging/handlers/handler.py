from abc import ABC, abstractmethod
from typing import Optional
from ..log_record import LogRecord
from ..log_level import LogLevel
from ..formatters import Formatter, LineFormatter


class Handler(ABC):
    def __init__(self, level: LogLevel = LogLevel.DEBUG, formatter: Optional[Formatter] = None):
        self.level = level
        self.formatter = formatter or LineFormatter()

    def should_handle(self, record: LogRecord) -> bool:
        return record.level >= self.level

    def handle(self, record: LogRecord):
        if self.should_handle(record):
            formatted = self.formatter.format(record)
            self.write(formatted, record)

    @abstractmethod
    def write(self, formatted_message: str, record: LogRecord):
        pass

    def close(self):
        pass
