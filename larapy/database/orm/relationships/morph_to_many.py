from typing import Optional, List, Dict, Any
from larapy.database.orm.relationships.morph_relation import MorphRelation
from larapy.database.orm.relationships.belongs_to_many import Pivot


class MorphToMany(MorphRelation):

    def __init__(
        self,
        query,
        parent,
        related_class,
        morph_name: str,
        table: Optional[str] = None,
        foreign_pivot_key: Optional[str] = None,
        related_pivot_key: Optional[str] = None,
        parent_key: Optional[str] = None,
        related_key: Optional[str] = None,
        inverse: bool = False,
    ):
        super().__init__(query, parent, related_class, morph_name)

        self._table = table
        self._foreign_pivot_key = foreign_pivot_key
        self._related_pivot_key = related_pivot_key
        self._parent_key = parent_key
        self._related_key = related_key
        self._inverse = inverse
        self._pivot_columns = []
        self._pivot_created_at = None
        self._pivot_updated_at = None

    def add_constraints(self):
        if self._constraints_applied:
            return

        if self._parent._exists:
            self._set_join()
            self._set_where()

        self._constraints_applied = True

    def add_eager_constraints(self, models: List):
        """Set constraints for eager loading MorphToMany relationship."""
        parent_key = self._get_parent_key()
        keys = [
            model.get_attribute(parent_key)
            for model in models
            if model.get_attribute(parent_key) is not None
        ]

        if keys:
            # Set up the join first (includes SELECT columns and JOIN clause)
            self._set_join()
            
            table = self._get_table()
            
            # For MorphToMany (not inverse): filter where taggable_id IN (post IDs)
            # For MorphedByMany (inverse): filter where tag_id IN (tag IDs)
            if not self._inverse:
                foreign_pivot_key = self._get_foreign_pivot_key()
                self._query.where_in(f"{table}.{foreign_pivot_key}", keys)
                self._query.where(f"{table}.{self._morph_type}", self.get_morph_class())
            else:
                # For inverse (MorphedByMany), use related_pivot_key (tag_id)
                related_pivot_key = self._get_related_pivot_key()
                self._query.where_in(f"{table}.{related_pivot_key}", keys)
                
                # Filter by related class morph_type
                from larapy.database.orm.morph_map import MorphMap
                related_class_name = f"{self._related_class.__module__}.{self._related_class.__name__}"
                morph_class_alias = MorphMap.get_morph_alias(related_class_name)
                if morph_class_alias is None:
                    morph_class_alias = related_class_name
                self._query.where(f"{table}.{self._morph_type}", morph_class_alias)

    def match(self, models: List, results: List, relation: str) -> List:
        from larapy.database.orm.collection import Collection

        dictionary = self._build_dictionary_collection(results)

        for model in models:
            key = model.get_attribute(self._get_parent_key())
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
            model = self._hydrate_model(row)
            model = self._hydrate_pivot(model, row)
            models.append(model)

        return Collection(models)

    def get_eager(self):
        results = self._query.get()
        models = []
        for row in results:
            model = self._hydrate_model(row)
            model = self._hydrate_pivot(model, row)
            models.append(model)
        return models

    def _set_join(self):
        pivot_table = self._get_table()
        related_table = self._related_class().get_table()
        related_key = self._get_related_key()
        related_pivot_key = self._get_related_pivot_key()

        select_columns = [f"{related_table}.*"]
        select_columns.append(
            f"{pivot_table}.{self._get_foreign_pivot_key()} as {pivot_table}_{self._get_foreign_pivot_key()}"
        )
        select_columns.append(
            f"{pivot_table}.{related_pivot_key} as {pivot_table}_{related_pivot_key}"
        )
        select_columns.append(
            f"{pivot_table}.{self._morph_type} as {pivot_table}_{self._morph_type}"
        )

        for column in self._pivot_columns:
            select_columns.append(f"{pivot_table}.{column} as {pivot_table}_{column}")

        if self._pivot_created_at:
            select_columns.append(
                f"{pivot_table}.{self._pivot_created_at} as {pivot_table}_created_at"
            )
        if self._pivot_updated_at:
            select_columns.append(
                f"{pivot_table}.{self._pivot_updated_at} as {pivot_table}_updated_at"
            )

        self._query.select(*select_columns)
        self._query.join(
            pivot_table, f"{related_table}.{related_key}", "=", f"{pivot_table}.{related_pivot_key}"
        )

    def _set_where(self):
        parent_key = self._get_parent_key()
        parent_id = self._parent.get_attribute(parent_key)

        if parent_id is not None:
            table = self._get_table()
            
            if not self._inverse:
                self._query.where(f"{table}.{self._morph_type}", self.get_morph_class())
            
            foreign_pivot_key = self._get_foreign_pivot_key()
            self._query.where(f"{table}.{foreign_pivot_key}", parent_id)

    def _hydrate_pivot(self, model, row: Dict):
        table = self._get_table()
        pivot_attributes = {}

        pivot_attributes[self._get_foreign_pivot_key()] = row.get(
            f"{table}_{self._get_foreign_pivot_key()}"
        )
        pivot_attributes[self._get_related_pivot_key()] = row.get(
            f"{table}_{self._get_related_pivot_key()}"
        )
        pivot_attributes[self._morph_type] = row.get(f"{table}_{self._morph_type}")

        for column in self._pivot_columns:
            pivot_attributes[column] = row.get(f"{table}_{column}")

        if self._pivot_created_at:
            pivot_attributes["created_at"] = row.get(f"{table}_created_at")
        if self._pivot_updated_at:
            pivot_attributes["updated_at"] = row.get(f"{table}_updated_at")

        model.pivot = Pivot(pivot_attributes, table)
        return model

    def _build_dictionary_collection(self, results: List):
        from larapy.database.orm.collection import Collection

        dictionary = {}
        foreign_pivot_key = self._get_foreign_pivot_key()

        for result in results:
            pivot_key = (
                getattr(result.pivot, foreign_pivot_key, None) if hasattr(result, "pivot") else None
            )
            if pivot_key:
                if pivot_key not in dictionary:
                    dictionary[pivot_key] = []
                dictionary[pivot_key].append(result)

        return {key: Collection(models) for key, models in dictionary.items()}

    def with_pivot(self, *columns):
        self._pivot_columns.extend(columns)
        return self

    def with_timestamps(self, created_at: str = "created_at", updated_at: str = "updated_at"):
        self._pivot_created_at = created_at
        self._pivot_updated_at = updated_at
        return self

    def attach(self, ids, attributes: Optional[Dict] = None):
        if not isinstance(ids, list):
            ids = [ids]

        connection = self._parent.get_connection()
        table = self._get_table()
        foreign_pivot_key = self._get_foreign_pivot_key()
        related_pivot_key = self._get_related_pivot_key()
        parent_id = self._parent.get_attribute(self._get_parent_key())

        for id_value in ids:
            record = {
                foreign_pivot_key: parent_id,
                related_pivot_key: id_value,
                self._morph_type: self.get_morph_class(),
            }

            if attributes:
                record.update(attributes)

            if self._pivot_created_at:
                from datetime import datetime
                record["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self._pivot_updated_at:
                from datetime import datetime
                record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            connection.table(table).insert(record)

    def detach(self, ids=None):
        connection = self._parent.get_connection()
        table = self._get_table()
        foreign_pivot_key = self._get_foreign_pivot_key()
        parent_id = self._parent.get_attribute(self._get_parent_key())

        query = connection.table(table).where(foreign_pivot_key, parent_id)
        
        if not self._inverse:
            query.where(self._morph_type, self.get_morph_class())

        if ids is not None:
            if not isinstance(ids, list):
                ids = [ids]
            related_pivot_key = self._get_related_pivot_key()
            query.where_in(related_pivot_key, ids)

        return query.delete()

    def sync(self, ids, detaching: bool = True):
        if not isinstance(ids, list):
            ids = [ids]

        changes = {"attached": [], "detached": [], "updated": []}

        current = self.get_results().pluck(self._get_related_key())
        current_ids = [int(id) for id in current]

        records_to_attach = [id for id in ids if id not in current_ids]

        if detaching:
            records_to_detach = [id for id in current_ids if id not in ids]
            if records_to_detach:
                self.detach(records_to_detach)
                changes["detached"] = records_to_detach

        if records_to_attach:
            self.attach(records_to_attach)
            changes["attached"] = records_to_attach

        return changes

    def toggle(self, ids):
        if not isinstance(ids, list):
            ids = [ids]

        changes = {"attached": [], "detached": []}

        current = self.get_results().pluck(self._get_related_key())
        current_ids = [int(id) for id in current]

        for id in ids:
            if id in current_ids:
                self.detach(id)
                changes["detached"].append(id)
            else:
                self.attach(id)
                changes["attached"].append(id)

        return changes

    def update_existing_pivot(self, id, attributes: Dict):
        parent_key = self._get_parent_key()
        parent_id = self._parent.get_attribute(parent_key)

        foreign_pivot_key = self._get_foreign_pivot_key()
        related_pivot_key = self._get_related_pivot_key()
        table = self._get_table()

        connection = self._parent.get_connection()
        query_builder = connection.table(table)

        if self._pivot_updated_at:
            from datetime import datetime
            attributes[self._pivot_updated_at] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = query_builder.where(foreign_pivot_key, parent_id).where(
            related_pivot_key, id
        )
        
        if not self._inverse:
            query.where(self._morph_type, self.get_morph_class())

        updated = query.update(attributes)

        return updated

    def _get_table(self) -> str:
        if self._table:
            return self._table

        return f"{self._morph_name}s"

    def _get_foreign_pivot_key(self) -> str:
        if self._foreign_pivot_key:
            return self._foreign_pivot_key

        return self._morph_id

    def _get_related_pivot_key(self) -> str:
        if self._related_pivot_key:
            return self._related_pivot_key

        related_instance = self._related_class()
        return f'{related_instance.get_table().rstrip("s")}_id'

    def _get_parent_key(self) -> str:
        if self._parent_key:
            return self._parent_key

        return self._parent.get_key_name()

    def _get_related_key(self) -> str:
        if self._related_key:
            return self._related_key

        related_instance = self._related_class()
        return related_instance.get_key_name()
