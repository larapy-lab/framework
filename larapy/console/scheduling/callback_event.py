from larapy.console.scheduling.event import Event
import inspect


class CallbackEvent(Event):
    def __init__(self, container, callback, parameters: list):
        super().__init__(container)
        self.callback = callback
        self.parameters = parameters

    async def run(self):
        try:
            if inspect.iscoroutinefunction(self.callback):
                await self.callback(*self.parameters)
            else:
                self.callback(*self.parameters)
            return True
        except Exception:
            return False

    def _build_description(self) -> str:
        if hasattr(self.callback, "__name__"):
            return f"Closure: {self.callback.__name__}"
        return "Closure"
