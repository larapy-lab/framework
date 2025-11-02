from typing import Dict, Optional
from .http_exception import HttpException


class NotFoundHttpException(HttpException):

    def __init__(
        self, message: Optional[str] = None, headers: Optional[Dict[str, str]] = None, code: int = 0
    ):
        super().__init__(status_code=404, message=message, headers=headers, code=code)
