from larapy.validation.validation_rule import ValidationRule


class DigitsBetweenRule(ValidationRule):
    def __init__(self, min_digits, max_digits):
        super().__init__()
        self.min_digits = int(min_digits)
        self.max_digits = int(max_digits)

    def passes(self, attribute, value, data):
        try:
            int_value = int(value)
            digit_count = len(str(abs(int_value)))
            return self.min_digits <= digit_count <= self.max_digits
        except (ValueError, TypeError):
            return False

    def message(self):
        return f"The :attribute must have between {self.min_digits} and {self.max_digits} digits."
