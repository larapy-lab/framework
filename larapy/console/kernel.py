from typing import Dict, List, Type, Optional, Any
import sys
from larapy.console.command import Command


class Kernel:

    def __init__(self, container=None):
        self._commands: Dict[str, Type[Command]] = {}
        self.container = container

    def register(self, command_class: Type[Command]):
        if callable(command_class) and not isinstance(command_class, type):
            command_instance = command_class()
        else:
            command_instance = command_class()

        command_name = command_instance.get_name()

        if not command_name:
            raise ValueError(
                f"Command {command_class.__name__ if hasattr(command_class, '__name__') else 'unknown'} has no name defined in signature"
            )

        self._commands[command_name] = command_class

    def register_many(self, command_classes: List[Type[Command]]):
        for command_class in command_classes:
            self.register(command_class)

    def has(self, name: str) -> bool:
        return name in self._commands

    def all(self) -> Dict[str, Type[Command]]:
        return self._commands.copy()

    def call(
        self,
        name: str,
        arguments: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> int:
        if not self.has(name):
            print(f"\033[31m[ERROR] Command '{name}' not found\033[0m")
            return 1

        command_factory = self._commands[name]

        if callable(command_factory) and not isinstance(command_factory, type):
            command = command_factory()
        else:
            command = command_factory()

        command.set_kernel(self)
        command.set_arguments(arguments or [])
        command.set_options(options or {})

        try:
            return command.handle()
        except Exception as e:
            command.error(f"Command failed: {str(e)}")
            return 1

    def run(self, argv: Optional[List[str]] = None) -> int:
        if argv is None:
            argv = sys.argv[1:]

        if not argv:
            self._show_help()
            return 0

        command_name = argv[0]

        if command_name in ["--help", "-h", "help"]:
            self._show_help()
            return 0

        if command_name == "list":
            self._list_commands()
            return 0

        arguments = []
        options = {}

        i = 1
        while i < len(argv):
            arg = argv[i]

            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    options[key] = value
                else:
                    key = arg[2:]
                    if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                        options[key] = argv[i + 1]
                        i += 1
                    else:
                        options[key] = True
            else:
                arguments.append(arg)

            i += 1

        return self.call(command_name, arguments, options)

    def _show_help(self):
        print("Larapy Framework")
        print("")
        print("Usage:")
        print("  command [arguments] [options]")
        print("")
        print("Available commands:")

        for name, command_factory in sorted(self._commands.items()):
            if callable(command_factory) and not isinstance(command_factory, type):
                command = command_factory()
            else:
                command = command_factory()
            description = command.description or "No description"
            print(f"  {name.ljust(30)} {description}")

    def _list_commands(self):
        print("Available commands:")
        print("")

        grouped_commands: Dict[str, List[tuple]] = {}

        for name, command_factory in self._commands.items():
            if callable(command_factory) and not isinstance(command_factory, type):
                command = command_factory()
            else:
                command = command_factory()
            description = command.description or "No description"

            if ":" in name:
                group = name.split(":")[0]
            else:
                group = "default"

            if group not in grouped_commands:
                grouped_commands[group] = []

            grouped_commands[group].append((name, description))

        for group in sorted(grouped_commands.keys()):
            if group != "default":
                print(f"{group}:")

            for name, description in sorted(grouped_commands[group]):
                print(f"  {name.ljust(30)} {description}")

            print("")

    def schedule(self, schedule):
        pass
