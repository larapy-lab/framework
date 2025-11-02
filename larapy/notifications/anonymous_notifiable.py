class AnonymousNotifiable:
    def __init__(self):
        self.routes = {}

    def route(self, channel: str, route):
        self.routes[channel] = route
        return self

    def route_notification_for(self, channel: str, notification=None):
        return self.routes.get(channel)
