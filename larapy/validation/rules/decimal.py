from larapy.validation.validation_rule import ValidationRule


class DecimalRule(ValidationRule):
    def __init__(self, min_places, max_places=None):
        super().__init__()
        self.min_places = int(min_places)
        self.max_places = int(max_places) if max_places is not None else int(min_places)

    def passes(self, attribute, value, data):
        try:
            str_value = str(value)

            if "." not in str_value:
                return False

            decimal_part = str_value.split(".")[1]
            decimal_places = len(decimal_part)

            return self.min_places <= decimal_places <= self.max_places
        except (ValueError, IndexError):
            return False

    def message(self):
        if self.min_places == self.max_places:
            return f"The :attribute must have exactly {self.min_places} decimal places."
        return f"The :attribute must have between {self.min_places} and {self.max_places} decimal places."
