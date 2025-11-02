from larapy.validation.validation_rule import ValidationRule


class RequiredIfAcceptedRule(ValidationRule):
    def __init__(self, other_field):
        super().__init__()
        self.other_field = other_field

    def passes(self, attribute, value, data):
        other_value = data.get(self.other_field)

        acceptable = ["yes", "on", "1", 1, True, "true"]
        if other_value in acceptable:
            if (
                value is None
                or value == ""
                or (isinstance(value, (list, dict)) and len(value) == 0)
            ):
                return False

        return True

    def message(self):
        return f"The :attribute field is required when {self.other_field} is accepted."
