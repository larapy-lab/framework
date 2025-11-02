from larapy.support import ServiceProvider


class BroadcastServiceProvider(ServiceProvider):
    def register(self):
        self.app.singleton("broadcast", lambda c: self._create_broadcast_manager(c))
        self.app.singleton("broadcast.channel", lambda c: self._create_channel_router())

    def _create_broadcast_manager(self, container):
        from larapy.broadcasting.broadcast_manager import BroadcastManager

        return BroadcastManager(container)

    def _create_channel_router(self):
        from larapy.broadcasting.channel_router import ChannelRouter

        return ChannelRouter()

    def boot(self):
        pass
