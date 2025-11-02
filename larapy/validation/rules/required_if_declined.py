from larapy.validation.validation_rule import ValidationRule


class RequiredIfDeclinedRule(ValidationRule):
    def __init__(self, other_field):
        super().__init__()
        self.other_field = other_field

    def passes(self, attribute, value, data):
        other_value = data.get(self.other_field)

        declined = ["no", "off", "0", 0, False, "false"]
        if other_value in declined:
            if (
                value is None
                or value == ""
                or (isinstance(value, (list, dict)) and len(value) == 0)
            ):
                return False

        return True

    def message(self):
        return f"The :attribute field is required when {self.other_field} is declined."
