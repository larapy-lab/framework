from typing import TYPE_CHECKING, Dict, Optional, Any, Callable
from larapy.http.client.client import HttpClient

if TYPE_CHECKING:
    from larapy.http.client.response import Response


class PendingRequest:

    def __init__(self, client: Optional[HttpClient] = None):
        self._client = client or HttpClient()

    def base_url(self, url: str) -> "PendingRequest":
        new_client = self._client._clone()
        new_client.base_url = url
        return PendingRequest(new_client)

    def with_headers(self, headers: Dict[str, str]) -> "PendingRequest":
        return PendingRequest(self._client.with_headers(headers))

    def with_header(self, key: str, value: str) -> "PendingRequest":
        return PendingRequest(self._client.with_header(key, value))

    def with_basic_auth(self, username: str, password: str) -> "PendingRequest":
        return PendingRequest(self._client.with_basic_auth(username, password))

    def with_digest_auth(self, username: str, password: str) -> "PendingRequest":
        return PendingRequest(self._client.with_digest_auth(username, password))

    def with_token(self, token: str, type: str = "Bearer") -> "PendingRequest":
        return PendingRequest(self._client.with_token(token, type))

    def accept(self, content_type: str) -> "PendingRequest":
        return PendingRequest(self._client.accept(content_type))

    def accept_json(self) -> "PendingRequest":
        return PendingRequest(self._client.accept_json())

    def content_type(self, content_type: str) -> "PendingRequest":
        return PendingRequest(self._client.content_type(content_type))

    def as_json(self) -> "PendingRequest":
        return PendingRequest(self._client.as_json())

    def as_form(self) -> "PendingRequest":
        return PendingRequest(self._client.as_form())

    def as_multipart(self) -> "PendingRequest":
        return PendingRequest(self._client.as_multipart())

    def body_format(self, format: str) -> "PendingRequest":
        return PendingRequest(self._client.body_format(format))

    def timeout(self, seconds: int) -> "PendingRequest":
        return PendingRequest(self._client.timeout(seconds))

    def retry(
        self, times: int = 3, sleep: int = 0, when: Optional[Callable] = None, throw: bool = True
    ) -> "PendingRequest":
        return PendingRequest(self._client.retry(times, sleep, when, throw))

    def without_redirecting(self) -> "PendingRequest":
        return PendingRequest(self._client.without_redirecting())

    def without_verifying(self) -> "PendingRequest":
        return PendingRequest(self._client.without_verifying())

    def with_cookies(self, cookies: Dict[str, str]) -> "PendingRequest":
        return PendingRequest(self._client.with_cookies(cookies))

    def with_options(self, options: Dict[str, Any]) -> "PendingRequest":
        return PendingRequest(self._client.with_options(options))

    def with_middleware(self, middleware: Callable) -> "PendingRequest":
        return PendingRequest(self._client.with_middleware(middleware))

    def before_sending(self, callback: Callable) -> "PendingRequest":
        return PendingRequest(self._client.before_sending(callback))

    def get(self, url: str, query: Optional[Dict] = None) -> "Response":
        return self._client.get(url, query)

    def post(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._client.post(url, data)

    def put(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._client.put(url, data)

    def patch(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._client.patch(url, data)

    def delete(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._client.delete(url, data)

    def head(self, url: str) -> "Response":
        return self._client.head(url)
