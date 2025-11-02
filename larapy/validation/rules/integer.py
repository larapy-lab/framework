from larapy.validation.validation_rule import ValidationRule
from typing import Any


class IntegerRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            try:
                int(value)
                return "." not in value
            except (ValueError, TypeError):
                return False
        return False

    def message(self) -> str:
        return "The :attribute must be an integer."
