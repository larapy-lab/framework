from typing import Optional
from .formatter import Formatter
from ..log_record import LogRecord


class LineFormatter(Formatter):
    def __init__(self, format_string: Optional[str] = None, date_format: str = "%Y-%m-%d %H:%M:%S"):
        self.format_string = format_string or "[{datetime}] {channel}.{level}: {message} {context}"
        self.date_format = date_format

    def format(self, record: LogRecord) -> str:
        formatted_datetime = record.datetime.strftime(self.date_format)
        context_str = self._format_context(record.context)

        message = self.format_string.format(
            datetime=formatted_datetime,
            channel=record.channel,
            level=record.level.to_name().upper(),
            message=record.message,
            context=context_str,
        )

        if record.exception:
            message += "\n" + self._format_exception(record.exception)

        return message

    def _format_context(self, context: dict) -> str:
        if not context:
            return ""

        items = [f"{k}={v}" for k, v in context.items()]
        return "{" + ", ".join(items) + "}"

    def _format_exception(self, exception: Exception) -> str:
        import traceback

        return "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )
