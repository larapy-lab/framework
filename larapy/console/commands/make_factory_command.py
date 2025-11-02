from larapy.console.command import Command
import os
import re


class MakeFactoryCommand(Command):

    signature = "make:factory {name} {--model=}"
    description = "Create a new model factory class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Factory name is required")
            return 1

        if not name.endswith("Factory"):
            name = f"{name}Factory"

        factory_path = self._config.get("seeders", {}).get("path", "database/factories")

        if "factories" in self._config:
            factory_path = self._config["factories"].get("path", factory_path)

        os.makedirs(factory_path, exist_ok=True)

        filename = self._convert_to_filename(name)
        filepath = os.path.join(factory_path, filename)

        if os.path.exists(filepath):
            self.error(f"Factory already exists: {filename}")
            return 1

        model_name = self.option("model") or self._extract_model_name(name)

        stub = self._get_stub(name, model_name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Created Factory: {filename}")

        return 0

    def _convert_to_filename(self, name: str) -> str:
        return f"{name}.py"

    def _extract_model_name(self, factory_name: str) -> str:
        if factory_name.endswith("Factory"):
            return factory_name[:-7]
        return factory_name

    def _get_stub(self, class_name: str, model_name: str) -> str:
        return f"""from larapy.database.seeding.factory import Factory


class {class_name}(Factory):

    def definition(self):
        return {{
            'name': self._faker.name(),
            'email': self._faker.email(),
        }}
"""
