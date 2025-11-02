from larapy.validation.validation_rule import ValidationRule
from datetime import datetime


class DateFormatRule(ValidationRule):
    def __init__(self, *formats):
        super().__init__()
        self.formats = formats

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        for fmt in self.formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue

        return False

    def message(self):
        return f"The :attribute must match the format {', '.join(self.formats)}."
