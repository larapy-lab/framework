from larapy.validation.validation_rule import ValidationRule
import socket


class ActiveUrlRule(ValidationRule):
    def __init__(self):
        super().__init__()

    def passes(self, attribute, value, data):
        if not isinstance(value, str):
            return False

        try:
            from urllib.parse import urlparse

            parsed = urlparse(value)
            hostname = parsed.hostname

            if not hostname:
                return False

            socket.gethostbyname(hostname)
            return True
        except (socket.gaierror, ValueError, AttributeError):
            return False

    def message(self):
        return "The :attribute is not a valid URL."
