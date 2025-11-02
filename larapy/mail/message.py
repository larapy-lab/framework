from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from pathlib import Path
import mimetypes


class Message:

    def __init__(self):
        self._message = MIMEMultipart("alternative")
        self._attachments: List[MIMEBase] = []

    def set_from(self, email: str, name: Optional[str] = None) -> "Message":
        if name:
            self._message["From"] = f'"{name}" <{email}>'
        else:
            self._message["From"] = email
        return self

    def set_to(self, recipients: List[str]) -> "Message":
        self._message["To"] = ", ".join(recipients)
        return self

    def set_cc(self, recipients: List[str]) -> "Message":
        if recipients:
            self._message["Cc"] = ", ".join(recipients)
        return self

    def set_bcc(self, recipients: List[str]) -> "Message":
        return self

    def set_reply_to(self, recipients: List[str]) -> "Message":
        if recipients:
            self._message["Reply-To"] = ", ".join(recipients)
        return self

    def set_subject(self, subject: str) -> "Message":
        self._message["Subject"] = subject
        return self

    def set_html_body(self, html: str) -> "Message":
        html_part = MIMEText(html, "html", "utf-8")
        self._message.attach(html_part)
        return self

    def set_text_body(self, text: str) -> "Message":
        text_part = MIMEText(text, "plain", "utf-8")
        self._message.attach(text_part)
        return self

    def attach_file(
        self, path: str, name: Optional[str] = None, mime: Optional[str] = None
    ) -> "Message":
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Attachment file not found: {path}")

        if mime is None:
            mime, _ = mimetypes.guess_type(str(file_path))
            if mime is None:
                mime = "application/octet-stream"

        main_type, sub_type = mime.split("/", 1)

        with open(file_path, "rb") as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)

        filename = name if name else file_path.name
        attachment.add_header("Content-Disposition", f'attachment; filename="{filename}"')

        self._attachments.append(attachment)
        return self

    def attach_data(self, data: bytes, name: str, mime: Optional[str] = None) -> "Message":
        if mime is None:
            mime = "application/octet-stream"

        main_type, sub_type = mime.split("/", 1)

        attachment = MIMEBase(main_type, sub_type)
        attachment.set_payload(data)
        encoders.encode_base64(attachment)

        attachment.add_header("Content-Disposition", f'attachment; filename="{name}"')

        self._attachments.append(attachment)
        return self

    def get_message(self) -> MIMEMultipart:
        for attachment in self._attachments:
            self._message.attach(attachment)

        return self._message

    def as_string(self) -> str:
        return self.get_message().as_string()
