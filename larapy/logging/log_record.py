from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Dict, Any, Optional
from .log_level import LogLevel


@dataclass
class LogRecord:
    level: LogLevel
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    channel: str = "default"
    datetime: dt = field(default_factory=dt.now)
    exception: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        record = {
            "level": self.level.to_name(),
            "level_value": self.level.value,
            "message": self.message,
            "context": self.context,
            "channel": self.channel,
            "datetime": self.datetime.isoformat(),
        }

        if self.exception:
            import traceback

            record["exception"] = {
                "class": type(self.exception).__name__,
                "message": str(self.exception),
                "trace": traceback.format_exception(
                    type(self.exception), self.exception, self.exception.__traceback__
                ),
            }

        return record
