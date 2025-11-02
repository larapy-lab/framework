from larapy.validation.validation_rule import ValidationRule
from typing import Any
from datetime import datetime


class DateRule(ValidationRule):
    def __init__(self, format: str = "%Y-%m-%d"):
        super().__init__()
        self.format = format

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, self.format)
            return True
        except (ValueError, TypeError):
            return False

    def message(self) -> str:
        return "The :attribute is not a valid date."
