from larapy.console.command import Command
from larapy.console.scheduling.schedule import Schedule
from datetime import datetime


class ScheduleListCommand(Command):
    signature = "schedule:list"
    description = "List all scheduled tasks"

    def __init__(self, container=None):
        super().__init__()
        self.container = container

    def handle(self) -> int:
        schedule = self.get_schedule()
        events = schedule.all_events()

        if not events:
            self.info("No scheduled tasks.")
            return 0

        self.line("")
        self.info("Scheduled Tasks:")
        self.line("")

        headers = ["Description", "Expression", "Next Due"]
        rows = []

        now = datetime.now()

        for event in events:
            next_run = self._get_next_run(event, now)

            rows.append([event.get_description(), event.get_expression(), next_run])

        self.table(headers, rows)

        return 0

    def _get_next_run(self, event, now: datetime) -> str:
        try:
            from croniter import croniter

            cron = croniter(event.get_expression(), now)
            next_run = cron.get_next(datetime)
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        except ImportError:
            return "Install croniter for next run times"
        except Exception:
            return "N/A"

    def get_schedule(self) -> Schedule:
        schedule = Schedule(self.container)

        try:
            from app.console.kernel import Kernel

            kernel = Kernel(self.container)
            kernel.schedule(schedule)
        except (ImportError, AttributeError):
            pass

        return schedule
