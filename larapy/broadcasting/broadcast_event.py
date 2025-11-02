class BroadcastEvent:
    def __init__(self, event):
        self.event = event

    def dispatch(self, broadcaster):
        if not hasattr(self.event, "broadcast_when") or not self.event.broadcast_when():
            return False

        channels = self.event.broadcast_on()
        event_name = self.event.broadcast_as()
        payload = self.event.broadcast_with()

        broadcaster.broadcast(channels, event_name, payload)
        return True
