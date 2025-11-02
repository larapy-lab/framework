from typing import Optional, Dict, Any, Callable
from larapy.http.exceptions import HttpException, NotFoundHttpException


def abort(
    status_code: int, message: Optional[str] = None, headers: Optional[Dict[str, str]] = None
) -> None:
    raise HttpException(status_code, message, headers)


def abort_if(
    condition: bool,
    status_code: int,
    message: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> None:
    if condition:
        abort(status_code, message, headers)


def abort_unless(
    condition: bool,
    status_code: int,
    message: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> None:
    if not condition:
        abort(status_code, message, headers)
