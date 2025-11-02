from typing import Optional, List, Dict
from larapy.database.orm.relationships.morph_to_many import MorphToMany


class MorphedByMany(MorphToMany):

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
    ):
        super().__init__(
            query,
            parent,
            related_class,
            morph_name,
            table,
            foreign_pivot_key,
            related_pivot_key,
            parent_key,
            related_key,
            inverse=True,
        )

    def _set_join(self):
        pivot_table = self._get_table()
        related_table = self._related_class().get_table()
        related_key = self._get_related_key()
        foreign_pivot_key = self._get_foreign_pivot_key()

        select_columns = [f"{related_table}.*"]
        select_columns.append(
            f"{pivot_table}.{foreign_pivot_key} as {pivot_table}_{foreign_pivot_key}"
        )
        select_columns.append(
            f"{pivot_table}.{self._get_related_pivot_key()} as {pivot_table}_{self._get_related_pivot_key()}"
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
            pivot_table, f"{related_table}.{related_key}", "=", f"{pivot_table}.{foreign_pivot_key}"
        )

    def _set_where(self):
        parent_key = self._get_parent_key()
        parent_id = self._parent.get_attribute(parent_key)

        if parent_id is not None:
            table = self._get_table()
            
            # For MorphedByMany, the morph_type should match the related class, not the parent
            from larapy.database.orm.morph_map import MorphMap
            related_class_name = f"{self._related_class.__module__}.{self._related_class.__name__}"
            morph_class_alias = MorphMap.get_morph_alias(related_class_name)
            if morph_class_alias is None:
                morph_class_alias = related_class_name
            
            self._query.where(f"{table}.{self._morph_type}", morph_class_alias)
            
            # For MorphedByMany, we filter by the tag_id (related_pivot_key), not the foreign_pivot_key
            related_pivot_key = self._get_related_pivot_key()
            self._query.where(f"{table}.{related_pivot_key}", parent_id)

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
                foreign_pivot_key: id_value,
                related_pivot_key: parent_id,
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
        related_pivot_key = self._get_related_pivot_key()
        parent_id = self._parent.get_attribute(self._get_parent_key())

        query = connection.table(table).where(related_pivot_key, parent_id)
        query.where(self._morph_type, self.get_morph_class())

        if ids is not None:
            if not isinstance(ids, list):
                ids = [ids]
            foreign_pivot_key = self._get_foreign_pivot_key()
            query.where_in(foreign_pivot_key, ids)

        return query.delete()

    def _get_foreign_pivot_key(self) -> str:
        if self._foreign_pivot_key:
            return self._foreign_pivot_key

        return self._morph_id

    def _get_related_pivot_key(self) -> str:
        if self._related_pivot_key:
            return self._related_pivot_key

        return f'{self._parent.get_table().rstrip("s")}_id'

    def _build_dictionary_collection(self, results: List):
        """
        Build dictionary collection for MorphedByMany.
        For inverse relationships, we group by related_pivot_key (e.g., tag_id) not foreign_pivot_key.
        """
        from larapy.database.orm.collection import Collection

        dictionary = {}
        related_pivot_key = self._get_related_pivot_key()

        for result in results:
            pivot_key = (
                getattr(result.pivot, related_pivot_key, None) if hasattr(result, "pivot") else None
            )
            if pivot_key:
                if pivot_key not in dictionary:
                    dictionary[pivot_key] = []
                dictionary[pivot_key].append(result)

        return {key: Collection(models) for key, models in dictionary.items()}
