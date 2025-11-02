from larapy.validation.validation_rule import ValidationRule
from typing import Any


class AlphaRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        return value.isalpha()

    def message(self) -> str:
        return "The :attribute may only contain letters."
