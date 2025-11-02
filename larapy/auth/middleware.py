from typing import Optional, Callable
from larapy.http.response import Response, RedirectResponse


class Authenticate:
    def __init__(self, auth_manager, guards: Optional[list] = None):
        self._auth = auth_manager
        self._guards = guards or []

    def handle(self, request, next_handler: Callable, *guards) -> Response:
        guards_to_check = list(guards) if guards else self._guards

        if not guards_to_check:
            guards_to_check = [None]

        for guard_name in guards_to_check:
            guard = self._auth.guard(guard_name)
            guard.setRequest(request)

            if hasattr(guard, "setSession") and hasattr(request, "_session"):
                guard.setSession(request._session)

            if guard.check():
                request._user = guard.user()
                return next_handler(request)

        return self._unauthenticated(request)

    def _unauthenticated(self, request) -> Response:
        if request.expectsJson():
            from larapy.http.response import JsonResponse

            return JsonResponse({"message": "Unauthenticated."}, status=401)

        return RedirectResponse("/login")


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


class EnsureEmailIsVerified:
    def __init__(self, auth_manager):
        self._auth = auth_manager

    def handle(self, request, next_handler: Callable) -> Response:
        guard = self._auth.guard()
        guard.setRequest(request)

        if hasattr(guard, "setSession") and hasattr(request, "_session"):
            guard.setSession(request._session)

        user = guard.user()

        if not user:
            if request.expectsJson():
                from larapy.http.response import JsonResponse

                return JsonResponse({"message": "Unauthenticated."}, status=401)
            return RedirectResponse("/login")

        if not self._has_verified_email(user):
            if request.expectsJson():
                from larapy.http.response import JsonResponse

                return JsonResponse({"message": "Your email address is not verified."}, status=403)
            return RedirectResponse("/email/verify")

        return next_handler(request)

    def _has_verified_email(self, user) -> bool:
        email_verified_at = user.get("email_verified_at")
        if email_verified_at is None:
            return False
        return True
