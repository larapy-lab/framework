from larapy.validation.validation_rule import ValidationRule


class AcceptedIfRule(ValidationRule):
    def __init__(self, other_field, value):
        super().__init__()
        self.other_field = other_field
        self.compare_value = value

    def passes(self, attribute, value, data):
        other_value = data.get(self.other_field)

        if str(other_value) == str(self.compare_value):
            acceptable = ["yes", "on", "1", 1, True, "true"]
            return value in acceptable

        return True

    def message(self):
        return f"The :attribute must be accepted when {self.other_field} is {self.compare_value}."
