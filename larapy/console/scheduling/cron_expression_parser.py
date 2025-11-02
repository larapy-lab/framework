from datetime import datetime
from typing import List, Set


class CronExpressionParser:
    def __init__(self, expression: str):
        self.expression = expression
        parts = expression.split()

        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")

        self.minute = parts[0]
        self.hour = parts[1]
        self.day = parts[2]
        self.month = parts[3]
        self.weekday = parts[4]

    def is_due(self, now: datetime) -> bool:
        return (
            self._matches_minute(now)
            and self._matches_hour(now)
            and self._matches_day(now)
            and self._matches_month(now)
            and self._matches_weekday(now)
        )

    def _matches_minute(self, now: datetime) -> bool:
        return self._matches_field(self.minute, now.minute, 0, 59)

    def _matches_hour(self, now: datetime) -> bool:
        return self._matches_field(self.hour, now.hour, 0, 23)

    def _matches_day(self, now: datetime) -> bool:
        return self._matches_field(self.day, now.day, 1, 31)

    def _matches_month(self, now: datetime) -> bool:
        return self._matches_field(self.month, now.month, 1, 12)

    def _matches_weekday(self, now: datetime) -> bool:
        weekday = now.weekday()
        if weekday == 6:
            weekday = 0
        else:
            weekday += 1

        return self._matches_field(self.weekday, weekday, 0, 6)

    def _matches_field(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        if field == "*":
            return True

        if "/" in field:
            return self._matches_step(field, value, min_val, max_val)

        if "," in field:
            return self._matches_list(field, value)

        if "-" in field:
            return self._matches_range(field, value)

        return int(field) == value

    def _matches_step(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        parts = field.split("/")
        range_part = parts[0]
        step = int(parts[1])

        if range_part == "*":
            start = min_val
            end = max_val
        elif "-" in range_part:
            range_parts = range_part.split("-")
            start = int(range_parts[0])
            end = int(range_parts[1])
        else:
            start = int(range_part)
            end = max_val

        if value < start or value > end:
            return False

        return (value - start) % step == 0

    def _matches_list(self, field: str, value: int) -> bool:
        values = [int(v.strip()) for v in field.split(",")]
        return value in values

    def _matches_range(self, field: str, value: int) -> bool:
        parts = field.split("-")
        start = int(parts[0])
        end = int(parts[1])
        return start <= value <= end
