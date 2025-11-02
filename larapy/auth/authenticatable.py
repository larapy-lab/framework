from abc import ABC, abstractmethod
from typing import Optional


class Authenticatable(ABC):
    @abstractmethod
    def getAuthIdentifierName(self) -> str:
        pass

    @abstractmethod
    def getAuthIdentifier(self):
        pass

    @abstractmethod
    def getAuthPasswordName(self) -> str:
        pass

    @abstractmethod
    def getAuthPassword(self) -> str:
        pass

    @abstractmethod
    def getRememberToken(self) -> Optional[str]:
        pass

    @abstractmethod
    def setRememberToken(self, value: Optional[str]) -> None:
        pass

    @abstractmethod
    def getRememberTokenName(self) -> str:
        pass
