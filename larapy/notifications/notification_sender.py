from typing import List, Optional
from larapy.notifications.events import NotificationSending, NotificationSent, NotificationFailed


class NotificationSender:
    def __init__(self, manager, events=None):
        self.manager = manager
        self.events = events
        self.locale = None

    def send(self, notifiables, notification):
        if not isinstance(notifiables, list):
            notifiables = [notifiables]

        for notifiable in notifiables:
            self.send_to_notifiable(notifiable, notification)

    def send_now(self, notifiables, notification, channels: Optional[List[str]] = None):
        if not isinstance(notifiables, list):
            notifiables = [notifiables]

        for notifiable in notifiables:
            self.send_to_notifiable(notifiable, notification, channels)

    def send_to_notifiable(self, notifiable, notification, channels: Optional[List[str]] = None):
        original_locale = None
        if self.locale:
            original_locale = self.get_notification_locale(notification)
            notification.locale = self.locale

        try:
            notification_channels = channels or notification.via(notifiable)

            for channel in notification_channels:
                if not notification.should_send(notifiable, channel):
                    continue

                self.send_through_channel(notifiable, notification, channel)

        finally:
            if self.locale and original_locale is not None:
                notification.locale = original_locale

    def send_through_channel(self, notifiable, notification, channel: str):
        try:
            if self.events:
                self.events.dispatch(NotificationSending(notifiable, notification, channel))

            response = self.manager.driver(channel).send(notifiable, notification)

            if self.events:
                self.events.dispatch(NotificationSent(notifiable, notification, channel, response))

            return response

        except Exception as e:
            if self.events:
                self.events.dispatch(NotificationFailed(notifiable, notification, channel, e))
            raise

    def get_notification_locale(self, notification):
        return getattr(notification, "locale", None)

    def with_locale(self, locale: str):
        self.locale = locale
        return self
