try:
    import requests
except ImportError:
    requests = None

from larapy.notifications.channels.channel import Channel


class SlackChannel(Channel):
    def __init__(self):
        self.http_client = requests

    def send(self, notifiable, notification):
        if not self.http_client:
            raise ImportError(
                "requests library is required for SlackChannel. Install it with: pip install requests"
            )

        if not hasattr(notification, "to_slack"):
            return

        message = notification.to_slack(notifiable)

        if not message:
            return

        webhook_url = notifiable.route_notification_for("slack", notification)

        if not webhook_url:
            return

        payload = message.to_dict() if hasattr(message, "to_dict") else message

        response = self.http_client.post(webhook_url, json=payload)

        if response.status_code != 200:
            raise Exception(f"Slack notification failed: {response.text}")

        return response
