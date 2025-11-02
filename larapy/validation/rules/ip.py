from larapy.validation.validation_rule import ValidationRule
from typing import Any
import ipaddress


class IpRule(ValidationRule):
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        if not isinstance(value, str):
            return False
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def message(self) -> str:
        return "The :attribute must be a valid IP address."
