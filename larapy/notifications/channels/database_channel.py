import json
import uuid
from datetime import datetime
from larapy.notifications.channels.channel import Channel


class DatabaseChannel(Channel):
    def __init__(self, database=None):
        self.database = database

    def send(self, notifiable, notification):
        data = self.get_data(notifiable, notification)

        notification_id = str(uuid.uuid4())
        notification_data = {
            "id": notification_id,
            "type": self.get_notification_type(notification),
            "notifiable_type": self.get_notifiable_type(notifiable),
            "notifiable_id": self.get_notifiable_id(notifiable),
            "data": json.dumps(data),
            "read_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        if hasattr(notifiable, "notifications"):
            notifications_relation = notifiable.notifications()
            if hasattr(notifications_relation, "create"):
                return notifications_relation.create(notification_data)

        if self.database:
            self.database.table("notifications").insert(notification_data)
            return notification_data

        if hasattr(notifiable, "_notifications"):
            notifiable._notifications.append(notification_data)
        else:
            notifiable._notifications = [notification_data]

        return notification_data

    def get_data(self, notifiable, notification):
        if hasattr(notification, "to_database"):
            return notification.to_database(notifiable)

        if hasattr(notification, "to_array"):
            return notification.to_array(notifiable)

        return {}

    def get_notification_type(self, notification):
        return notification.__class__.__name__

    def get_notifiable_type(self, notifiable):
        return notifiable.__class__.__name__

    def get_notifiable_id(self, notifiable):
        if hasattr(notifiable, "id"):
            return notifiable.id
        if hasattr(notifiable, "get_key"):
            return notifiable.get_key()
        return None
