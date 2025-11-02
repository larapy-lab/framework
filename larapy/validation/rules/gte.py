from larapy.validation.validation_rule import ValidationRule


class GteRule(ValidationRule):
    def __init__(self, other_field):
        super().__init__()
        self.other_field = other_field

    def passes(self, attribute, value, data):
        other_value = data.get(self.other_field)

        if other_value is None:
            return False

        if isinstance(value, str):
            return len(value) >= len(str(other_value))
        elif isinstance(value, (int, float)):
            try:
                return float(value) >= float(other_value)
            except (ValueError, TypeError):
                return False
        elif isinstance(value, (list, dict)):
            other_len = len(other_value) if isinstance(other_value, (list, dict, str)) else 0
            return len(value) >= other_len

        return False

    def message(self):
        return f"The :attribute must be greater than or equal to {self.other_field}."
