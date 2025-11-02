from typing import List
from .handler import Handler
from ..log_record import LogRecord


class StackHandler(Handler):
    def __init__(self, handlers: List[Handler], ignore_exceptions: bool = False):
        super().__init__()
        self.handlers = handlers
        self.ignore_exceptions = ignore_exceptions

    def write(self, formatted_message: str, record: LogRecord):
        for handler in self.handlers:
            try:
                handler.handle(record)
            except Exception as e:
                if not self.ignore_exceptions:
                    raise

    def close(self):
        for handler in self.handlers:
            try:
                handler.close()
            except Exception:
                pass
