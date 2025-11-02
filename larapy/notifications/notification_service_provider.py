from larapy.support import ServiceProvider
from larapy.notifications.channel_manager import ChannelManager
from larapy.notifications.notification_sender import NotificationSender


class NotificationServiceProvider(ServiceProvider):
    def register(self):
        self.app.singleton("notification.channel", lambda c: ChannelManager(c))

        self.app.singleton(
            "notification",
            lambda c: NotificationSender(
                c.make("notification.channel"), c.make("events") if c.bound("events") else None
            ),
        )

    def boot(self):
        pass
