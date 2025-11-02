from typing import Dict, Optional, Any


class HttpException(Exception):

    def __init__(
        self,
        status_code: int,
        message: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        code: int = 0,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.code = code

        if message is None:
            message = self._get_default_message()

        super().__init__(message)

    def _get_default_message(self) -> str:
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            408: "Request Timeout",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        return status_messages.get(self.status_code, "HTTP Error")

    def get_status_code(self) -> int:
        return self.status_code

    def get_headers(self) -> Dict[str, str]:
        return self.headers

    def set_headers(self, headers: Dict[str, str]) -> "HttpException":
        self.headers = headers
        return self
