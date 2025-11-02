from larapy.validation.validation_rule import ValidationRule
from typing import Any


class BetweenRule(ValidationRule):
    def __init__(self, min_value: int, max_value: int):
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, str):
            return self.min_value <= len(value) <= self.max_value
        elif isinstance(value, (int, float)):
            return self.min_value <= value <= self.max_value
        elif isinstance(value, (list, dict)):
            return self.min_value <= len(value) <= self.max_value
        return False

    def message(self) -> str:
        return f"The :attribute must be between {self.min_value} and {self.max_value}."
