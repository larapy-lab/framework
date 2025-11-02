from larapy.validation.validation_rule import ValidationRule
from typing import Any


class RequiredRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    def message(self) -> str:
        return "The :attribute field is required."
