from abc import ABC, abstractmethod


class Seeder(ABC):

    def __init__(self, connection):
        self._connection = connection

    @abstractmethod
    def run(self):
        pass
