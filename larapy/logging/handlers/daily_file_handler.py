from pathlib import Path
from datetime import datetime as dt, timedelta
from typing import Optional
from .handler import Handler
from ..log_record import LogRecord
from ..log_level import LogLevel
from ..formatters import Formatter


class DailyFileHandler(Handler):
    def __init__(
        self,
        path: str,
        days: int = 7,
        level: LogLevel = LogLevel.DEBUG,
        formatter: Optional[Formatter] = None,
    ):
        super().__init__(level, formatter)
        self.base_path = Path(path)
        self.days = days
        self.current_date = None
        self.file_handle = None

    def write(self, formatted_message: str, record: LogRecord):
        self._ensure_directory_exists()
        self._rotate_if_needed(record.datetime)

        if self.file_handle:
            self.file_handle.write(formatted_message + "\n")
            self.file_handle.flush()

    def _rotate_if_needed(self, log_datetime: dt):
        log_date = log_datetime.date()

        if self.current_date != log_date:
            self._close_current_file()
            self._open_new_file(log_date)
            self._cleanup_old_files(log_date)

    def _close_current_file(self):
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.close()

    def _open_new_file(self, date):
        self.current_date = date
        file_path = self._get_daily_path(date)
        self.file_handle = open(file_path, "a", encoding="utf-8")

    def _get_daily_path(self, date) -> Path:
        name_without_ext = self.base_path.stem
        extension = self.base_path.suffix
        date_str = date.strftime("%Y-%m-%d")

        daily_name = f"{name_without_ext}-{date_str}{extension}"
        return self.base_path.parent / daily_name

    def _cleanup_old_files(self, current_date):
        if self.days <= 0:
            return

        cutoff_date = current_date - timedelta(days=self.days)

        for file in self.base_path.parent.glob(f"{self.base_path.stem}-*{self.base_path.suffix}"):
            try:
                date_str = file.stem.split("-", 1)[1]
                file_date = dt.strptime(date_str, "%Y-%m-%d").date()

                if file_date < cutoff_date:
                    file.unlink()
            except (ValueError, IndexError):
                continue

    def _ensure_directory_exists(self):
        self.base_path.parent.mkdir(parents=True, exist_ok=True)

    def close(self):
        self._close_current_file()
