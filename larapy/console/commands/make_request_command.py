from larapy.console.command import Command
from typing import Optional
import os


class MakeRequestCommand(Command):
    signature = "make:request {name}"
    description = "Create a new form request class"

    def __init__(self, config: Optional[dict] = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Request name is required")
            return 1

        if not name.endswith("Request"):
            name = f"{name}Request"

        request_path = self._config.get("requests", {}).get("path", "app/http/requests")
        os.makedirs(request_path, exist_ok=True)

        filename = f"{name}.py"
        filepath = os.path.join(request_path, filename)

        if os.path.exists(filepath):
            self.error(f"Request {name} already exists")
            return 1

        stub = self._get_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Request created: {filepath}")
        return 0

    def _get_stub(self, name: str) -> str:
        return f"""from larapy.validation.form_request import FormRequest


class {name}(FormRequest):

    def authorize(self) -> bool:
        return True

    def rules(self) -> dict:
        return {{

        }}

    def messages(self) -> dict:
        return {{

        }}

    def attributes(self) -> dict:
        return {{

        }}
"""
