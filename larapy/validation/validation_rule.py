from abc import ABC, abstractmethod
from typing import Any, Optional


class ValidationRule(ABC):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._message: Optional[str] = None

    @abstractmethod
    def passes(self, attribute: str, value: Any, data: dict) -> bool:
        pass

    @abstractmethod
    def message(self) -> str:
        pass

    def setMessage(self, message: str) -> "ValidationRule":
        self._message = message
        return self

    def getMessage(self, attribute: str) -> str:
        if self._message:
            return self._message.replace(":attribute", attribute)
        return self.message().replace(":attribute", attribute)
