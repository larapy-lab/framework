from typing import Dict, Any, Optional, List, Callable, Type, Union
import sys
from larapy.exceptions.error_renderer import ErrorRenderer
from larapy.exceptions.exception_context import ExceptionContext
from larapy.http.exceptions import HttpException


class ExceptionHandler:

    dont_report: List[Union[Type[Exception], str]] = []

    dont_flash: List[str] = [
        "password",
        "password_confirmation",
        "token",
        "secret",
        "api_key",
    ]

    def __init__(self, app: Optional[Any] = None, debug: bool = False):
        self.app = app
        self.debug = debug
        self.renderer = ErrorRenderer(debug=debug)
        self.context_collector = ExceptionContext(dont_flash=self.dont_flash)
        self.reportable_callbacks: List[Callable[[Exception], bool]] = []
        self.report_callbacks: Dict[Type[Exception], List[Callable]] = {}
        self.renderable_callbacks: Dict[Type[Exception], Callable] = {}
        self.logger: Optional[Any] = None

        self.register()

    def register(self) -> None:
        pass

    def report(self, exception: Exception) -> None:
        if not self.should_report(exception):
            return

        exception_type = type(exception)

        if exception_type in self.report_callbacks:
            for callback in self.report_callbacks[exception_type]:
                try:
                    callback(exception)
                except Exception:
                    pass

        if self.logger:
            self._log_exception(exception)
        else:
            self._default_report(exception)

    def render(self, request: Optional[Any], exception: Exception) -> Dict[str, Any]:
        status_code = self._get_status_code(exception)

        exception_type = type(exception)
        if exception_type in self.renderable_callbacks:
            try:
                return self.renderable_callbacks[exception_type](request, exception)
            except Exception:
                pass

        context = self.context_collector.collect(
            exception, request=request, user=self._get_user(request) if request else None
        )

        if self._wants_json(request):
            content = self.renderer.render_json(exception, status_code, context)
            content_type = "application/json"
        else:
            content = self.renderer.render_html(exception, status_code, context)
            content_type = "text/html"

        return {
            "content": content,
            "status_code": status_code,
            "content_type": content_type,
            "headers": self._get_exception_headers(exception),
        }

    def should_report(self, exception: Exception) -> bool:
        for dont_report_type in self.dont_report:
            if isinstance(dont_report_type, str):
                if type(exception).__name__ == dont_report_type:
                    return False
                if f"{type(exception).__module__}.{type(exception).__name__}" == dont_report_type:
                    return False
            elif isinstance(exception, dont_report_type):
                return False

        for callback in self.reportable_callbacks:
            try:
                if callback(exception):
                    return True
            except Exception:
                pass

        return True

    def reportable(self, callback: Callable[[Exception], bool]) -> "ReportableRegistration":
        self.reportable_callbacks.append(callback)
        return ReportableRegistration(self, callback)

    def renderable(
        self, exception_type: Type[Exception], callback: Callable[[Any, Exception], Dict[str, Any]]
    ) -> None:
        self.renderable_callbacks[exception_type] = callback

    def set_logger(self, logger: Any) -> None:
        self.logger = logger

    def context(self) -> Dict[str, Any]:
        return {}

    def add_context_provider(self, provider: Callable[[], Dict[str, Any]]) -> None:
        self.context_collector.add_provider(provider)

    def _log_exception(self, exception: Exception) -> None:
        if not self.logger:
            return

        context = {"exception": type(exception).__name__}

        if isinstance(exception, HttpException):
            if exception.status_code < 500:
                self.logger.warning(str(exception), context)
            else:
                self.logger.error(str(exception), context, exception=exception)
        else:
            self.logger.error(str(exception), context, exception=exception)

    def _default_report(self, exception: Exception) -> None:
        import traceback

        print(f"\nException: {type(exception).__name__}", file=sys.stderr)
        print(f"Message: {str(exception)}", file=sys.stderr)
        print("\nTraceback:", file=sys.stderr)
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )

    def _get_status_code(self, exception: Exception) -> int:
        if isinstance(exception, HttpException):
            return exception.get_status_code()
        return 500

    def _get_exception_headers(self, exception: Exception) -> Dict[str, str]:
        if isinstance(exception, HttpException):
            return exception.get_headers()
        return {}

    def _wants_json(self, request: Optional[Any]) -> bool:
        if request is None:
            return False

        if hasattr(request, "headers"):
            accept = request.headers.get("Accept", "")
            if "application/json" in accept:
                return True

            content_type = request.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return True

        if hasattr(request, "path"):
            if request.path.startswith("/api"):
                return True

        return False

    def _get_user(self, request: Any) -> Optional[Any]:
        if hasattr(request, "user"):
            user = request.user
            if callable(user):
                return user()
            return user

        if hasattr(request, "auth") and hasattr(request.auth, "user"):
            return request.auth.user

        return None


class ReportableRegistration:

    def __init__(self, handler: ExceptionHandler, condition: Callable[[Exception], bool]):
        self.handler = handler
        self.condition = condition
        self.exception_type: Optional[Type[Exception]] = None

    def using(self, callback: Callable[[Exception], None]) -> None:
        if self.exception_type is None:
            for exception_type in [Exception]:
                if exception_type not in self.handler.report_callbacks:
                    self.handler.report_callbacks[exception_type] = []

                self.handler.report_callbacks[exception_type].append(
                    lambda e: callback(e) if self.condition(e) else None
                )
        else:
            if self.exception_type not in self.handler.report_callbacks:
                self.handler.report_callbacks[self.exception_type] = []

            self.handler.report_callbacks[self.exception_type].append(callback)
