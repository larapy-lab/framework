import json
from .formatter import Formatter
from ..log_record import LogRecord


class JsonFormatter(Formatter):
    def __init__(self, pretty: bool = False):
        self.pretty = pretty

    def format(self, record: LogRecord) -> str:
        data = record.to_dict()

        if self.pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
