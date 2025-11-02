from larapy.console.command import Command
import os


class MakeModelCommand(Command):

    signature = "make:model {name} {--migration} {--factory} {--resource} {--all}"
    description = "Create a new Eloquent model class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Model name is required")
            return 1

        model_path = self._config.get("models", {}).get("path", "app/models")
        os.makedirs(model_path, exist_ok=True)

        filename = f"{name}.py"
        filepath = os.path.join(model_path, filename)

        if os.path.exists(filepath):
            self.error(f"Model {name} already exists")
            return 1

        stub = self._get_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Model created: {filepath}")

        all_option = self.option("all", False)

        if self.option("migration", False) or all_option:
            table_name = self._get_table_name(name)
            self.call(
                "make:migration", {"name": f"create_{table_name}_table", "--create": table_name}
            )

        if self.option("factory", False) or all_option:
            self.call("make:factory", {"name": f"{name}Factory"})

        if self.option("resource", False) or all_option:
            self.call("make:resource", {"name": f"{name}Resource"})

        return 0

    def _get_stub(self, name: str) -> str:
        table_name = self._get_table_name(name)

        return f"""from larapy.database.eloquent import Model


class {name}(Model):

    table = '{table_name}'

    fillable = []

    hidden = []

    casts = {{}}
"""

    def _get_table_name(self, name: str) -> str:
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        table_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        if not table_name.endswith("s"):
            table_name += "s"

        return table_name
