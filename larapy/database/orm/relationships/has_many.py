from typing import List
from larapy.database.orm.relationships.relation import Relation


class HasMany(Relation):

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
        from larapy.database.orm.collection import Collection

        dictionary = self._build_dictionary_collection(results)

        for model in models:
            key = model.get_attribute(self.get_local_key())
            if key in dictionary:
                model.set_relation(relation, dictionary[key])
            else:
                model.set_relation(relation, Collection([]))

        return models

    def get_results(self):
        from larapy.database.orm.collection import Collection

        if not self._constraints_applied:
            self.add_constraints()

        results = self._query.get()

        models = []
        for row in results:
            models.append(self._hydrate_model(row))

        return Collection(models)

    def get_eager(self):
        results = self._query.get()
        models = []
        for row in results:
            models.append(self._hydrate_model(row))
        return models

    def _build_dictionary_collection(self, results: List):
        from larapy.database.orm.collection import Collection

        dictionary = {}
        foreign_key = self.get_foreign_key()

        for result in results:
            key = result.get_attribute(foreign_key)
            if key not in dictionary:
                dictionary[key] = []
            dictionary[key].append(result)

        return {key: Collection(models) for key, models in dictionary.items()}

    def create(self, attributes: dict):
        instance = self._related_class(attributes, self._parent.get_connection())

        foreign_key = self.get_foreign_key()
        local_key = self.get_local_key()
        instance.set_attribute(foreign_key, self._parent.get_attribute(local_key))

        instance.save()
        return instance

    def create_many(self, records: List[dict]):
        from larapy.database.orm.collection import Collection

        instances = []
        for attributes in records:
            instances.append(self.create(attributes))

        return Collection(instances)

    def save_many(self, models: List):
        foreign_key = self.get_foreign_key()
        local_key = self.get_local_key()

        for model in models:
            model.set_attribute(foreign_key, self._parent.get_attribute(local_key))
            model.save()

        return models

    def find(self, id):
        if not self._constraints_applied:
            self.add_constraints()

        related_instance = self._related_class()
        results = self._query.where(related_instance.get_key_name(), id).get()

        if not results:
            return None

        return self._hydrate_model(results[0])
