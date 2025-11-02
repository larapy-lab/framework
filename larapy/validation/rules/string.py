from larapy.validation.validation_rule import ValidationRule
from typing import Any


class StringRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return isinstance(value, str)

    def message(self) -> str:
        return "The :attribute must be a string."
