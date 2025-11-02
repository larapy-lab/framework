from typing import Dict, Optional
from .http_exception import HttpException


class ServiceUnavailableHttpException(HttpException):

    def __init__(
        self,
        retry_after: Optional[int] = None,
        message: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        code: int = 0,
    ):
        self.retry_after = retry_after

        if headers is None:
            headers = {}

        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)

        super().__init__(status_code=503, message=message, headers=headers, code=code)
