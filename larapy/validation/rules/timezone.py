from larapy.validation.validation_rule import ValidationRule
import pytz


class TimezoneRule(ValidationRule):
    def __init__(self, group="all"):
        super().__init__()
        self.group = group

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        try:
            all_timezones = pytz.all_timezones

            if self.group == "all":
                return value in all_timezones
            elif self.group in [
                "Africa",
                "America",
                "Antarctica",
                "Arctic",
                "Asia",
                "Atlantic",
                "Australia",
                "Europe",
                "Indian",
                "Pacific",
            ]:
                return value.startswith(self.group + "/") and value in all_timezones
            elif self.group.startswith("per_country,"):
                country_code = self.group.split(",")[1]
                country_timezones = pytz.country_timezones.get(country_code, [])
                return value in country_timezones
            else:
                return value in all_timezones
        except Exception:
            return False

    def message(self):
        return "The :attribute must be a valid timezone."
