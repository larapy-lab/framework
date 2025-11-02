from larapy.validation.validation_rule import ValidationRule
from typing import Any
import re


class UrlRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, value, re.IGNORECASE))

    def message(self) -> str:
        return "The :attribute format is invalid."
