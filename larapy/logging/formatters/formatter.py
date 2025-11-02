from abc import ABC, abstractmethod
from ..log_record import LogRecord


class Formatter(ABC):
    @abstractmethod
    def format(self, record: LogRecord) -> str:
        pass
