from typing import Callable, Optional, Dict, Any
import time
import hashlib


class RateLimiter:

    def __init__(self, cache):
        self.cache = cache
        self.limiters: Dict[str, Callable] = {}

    def for_(self, name: str, callback: Callable) -> "RateLimiter":
        self.limiters[name] = callback
        return self

    def for_rate(self, name: str, callback: Callable) -> "RateLimiter":
        return self.for_(name, callback)

    def limiter(self, name: str) -> Optional[Callable]:
        return self.limiters.get(name)

    def attempt(self, key: str, max_attempts: int, decay_seconds: int = 60) -> bool:
        if self.too_many_attempts(key, max_attempts):
            return False

        self.hit(key, decay_seconds)
        return True

    def too_many_attempts(self, key: str, max_attempts: int) -> bool:
        if self.attempts(key) >= max_attempts:
            if self.cache.has(self._timer_key(key)):
                return True

            self.reset_attempts(key)

        return False

    def hit(self, key: str, decay_seconds: int = 60) -> int:
        timer_key = self._timer_key(key)

        self.cache.add(timer_key, self._available_at(decay_seconds), decay_seconds)

        added = self.cache.add(key, 0, decay_seconds)

        hits = int(self.cache.increment(key))

        if not added and hits == 1:
            self.cache.put(key, 1, decay_seconds)

        return hits

    def attempts(self, key: str) -> int:
        return int(self.cache.get(key, 0))

    def reset_attempts(self, key: str) -> None:
        self.cache.forget(key)
        self.cache.forget(self._timer_key(key))

    def remaining_attempts(self, key: str, max_attempts: int) -> int:
        attempts = self.attempts(key)
        return max(0, max_attempts - attempts)

    def remaining(self, key: str, max_attempts: int) -> int:
        return self.remaining_attempts(key, max_attempts)

    def available_in(self, key: str) -> int:
        return max(0, self.cache.get(self._timer_key(key), 0) - int(time.time()))

    def clear(self, key: str) -> None:
        self.reset_attempts(key)

    def _timer_key(self, key: str) -> str:
        return key + ":timer"

    def _available_at(self, seconds: int) -> int:
        return int(time.time() + seconds)


class Limit:

    def __init__(self, max_attempts: int, decay_minutes: float = 1):
        self.max_attempts = max_attempts
        self.decay_minutes = decay_minutes
        self.key: Optional[str] = None
        self.response_callback: Optional[Callable] = None

    @staticmethod
    def per_minute(max_attempts: int) -> "Limit":
        return Limit(max_attempts, 1)

    @staticmethod
    def per_hour(max_attempts: int) -> "Limit":
        return Limit(max_attempts, 60)

    @staticmethod
    def per_day(max_attempts: int) -> "Limit":
        return Limit(max_attempts, 1440)

    @staticmethod
    def per_minutes(max_attempts: int, minutes: int) -> "Limit":
        return Limit(max_attempts, minutes)

    @staticmethod
    def per_second(max_attempts: int) -> "Limit":
        return Limit(max_attempts, 0.0166667)

    @staticmethod
    def none() -> "Limit":
        return Limit(999999999)

    def by(self, key: Any) -> "Limit":
        self.key = str(key)
        return self

    def response(self, callback: Callable) -> "Limit":
        self.response_callback = callback
        return self
