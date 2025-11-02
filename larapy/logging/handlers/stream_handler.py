import sys
from typing import Optional, Union, TextIO
from .handler import Handler
from ..log_record import LogRecord
from ..log_level import LogLevel
from ..formatters import Formatter


class StreamHandler(Handler):
    def __init__(
        self,
        stream: Union[str, TextIO] = "stderr",
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        super().__init__(level, formatter)

        if stream == "stderr":
            self.stream = sys.stderr
        elif stream == "stdout":
            self.stream = sys.stdout
        else:
            self.stream = stream

    def write(self, formatted_message: str, record: LogRecord):
        self.stream.write(formatted_message + "\n")
        self.stream.flush()
