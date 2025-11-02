from larapy.validation.validation_rule import ValidationRule
from typing import Any


class MaxRule(ValidationRule):
    def __init__(self, max_value: int):
        super().__init__()
        self.max_value = max_value

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, str):
            return len(value) <= self.max_value
        elif isinstance(value, (int, float)):
            return value <= self.max_value
        elif isinstance(value, (list, dict)):
            return len(value) <= self.max_value
        return False

    def message(self) -> str:
        return f"The :attribute may not be greater than {self.max_value}."
