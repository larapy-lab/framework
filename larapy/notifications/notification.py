from typing import List, Any, Optional
from abc import ABC, abstractmethod


class Notification(ABC):
    def __init__(self):
        self.id = None
        self.locale = None
        self.connection = None
        self.queue = None
        self.delay = None

    @abstractmethod
    def via(self, notifiable) -> List[str]:
        pass

    def to_mail(self, notifiable):
        raise NotImplementedError(f"{self.__class__.__name__} does not implement to_mail method")

    def to_database(self, notifiable) -> dict:
        return self.to_array(notifiable)

    def to_array(self, notifiable) -> dict:
        return {}

    def to_broadcast(self, notifiable):
        return self.to_array(notifiable)

    def to_slack(self, notifiable):
        raise NotImplementedError(f"{self.__class__.__name__} does not implement to_slack method")

    def via_connections(self) -> dict:
        return {}

    def via_queues(self) -> dict:
        return {}

    def should_send(self, notifiable, channel: str) -> bool:
        return True
