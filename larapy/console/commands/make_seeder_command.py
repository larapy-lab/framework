from larapy.console.command import Command
import os
import re


class MakeSeederCommand(Command):

    signature = "make:seeder {name}"
    description = "Create a new seeder class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Seeder name is required")
            return 1

        if not name.endswith("Seeder"):
            name = f"{name}Seeder"

        seeder_path = self._config.get("seeders", {}).get("path", "database/seeders")

        os.makedirs(seeder_path, exist_ok=True)

        filename = self._convert_to_filename(name)
        filepath = os.path.join(seeder_path, filename)

        if os.path.exists(filepath):
            self.error(f"Seeder already exists: {filename}")
            return 1

        stub = self._get_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Created Seeder: {filename}")

        return 0

    def _convert_to_filename(self, name: str) -> str:
        return f"{name}.py"

    def _get_stub(self, class_name: str) -> str:
        return f"""from larapy.database.seeding.seeder import Seeder


class {class_name}(Seeder):

    def run(self):
        pass
"""
