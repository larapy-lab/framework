from larapy.validation.validation_rule import ValidationRule
from typing import Any


class AlphaNumRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        return value.isalnum()

    def message(self) -> str:
        return "The :attribute may only contain letters and numbers."
