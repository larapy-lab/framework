from enum import IntEnum
from typing import Union


class LogLevel(IntEnum):
    DEBUG = 100
    INFO = 200
    NOTICE = 250
    WARNING = 300
    ERROR = 400
    CRITICAL = 500
    ALERT = 550
    EMERGENCY = 600

    @classmethod
    def from_name(cls, name: str) -> "LogLevel":
        name = name.upper()
        return cls[name]

    @classmethod
    def from_value(cls, value: Union[int, str, "LogLevel"]) -> "LogLevel":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_name(value)
        return cls(value)

    def to_name(self) -> str:
        return self.name.lower()


LEVEL_DEBUG = LogLevel.DEBUG
LEVEL_INFO = LogLevel.INFO
LEVEL_NOTICE = LogLevel.NOTICE
LEVEL_WARNING = LogLevel.WARNING
LEVEL_ERROR = LogLevel.ERROR
LEVEL_CRITICAL = LogLevel.CRITICAL
LEVEL_ALERT = LogLevel.ALERT
LEVEL_EMERGENCY = LogLevel.EMERGENCY
