from larapy.validation.validation_rule import ValidationRule
import re


class MacAddressRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return bool(re.match(pattern, value))

    def message(self):
        return "The :attribute must be a valid MAC address."
