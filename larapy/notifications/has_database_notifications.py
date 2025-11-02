import json
from datetime import datetime
from typing import Optional, List


class HasDatabaseNotifications:
    def notifications(self):
        if hasattr(self, "_notifications"):
            return DatabaseNotificationCollection(self._notifications)

        if not hasattr(self, "_notifications"):
            self._notifications = []

        return DatabaseNotificationCollection(self._notifications)

    def unread_notifications(self):
        all_notifications = self.notifications()
        return DatabaseNotificationCollection(
            [n for n in all_notifications.items if n.get("read_at") is None]
        )

    def read_notifications(self):
        all_notifications = self.notifications()
        return DatabaseNotificationCollection(
            [n for n in all_notifications.items if n.get("read_at") is not None]
        )

    def mark_as_read(self, notification_ids: Optional[List[str]] = None):
        notifications = self.notifications()

        if notification_ids:
            for notification in notifications.items:
                if notification.get("id") in notification_ids:
                    notification["read_at"] = datetime.now()
        else:
            for notification in notifications.items:
                notification["read_at"] = datetime.now()

    def mark_as_unread(self, notification_ids: Optional[List[str]] = None):
        notifications = self.notifications()

        if notification_ids:
            for notification in notifications.items:
                if notification.get("id") in notification_ids:
                    notification["read_at"] = None
        else:
            for notification in notifications.items:
                notification["read_at"] = None


class DatabaseNotificationCollection:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def count(self):
        return len(self.items)

    def first(self):
        return self.items[0] if self.items else None

    def find(self, notification_id: str):
        for item in self.items:
            if item.get("id") == notification_id:
                return item
        return None

    def where(self, key: str, value):
        return DatabaseNotificationCollection(
            [item for item in self.items if item.get(key) == value]
        )

    def pluck(self, key: str):
        return [item.get(key) for item in self.items]

    def create(self, data: dict):
        self.items.append(data)
        return data

    def mark_as_read(self):
        for item in self.items:
            item["read_at"] = datetime.now()
        return self

    def mark_as_unread(self):
        for item in self.items:
            item["read_at"] = None
        return self

    def delete(self):
        self.items.clear()
        return True
