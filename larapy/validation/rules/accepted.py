from larapy.validation.validation_rule import ValidationRule


class AcceptedRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        acceptable = ["yes", "on", "1", 1, True, "true"]
        return value in acceptable

    def message(self):
        return "The :attribute must be accepted."
