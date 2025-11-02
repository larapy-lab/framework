from larapy.validation.validation_rule import ValidationRule
from typing import Any


class BooleanRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return value in [True, False, 1, 0, "1", "0", "true", "false"]

    def message(self) -> str:
        return "The :attribute field must be true or false."
