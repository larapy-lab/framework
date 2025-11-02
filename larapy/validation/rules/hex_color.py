from larapy.validation.validation_rule import ValidationRule
import re


class HexColorRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        pattern = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3}|[A-Fa-f0-9]{8})$"
        return bool(re.match(pattern, value))

    def message(self):
        return "The :attribute must be a valid hexadecimal color."
