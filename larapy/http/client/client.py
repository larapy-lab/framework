from typing import TYPE_CHECKING, Dict, Optional, Any, Callable, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

if TYPE_CHECKING:
    from larapy.http.client.response import Response


class HttpClient:

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_url = self.config.get("base_url", "")
        self.headers = self.config.get("headers", {})
        self._timeout = self.config.get("timeout", 30)
        self.verify = self.config.get("verify", True)
        self.proxies = self.config.get("proxies", None)
        self.allow_redirects = self.config.get("allow_redirects", True)

        self._middleware = []
        self._retry_config = None
        self._session = None
        self._before_sending_callbacks = []

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()

            if self._retry_config:
                retry = Retry(**self._retry_config)
                adapter = HTTPAdapter(max_retries=retry)
                self._session.mount("http://", adapter)
                self._session.mount("https://", adapter)

        return self._session

    def with_headers(self, headers: Dict[str, str]) -> "HttpClient":
        new_client = self._clone()
        new_client.headers.update(headers)
        return new_client

    def with_header(self, key: str, value: str) -> "HttpClient":
        return self.with_headers({key: value})

    def with_basic_auth(self, username: str, password: str) -> "HttpClient":
        import base64

        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return self.with_headers({"Authorization": f"Basic {credentials}"})

    def with_digest_auth(self, username: str, password: str) -> "HttpClient":
        from requests.auth import HTTPDigestAuth

        new_client = self._clone()
        new_client.config["auth"] = HTTPDigestAuth(username, password)
        return new_client

    def with_token(self, token: str, type: str = "Bearer") -> "HttpClient":
        return self.with_headers({"Authorization": f"{type} {token}"})

    def accept(self, content_type: str) -> "HttpClient":
        return self.with_headers({"Accept": content_type})

    def accept_json(self) -> "HttpClient":
        return self.accept("application/json")

    def content_type(self, content_type: str) -> "HttpClient":
        return self.with_headers({"Content-Type": content_type})

    def as_json(self) -> "HttpClient":
        return self.content_type("application/json").accept_json()

    def as_form(self) -> "HttpClient":
        return self.content_type("application/x-www-form-urlencoded")

    def as_multipart(self) -> "HttpClient":
        return self.content_type("multipart/form-data")

    def body_format(self, format: str) -> "HttpClient":
        new_client = self._clone()
        new_client.config["body_format"] = format
        return new_client

    def timeout(self, seconds: Union[int, float]) -> "HttpClient":
        new_client = self._clone()
        new_client._timeout = seconds
        return new_client

    def retry(
        self,
        times: int = 3,
        sleep: Union[int, float] = 0,
        when: Optional[Callable] = None,
        throw: bool = True,
    ) -> "HttpClient":
        new_client = self._clone()

        if times > 0:
            new_client._retry_config = {
                "total": times,
                "backoff_factor": sleep if sleep > 0 else 0.3,
                "status_forcelist": [429, 500, 502, 503, 504],
                "allowed_methods": ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "POST", "PATCH"],
                "raise_on_status": throw,
            }

        return new_client

    def without_redirecting(self) -> "HttpClient":
        new_client = self._clone()
        new_client.allow_redirects = False
        return new_client

    def without_verifying(self) -> "HttpClient":
        new_client = self._clone()
        new_client.verify = False
        return new_client

    def with_cookies(self, cookies: Dict) -> "HttpClient":
        new_client = self._clone()
        new_client.config["cookies"] = cookies
        return new_client

    def with_options(self, options: Dict) -> "HttpClient":
        new_client = self._clone()
        new_client.config.update(options)
        return new_client

    def with_middleware(self, middleware: Callable) -> "HttpClient":
        new_client = self._clone()
        new_client._middleware.append(middleware)
        return new_client

    def before_sending(self, callback: Callable) -> "HttpClient":
        new_client = self._clone()
        new_client._before_sending_callbacks.append(callback)
        return new_client

    def get(self, url: str, query: Optional[Dict] = None) -> "Response":
        return self._send("GET", url, params=query)

    def post(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._send("POST", url, data=data)

    def put(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._send("PUT", url, data=data)

    def patch(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._send("PATCH", url, data=data)

    def delete(self, url: str, data: Optional[Any] = None) -> "Response":
        return self._send("DELETE", url, data=data)

    def head(self, url: str) -> "Response":
        return self._send("HEAD", url)

    def _send(self, method: str, url: str, **kwargs) -> "Response":
        from larapy.http.client.response import Response
        from larapy.http.client.exceptions import ConnectionException, TimeoutException

        full_url = self._build_url(url)

        merged_headers = self.headers.copy()
        if "headers" in kwargs:
            merged_headers.update(kwargs.pop("headers"))

        if "data" in kwargs and kwargs["data"] is not None:
            body_format = self.config.get("body_format", "json")

            if body_format == "json" or "application/json" in merged_headers.get(
                "Content-Type", ""
            ):
                if not isinstance(kwargs["data"], str):
                    import json

                    kwargs["json"] = kwargs.pop("data")
            elif body_format == "form":
                kwargs["data"] = kwargs.get("data")

        for callback in self._before_sending_callbacks:
            callback({"method": method, "url": full_url, "headers": merged_headers})

        for middleware in self._middleware:
            result = middleware({"method": method, "url": full_url, "headers": merged_headers})
            if result and isinstance(result, dict):
                if "headers" in result:
                    merged_headers.update(result["headers"])

        session = self._get_session()

        try:
            response = session.request(
                method=method,
                url=full_url,
                headers=merged_headers,
                timeout=self._timeout,
                verify=self.verify,
                proxies=self.proxies,
                allow_redirects=self.allow_redirects,
                auth=self.config.get("auth"),
                cookies=self.config.get("cookies"),
                **kwargs,
            )

            return Response(response)

        except requests.exceptions.Timeout as e:
            raise TimeoutException(f"Request timed out: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(f"Connection error: {str(e)}")
        except Exception as e:
            raise ConnectionException(f"Request failed: {str(e)}")

    def _build_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url

        base = self.base_url.rstrip("/")
        path = url.lstrip("/")

        if base:
            return f"{base}/{path}"

        return url

    def _clone(self) -> "HttpClient":
        new_client = HttpClient(self.config.copy())
        new_client.base_url = self.base_url
        new_client.headers = self.headers.copy()
        new_client._timeout = self._timeout
        new_client.verify = self.verify
        new_client.proxies = self.proxies
        new_client.allow_redirects = self.allow_redirects
        new_client._middleware = self._middleware.copy()
        new_client._retry_config = self._retry_config
        new_client._before_sending_callbacks = self._before_sending_callbacks.copy()
        return new_client

    def __del__(self):
        if self._session:
            self._session.close()
