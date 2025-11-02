from larapy.validation.validation_rule import ValidationRule
from typing import Any, List


class NotInRule(ValidationRule):
    def __init__(self, values: List[Any]):
        super().__init__()
        self.values = values

    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        return value not in self.values

    def message(self) -> str:
        return "The selected :attribute is invalid."
