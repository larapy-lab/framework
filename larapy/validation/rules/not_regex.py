from larapy.validation.validation_rule import ValidationRule
import re


class NotRegexRule(ValidationRule):
    def __init__(self, pattern):
        super().__init__()
        self.pattern = pattern

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return True

        return not bool(re.search(self.pattern, value))

    def message(self):
        return "The :attribute format is invalid."
