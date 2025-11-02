from typing import Optional, List
from larapy.database.orm.relationships.relation import Relation


class BelongsTo(Relation):

    def add_constraints(self):
        if self._constraints_applied:
            return

        if self._parent._exists:
            foreign_key = self.get_foreign_key()
            owner_key = self.get_owner_key()
            foreign_value = self._parent.get_attribute(foreign_key)

            if foreign_value is not None:
                self._query.where(owner_key, foreign_value)

        self._constraints_applied = True

    def add_eager_constraints(self, models: List):
        foreign_key = self.get_foreign_key()
        owner_key = self.get_owner_key()

        keys = [
            model.get_attribute(foreign_key)
            for model in models
            if model.get_attribute(foreign_key) is not None
        ]

        if keys:
            self._query.where_in(owner_key, keys)

    def match(self, models: List, results: List, relation: str) -> List:
        dictionary = {result.get_attribute(self.get_owner_key()): result for result in results}

        for model in models:
            key = model.get_attribute(self.get_foreign_key())
            if key in dictionary:
                model.set_relation(relation, dictionary[key])
            else:
                model.set_relation(relation, None)

        return models

    def get_results(self):
        if not self._constraints_applied:
            self.add_constraints()

        results = self._query.limit(1).get()

        if not results:
            return None

        return self._hydrate_model(results[0])

    def get_eager(self):
        results = self._query.get()
        models = []
        for row in results:
            models.append(self._hydrate_model(row))
        return models

    def get_owner_key(self) -> str:
        if self._local_key:
            return self._local_key

        related_instance = self._related_class()
        return related_instance.get_key_name()

    def _guess_foreign_key(self) -> str:
        related_name = self._related_class.__name__.lower()
        return f"{related_name}_id"

    def associate(self, model):
        foreign_key = self.get_foreign_key()
        owner_key = self.get_owner_key()

        self._parent.set_attribute(foreign_key, model.get_attribute(owner_key))

        return self._parent

    def dissociate(self):
        foreign_key = self.get_foreign_key()
        self._parent.set_attribute(foreign_key, None)

        return self._parent
