from larapy.notifications.channels.channel import Channel


class BroadcastChannel(Channel):
    def __init__(self, events):
        self.events = events

    def send(self, notifiable, notification):
        event_data = self.get_data(notifiable, notification)

        channels = self.get_channels(notifiable, notification)

        for channel in channels:
            self.events.dispatch(f"broadcast.{channel}", event_data)

        return event_data

    def get_data(self, notifiable, notification):
        if hasattr(notification, "to_broadcast"):
            return notification.to_broadcast(notifiable)

        if hasattr(notification, "to_array"):
            return notification.to_array(notifiable)

        return {}

    def get_channels(self, notifiable, notification):
        channels = notifiable.route_notification_for("broadcast", notification)

        if isinstance(channels, str):
            return [channels]

        if isinstance(channels, list):
            return channels

        return [f"{notifiable.__class__.__name__}.{notifiable.id}"]
