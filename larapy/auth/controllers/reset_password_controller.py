from typing import Dict, Any
from larapy.http.controllers import Controller
from larapy.http.response import Response, RedirectResponse, JsonResponse
from larapy.validation import Validator
from larapy.auth.passwords import Hash


class ResetPasswordController(Controller):
    def __init__(self, password_broker, auth_manager, view_engine=None):
        super().__init__()
        self._broker = password_broker
        self._auth = auth_manager
        self._view_engine = view_engine
        self._redirect_to = "/dashboard"

    def showResetForm(self, request, token: str):
        email = self._get_email_from_request(request)

        if self._view_engine:
            html = self._view_engine.render(
                "auth.passwords.reset", {"token": token, "email": email}
            )
            return Response(html)

        return Response(
            f'<h1>Reset Password</h1><form method="POST"><input type="hidden" name="token" value="{token}"><input name="email" value="{email}"><input type="password" name="password"><input type="password" name="password_confirmation"><button>Reset Password</button></form>'
        )

    def reset(self, request):
        validated = self._validate_reset(request)

        def reset_password(user, password):
            user._attributes["password"] = Hash.make(password)
            self._update_user_password(user)

        response = self._broker.reset_sync(validated, reset_password)

        if response == self._broker.PASSWORD_RESET:
            return self._send_reset_response(request, response)

        return self._send_reset_failed_response(request, response)

    def _validate_reset(self, request) -> Dict[str, Any]:
        data = self._get_request_data(request)

        rules = {
            "token": "required",
            "email": "required|email",
            "password": "required|min:8|confirmed",
        }

        validator = Validator(data, rules)
        return validator.validate()

    def _update_user_password(self, user):
        pass

    def _send_reset_response(self, request, response):
        if request.expectsJson():
            return JsonResponse({"message": "Your password has been reset!"})

        if hasattr(request, "_session"):
            request._session.flash("status", "Your password has been reset!")

        return RedirectResponse("/login")

    def _send_reset_failed_response(self, request, response):
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

        return RedirectResponse("/password/reset")

    def _get_response_message(self, response: str) -> str:
        messages = {
            self._broker.INVALID_USER: "We cannot find a user with that email address.",
            self._broker.INVALID_TOKEN: "This password reset token is invalid.",
            self._broker.THROTTLED: "Please wait before retrying.",
        }
        return messages.get(response, "An error occurred.")

    def _get_email_from_request(self, request) -> str:
        if hasattr(request, "input") and callable(request.input):
            return request.input("email", "")
        if hasattr(request, "query_params"):
            return request.query_params.get("email", "")
        return ""

    def _get_request_data(self, request) -> Dict[str, Any]:
        if hasattr(request, "all") and callable(request.all):
            return request.all()
        if hasattr(request, "input") and callable(request.input):
            return {
                "token": request.input("token"),
                "email": request.input("email"),
                "password": request.input("password"),
                "password_confirmation": request.input("password_confirmation"),
            }
        return {}
