from larapy.validation.validation_rule import ValidationRule
from typing import Any


class ConfirmedRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        confirmation_field = f"{attribute}_confirmation"
        return data.get(confirmation_field) == value

    def message(self) -> str:
        return "The :attribute confirmation does not match."
