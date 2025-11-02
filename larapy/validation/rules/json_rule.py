from larapy.validation.validation_rule import ValidationRule
from typing import Any
import json


class JsonRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            return False

    def message(self) -> str:
        return "The :attribute must be a valid JSON string."
