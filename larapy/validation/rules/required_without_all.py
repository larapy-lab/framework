from larapy.validation.validation_rule import ValidationRule


class RequiredWithoutAllRule(ValidationRule):
    def __init__(self, *fields):
        super().__init__()
        self.fields = fields

    def passes(self, attribute, value, data):
        all_absent = all(field not in data or data[field] in [None, ""] for field in self.fields)

        if all_absent:
            if (
                value is None
                or value == ""
                or (isinstance(value, (list, dict)) and len(value) == 0)
            ):
                return False

        return True

    def message(self):
        return (
            f"The :attribute field is required when none of {', '.join(self.fields)} are present."
        )
