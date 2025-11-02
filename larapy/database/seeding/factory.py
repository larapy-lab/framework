from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
from faker import Faker


class Factory(ABC):

    def __init__(self, connection, faker: Optional[Faker] = None):
        self._connection = connection
        self._faker = faker or Faker()
        self._count = 1
        self._state_callbacks = []

    @abstractmethod
    def definition(self) -> Dict[str, Any]:
        pass

    def count(self, amount: int):
        instance = self.__class__(self._connection, self._faker)
        instance._count = amount
        instance._state_callbacks = self._state_callbacks.copy()
        return instance

    def state(self, callback: Callable[[Dict[str, Any]], Dict[str, Any]]):
        instance = self.__class__(self._connection, self._faker)
        instance._count = self._count
        instance._state_callbacks = self._state_callbacks.copy()
        instance._state_callbacks.append(callback)
        return instance

    def make(self, attributes: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        attributes = attributes or {}
        instances = []

        for _ in range(self._count):
            instance = self.definition()

            for callback in self._state_callbacks:
                instance = {**instance, **callback(instance)}

            instance = {**instance, **attributes}
            instances.append(instance)

        if self._count == 1:
            return instances[0]

        return instances

    def create(self, attributes: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        instances = self.make(attributes)

        if isinstance(instances, dict):
            instances = [instances]

        table_name = self._get_table_name()

        for instance in instances:
            self._connection.table(table_name).insert(instance)

        if self._count == 1:
            return instances[0]

        return instances

    def _get_table_name(self) -> str:
        class_name = self.__class__.__name__

        if class_name.endswith("Factory"):
            class_name = class_name[:-7]

        parts = []
        current = ""

        for char in class_name:
            if char.isupper() and current:
                parts.append(current.lower())
                current = char
            else:
                current += char

        if current:
            parts.append(current.lower())

        return "_".join(parts) + "s"

    def raw(self, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.make(attributes)
