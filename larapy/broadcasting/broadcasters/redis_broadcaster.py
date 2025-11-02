import json
from typing import List
from larapy.broadcasting.broadcaster import Broadcaster


class RedisBroadcaster(Broadcaster):
    def __init__(self, redis_client, connection: str):
        self.redis = redis_client
        self.connection = connection

    def broadcast(self, channels: List[str], event: str, payload: dict):
        formatted_channels = self.format_channels(channels)

        message = json.dumps({"event": event, "data": payload})

        for channel in formatted_channels:
            self.redis.publish(channel, message)

        return True
