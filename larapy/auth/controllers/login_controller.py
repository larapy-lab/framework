from typing import Dict, Any
from larapy.http.controllers import Controller
from larapy.http.response import Response, RedirectResponse, JsonResponse
from larapy.validation import Validator


class LoginController(Controller):
    def __init__(self, auth_manager, view_engine=None):
        super().__init__()
        self._auth = auth_manager
        self._view_engine = view_engine
        self._redirect_to = "/dashboard"

    def showLoginForm(self, request):
        if self._view_engine:
            html = self._view_engine.render("auth.login", {})
            return Response(html)
        return Response(
            '<h1>Login</h1><form method="POST"><input name="email"><input type="password" name="password"><button>Login</button></form>'
        )

    def login(self, request):
        credentials = self._validate_login(request)

        if self._attempt_login(request, credentials):
            return self._send_login_response(request)

        return self._send_failed_login_response(request)

    def logout(self, request):
        self._guard().logout()

        if hasattr(request, "_session"):
            request._session.invalidate()
            request._session.regenerateToken()

        if request.expectsJson():
            return JsonResponse({"message": "Logged out successfully."})

        return RedirectResponse("/login")

    def _validate_login(self, request) -> Dict[str, Any]:
        data = self._get_request_data(request)

        rules = {
            self._username(): "required|string",
            "password": "required|string",
        }

        validator = Validator(data, rules)
        return validator.validate()

    def _attempt_login(self, request, credentials: Dict[str, Any]) -> bool:
        remember = credentials.get("remember", False) or self._get_request_data(request).get(
            "remember", False
        )

        return self._guard().attempt(
            {
                self._username(): credentials.get(self._username()),
                "password": credentials.get("password"),
            },
            remember,
        )

    def _send_login_response(self, request):
        if hasattr(request, "_session"):
            request._session.regenerate()

        if request.expectsJson():
            return JsonResponse({"message": "Logged in successfully."})

        return self._authenticated(request, self._guard().user()) or RedirectResponse(
            self._redirect_to
        )

    def _send_failed_login_response(self, request):
        if request.expectsJson():
            return JsonResponse(
                {
                    "message": "These credentials do not match our records.",
                    "errors": {self._username(): ["These credentials do not match our records."]},
                },
                status=422,
            )

        if hasattr(request, "_session"):
            request._session.flash("error", "These credentials do not match our records.")

        return RedirectResponse("/login")

    def _authenticated(self, request, user):
        if hasattr(request, "input") and callable(request.input):
            intended = request.input("intended")
            if intended:
                return RedirectResponse(intended)
        return None

    def _guard(self):
        return self._auth.guard()

    def _username(self) -> str:
        return "email"

    def _get_request_data(self, request) -> Dict[str, Any]:
        if hasattr(request, "all") and callable(request.all):
            return request.all()
        if hasattr(request, "input") and callable(request.input):
            return {
                "email": request.input("email"),
                "password": request.input("password"),
                "remember": request.input("remember", False),
            }
        return {}
