from larapy.validation.validation_rule import ValidationRule
from typing import Any


class DifferentRule(ValidationRule):
    def __init__(self, other_field: str):
        super().__init__()
        self.other_field = other_field

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return data.get(self.other_field) != value

    def message(self) -> str:
        return f"The :attribute and {self.other_field} must be different."
