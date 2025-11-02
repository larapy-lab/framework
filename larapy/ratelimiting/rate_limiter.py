import time
from typing import Optional, Callable, Any


class RateLimiter:

    def __init__(self, cache_store):
        self._cache = cache_store

    def attempt(
        self, key: str, max_attempts: int, callback: Callable, decay_minutes: int = 1
    ) -> bool:
        if self.too_many_attempts(key, max_attempts):
            return False

        result = callback()

        self.hit(key, decay_minutes * 60)

        return result

    def too_many_attempts(self, key: str, max_attempts: int) -> bool:
        if self.attempts(key) >= max_attempts:
            if self._cache.has(self._timer_key(key)):
                return True

            self.reset_attempts(key)

        return False

    def hit(self, key: str, decay_seconds: int = 60) -> int:
        timer_key = self._timer_key(key)

        self._cache.add(timer_key, self._available_at(decay_seconds), decay_seconds)

        added = self._cache.add(key, 0, decay_seconds)

        hits = self._cache.increment(key) if not added else 1

        return hits

    def attempts(self, key: str) -> int:
        return self._cache.get(key, 0)

    def reset_attempts(self, key: str) -> None:
        self._cache.forget(key)

    def remaining(self, key: str, max_attempts: int) -> int:
        return max(0, max_attempts - self.attempts(key))

    def available_in(self, key: str) -> int:
        timer_key = self._timer_key(key)
        available_at = self._cache.get(timer_key)

        if available_at is None:
            return 0

        return max(0, available_at - self._current_time())

    def clear(self, key: str) -> None:
        self.reset_attempts(key)
        self._cache.forget(self._timer_key(key))

    def _timer_key(self, key: str) -> str:
        return f"{key}:timer"

    def _available_at(self, delay: int = 0) -> int:
        return self._current_time() + delay

    def _current_time(self) -> int:
        return int(time.time())
