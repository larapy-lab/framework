from larapy.validation.validation_rule import ValidationRule


class UppercaseRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        return value == value.upper() and value != ""

    def message(self):
        return "The :attribute must be uppercase."
