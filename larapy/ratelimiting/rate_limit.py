from typing import Callable, Optional
from larapy.cache.rate_limiter import RateLimiter, Limit


class RateLimit:

    _instance: Optional[RateLimiter] = None

    @classmethod
    def set_limiter(cls, limiter: RateLimiter) -> None:
        cls._instance = limiter

    @classmethod
    def get_limiter(cls) -> RateLimiter:
        if cls._instance is None:
            raise RuntimeError("RateLimiter not initialized. Call RateLimit.set_limiter() first.")
        return cls._instance

    @classmethod
    def for_(cls, name: str, callback: Callable) -> RateLimiter:
        return cls.get_limiter().for_(name, callback)

    @classmethod
    def attempt(
        cls, key: str, max_attempts: int, callback: Callable, decay_minutes: int = 1
    ) -> bool:
        limiter = cls.get_limiter()
        decay_seconds = decay_minutes * 60

        if limiter.too_many_attempts(key, max_attempts):
            return False

        result = callback()
        limiter.hit(key, decay_seconds)

        return result

    @classmethod
    def too_many_attempts(cls, key: str, max_attempts: int) -> bool:
        return cls.get_limiter().too_many_attempts(key, max_attempts)

    @classmethod
    def hit(cls, key: str, decay_seconds: int = 60) -> int:
        return cls.get_limiter().hit(key, decay_seconds)

    @classmethod
    def attempts(cls, key: str) -> int:
        return cls.get_limiter().attempts(key)

    @classmethod
    def reset_attempts(cls, key: str) -> None:
        cls.get_limiter().reset_attempts(key)

    @classmethod
    def remaining(cls, key: str, max_attempts: int) -> int:
        return cls.get_limiter().remaining(key, max_attempts)

    @classmethod
    def available_in(cls, key: str) -> int:
        return cls.get_limiter().available_in(key)

    @classmethod
    def clear(cls, key: str) -> None:
        cls.get_limiter().clear(key)
