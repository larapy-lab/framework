from larapy.validation.validation_rule import ValidationRule


class BailRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        return True

    def message(self):
        return ""
