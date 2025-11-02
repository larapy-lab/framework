from typing import Dict, Any, Optional, List, Callable, Protocol
import os
import sys


class ContextProvider(Protocol):
    def provide(self) -> Dict[str, Any]: ...


class ExceptionContext:

    def __init__(
        self,
        max_string_length: int = 1000,
        max_array_items: int = 50,
        dont_flash: Optional[List[str]] = None,
    ):
        self.max_string_length = max_string_length
        self.max_array_items = max_array_items
        self.dont_flash = dont_flash or [
            "password",
            "password_confirmation",
            "token",
            "secret",
            "api_key",
            "api_secret",
        ]
        self.providers: List[Callable[[], Dict[str, Any]]] = []

    def add_provider(self, provider: Callable[[], Dict[str, Any]]) -> None:
        self.providers.append(provider)

    def collect(
        self, exception: Exception, request: Optional[Any] = None, user: Optional[Any] = None
    ) -> Dict[str, Any]:
        context = {
            "exception": {
                "type": type(exception).__name__,
                "message": str(exception),
                "file": self._get_exception_file(exception),
                "line": self._get_exception_line(exception),
            },
            "environment": self._get_environment_context(),
        }

        if request is not None:
            context["request"] = self._get_request_context(request)

        if user is not None:
            context["user"] = self._get_user_context(user)

        for provider in self.providers:
            try:
                custom_context = provider()
                if isinstance(custom_context, dict):
                    context.update(custom_context)
            except Exception:
                pass

        return context

    def _get_exception_file(self, exception: Exception) -> Optional[str]:
        import traceback

        tb = exception.__traceback__
        if tb is None:
            return None

        while tb.tb_next is not None:
            tb = tb.tb_next

        return tb.tb_frame.f_code.co_filename

    def _get_exception_line(self, exception: Exception) -> Optional[int]:
        tb = exception.__traceback__
        if tb is None:
            return None

        while tb.tb_next is not None:
            tb = tb.tb_next

        return tb.tb_lineno

    def _get_environment_context(self) -> Dict[str, Any]:
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
        }

    def _get_request_context(self, request: Any) -> Dict[str, Any]:
        context = {}

        if hasattr(request, "method"):
            context["method"] = request.method

        if hasattr(request, "path"):
            context["path"] = request.path
        elif hasattr(request, "url"):
            context["path"] = request.url

        if hasattr(request, "query_params"):
            try:
                context["query"] = self._filter_sensitive(dict(request.query_params))
            except (TypeError, ValueError):
                pass
        elif hasattr(request, "args"):
            try:
                context["query"] = self._filter_sensitive(dict(request.args))
            except (TypeError, ValueError):
                pass

        if hasattr(request, "headers"):
            try:
                context["headers"] = self._filter_headers(dict(request.headers))
            except (TypeError, ValueError):
                pass

        if hasattr(request, "form") and request.form is not None:
            try:
                context["body"] = self._filter_sensitive(dict(request.form))
            except (TypeError, ValueError):
                pass
        elif hasattr(request, "json") and callable(request.json):
            try:
                json_data = request.json()
                if isinstance(json_data, dict):
                    context["body"] = self._filter_sensitive(json_data)
            except Exception:
                pass

        if hasattr(request, "remote_addr"):
            context["ip"] = request.remote_addr
        elif hasattr(request, "client") and hasattr(request.client, "host"):
            context["ip"] = request.client.host

        return self._truncate_values(context)

    def _get_user_context(self, user: Any) -> Dict[str, Any]:
        context = {}

        if hasattr(user, "id"):
            context["id"] = user.id
        elif hasattr(user, "get_id") and callable(user.get_id):
            context["id"] = user.get_id()

        if hasattr(user, "email"):
            context["email"] = user.email

        if hasattr(user, "name"):
            context["name"] = user.name
        elif hasattr(user, "username"):
            context["name"] = user.username

        return context

    def _filter_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.dont_flash):
                filtered[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive(value)
            else:
                filtered[key] = value

        return filtered

    def _filter_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        filtered = {}

        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = "***FILTERED***"
            else:
                filtered[key] = value

        return filtered

    def _truncate_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}

        for key, value in data.items():
            if isinstance(value, str) and len(value) > self.max_string_length:
                result[key] = value[: self.max_string_length] + "..."
            elif isinstance(value, (list, tuple)) and len(value) > self.max_array_items:
                result[key] = list(value[: self.max_array_items]) + ["..."]
            elif isinstance(value, dict):
                result[key] = self._truncate_values(value)
            else:
                result[key] = value

        return result
