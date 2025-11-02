from larapy.validation.validation_rule import ValidationRule
from typing import Any
import re


class EmailRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, value))

    def message(self) -> str:
        return "The :attribute must be a valid email address."
