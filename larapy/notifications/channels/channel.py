from abc import ABC, abstractmethod
from typing import Any, Optional


class Channel(ABC):
    @abstractmethod
    def send(self, notifiable, notification) -> Optional[Any]:
        pass
