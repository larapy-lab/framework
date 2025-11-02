from abc import ABC, abstractmethod
from typing import List


class ShouldBroadcast(ABC):
    @abstractmethod
    def broadcast_on(self) -> List[str]:
        pass

    def broadcast_as(self) -> str:
        return self.__class__.__name__

    def broadcast_with(self) -> dict:
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

    def broadcast_when(self) -> bool:
        return True
