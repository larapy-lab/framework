from typing import Callable, List, Optional
from datetime import datetime


class Schedule:
    def __init__(self, container):
        self.container = container
        self.events: List = []
        self.timezone: Optional[str] = None

    def command(self, command: str, parameters: list = None):
        from larapy.console.scheduling.command_event import CommandEvent

        parameters = parameters or []
        event = CommandEvent(self.container, command, parameters)

        if self.timezone:
            event.use_timezone(self.timezone)

        self.events.append(event)
        return event

    def call(self, callback: Callable, parameters: list = None):
        from larapy.console.scheduling.callback_event import CallbackEvent

        parameters = parameters or []
        event = CallbackEvent(self.container, callback, parameters)

        if self.timezone:
            event.use_timezone(self.timezone)

        self.events.append(event)
        return event

    def job(self, job, queue: str = None):
        from larapy.console.scheduling.job_event import JobEvent

        event = JobEvent(self.container, job, queue)

        if self.timezone:
            event.use_timezone(self.timezone)

        self.events.append(event)
        return event

    def exec(self, command: str, parameters: list = None):
        from larapy.console.scheduling.exec_event import ExecEvent

        parameters = parameters or []
        event = ExecEvent(self.container, command, parameters)

        if self.timezone:
            event.use_timezone(self.timezone)

        self.events.append(event)
        return event

    def use_timezone(self, timezone: str) -> "Schedule":
        self.timezone = timezone

        for event in self.events:
            event.use_timezone(timezone)

        return self

    def due_events(self, now: datetime = None) -> List:
        now = now or datetime.now()

        return [event for event in self.events if event.is_due(now)]

    def all_events(self) -> List:
        return self.events
