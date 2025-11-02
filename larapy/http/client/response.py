from typing import Dict, Optional, Any, Callable
import json


class Response:

    def __init__(self, response):
        self._response = response
        self._cached_json = None

    def json(self, key: Optional[str] = None, default: Any = None) -> Any:
        if self._cached_json is None:
            try:
                self._cached_json = self._response.json()
            except (ValueError, json.JSONDecodeError, AttributeError):
                self._cached_json = {}

        if key:
            parts = key.split(".")
            current = self._cached_json
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current

        return self._cached_json if self._cached_json else default

    def body(self) -> str:
        try:
            return self._response.text
        except AttributeError:
            return ""

    def status(self) -> int:
        try:
            return self._response.status_code
        except AttributeError:
            return 0

    def headers(self) -> Dict:
        try:
            return dict(self._response.headers)
        except AttributeError:
            return {}

    def header(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            return self._response.headers.get(key, default)
        except AttributeError:
            return default

    def cookies(self) -> Dict:
        try:
            return dict(self._response.cookies)
        except AttributeError:
            return {}

    def successful(self) -> bool:
        return 200 <= self.status() < 300

    def ok(self) -> bool:
        return self.successful()

    def redirect(self) -> bool:
        return 300 <= self.status() < 400

    def failed(self) -> bool:
        return self.status() >= 400

    def client_error(self) -> bool:
        return 400 <= self.status() < 500

    def server_error(self) -> bool:
        return self.status() >= 500

    def throw(self, callback: Optional[Callable] = None) -> "Response":
        if self.failed():
            if callback:
                callback(self)

            from larapy.http.client.exceptions import RequestException

            raise RequestException(self)

        return self

    def throw_if(self, condition: bool) -> "Response":
        if condition:
            from larapy.http.client.exceptions import RequestException

            raise RequestException(self)
        return self

    def throw_unless(self, condition: bool) -> "Response":
        return self.throw_if(not condition)

    def on_error(self, callback: Callable) -> "Response":
        if self.failed():
            callback(self)
        return self

    def collect(self, key: Optional[str] = None):
        from larapy.database.orm.collection import Collection

        data = self.json(key) if key else self.json()

        if isinstance(data, list):
            return Collection(data)
        elif isinstance(data, dict):
            return Collection([data])

        return Collection([])

    def __getitem__(self, key: str) -> Any:
        return self.json(key)

    def __str__(self) -> str:
        return self.body()

    def __repr__(self) -> str:
        return f"<Response [{self.status()}]>"
