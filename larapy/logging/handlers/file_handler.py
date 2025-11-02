from pathlib import Path
from typing import Optional, TextIO
from .handler import Handler
from ..log_record import LogRecord
from ..log_level import LogLevel
from ..formatters import Formatter


class FileHandler(Handler):
    def __init__(
        self, path: str, level: LogLevel = LogLevel.DEBUG, formatter: Optional[Formatter] = None
    ):
        super().__init__(level, formatter)
        self.path = Path(path)
        self.file_handle: Optional[TextIO] = None

    def write(self, formatted_message: str, record: LogRecord):
        self._ensure_directory_exists()
        self._ensure_file_open()

        self.file_handle.write(formatted_message + "\n")
        self.file_handle.flush()

    def _ensure_directory_exists(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_file_open(self):
        if self.file_handle is None or self.file_handle.closed:
            self.file_handle = open(self.path, "a", encoding="utf-8")

    def close(self):
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.close()
