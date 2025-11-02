from typing import List
from larapy.broadcasting.broadcaster import Broadcaster


class NullBroadcaster(Broadcaster):
    def broadcast(self, channels: List[str], event: str, payload: dict):
        pass
