from typing import Callable
from larapy.http.response import Response, RedirectResponse


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
