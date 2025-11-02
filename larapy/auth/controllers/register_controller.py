from typing import Dict, Any
from larapy.http.controllers import Controller
from larapy.http.response import Response, RedirectResponse, JsonResponse
from larapy.validation import Validator
from larapy.auth.passwords import Hash


class RegisterController(Controller):
    def __init__(self, auth_manager, user_provider, view_engine=None):
        super().__init__()
        self._auth = auth_manager
        self._user_provider = user_provider
        self._view_engine = view_engine
        self._redirect_to = "/dashboard"

    def showRegistrationForm(self, request):
        if self._view_engine:
            html = self._view_engine.render("auth.register", {})
            return Response(html)
        return Response(
            '<h1>Register</h1><form method="POST"><input name="name"><input name="email"><input type="password" name="password"><input type="password" name="password_confirmation"><button>Register</button></form>'
        )

    def register(self, request):
        validated = self._validator(request).validate()

        user = self._create(validated)

        self._guard().login(user)

        if hasattr(request, "_session"):
            request._session.regenerate()

        return self._registered(request, user) or self._send_registration_response(request)

    def _validator(self, request) -> Validator:
        data = self._get_request_data(request)

        rules = {
            "name": "required|string|max:255",
            "email": "required|string|email|max:255",
            "password": "required|string|min:8|confirmed",
        }

        return Validator(data, rules)

    def _create(self, data: Dict[str, Any]):
        user_data = {
            "name": data["name"],
            "email": data["email"],
            "password": Hash.make(data["password"]),
        }

        user_id = self._user_provider.create(user_data)

        user_data["id"] = user_id

        from larapy.auth.user import User

        return User(user_data)

    def _registered(self, request, user):
        return None

    def _send_registration_response(self, request):
        if request.expectsJson():
            return JsonResponse({"message": "Registration successful."})

        return RedirectResponse(self._redirect_to)

    def _guard(self):
        return self._auth.guard()

    def _get_request_data(self, request) -> Dict[str, Any]:
        if hasattr(request, "all") and callable(request.all):
            return request.all()
        if hasattr(request, "input") and callable(request.input):
            return {
                "name": request.input("name"),
                "email": request.input("email"),
                "password": request.input("password"),
                "password_confirmation": request.input("password_confirmation"),
            }
        return {}
