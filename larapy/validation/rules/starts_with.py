from larapy.validation.validation_rule import ValidationRule


class StartsWithRule(ValidationRule):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        return any(value.startswith(v) for v in self.values)

    def message(self):
        return f"The :attribute must start with one of the following: {', '.join(map(str, self.values))}."
