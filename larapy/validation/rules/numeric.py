from larapy.validation.validation_rule import ValidationRule
from typing import Any


class NumericRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        return False

    def message(self) -> str:
        return "The :attribute must be a number."
