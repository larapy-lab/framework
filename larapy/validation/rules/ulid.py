from larapy.validation.validation_rule import ValidationRule
import re


class UlidRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        if len(value) != 26:
            return False

        ulid_pattern = r"^[0-9A-HJKMNP-TV-Z]{26}$"
        return bool(re.match(ulid_pattern, value))

    def message(self):
        return "The :attribute must be a valid ULID."
