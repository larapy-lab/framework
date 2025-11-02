from larapy.console.command import Command
from larapy.console.scheduling.schedule import Schedule
from larapy.console.scheduling.schedule_runner import ScheduleRunner
from larapy.console.scheduling.event_mutex import EventMutex
import asyncio


class ScheduleRunCommand(Command):
    signature = "schedule:run"
    description = "Run the scheduled commands"

    def __init__(self, container=None):
        super().__init__()
        self.container = container

    def handle(self) -> int:
        return asyncio.run(self.handle_async())

    async def handle_async(self):
        schedule = self.get_schedule()

        try:
            from larapy.cache.cache_manager import CacheManager

            cache_manager = CacheManager(
                {
                    "default": "file",
                    "stores": {"file": {"driver": "file", "path": "storage/framework/cache"}},
                }
            )
            cache = cache_manager.store()
        except Exception:
            cache = SimpleCache()

        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)

        self.info("Running scheduled tasks...")

        results = await runner.run()

        self.line("")
        self.info(f"Total events: {results['total']}")
        self.info(f"Ran: {results['ran']}")
        self.info(f"Skipped: {results['skipped']}")
        self.info(f"Failed: {results['failed']}")

        return 0

    def get_schedule(self) -> Schedule:
        schedule = Schedule(self.container)

        try:
            from app.console.kernel import Kernel

            kernel = Kernel(self.container)
            kernel.schedule(schedule)
        except (ImportError, AttributeError):
            pass

        return schedule


class SimpleCache:
    def __init__(self):
        self.data = {}

    def add(self, key: str, value, ttl: int = None) -> bool:
        if key not in self.data:
            self.data[key] = value
            return True
        return False

    def put(self, key: str, value, ttl: int = None):
        self.data[key] = value

    def has(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def forget(self, key: str):
        if key in self.data:
            del self.data[key]

    def delete(self, key: str):
        self.forget(key)
