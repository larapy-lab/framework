from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import timedelta


class QueueInterface(ABC):

    @abstractmethod
    def push(
        self, job: str, data: Optional[Dict[str, Any]] = None, queue: Optional[str] = None
    ) -> Any:
        pass

    @abstractmethod
    def push_raw(
        self, payload: str, queue: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        pass

    @abstractmethod
    def later(
        self,
        delay: timedelta,
        job: str,
        data: Optional[Dict[str, Any]] = None,
        queue: Optional[str] = None,
    ) -> Any:
        pass

    @abstractmethod
    def pop(self, queue: Optional[str] = None) -> Optional[Any]:
        pass

    @abstractmethod
    def size(self, queue: Optional[str] = None) -> int:
        pass

    def get_connection_name(self) -> str:
        return self.connection_name

    def set_connection_name(self, name: str) -> "QueueInterface":
        self.connection_name = name
        return self
