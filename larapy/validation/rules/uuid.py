from larapy.validation.validation_rule import ValidationRule
import re


class UuidRule(ValidationRule):
    def __init__(self, version=None):
        super().__init__()
        self.version = version

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

        if not re.match(uuid_pattern, value, re.IGNORECASE):
            return False

        if self.version is not None:
            version_digit = value[14]
            return version_digit == str(self.version)

        return True

    def message(self):
        if self.version:
            return f"The :attribute must be a valid UUID version {self.version}."
        return "The :attribute must be a valid UUID."
