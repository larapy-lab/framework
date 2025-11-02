class NotificationSending:
    def __init__(self, notifiable, notification, channel):
        self.notifiable = notifiable
        self.notification = notification
        self.channel = channel


class NotificationSent:
    def __init__(self, notifiable, notification, channel, response=None):
        self.notifiable = notifiable
        self.notification = notification
        self.channel = channel
        self.response = response


class NotificationFailed:
    def __init__(self, notifiable, notification, channel, exception):
        self.notifiable = notifiable
        self.notification = notification
        self.channel = channel
        self.exception = exception
