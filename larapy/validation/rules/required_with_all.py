from larapy.validation.validation_rule import ValidationRule


class RequiredWithAllRule(ValidationRule):
    def __init__(self, *fields):
        super().__init__()
        self.fields = fields

    def passes(self, attribute, value, data):
        all_present = all(field in data and data[field] not in [None, ""] for field in self.fields)

        if all_present:
            if (
                value is None
                or value == ""
                or (isinstance(value, (list, dict)) and len(value) == 0)
            ):
                return False

        return True

    def message(self):
        return f"The :attribute field is required when {', '.join(self.fields)} are present."
