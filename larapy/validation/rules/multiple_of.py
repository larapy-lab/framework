from larapy.validation.validation_rule import ValidationRule


class MultipleOfRule(ValidationRule):
    def __init__(self, value):
        super().__init__()
        self.value = float(value)

    def passes(self, attribute, value, data):
        try:
            num_value = float(value)
            return num_value % self.value == 0
        except (ValueError, TypeError, ZeroDivisionError):
            return False

    def message(self):
        return f"The :attribute must be a multiple of {self.value}."
