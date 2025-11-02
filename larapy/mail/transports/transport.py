from abc import ABC, abstractmethod
from typing import List
from ..message import Message


class Transport(ABC):

    @abstractmethod
    def send(self, message: Message, recipients: List[str]) -> bool:
        pass
