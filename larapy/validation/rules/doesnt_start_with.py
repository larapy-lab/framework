from larapy.validation.validation_rule import ValidationRule


class DoesntStartWithRule(ValidationRule):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return True

        return not any(value.startswith(v) for v in self.values)

    def message(self):
        return f"The :attribute must not start with one of the following: {', '.join(map(str, self.values))}."
