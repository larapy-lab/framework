import hashlib
import hmac
from typing import Dict, Any
from larapy.http.controllers import Controller
from larapy.http.response import Response, RedirectResponse, JsonResponse


class VerificationController(Controller):
    def __init__(self, auth_manager, user_provider, view_engine=None):
        super().__init__()
        self._auth = auth_manager
        self._user_provider = user_provider
        self._view_engine = view_engine
        self._redirect_to = "/dashboard"

    def show(self, request):
        user = self._guard().user()

        if user and self._has_verified_email(user):
            return RedirectResponse(self._redirect_to)

        if self._view_engine:
            html = self._view_engine.render("auth.verify", {"user": user})
            return Response(html)

        return Response(
            '<h1>Verify Your Email Address</h1><p>Please check your email for a verification link.</p><form method="POST" action="/email/resend"><button>Resend Verification Email</button></form>'
        )

    def verify(self, request, user_id: str, hash_value: str):
        user = self._user_provider.retrieveById(user_id)

        if not user:
            return self._verification_failed_response(request, "User not found.")

        if not self._valid_hash(user, hash_value):
            return self._verification_failed_response(request, "Invalid verification link.")

        if self._has_verified_email(user):
            return self._already_verified_response(request)

        self._mark_email_as_verified(user)

        return self._verified_response(request)

    def resend(self, request):
        user = self._guard().user()

        if not user:
            return RedirectResponse("/login")

        if self._has_verified_email(user):
            return RedirectResponse(self._redirect_to)

        self._send_email_verification_notification(user)

        if request.expectsJson():
            return JsonResponse(
                {"message": "A fresh verification link has been sent to your email address."}
            )

        if hasattr(request, "_session"):
            request._session.flash(
                "status", "A fresh verification link has been sent to your email address."
            )

        return RedirectResponse("/email/verify")

    def _valid_hash(self, user, hash_value: str) -> bool:
        email = user.get("email", "")
        expected = hashlib.sha1(email.encode()).hexdigest()
        return hmac.compare_digest(expected, hash_value)

    def _has_verified_email(self, user) -> bool:
        email_verified_at = user.get("email_verified_at")
        if email_verified_at is None:
            return False
        return True

    def _mark_email_as_verified(self, user):
        from datetime import datetime

        user._attributes["email_verified_at"] = datetime.now()

    def _send_email_verification_notification(self, user):
        pass

    def _verified_response(self, request):
        if request.expectsJson():
            return JsonResponse({"message": "Your email has been verified!"})

        if hasattr(request, "_session"):
            request._session.flash("status", "Your email has been verified!")

        return RedirectResponse(self._redirect_to)

    def _verification_failed_response(self, request, message: str):
        if request.expectsJson():
            return JsonResponse({"message": message}, status=403)

        if hasattr(request, "_session"):
            request._session.flash("error", message)

        return RedirectResponse("/email/verify")

    def _already_verified_response(self, request):
        if request.expectsJson():
            return JsonResponse({"message": "Email already verified."})

        return RedirectResponse(self._redirect_to)

    def _guard(self):
        return self._auth.guard()
