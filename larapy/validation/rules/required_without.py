from larapy.validation.validation_rule import ValidationRule
from typing import Any, List


class RequiredWithoutRule(ValidationRule):
    def __init__(self, fields: List[str]):
        super().__init__()
        self.fields = fields

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if any(data.get(field) is None for field in self.fields):
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return False
        return True

    def message(self) -> str:
        return f'The :attribute field is required when {", ".join(self.fields)} is not present.'
