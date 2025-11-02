from typing import TYPE_CHECKING, Dict, Optional, Any, List, Callable, Union
from larapy.http.client.response import Response
import requests

if TYPE_CHECKING:
    pass


class FakeResponse:

    def __init__(
        self, body: Union[str, Dict, List] = "", status: int = 200, headers: Optional[Dict] = None
    ):
        self.body = body
        self.status = status
        self.headers = headers or {}

        self._response = requests.Response()
        self._response.status_code = status
        self._response.headers.update(self.headers)

        if isinstance(body, dict) or isinstance(body, list):
            import json

            self._response._content = json.dumps(body).encode("utf-8")
            self._response.headers["Content-Type"] = "application/json"
        else:
            self._response._content = str(body).encode("utf-8")

    def to_response(self) -> Response:
        return Response(self._response)


class FakeSequence:

    def __init__(self, responses: List[FakeResponse]):
        self.responses = responses
        self.current_index = 0

    def next(self) -> FakeResponse:
        if self.current_index >= len(self.responses):
            return self.responses[-1]

        response = self.responses[self.current_index]
        self.current_index += 1
        return response


class RequestRecorder:

    def __init__(self):
        self.requests: List[Dict[str, Any]] = []

    def record(self, method: str, url: str, **kwargs):
        self.requests.append(
            {
                "method": method.upper(),
                "url": url,
                "headers": kwargs.get("headers", {}),
                "data": kwargs.get("data"),
                "json": kwargs.get("json"),
                "params": kwargs.get("params"),
            }
        )

    def filter(self, callback: Callable) -> List[Dict[str, Any]]:
        return [req for req in self.requests if callback(req)]

    def count(self, callback: Optional[Callable] = None) -> int:
        if callback is None:
            return len(self.requests)
        return len(self.filter(callback))


class FakeHttpClient:

    def __init__(self):
        self._responses: Dict[str, Union[FakeResponse, FakeSequence]] = {}
        self._default_response = FakeResponse()
        self._recorder = RequestRecorder()
        self._stubbed = False

    def fake(self, responses: Optional[Dict[str, Union[FakeResponse, Dict, List]]] = None):
        self._stubbed = True

        if responses is None:
            return self

        for url_pattern, response in responses.items():
            if isinstance(response, FakeResponse):
                self._responses[url_pattern] = response
            elif isinstance(response, dict) or isinstance(response, list):
                self._responses[url_pattern] = FakeResponse(body=response)
            else:
                self._responses[url_pattern] = FakeResponse(body=str(response))

        return self

    def sequence(self, url_pattern: str, responses: List[Union[FakeResponse, Dict]]):
        fake_responses = []
        for response in responses:
            if isinstance(response, FakeResponse):
                fake_responses.append(response)
            elif isinstance(response, dict):
                fake_responses.append(FakeResponse(body=response))
            else:
                fake_responses.append(FakeResponse(body=str(response)))

        self._responses[url_pattern] = FakeSequence(fake_responses)
        return self

    def _find_response(self, url: str) -> FakeResponse:
        for pattern, response in self._responses.items():
            if pattern == "*" or pattern in url:
                if isinstance(response, FakeSequence):
                    return response.next()
                return response

        return self._default_response

    def get(self, url: str, query: Optional[Dict] = None, **kwargs) -> Response:
        self._recorder.record("GET", url, params=query, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def post(self, url: str, data: Optional[Any] = None, **kwargs) -> Response:
        self._recorder.record("POST", url, data=data, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def put(self, url: str, data: Optional[Any] = None, **kwargs) -> Response:
        self._recorder.record("PUT", url, data=data, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def patch(self, url: str, data: Optional[Any] = None, **kwargs) -> Response:
        self._recorder.record("PATCH", url, data=data, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def delete(self, url: str, data: Optional[Any] = None, **kwargs) -> Response:
        self._recorder.record("DELETE", url, data=data, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def head(self, url: str, **kwargs) -> Response:
        self._recorder.record("HEAD", url, **kwargs)
        fake_response = self._find_response(url)
        return fake_response.to_response()

    def assert_sent(self, callback: Callable):
        matching = self._recorder.filter(callback)
        assert len(matching) > 0, "Expected request was not sent"

    def assert_sent_count(self, url: str, count: int):
        matching = self._recorder.filter(lambda req: url in req["url"])
        actual_count = len(matching)
        assert actual_count == count, f"Expected {count} requests to {url}, but got {actual_count}"

    def assert_not_sent(self, callback: Callable):
        matching = self._recorder.filter(callback)
        assert len(matching) == 0, "Unexpected request was sent"

    def recorded(self) -> List[Dict[str, Any]]:
        return self._recorder.requests
