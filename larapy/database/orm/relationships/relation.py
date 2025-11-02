from abc import ABC, abstractmethod
from typing import Any, Optional, Type, List, Dict


class Relation(ABC):

    def __init__(
        self,
        query,
        parent,
        related_class: Type,
        foreign_key: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        self._query = query
        self._parent = parent
        self._related_class = related_class
        self._foreign_key = foreign_key
        self._local_key = local_key
        self._constraints_applied = False

    @abstractmethod
    def add_constraints(self):
        pass

    @abstractmethod
    def add_eager_constraints(self, models: List):
        pass

    @abstractmethod
    def match(self, models: List, results: List, relation: str) -> List:
        pass

    @abstractmethod
    def get_results(self):
        pass

    def get_eager(self):
        return self.get()

    def get(self):
        return self.get_results()

    def get_query(self):
        return self._query

    def get_parent(self):
        return self._parent

    def get_related(self):
        return self._related_class

    def get_foreign_key(self) -> str:
        if self._foreign_key:
            return self._foreign_key

        return self._guess_foreign_key()

    def _guess_foreign_key(self) -> str:
        parent_name = self._parent.__class__.__name__.lower()
        return f"{parent_name}_id"

    def get_local_key(self) -> str:
        if self._local_key:
            return self._local_key

        return self._parent.get_key_name()

    def _hydrate_model(self, attributes):
        related_instance = self._related_class(connection=self._parent.get_connection())
        related_instance._attributes = attributes.copy()
        related_instance._original = attributes.copy()
        related_instance._exists = True
        related_instance._was_recently_created = False

        return related_instance

    def _build_dictionary(self, results: List) -> Dict:
        return {self._get_dictionary_key(result): result for result in results}

    def _get_dictionary_key(self, result):
        return result.get_attribute(self.get_foreign_key())

    def where(self, *args, **kwargs):
        self._query.where(*args, **kwargs)
        return self

    def order_by(self, column: str, direction: str = "asc"):
        self._query.order_by(column, direction)
        return self
