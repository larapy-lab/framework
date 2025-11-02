from larapy.validation.validation_rule import ValidationRule


class FilledRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if attribute not in data:
            return True

        if value is None:
            return False
        if value == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False

        return True

    def message(self):
        return "The :attribute field must not be empty when present."
