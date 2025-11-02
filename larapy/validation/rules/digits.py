from larapy.validation.validation_rule import ValidationRule
from typing import Any


class DigitsRule(ValidationRule):
    def __init__(self, length: int):
        super().__init__()
        self.length = length

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str):
            return False
        return value.isdigit() and len(value) == self.length

    def message(self) -> str:
        return f"The :attribute must be {self.length} digits."
