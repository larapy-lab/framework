from larapy.validation.validation_rule import ValidationRule
from typing import Any


class RequiredUnlessRule(ValidationRule):
    def __init__(self, other_field: str, value: Any):
        super().__init__()
        self.other_field = other_field
        self.value = value

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if data.get(self.other_field) != self.value:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return False
        return True

    def message(self) -> str:
        return f"The :attribute field is required unless {self.other_field} is {self.value}."
