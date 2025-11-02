from larapy.validation.validation_rule import ValidationRule
from typing import Any
import re


class RegexRule(ValidationRule):
    def __init__(self, pattern: str):
        super().__init__()
        self.pattern = pattern

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.match(self.pattern, value))

    def message(self) -> str:
        return "The :attribute format is invalid."
