from larapy.validation.validation_rule import ValidationRule


class DoesntContainRule(ValidationRule):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def passes(self, attribute, value, data):
        if not isinstance(value, (list, dict)):
            return True

        if isinstance(value, dict):
            value = list(value.values())

        for forbidden in self.values:
            if forbidden in value:
                return False

        return True

    def message(self):
        return f"The :attribute must not contain any of the following: {', '.join(map(str, self.values))}."
