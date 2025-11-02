from larapy.validation.validation_rule import ValidationRule


class MaxDigitsRule(ValidationRule):
    def __init__(self, max_digits):
        super().__init__()
        self.max_digits = int(max_digits)

    def passes(self, attribute, value, data):
        try:
            int_value = int(value)
            digit_count = len(str(abs(int_value)))
            return digit_count <= self.max_digits
        except (ValueError, TypeError):
            return False

    def message(self):
        return f"The :attribute must not have more than {self.max_digits} digits."
