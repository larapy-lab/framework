from typing import Any, Optional


class Controller:

    def __init__(self):
        self.middleware_stack = []

    def middleware(self, *middleware: str):
        self.middleware_stack.extend(middleware)
        return self

    def call_action(self, method: str, parameters: dict[str, Any]) -> Any:
        if not hasattr(self, method):
            raise AttributeError(
                f"Method {method} does not exist on controller {self.__class__.__name__}"
            )

        return getattr(self, method)(**parameters)
