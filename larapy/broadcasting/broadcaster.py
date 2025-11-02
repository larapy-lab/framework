from abc import ABC, abstractmethod
from typing import List


class Broadcaster(ABC):
    @abstractmethod
    def broadcast(self, channels: List[str], event: str, payload: dict):
        pass

    def format_channels(self, channels: List[str]) -> List[str]:
        formatted = []
        for channel in channels:
            if isinstance(channel, str):
                formatted.append(channel)
            else:
                formatted.append(str(channel))
        return formatted
