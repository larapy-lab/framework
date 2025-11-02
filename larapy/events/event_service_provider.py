from larapy.support import ServiceProvider
from larapy.events import Dispatcher, set_event_dispatcher


class EventServiceProvider(ServiceProvider):
    def __init__(self, app):
        super().__init__(app)
        self.listen = {}
        self.subscribe = []

    def register(self):
        self.app.singleton("events", lambda app: Dispatcher(app))

    def boot(self):
        dispatcher = self.app.make("events")
        set_event_dispatcher(dispatcher)

        for event_name, listeners in self.listen.items():
            if not isinstance(listeners, list):
                listeners = [listeners]

            for listener in listeners:
                dispatcher.listen(event_name, listener)

        for subscriber in self.subscribe:
            dispatcher.subscribe(subscriber)

    def should_discover_events(self) -> bool:
        return True

    def discover_events_within(self):
        return []
