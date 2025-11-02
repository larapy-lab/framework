from typing import Optional, List, Callable, Any


class MailMessage:
    def __init__(self):
        self.view_template = None
        self.view_data = {}
        self.markdown_template = None
        self.theme = "default"
        self.from_address = None
        self.reply_to_address = None
        self.cc_addresses = []
        self.bcc_addresses = []
        self.attachments = []
        self.raw_attachments = []
        self.priority = None
        self.callbacks = []

        self.subject_text = None
        self.greeting_text = None
        self.salutation_text = "Regards"
        self.intro_lines = []
        self.outro_lines = []
        self.action_text = None
        self.action_url = None
        self.action_color = None
        self.level = "info"
        self.mailer = None

    def from_email(self, address: str, name: Optional[str] = None):
        self.from_address = (address, name) if name else address
        return self

    def replyTo(self, address: str, name: Optional[str] = None):
        self.reply_to_address = (address, name) if name else address
        return self

    def cc(self, address: str, name: Optional[str] = None):
        self.cc_addresses.append((address, name) if name else address)
        return self

    def bcc(self, address: str, name: Optional[str] = None):
        self.bcc_addresses.append((address, name) if name else address)
        return self

    def attach(self, file_path: str, options: Optional[dict] = None):
        self.attachments.append({"file": file_path, "options": options or {}})
        return self

    def attach_data(self, data: bytes, name: str, options: Optional[dict] = None):
        self.raw_attachments.append({"data": data, "name": name, "options": options or {}})
        return self

    def priority_level(self, level: int):
        self.priority = level
        return self

    def subject(self, subject: str):
        self.subject_text = subject
        return self

    def greeting(self, greeting: str):
        self.greeting_text = greeting
        return self

    def salutation(self, salutation: str):
        self.salutation_text = salutation
        return self

    def line(self, line: str):
        self.intro_lines.append(line)
        return self

    def lines(self, lines: List[str]):
        self.intro_lines.extend(lines)
        return self

    def with_content(self, line: str):
        return self.line(line)

    def action(self, text: str, url: str, color: Optional[str] = None):
        self.action_text = text
        self.action_url = url
        if color:
            self.action_color = color
        return self

    def success(self):
        self.level = "success"
        return self

    def error(self):
        self.level = "error"
        return self

    def warning(self):
        self.level = "warning"
        return self

    def info(self):
        self.level = "info"
        return self

    def view(self, template: str, data: Optional[dict] = None):
        self.view_template = template
        self.view_data = data or {}
        return self

    def markdown(self, template: str, data: Optional[dict] = None):
        self.markdown_template = template
        self.view_data = data or {}
        return self

    def template(self, template: str):
        self.theme = template
        return self

    def with_swift_message(self, callback: Callable):
        self.callbacks.append(callback)
        return self

    def mailer_driver(self, mailer: str):
        self.mailer = mailer
        return self

    def to_dict(self) -> dict:
        return {
            "subject": self.subject_text,
            "greeting": self.greeting_text,
            "salutation": self.salutation_text,
            "intro_lines": self.intro_lines,
            "outro_lines": self.outro_lines,
            "action_text": self.action_text,
            "action_url": self.action_url,
            "action_color": self.action_color,
            "level": self.level,
            "view": self.view_template,
            "view_data": self.view_data,
            "markdown": self.markdown_template,
            "theme": self.theme,
            "from": self.from_address,
            "reply_to": self.reply_to_address,
            "cc": self.cc_addresses,
            "bcc": self.bcc_addresses,
            "attachments": self.attachments,
            "raw_attachments": self.raw_attachments,
            "priority": self.priority,
            "mailer": self.mailer,
        }
