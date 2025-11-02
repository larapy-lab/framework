from larapy.console.command import Command
import os
import re


class MakeCommandCommand(Command):

    signature = "make:command {name}"
    description = "Create a new Artisan command"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Command name is required")
            return 1

        command_path = self._config.get("commands", {}).get("path", "app/console/commands")
        os.makedirs(command_path, exist_ok=True)

        filename = f"{self._snake_case(name)}.py"
        filepath = os.path.join(command_path, filename)

        if os.path.exists(filepath):
            self.error(f"Command {name} already exists")
            return 1

        stub = self._get_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Command created: {filepath}")
        self.new_line()
        self.line("Register your command in console/kernel.py:")
        self.line(f"  kernel.register({name})")

        return 0

    def _get_stub(self, name: str) -> str:
        command_name = self._command_name(name)

        return f"""from larapy.console.command import Command


class {name}(Command):

    signature = '{command_name} {{argument}} {{--option}}'
    description = 'Command description'

    def handle(self) -> int:
        argument = self.argument('argument')
        option = self.option('option')

        self.info(f'Processing {{argument}}...')

        if option:
            self.line(f'Option set: {{option}}')

        self.info('Command completed successfully')

        return 0
"""

    def _command_name(self, name: str) -> str:
        command = self._snake_case(name)

        if command.endswith("_command"):
            command = command[:-8]

        parts = command.split("_")
        if len(parts) > 1:
            return f'{parts[0]}:{"-".join(parts[1:])}'

        return command

    def _snake_case(self, text: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
