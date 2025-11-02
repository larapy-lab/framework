from larapy.notifications.channels.channel import Channel


class MailChannel(Channel):
    def __init__(self, mailer):
        self.mailer = mailer

    def send(self, notifiable, notification):
        try:
            if not hasattr(notification, "to_mail"):
                return

            message = notification.to_mail(notifiable)
        except NotImplementedError:
            return

        if not message:
            return

        to_address = notifiable.route_notification_for("mail", notification)

        if not to_address:
            return

        if hasattr(message, "to_dict"):
            message_dict = message.to_dict()

            subject = message_dict.get("subject", "Notification")
            from_addr = message_dict.get("from")

            if hasattr(self.mailer, "send"):
                self.mailer.send(
                    to=to_address,
                    subject=subject,
                    body=self._build_body(message_dict),
                    from_email=from_addr,
                )
            else:
                mail_data = {"to": to_address, "subject": subject, "message": message_dict}
                return mail_data

        return message

    def _build_body(self, message_dict):
        lines = []

        if message_dict.get("greeting"):
            lines.append(message_dict["greeting"])
            lines.append("")

        lines.extend(message_dict.get("intro_lines", []))

        if message_dict.get("action_text") and message_dict.get("action_url"):
            lines.append("")
            lines.append(f"{message_dict['action_text']}: {message_dict['action_url']}")

        if message_dict.get("outro_lines"):
            lines.append("")
            lines.extend(message_dict["outro_lines"])

        if message_dict.get("salutation"):
            lines.append("")
            lines.append(message_dict["salutation"])

        return "\n".join(lines)
