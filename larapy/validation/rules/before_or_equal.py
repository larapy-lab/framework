from larapy.validation.validation_rule import ValidationRule
from datetime import datetime


class BeforeOrEqualRule(ValidationRule):
    def __init__(self, date_or_field):
        super().__init__()
        self.date_or_field = date_or_field

    def passes(self, attribute, value, data):
        try:
            if isinstance(value, str):
                value_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif isinstance(value, datetime):
                value_date = value
            else:
                return False

            if self.date_or_field == "today":
                compare_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif self.date_or_field == "tomorrow":
                from datetime import timedelta

                compare_date = (datetime.now() + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif self.date_or_field == "yesterday":
                from datetime import timedelta

                compare_date = (datetime.now() - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif self.date_or_field in data:
                other_value = data[self.date_or_field]
                if isinstance(other_value, str):
                    compare_date = datetime.fromisoformat(other_value.replace("Z", "+00:00"))
                elif isinstance(other_value, datetime):
                    compare_date = other_value
                else:
                    return False
            else:
                compare_date = datetime.fromisoformat(self.date_or_field.replace("Z", "+00:00"))

            return value_date <= compare_date
        except (ValueError, TypeError):
            return False

    def message(self):
        return f"The :attribute must be a date before or equal to {self.date_or_field}."
