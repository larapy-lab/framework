from typing import Optional, List


class Notifiable:
    def notify(self, notification):
        from larapy.notifications.notification_sender import NotificationSender

        if hasattr(self, "container"):
            notification_manager = self.container.make("notification")
            notification_manager.send([self], notification)
        else:
            sender = NotificationSender(None)
            sender.send([self], notification)

    def notify_now(self, notification, channels: Optional[List[str]] = None):
        from larapy.notifications.notification_sender import NotificationSender

        if hasattr(self, "container"):
            notification_manager = self.container.make("notification")
            notification_manager.send_now([self], notification, channels)
        else:
            sender = NotificationSender(None)
            sender.send_now([self], notification, channels)

    def route_notification_for(self, channel: str, notification=None):
        method = f"route_notification_for_{channel}"

        if hasattr(self, method):
            return getattr(self, method)(notification)

        if channel == "mail":
            if hasattr(self, "email"):
                return self.email
            elif hasattr(self, "mail"):
                return self.mail

        elif channel == "database":
            return self

        elif channel == "broadcast":
            return f"{self.__class__.__name__}.{self.id}"

        return None
