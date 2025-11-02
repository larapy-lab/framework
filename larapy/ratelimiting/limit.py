from typing import Optional, Callable, Any


class Limit:

    def __init__(self, max_attempts: int, decay_minutes: int = 1):
        self.max_attempts = max_attempts
        self.decay_minutes = decay_minutes
        self._key: Optional[str] = None
        self._response_callback: Optional[Callable] = None

    @classmethod
    def per_minute(cls, max_attempts: int) -> "Limit":
        return cls(max_attempts, decay_minutes=1)

    @classmethod
    def per_hour(cls, max_attempts: int) -> "Limit":
        return cls(max_attempts, decay_minutes=60)

    @classmethod
    def per_day(cls, max_attempts: int) -> "Limit":
        return cls(max_attempts, decay_minutes=1440)

    @classmethod
    def per_minutes(cls, max_attempts: int, minutes: int) -> "Limit":
        return cls(max_attempts, decay_minutes=minutes)

    @classmethod
    def none(cls) -> "Limit":
        return cls(max_attempts=999999, decay_minutes=1)

    def by(self, key: str) -> "Limit":
        self._key = key
        return self

    def response(self, callback: Callable) -> "Limit":
        self._response_callback = callback
        return self

    def get_key(self) -> Optional[str]:
        return self._key

    def get_response_callback(self) -> Optional[Callable]:
        return self._response_callback
