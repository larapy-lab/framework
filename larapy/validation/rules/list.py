from larapy.validation.validation_rule import ValidationRule


class ListRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, list):
            return False

        expected_keys = list(range(len(value)))
        actual_keys = list(range(len(value)))

        return expected_keys == actual_keys

    def message(self):
        return "The :attribute must be a list with consecutive integer keys starting from 0."
