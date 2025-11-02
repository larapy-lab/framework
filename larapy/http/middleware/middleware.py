from typing import Any, Callable


class Middleware:

    def handle(self, request: Any, next_handler: Callable) -> Any:
        raise NotImplementedError("Middleware must implement handle method")

    def terminate(self, request: Any, response: Any) -> None:
        pass
