from larapy.validation.validation_rule import ValidationRule


class AsciiRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        try:
            value.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False

    def message(self):
        return "The :attribute must only contain ASCII characters."
