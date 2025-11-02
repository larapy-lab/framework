from larapy.validation.validation_rule import ValidationRule


class DistinctRule(ValidationRule):
    def __init__(self, strict=False, ignore_case=False):
        super().__init__()
        self.strict = strict
        self.ignore_case = ignore_case

    def passes(self, attribute, value, data):
        if not isinstance(value, list):
            return True

        seen = []
        for item in value:
            compare_item = item
            if self.ignore_case and isinstance(item, str):
                compare_item = item.lower()

            if self.strict:
                if compare_item in seen:
                    return False
            else:
                if any(self._loose_compare(compare_item, s) for s in seen):
                    return False

            seen.append(compare_item)

        return True

    def _loose_compare(self, a, b):
        return str(a) == str(b)

    def message(self):
        return "The :attribute field has duplicate values."
