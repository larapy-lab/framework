from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse
from larapy.cache.rate_limiter import RateLimiter, Limit
from typing import Callable, Optional, Union
import hashlib


class ThrottleRequests:

    def __init__(self, limiter: RateLimiter):
        self.limiter = limiter

    def handle(
        self,
        request: Request,
        next_handler: Callable,
        max_attempts: Union[int, str] = 60,
        decay_minutes: float = 1,
    ):
        if isinstance(max_attempts, str):
            return self._handle_named_limiter(request, next_handler, max_attempts)

        key = self.resolve_request_signature(request)
        max_attempts = int(max_attempts)
        decay_seconds = int(decay_minutes * 60)

        if self.limiter.too_many_attempts(key, max_attempts):
            return self._build_too_many_attempts_response(request, key, max_attempts)

        self.limiter.hit(key, decay_seconds)

        response = next_handler(request)

        return self._add_headers(
            response,
            max_attempts,
            self._calculate_remaining_attempts(key, max_attempts),
            self.limiter.available_in(key),
        )

    def _handle_named_limiter(self, request: Request, next_handler: Callable, limiter_name: str):
        limiter_callback = self.limiter.limiter(limiter_name)

        if limiter_callback is None:
            return next_handler(request)

        limit = limiter_callback(request)

        if not isinstance(limit, Limit):
            return next_handler(request)

        key = self._resolve_named_limiter_key(request, limit)
        max_attempts = limit.max_attempts
        decay_seconds = int(limit.decay_minutes * 60)

        if self.limiter.too_many_attempts(key, max_attempts):
            if limit.response_callback:
                return limit.response_callback(request)

            return self._build_too_many_attempts_response(request, key, max_attempts)

        self.limiter.hit(key, decay_seconds)

        response = next_handler(request)

        return self._add_headers(
            response,
            max_attempts,
            self._calculate_remaining_attempts(key, max_attempts),
            self.limiter.available_in(key),
        )

    def _resolve_named_limiter_key(self, request: Request, limit: Limit) -> str:
        if limit.key:
            return self._signature_hash(f"{request.method()}.{request.path()}.{limit.key}")

        return self.resolve_request_signature(request)

    def resolve_request_signature(self, request: Request) -> str:
        user = None

        if hasattr(request, "user"):
            user_attr = getattr(request, "user")
            if callable(user_attr):
                user = user_attr()
            else:
                user = user_attr

        if user:
            user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
            if user_id:
                return self._signature_hash(f"{request.method()}.{request.path()}.{user_id}")

        return self._signature_hash(f"{request.method()}.{request.path()}.{request.ip()}")

    def _signature_hash(self, signature: str) -> str:
        return hashlib.sha1(signature.encode()).hexdigest()

    def _build_too_many_attempts_response(self, request: Request, key: str, max_attempts: int):
        retry_after = self.limiter.available_in(key)

        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(max_attempts),
            "X-RateLimit-Remaining": "0",
        }

        if self._expects_json(request):
            return JsonResponse({"message": "Too Many Attempts."}, 429, headers)

        return Response("Too Many Attempts.", 429, headers)

    def _expects_json(self, request: Request) -> bool:
        accept = request.header("Accept", "")

        if not accept or accept == "*/*":
            return False

        if "application/json" in accept:
            return True

        return False

    def _calculate_remaining_attempts(self, key: str, max_attempts: int) -> int:
        return self.limiter.remaining_attempts(key, max_attempts)

    def _add_headers(
        self, response: Response, max_attempts: int, remaining_attempts: int, retry_after: int
    ):
        response.header("X-RateLimit-Limit", str(max_attempts))
        response.header("X-RateLimit-Remaining", str(remaining_attempts))

        if remaining_attempts == 0:
            response.header("Retry-After", str(retry_after))

        return response
