from abc import ABC, abstractmethod


class Migration(ABC):

    def __init__(self, connection):
        self._connection = connection

    @abstractmethod
    def up(self):
        pass

    @abstractmethod
    def down(self):
        pass
