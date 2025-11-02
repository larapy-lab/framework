from larapy.validation.validation_rule import ValidationRule
from typing import Any
import re


class AlphaDashRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, value))

    def message(self) -> str:
        return "The :attribute may only contain letters, numbers, dashes and underscores."
