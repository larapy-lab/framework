from typing import List, Optional
from larapy.broadcasting.broadcaster import Broadcaster


class LogBroadcaster(Broadcaster):
    def __init__(self, logger: Optional[object] = None):
        self.logger = logger

    def broadcast(self, channels: List[str], event: str, payload: dict):
        formatted_channels = self.format_channels(channels)

        message = (
            f"Broadcasting event '{event}' to channels {formatted_channels} with payload: {payload}"
        )

        if self.logger:
            self.logger.info(message)
        else:
            print(f"[BROADCAST] {message}")

        return True
