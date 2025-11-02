from typing import Optional, Dict, Any, List, TYPE_CHECKING
from .mailable import Mailable, Address
from .message import Message
from .transports import Transport, SmtpTransport

if TYPE_CHECKING:
    from ..views.engine import Engine


class Mailer:

    def __init__(
        self,
        transport: Transport,
        from_address: Optional[Address] = None,
        view_engine: Optional["Engine"] = None,
    ):
        self.transport = transport
        self.from_address = from_address
        self.view_engine = view_engine

    def send(self, mailable: Mailable) -> bool:
        mailable.build()

        if not mailable.get_from() and self.from_address:
            mailable.from_address(self.from_address)

        self._render_views(mailable)

        message = self._build_message(mailable)

        recipients = self._get_all_recipients(mailable)

        if not recipients:
            raise ValueError("No recipients specified for email")

        return self.transport.send(message, recipients)

    def _render_views(self, mailable: Mailable) -> None:
        if not self.view_engine:
            return

        view = mailable.get_view()
        if view and not mailable.get_html():
            html = self.view_engine.render(view, mailable.get_view_data())
            mailable.html(html)

        text_view = mailable.get_text_view()
        if text_view and not mailable.get_text():
            text = self.view_engine.render(text_view, mailable.get_view_data())
            mailable.text_content(text)

    def _build_message(self, mailable: Mailable) -> Message:
        message = Message()

        from_addr = mailable.get_from()
        if from_addr:
            message.set_from(from_addr.email, from_addr.name)

        to_addresses = [addr.email for addr in mailable.get_to()]
        if to_addresses:
            message.set_to(to_addresses)

        cc_addresses = [addr.email for addr in mailable.get_cc()]
        if cc_addresses:
            message.set_cc(cc_addresses)

        bcc_addresses = [addr.email for addr in mailable.get_bcc()]
        if bcc_addresses:
            message.set_bcc(bcc_addresses)

        reply_to_addresses = [addr.email for addr in mailable.get_reply_to()]
        if reply_to_addresses:
            message.set_reply_to(reply_to_addresses)

        subject = mailable.get_subject()
        if subject:
            message.set_subject(subject)

        text_content = mailable.get_text()
        if text_content:
            message.set_text_body(text_content)

        html_content = mailable.get_html()
        if html_content:
            message.set_html_body(html_content)

        for attachment in mailable.get_attachments():
            message.attach_file(attachment["path"], attachment.get("name"), attachment.get("mime"))

        for attachment in mailable.get_raw_attachments():
            message.attach_data(attachment["data"], attachment["name"], attachment.get("mime"))

        return message

    def _get_all_recipients(self, mailable: Mailable) -> List[str]:
        recipients = []

        recipients.extend([addr.email for addr in mailable.get_to()])
        recipients.extend([addr.email for addr in mailable.get_cc()])
        recipients.extend([addr.email for addr in mailable.get_bcc()])

        return list(set(recipients))
