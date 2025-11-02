from abc import ABC, abstractmethod
from typing import Callable, List, Optional
from datetime import datetime, time as time_type
import os


class Event(ABC):
    def __init__(self, container):
        self.container = container
        self.expression = "* * * * *"
        self.timezone = None

        self.filters: List[Callable] = []
        self.rejects: List[Callable] = []

        self.before_callbacks: List[Callable] = []
        self.after_callbacks: List[Callable] = []
        self.success_callbacks: List[Callable] = []
        self.failure_callbacks: List[Callable] = []

        self.output_path: Optional[str] = None
        self.output_append = False

        self.without_overlapping_enabled = False
        self.overlapping_expires_at = 1440

        self.environments_list: List[str] = []

        self.description_text: Optional[str] = None

    @abstractmethod
    async def run(self):
        pass

    def is_due(self, now: datetime = None) -> bool:
        now = now or datetime.now()

        if self.timezone:
            try:
                import pytz

                tz = pytz.timezone(self.timezone)
                now = now.astimezone(tz)
            except ImportError:
                pass

        if not self._is_due_cron(now):
            return False

        if not self._passes_filters():
            return False

        if self._fails_rejects():
            return False

        return True

    def _is_due_cron(self, now: datetime) -> bool:
        try:
            from croniter import croniter

            cron = croniter(self.expression, now)
            prev_run = cron.get_prev(datetime)

            time_diff = (now - prev_run).total_seconds()
            return time_diff < 60
        except ImportError:
            from larapy.console.scheduling.cron_expression_parser import CronExpressionParser

            parser = CronExpressionParser(self.expression)
            return parser.is_due(now)

    def _passes_filters(self) -> bool:
        for filter_func in self.filters:
            try:
                if not filter_func():
                    return False
            except Exception:
                return False
        return True

    def _fails_rejects(self) -> bool:
        for reject_func in self.rejects:
            try:
                if reject_func():
                    return True
            except Exception:
                pass
        return False

    def cron(self, expression: str) -> "Event":
        self.expression = expression
        return self

    def every_minute(self) -> "Event":
        return self.cron("* * * * *")

    def every_two_minutes(self) -> "Event":
        return self.cron("*/2 * * * *")

    def every_three_minutes(self) -> "Event":
        return self.cron("*/3 * * * *")

    def every_four_minutes(self) -> "Event":
        return self.cron("*/4 * * * *")

    def every_five_minutes(self) -> "Event":
        return self.cron("*/5 * * * *")

    def every_ten_minutes(self) -> "Event":
        return self.cron("*/10 * * * *")

    def every_fifteen_minutes(self) -> "Event":
        return self.cron("*/15 * * * *")

    def every_thirty_minutes(self) -> "Event":
        return self.cron("*/30 * * * *")

    def hourly(self) -> "Event":
        return self.cron("0 * * * *")

    def hourly_at(self, minute: int) -> "Event":
        return self.cron(f"{minute} * * * *")

    def every_two_hours(self) -> "Event":
        return self.cron("0 */2 * * *")

    def every_three_hours(self) -> "Event":
        return self.cron("0 */3 * * *")

    def every_four_hours(self) -> "Event":
        return self.cron("0 */4 * * *")

    def every_six_hours(self) -> "Event":
        return self.cron("0 */6 * * *")

    def daily(self) -> "Event":
        return self.cron("0 0 * * *")

    def daily_at(self, time_str: str) -> "Event":
        parts = time_str.split(":")
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else "0"
        return self.cron(f"{minute} {hour} * * *")

    def twice_daily(self, hour1: int = 1, hour2: int = 13) -> "Event":
        return self.cron(f"0 {hour1},{hour2} * * *")

    def weekly(self) -> "Event":
        return self.cron("0 0 * * 0")

    def weekly_on(self, day: int, time: str = "0:00") -> "Event":
        """Run the event weekly on a specific day at a specific time."""
        parts = time.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        self.expression = f"{minute} {hour} * * {day}"
        return self

    def monthly(self) -> "Event":
        return self.cron("0 0 1 * *")

    def monthly_on(self, day: int, time_str: str = "0:00") -> "Event":
        parts = time_str.split(":")
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else "0"
        return self.cron(f"{minute} {hour} {day} * *")

    def twice_monthly(self, day1: int = 1, day2: int = 16, time_str: str = "0:00") -> "Event":
        parts = time_str.split(":")
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else "0"
        return self.cron(f"{minute} {hour} {day1},{day2} * *")

    def quarterly(self) -> "Event":
        return self.cron("0 0 1 */3 *")

    def yearly(self) -> "Event":
        return self.cron("0 0 1 1 *")

    def yearly_on(self, month: int = 1, day: int = 1, time_str: str = "0:00") -> "Event":
        parts = time_str.split(":")
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else "0"
        return self.cron(f"{minute} {hour} {day} {month} *")

    def weekdays(self) -> "Event":
        return self.cron("0 0 * * 1-5")

    def weekends(self) -> "Event":
        return self.cron("0 0 * * 0,6")

    def mondays(self) -> "Event":
        return self.cron("0 0 * * 1")

    def tuesdays(self) -> "Event":
        return self.cron("0 0 * * 2")

    def wednesdays(self) -> "Event":
        return self.cron("0 0 * * 3")

    def thursdays(self) -> "Event":
        return self.cron("0 0 * * 4")

    def fridays(self) -> "Event":
        return self.cron("0 0 * * 5")

    def saturdays(self) -> "Event":
        return self.cron("0 0 * * 6")

    def sundays(self) -> "Event":
        return self.cron("0 0 * * 0")

    def at(self, time_str: str) -> "Event":
        parts = time_str.split(":")
        hour = parts[0]
        minute = parts[1] if len(parts) > 1 else "0"

        cron_parts = self.expression.split()
        cron_parts[0] = minute
        cron_parts[1] = hour
        self.expression = " ".join(cron_parts)
        return self

    def between(self, start_time: str, end_time: str) -> "Event":
        def filter_func():
            now = datetime.now().time()
            start_parts = start_time.split(":")
            end_parts = end_time.split(":")
            start = time_type(
                int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0
            )
            end = time_type(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)
            return start <= now <= end

        self.filters.append(filter_func)
        return self

    def unless_between(self, start_time: str, end_time: str) -> "Event":
        def filter_func():
            now = datetime.now().time()
            start_parts = start_time.split(":")
            end_parts = end_time.split(":")
            start = time_type(
                int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0
            )
            end = time_type(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)
            return not (start <= now <= end)

        self.filters.append(filter_func)
        return self

    def when(self, callback: Callable) -> "Event":
        self.filters.append(callback)
        return self

    def skip(self, callback: Callable) -> "Event":
        self.rejects.append(callback)
        return self

    def environments(self, *environments) -> "Event":
        self.environments_list = list(environments)

        def filter_func():
            env = os.getenv("APP_ENV", "production")
            return env in self.environments_list

        self.filters.append(filter_func)
        return self

    def without_overlapping(self, expires_at: int = 1440) -> "Event":
        self.without_overlapping_enabled = True
        self.overlapping_expires_at = expires_at
        return self

    def before(self, callback: Callable) -> "Event":
        self.before_callbacks.append(callback)
        return self

    def after(self, callback: Callable) -> "Event":
        self.after_callbacks.append(callback)
        return self

    def on_success(self, callback: Callable) -> "Event":
        self.success_callbacks.append(callback)
        return self

    def on_failure(self, callback: Callable) -> "Event":
        self.failure_callbacks.append(callback)
        return self

    def send_output_to(self, path: str) -> "Event":
        self.output_path = path
        self.output_append = False
        return self

    def append_output_to(self, path: str) -> "Event":
        self.output_path = path
        self.output_append = True
        return self

    def description(self, text: str) -> "Event":
        self.description_text = text
        return self

    def get_expression(self) -> str:
        return self.expression

    def get_description(self) -> str:
        return self.description_text or self._build_description()

    @abstractmethod
    def _build_description(self) -> str:
        pass

    def use_timezone(self, timezone: str) -> "Event":
        self.timezone = timezone
        return self
