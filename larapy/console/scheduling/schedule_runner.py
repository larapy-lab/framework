from typing import Dict
from larapy.console.scheduling.schedule import Schedule
from larapy.console.scheduling.event import Event
from larapy.console.scheduling.event_mutex import EventMutex
import inspect


class ScheduleRunner:
    def __init__(self, schedule: Schedule, event_mutex: EventMutex):
        self.schedule = schedule
        self.event_mutex = event_mutex

    async def run(self) -> Dict[str, int]:
        events = self.schedule.due_events()

        results = {"total": len(events), "ran": 0, "skipped": 0, "failed": 0}

        for event in events:
            result = await self.run_event(event)

            if result == "ran":
                results["ran"] += 1
            elif result == "skipped":
                results["skipped"] += 1
            elif result == "failed":
                results["failed"] += 1

        return results

    async def run_event(self, event: Event) -> str:
        if event.without_overlapping_enabled:
            if self.event_mutex.exists(event):
                return "skipped"

            if not self.event_mutex.create(event):
                return "skipped"

        try:
            await self._run_before_callbacks(event)

            success = await event.run()

            await self._run_after_callbacks(event)

            if success:
                await self._run_success_callbacks(event)
            else:
                await self._run_failure_callbacks(event)

            return "ran" if success else "failed"

        except Exception as e:
            await self._run_failure_callbacks(event)
            return "failed"

    async def _run_before_callbacks(self, event: Event):
        for callback in event.before_callbacks:
            await self._run_callback(callback)

    async def _run_after_callbacks(self, event: Event):
        for callback in event.after_callbacks:
            await self._run_callback(callback)

    async def _run_success_callbacks(self, event: Event):
        for callback in event.success_callbacks:
            await self._run_callback(callback)

    async def _run_failure_callbacks(self, event: Event):
        for callback in event.failure_callbacks:
            await self._run_callback(callback)

    async def _run_callback(self, callback):
        try:
            if inspect.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        except Exception:
            pass
