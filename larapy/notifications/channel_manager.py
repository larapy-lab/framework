from typing import Dict, Any, Optional


class ChannelManager:
    def __init__(self, container):
        self.container = container
        self.channels = {}
        self.custom_creators = {}

    def send(self, notifiables, notification):
        if not isinstance(notifiables, list):
            notifiables = [notifiables]

        for notifiable in notifiables:
            self.send_to_notifiable(notifiable, notification)

    def send_to_notifiable(self, notifiable, notification):
        channels = notification.via(notifiable)

        for channel in channels:
            if not notification.should_send(notifiable, channel):
                continue

            self.driver(channel).send(notifiable, notification)

    def driver(self, name: Optional[str] = None):
        return self.channel(name)

    def channel(self, name: Optional[str] = None):
        name = name or self.get_default_channel()

        if name not in self.channels:
            self.channels[name] = self.create_channel(name)

        return self.channels[name]

    def create_channel(self, name: str):
        if name in self.custom_creators:
            return self.custom_creators[name](self.container)

        method = f"create_{name}_channel"
        if hasattr(self, method):
            return getattr(self, method)()

        raise ValueError(f"Channel [{name}] not supported.")

    def create_mail_channel(self):
        from larapy.notifications.channels import MailChannel

        mailer = self.container.make("mail")
        return MailChannel(mailer)

    def create_database_channel(self):
        from larapy.notifications.channels import DatabaseChannel

        database = self.container.make("db") if self.container.bound("db") else None
        return DatabaseChannel(database)

    def create_slack_channel(self):
        from larapy.notifications.channels import SlackChannel

        return SlackChannel()

    def create_broadcast_channel(self):
        from larapy.notifications.channels import BroadcastChannel

        events = self.container.make("events")
        return BroadcastChannel(events)

    def extend(self, name: str, creator):
        self.custom_creators[name] = creator
        return self

    def get_default_channel(self):
        return "mail"

    def forget(self, name: str):
        if name in self.channels:
            del self.channels[name]
