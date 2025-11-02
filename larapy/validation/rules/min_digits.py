from larapy.validation.validation_rule import ValidationRule


class MinDigitsRule(ValidationRule):
    def __init__(self, min_digits):
        super().__init__()
        self.min_digits = int(min_digits)

    def passes(self, attribute, value, data):
        try:
            int_value = int(value)
            digit_count = len(str(abs(int_value)))
            return digit_count >= self.min_digits
        except (ValueError, TypeError):
            return False

    def message(self):
        return f"The :attribute must have at least {self.min_digits} digits."
