from .handler import Handler
from ..log_record import LogRecord


class NullHandler(Handler):
    def write(self, formatted_message: str, record: LogRecord):
        pass
