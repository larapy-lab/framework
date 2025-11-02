from typing import List, Dict
from larapy.broadcasting.broadcaster import Broadcaster


class PusherBroadcaster(Broadcaster):
    def __init__(self, pusher_client, config: dict):
        self.pusher = pusher_client
        self.config = config

    def broadcast(self, channels: List[str], event: str, payload: dict):
        formatted_channels = self.format_channels(channels)

        socket_id = payload.get("socket_id")
        data = payload.copy()
        if "socket_id" in data:
            del data["socket_id"]

        return self.pusher.trigger(
            channels=formatted_channels, event_name=event, data=data, socket_id=socket_id
        )

    def format_channels(self, channels: List[str]) -> List[str]:
        formatted = []
        for channel in channels:
            if isinstance(channel, str):
                formatted.append(channel)
            else:
                formatted.append(str(channel))
        return formatted

    def auth(self, channel_name: str, socket_id: str, custom_data: Dict = None):
        if channel_name.startswith("presence-"):
            return self.pusher.authenticate(
                channel=channel_name, socket_id=socket_id, custom_data=custom_data
            )
        else:
            return self.pusher.authenticate(channel=channel_name, socket_id=socket_id)
