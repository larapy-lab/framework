from typing import Dict, Optional, List
from .http_exception import HttpException


class MethodNotAllowedHttpException(HttpException):

    def __init__(
        self,
        allowed_methods: Optional[List[str]] = None,
        message: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        code: int = 0,
    ):
        self.allowed_methods = allowed_methods or []

        if headers is None:
            headers = {}

        if self.allowed_methods:
            headers["Allow"] = ", ".join(self.allowed_methods)

        super().__init__(status_code=405, message=message, headers=headers, code=code)
