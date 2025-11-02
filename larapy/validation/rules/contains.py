from larapy.validation.validation_rule import ValidationRule


class ContainsRule(ValidationRule):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def passes(self, attribute, value, data):
        if not isinstance(value, (list, dict)):
            return False

        if isinstance(value, dict):
            value = list(value.values())

        for required in self.values:
            if required not in value:
                return False

        return True

    def message(self):
        return (
            f"The :attribute must contain all of the following: {', '.join(map(str, self.values))}."
        )
