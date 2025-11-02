from larapy.validation.validation_rule import ValidationRule


class RequiredArrayKeysRule(ValidationRule):
    def __init__(self, *keys):
        super().__init__()
        self.keys = keys

    def passes(self, attribute, value, data):
        if not isinstance(value, (dict, list)):
            return False

        if isinstance(value, dict):
            for key in self.keys:
                if key not in value:
                    return False

        return True

    def message(self):
        return f"The :attribute must contain the following keys: {', '.join(self.keys)}."
