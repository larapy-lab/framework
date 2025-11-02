from larapy.validation.validation_rule import ValidationRule


class DeclinedRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        acceptable = ["no", "off", "0", 0, False, "false"]
        return value in acceptable

    def message(self):
        return "The :attribute must be declined."
