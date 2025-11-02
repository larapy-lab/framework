from abc import ABC, abstractmethod
import re
import sys
from typing import Any, Dict, List, Optional, Callable


class Command(ABC):

    signature: str = ""
    description: str = ""

    def __init__(self):
        self._arguments: Dict[str, Any] = {}
        self._options: Dict[str, Any] = {}
        self._output: List[str] = []
        self._kernel = None
        self._parse_signature()

    def set_kernel(self, kernel):
        self._kernel = kernel

    def _parse_signature(self):
        if not self.signature:
            return

        parts = self.signature.split()
        self._name = parts[0] if parts else ""

        self._argument_definitions = []
        self._option_definitions = {}

        for part in parts[1:]:
            if part.startswith("{--"):
                option_match = re.match(r"\{--(\w+)(=)?(\w*)?\}", part)
                if option_match:
                    option_name = option_match.group(1)
                    has_value = option_match.group(2) == "="
                    default_value = option_match.group(3) if option_match.group(3) else None
                    self._option_definitions[option_name] = {
                        "default": default_value,
                        "required": False,
                        "has_value": has_value,
                    }
            elif part.startswith("{"):
                arg_match = re.match(r"\{(\w+)(\?)?\}", part)
                if arg_match:
                    arg_name = arg_match.group(1)
                    is_optional = arg_match.group(2) == "?"
                    self._argument_definitions.append({"name": arg_name, "optional": is_optional})

    def set_arguments(self, arguments: List[str]):
        for i, arg_def in enumerate(self._argument_definitions):
            if i < len(arguments):
                self._arguments[arg_def["name"]] = arguments[i]
            elif arg_def["optional"]:
                self._arguments[arg_def["name"]] = None
            else:
                raise ValueError(f"Missing required argument: {arg_def['name']}")

    def set_options(self, options: Dict[str, Any]):
        for option_name, option_def in self._option_definitions.items():
            if option_name in options:
                value = options[option_name]
                self._options[option_name] = value if value is not None else option_def["default"]
            else:
                self._options[option_name] = option_def["default"]

    def argument(self, name: str, default: Any = None) -> Any:
        value = self._arguments.get(name)
        return value if value is not None else default

    def option(self, name: str, default: Any = None) -> Any:
        value = self._options.get(name)
        return value if value is not None else default

    def line(self, text: str = ""):
        self._output.append(text)
        print(text)

    def info(self, text: str):
        message = f"[INFO] {text}"
        self._output.append(message)
        print(f"\033[36m{message}\033[0m")

    def comment(self, text: str):
        message = f"[COMMENT] {text}"
        self._output.append(message)
        print(f"\033[90m{message}\033[0m")

    def question(self, text: str):
        message = f"[QUESTION] {text}"
        self._output.append(message)
        print(f"\033[35m{message}\033[0m")

    def error(self, text: str):
        message = f"[ERROR] {text}"
        self._output.append(message)
        print(f"\033[31m{message}\033[0m")

    def warn(self, text: str):
        message = f"[WARNING] {text}"
        self._output.append(message)
        print(f"\033[33m{message}\033[0m")

    def table(self, headers: List[str], rows: List[List[str]]):
        col_widths = [len(h) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * w for w in col_widths)

        self.line(header_row)
        self.line(separator)

        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            self.line(row_str)

    def get_output(self) -> List[str]:
        return self._output

    def get_name(self) -> str:
        return getattr(self, "_name", "")

    def ask(self, question: str, default: Optional[str] = None) -> str:
        if default:
            prompt = f"{question} [{default}]: "
        else:
            prompt = f"{question}: "

        self.question(prompt.rstrip(": "))
        response = input().strip()
        return response if response else (default or "")

    def confirm(self, question: str, default: bool = False) -> bool:
        default_text = "Y/n" if default else "y/N"
        prompt = f"{question} [{default_text}]: "

        self.question(prompt.rstrip(": "))
        response = input().strip().lower()

        if not response:
            return default

        return response in ["y", "yes", "1", "true"]

    def choice(self, question: str, choices: List[str], default: Optional[str] = None) -> str:
        self.question(question)

        for i, choice in enumerate(choices, 1):
            default_marker = " (default)" if choice == default else ""
            self.line(f"  [{i}] {choice}{default_marker}")

        while True:
            self.question("Select an option: ")
            response = input().strip()

            if not response and default:
                return default

            if response.isdigit():
                index = int(response) - 1
                if 0 <= index < len(choices):
                    return choices[index]

            if response in choices:
                return response

            self.error("Invalid selection. Please try again.")

    def new_line(self, count: int = 1):
        for _ in range(count):
            self.line()

    def progress_bar(self, max_steps: int):
        from larapy.console.progress_bar import ProgressBar

        return ProgressBar(self, max_steps)

    def with_progress_bar(self, items: List[Any], callback: Callable):
        progress = self.progress_bar(len(items))
        progress.start()

        results = []
        for item in items:
            result = callback(item)
            results.append(result)
            progress.advance()

        progress.finish()
        return results

    def call(self, command: str, arguments: Optional[Dict[str, Any]] = None) -> int:
        if not self._kernel:
            self.error("Cannot call command: Kernel not set")
            return 1

        args = []
        opts = {}

        if arguments:
            for key, value in arguments.items():
                if key.startswith("--"):
                    opts[key[2:]] = value
                else:
                    args.append(value)

        return self._kernel.call(command, args, opts)

    def call_silent(self, command: str, arguments: Optional[Dict[str, Any]] = None) -> int:
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            sys.stdout = open("/dev/null", "w")
            sys.stderr = open("/dev/null", "w")
            return self.call(command, arguments)
        finally:
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    @abstractmethod
    def handle(self) -> int:
        pass
