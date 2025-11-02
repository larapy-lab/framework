from larapy.validation.validation_rule import ValidationRule


class EndsWithRule(ValidationRule):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        return any(value.endswith(v) for v in self.values)

    def message(self):
        return f"The :attribute must end with one of the following: {', '.join(map(str, self.values))}."
