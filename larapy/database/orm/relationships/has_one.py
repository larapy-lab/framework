from typing import Optional, List
from larapy.database.orm.relationships.relation import Relation


class HasOne(Relation):

    def add_constraints(self):
        if self._constraints_applied:
            return

        if self._parent._exists:
            foreign_key = self.get_foreign_key()
            local_key = self.get_local_key()
            local_value = self._parent.get_attribute(local_key)

            if local_value is not None:
                self._query.where(foreign_key, local_value)

        self._constraints_applied = True

    def add_eager_constraints(self, models: List):
        foreign_key = self.get_foreign_key()
        local_key = self.get_local_key()

        keys = [
            model.get_attribute(local_key)
            for model in models
            if model.get_attribute(local_key) is not None
        ]

        if keys:
            self._query.where_in(foreign_key, keys)

    def match(self, models: List, results: List, relation: str) -> List:
        dictionary = self._build_dictionary(results)

        for model in models:
            key = model.get_attribute(self.get_local_key())
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

    def _build_dictionary(self, results: List):
        return {result.get_attribute(self.get_foreign_key()): result for result in results}

    def create(self, attributes: dict):
        instance = self._related_class(attributes, self._parent.get_connection())

        foreign_key = self.get_foreign_key()
        local_key = self.get_local_key()
        instance.set_attribute(foreign_key, self._parent.get_attribute(local_key))

        instance.save()
        return instance

    def save(self, model):
        foreign_key = self.get_foreign_key()
        local_key = self.get_local_key()
        model.set_attribute(foreign_key, self._parent.get_attribute(local_key))

        return model.save()
