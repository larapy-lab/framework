from larapy.validation.validation_rule import ValidationRule
from typing import Any


class NullableRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return True

    def message(self) -> str:
        return ""
