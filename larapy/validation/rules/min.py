from larapy.validation.validation_rule import ValidationRule
from typing import Any


class MinRule(ValidationRule):
    def __init__(self, min_value: int):
        super().__init__()
        self.min_value = min_value

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, str):
            return len(value) >= self.min_value
        elif isinstance(value, (int, float)):
            return value >= self.min_value
        elif isinstance(value, (list, dict)):
            return len(value) >= self.min_value
        return False

    def message(self) -> str:
        return f"The :attribute must be at least {self.min_value}."
