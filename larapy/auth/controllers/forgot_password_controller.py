from typing import Dict, Any
from larapy.http.controllers import Controller
from larapy.http.response import Response, RedirectResponse, JsonResponse
from larapy.validation import Validator


class ForgotPasswordController(Controller):
    def __init__(self, password_broker, view_engine=None):
        super().__init__()
        self._broker = password_broker
        self._view_engine = view_engine

    def showLinkRequestForm(self, request):
        if self._view_engine:
            html = self._view_engine.render("auth.passwords.email", {})
            return Response(html)
        return Response(
            '<h1>Reset Password</h1><form method="POST"><input name="email" placeholder="Email"><button>Send Reset Link</button></form>'
        )

    def sendResetLinkEmail(self, request):
        validated = self._validate_email(request)

        response = self._broker.send_reset_link_sync(validated)

        if response == self._broker.RESET_LINK_SENT:
            return self._send_reset_link_response(request, response)

        return self._send_reset_link_failed_response(request, response)

    def _validate_email(self, request) -> Dict[str, Any]:
        data = self._get_request_data(request)

        rules = {
            "email": "required|email",
        }

        validator = Validator(data, rules)
        return validator.validate()

    def _send_reset_link_response(self, request, response):
        if request.expectsJson():
            return JsonResponse({"message": "We have emailed your password reset link!"})

        if hasattr(request, "_session"):
            request._session.flash("status", "We have emailed your password reset link!")

        return RedirectResponse("/password/email")

    def _send_reset_link_failed_response(self, request, response):
        if request.expectsJson():
            return JsonResponse(
                {
                    "message": self._get_response_message(response),
                    "errors": {"email": [self._get_response_message(response)]},
                },
                status=422,
            )

        if hasattr(request, "_session"):
            request._session.flash("error", self._get_response_message(response))

        return RedirectResponse("/password/email")

    def _get_response_message(self, response: str) -> str:
        messages = {
            self._broker.INVALID_USER: "We cannot find a user with that email address.",
            self._broker.THROTTLED: "Please wait before retrying.",
        }
        return messages.get(response, "An error occurred.")

    def _get_request_data(self, request) -> Dict[str, Any]:
        if hasattr(request, "all") and callable(request.all):
            return request.all()
        if hasattr(request, "input") and callable(request.input):
            return {"email": request.input("email")}
        return {}
