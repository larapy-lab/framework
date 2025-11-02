from larapy.validation.validation_rule import ValidationRule


class PresentRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        return attribute in data

    def message(self):
        return "The :attribute field must be present."
