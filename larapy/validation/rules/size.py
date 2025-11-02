from larapy.validation.validation_rule import ValidationRule
from typing import Any


class SizeRule(ValidationRule):
    def __init__(self, size: int):
        super().__init__()
        self.size = size

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, str):
            return len(value) == self.size
        elif isinstance(value, (int, float)):
            return value == self.size
        elif isinstance(value, (list, dict)):
            return len(value) == self.size
        return False

    def message(self) -> str:
        return f"The :attribute must be {self.size}."
