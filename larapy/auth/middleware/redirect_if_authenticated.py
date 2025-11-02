from typing import Callable
from larapy.http.response import Response, RedirectResponse


class RedirectIfAuthenticated:
    def __init__(self, auth_manager):
        self._auth = auth_manager

    def handle(self, request, next_handler: Callable, *guards) -> Response:
        guards_to_check = list(guards) if guards else [None]

        for guard_name in guards_to_check:
            guard = self._auth.guard(guard_name)
            guard.setRequest(request)

            if hasattr(guard, "setSession") and hasattr(request, "_session"):
                guard.setSession(request._session)

            if guard.check():
                return RedirectResponse("/dashboard")

        return next_handler(request)
