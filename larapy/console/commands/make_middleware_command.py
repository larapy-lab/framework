from larapy.console.command import Command
import os


class MakeMiddlewareCommand(Command):

    signature = "make:middleware {name}"
    description = "Create a new middleware class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Middleware name is required")
            return 1

        middleware_path = self._config.get("middleware", {}).get("path", "app/http/middleware")
        os.makedirs(middleware_path, exist_ok=True)

        filename = f"{name}.py"
        filepath = os.path.join(middleware_path, filename)

        if os.path.exists(filepath):
            self.error(f"Middleware {name} already exists")
            return 1

        stub = self._get_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Middleware created: {filepath}")
        self.new_line()
        self.line("Register your middleware in app/http/kernel.py")

        return 0

    def _get_stub(self, name: str) -> str:
        return f"""from larapy.http.middleware import Middleware


class {name}(Middleware):

    def handle(self, request, next):

        response = next(request)

        return response
"""
