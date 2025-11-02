from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from larapy.http.client.response import Response


class RequestException(Exception):

    def __init__(self, response: "Response"):
        self.response = response
        message = f"HTTP {response.status()}: {response.body()[:200]}"
        super().__init__(message)


class ConnectionException(RequestException):

    def __init__(self, message: str):
        self.response = None
        super(RequestException, self).__init__(message)


class TimeoutException(RequestException):

    def __init__(self, message: str):
        self.response = None
        super(RequestException, self).__init__(message)
