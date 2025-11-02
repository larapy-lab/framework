import smtplib
from typing import Dict, Any, List
from ..message import Message
from .transport import Transport


class SmtpTransport(Transport):

    def __init__(self, config: Dict[str, Any]):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.encryption = config.get("encryption", "tls")
        self.timeout = config.get("timeout", 30)

    def send(self, message: Message, recipients: List[str]) -> bool:
        try:
            if self.encryption == "ssl":
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                smtp = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

                if self.encryption == "tls":
                    smtp.starttls()

            if self.username and self.password:
                smtp.login(self.username, self.password)

            smtp.send_message(message.get_message())
            smtp.quit()

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to send email: {str(e)}")
