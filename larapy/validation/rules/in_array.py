from larapy.validation.validation_rule import ValidationRule


class InArrayRule(ValidationRule):
    def __init__(self, other_field):
        super().__init__()
        self.other_field = other_field

    def passes(self, attribute, value, data):
        other_value = self._get_nested_value(data, self.other_field)

        if not isinstance(other_value, (list, dict)):
            return False

        if isinstance(other_value, dict):
            other_value = list(other_value.values())

        return value in other_value

    def _get_nested_value(self, data, key):
        if ".*" in key:
            base_key = key.replace(".*", "")
            if base_key in data:
                return data[base_key]

        if key in data:
            return data[key]

        if "." in key:
            keys = key.split(".")
            current = data
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current

        return None

    def message(self):
        return f"The :attribute must exist in {self.other_field}."
