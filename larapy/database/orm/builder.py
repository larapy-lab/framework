from typing import Any, Dict, List, Optional, Type, Union


class Builder:

    def __init__(self, query, model_class: Type, connection):
        self._query = query
        self._model_class = model_class
        self._connection = connection
        self._eager_load = {}

    def find(self, id: Any) -> Optional[Any]:
        model = self._model_class()
        results = self._query.where(model.get_key_name(), id).get()

        if not results:
            return None

        return self._hydrate_model(results[0])

    def first(self) -> Optional[Any]:
        results = self._query.limit(1).get()

        if not results:
            return None

        return self._hydrate_model(results[0])

    def get(self) -> "Collection":
        results = self._query.get()

        models = []
        for row in results:
            models.append(self._hydrate_model(row))

        from larapy.database.orm.collection import Collection

        collection = Collection(models)

        if self._eager_load:
            collection = self._eager_load_relations(collection)

        return collection

    def all(self) -> "Collection":
        return self.get()

    def _hydrate_model(self, attributes: Dict[str, Any]) -> Any:
        model = self._model_class(connection=self._connection)
        model._attributes = attributes.copy()
        model._original = attributes.copy()
        model._exists = True
        model._was_recently_created = False

        return model

    def where(self, *args, **kwargs) -> "Builder":
        self._query.where(*args, **kwargs)
        return self

    def or_where(self, *args, **kwargs) -> "Builder":
        self._query.or_where(*args, **kwargs)
        return self

    def where_in(self, column: str, values: List[Any]) -> "Builder":
        self._query.where_in(column, values)
        return self

    def where_not_in(self, column: str, values: List[Any]) -> "Builder":
        self._query.where_not_in(column, values)
        return self

    def where_null(self, column: str) -> "Builder":
        self._query.where_null(column)
        return self

    def where_not_null(self, column: str) -> "Builder":
        self._query.where_not_null(column)
        return self

    def order_by(self, column: str, direction: str = "asc") -> "Builder":
        self._query.order_by(column, direction)
        return self

    def limit(self, value: int) -> "Builder":
        self._query.limit(value)
        return self

    def offset(self, value: int) -> "Builder":
        self._query.offset(value)
        return self

    def count(self) -> int:
        return self._query.count()

    def max(self, column: str) -> Any:
        return self._query.max(column)

    def min(self, column: str) -> Any:
        return self._query.min(column)

    def avg(self, column: str) -> Any:
        return self._query.avg(column)

    def sum(self, column: str) -> Any:
        return self._query.sum(column)

    def create(self, attributes: Dict[str, Any]) -> Any:
        model = self._model_class(attributes, self._connection)
        model.save()
        return model

    def update(self, attributes: Dict[str, Any]) -> int:
        return self._query.update(attributes)

    def delete(self) -> int:
        return self._query.delete()

    def with_(self, *relations) -> "Builder":
        if not relations:
            return self

        for relation in relations:
            if isinstance(relation, str):
                self._eager_load[relation] = lambda query: query
            elif isinstance(relation, dict):
                for rel_name, callback in relation.items():
                    self._eager_load[rel_name] = callback

        return self

    def _eager_load_relations(self, collection: "Collection") -> "Collection":
        for relation_name in self._eager_load.keys():
            collection = self._eager_load_relation(collection, relation_name)

        return collection

    def _eager_load_relation(self, collection: "Collection", relation: str) -> "Collection":
        if not collection or collection.is_empty():
            return collection

        nested_relations = self._parse_nested_relations(relation)
        base_relation = nested_relations["base"]
        nested = nested_relations["nested"]

        first_model = collection.first()
        if not first_model or not hasattr(first_model.__class__, base_relation):
            return collection

        relation_method = getattr(first_model.__class__, base_relation, None)
        if not relation_method or not callable(relation_method):
            return collection

        relation_instance = relation_method(first_model)

        # Special handling for MorphTo relationships
        from larapy.database.orm.relationships.morph_to import MorphTo
        if isinstance(relation_instance, MorphTo):
            # MorphTo needs special eager loading - group by type and load each type
            results_by_type = relation_instance.morph_with(collection.all())
            
            # Match results back to models
            for model in collection.all():
                morph_type = model.get_attribute(relation_instance._morph_type_field)
                morph_id = model.get_attribute(relation_instance._morph_id_field)
                
                if morph_type and morph_id and morph_type in results_by_type:
                    type_results = results_by_type[morph_type]
                    if morph_id in type_results:
                        model.set_relation(base_relation, type_results[morph_id])
                    else:
                        model.set_relation(base_relation, None)
                else:
                    model.set_relation(base_relation, None)
            
            return collection

        if not hasattr(relation_instance, "add_eager_constraints"):
            return collection

        relation_instance.add_eager_constraints(collection.all())

        if base_relation in self._eager_load:
            callback = self._eager_load[base_relation]
            if callable(callback):
                callback(relation_instance.get_query())

        results = relation_instance.get_eager()

        if hasattr(relation_instance, "match"):
            from larapy.database.orm.collection import Collection

            matched_models = relation_instance.match(collection.all(), results, base_relation)
            collection = Collection(matched_models)

        if nested and results:
            from larapy.database.orm.collection import Collection

            for model in collection.all():
                relation_value = model.get_relation(base_relation)
                if relation_value is not None:
                    if isinstance(relation_value, Collection):
                        for item in relation_value.all():
                            if hasattr(item, "load"):
                                item.load(nested)
                    elif hasattr(relation_value, "load"):
                        relation_value.load(nested)

        return collection

    def _parse_nested_relations(self, relation: str) -> dict:
        parts = relation.split(".", 1)
        return {"base": parts[0], "nested": parts[1] if len(parts) > 1 else None}

    def paginate(self, per_page: int = 15, page: int = 1) -> Dict[str, Any]:
        total = self.count()

        offset = (page - 1) * per_page
        items = self.offset(offset).limit(per_page).get()

        return {
            "data": items,
            "total": total,
            "per_page": per_page,
            "current_page": page,
            "last_page": (total + per_page - 1) // per_page if total > 0 else 1,
            "from": offset + 1 if total > 0 else None,
            "to": min(offset + per_page, total) if total > 0 else None,
        }

    def chunk(self, size: int, callback) -> None:
        page = 1

        while True:
            results = self.offset((page - 1) * size).limit(size).get()

            if not results:
                break

            if callback(results) is False:
                break

            page += 1

    def exists(self) -> bool:
        return self.count() > 0

    def doesnt_exist(self) -> bool:
        return not self.exists()

    def cursor(self) -> "LazyCollection":
        from larapy.support.lazy_collection import LazyCollection

        def generator():
            for row in self._query.get():
                yield self._hydrate_model(row)

        return LazyCollection(generator)

    def lazy(self, chunk_size: int = 1000) -> "LazyCollection":
        from larapy.support.lazy_collection import LazyCollection

        def generator():
            offset = 0
            while True:
                chunk = self._query.offset(offset).limit(chunk_size).get()
                if not chunk:
                    break
                for row in chunk:
                    yield self._hydrate_model(row)
                offset += chunk_size

        return LazyCollection(generator)
