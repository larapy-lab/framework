from typing import TYPE_CHECKING, Dict, Optional, Any, Callable
from larapy.http.client.pending_request import PendingRequest

if TYPE_CHECKING:
    from larapy.http.client.response import Response


class Http:

    @classmethod
    def _create_client(cls) -> PendingRequest:
        return PendingRequest()

    @classmethod
    def base_url(cls, url: str) -> PendingRequest:
        return cls._create_client().base_url(url)

    @classmethod
    def with_headers(cls, headers: Dict[str, str]) -> PendingRequest:
        return cls._create_client().with_headers(headers)

    @classmethod
    def with_header(cls, key: str, value: str) -> PendingRequest:
        return cls._create_client().with_header(key, value)

    @classmethod
    def with_basic_auth(cls, username: str, password: str) -> PendingRequest:
        return cls._create_client().with_basic_auth(username, password)

    @classmethod
    def with_digest_auth(cls, username: str, password: str) -> PendingRequest:
        return cls._create_client().with_digest_auth(username, password)

    @classmethod
    def with_token(cls, token: str, type: str = "Bearer") -> PendingRequest:
        return cls._create_client().with_token(token, type)

    @classmethod
    def accept(cls, content_type: str) -> PendingRequest:
        return cls._create_client().accept(content_type)

    @classmethod
    def accept_json(cls) -> PendingRequest:
        return cls._create_client().accept_json()

    @classmethod
    def content_type(cls, content_type: str) -> PendingRequest:
        return cls._create_client().content_type(content_type)

    @classmethod
    def as_json(cls) -> PendingRequest:
        return cls._create_client().as_json()

    @classmethod
    def as_form(cls) -> PendingRequest:
        return cls._create_client().as_form()

    @classmethod
    def as_multipart(cls) -> PendingRequest:
        return cls._create_client().as_multipart()

    @classmethod
    def timeout(cls, seconds: int) -> PendingRequest:
        return cls._create_client().timeout(seconds)

    @classmethod
    def retry(
        cls, times: int = 3, sleep: int = 0, when: Optional[Callable] = None, throw: bool = True
    ) -> PendingRequest:
        return cls._create_client().retry(times, sleep, when, throw)

    @classmethod
    def without_redirecting(cls) -> PendingRequest:
        return cls._create_client().without_redirecting()

    @classmethod
    def without_verifying(cls) -> PendingRequest:
        return cls._create_client().without_verifying()

    @classmethod
    def with_cookies(cls, cookies: Dict[str, str]) -> PendingRequest:
        return cls._create_client().with_cookies(cookies)

    @classmethod
    def with_middleware(cls, middleware: Callable) -> PendingRequest:
        return cls._create_client().with_middleware(middleware)

    @classmethod
    def before_sending(cls, callback: Callable) -> PendingRequest:
        return cls._create_client().before_sending(callback)

    @classmethod
    def get(cls, url: str, query: Optional[Dict] = None) -> "Response":
        return cls._create_client().get(url, query)

    @classmethod
    def post(cls, url: str, data: Optional[Any] = None) -> "Response":
        return cls._create_client().post(url, data)

    @classmethod
    def put(cls, url: str, data: Optional[Any] = None) -> "Response":
        return cls._create_client().put(url, data)

    @classmethod
    def patch(cls, url: str, data: Optional[Any] = None) -> "Response":
        return cls._create_client().patch(url, data)

    @classmethod
    def delete(cls, url: str, data: Optional[Any] = None) -> "Response":
        return cls._create_client().delete(url, data)

    @classmethod
    def head(cls, url: str) -> "Response":
        return cls._create_client().head(url)
