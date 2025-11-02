from larapy.validation.validation_rule import ValidationRule
from typing import Any


class ArrayRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return isinstance(value, (list, dict))

    def message(self) -> str:
        return "The :attribute must be an array."
