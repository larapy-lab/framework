from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Set
import re
import json


class Model(ABC):

    _connection = None
    _table: Optional[str] = None
    _primary_key: str = "id"
    _incrementing: bool = True
    _key_type: str = "int"
    _timestamps: bool = True
    _date_format: str = "%Y-%m-%d %H:%M:%S"
    _fillable: List[str] = []
    _guarded: List[str] = ["*"]
    _casts: Dict[str, str] = {}
    _attributes: Dict[str, Any] = {}
    _original: Dict[str, Any] = {}
    _exists: bool = False
    _was_recently_created: bool = False

    # Serialization properties
    _hidden: List[str] = []
    _visible: List[str] = []
    _appends: List[str] = []
    _with_relations: List[str] = []
    _dateFormat: str = "iso8601"

    # Runtime visibility modifications
    _runtime_hidden: Set[str] = set()
    _runtime_visible: Set[str] = set()
    _runtime_appends: List[str] = []

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    def __init__(self, attributes: Optional[Dict[str, Any]] = None, connection=None):
        if connection:
            self._connection = connection

        self._attributes = {}
        self._original = {}
        self._relations = {}

        # Initialize runtime visibility modifications
        self._runtime_hidden = set()
        self._runtime_visible = set()
        self._runtime_appends = []

        if attributes:
            self.fill(attributes)

    def get_table(self) -> str:
        if self._table:
            return self._table

        class_name = self.__class__.__name__
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

        if snake_case.endswith("y"):
            return snake_case[:-1] + "ies"
        elif snake_case.endswith("s"):
            return snake_case + "es"
        else:
            return snake_case + "s"

    def get_key_name(self) -> str:
        return self._primary_key

    def get_key(self) -> Any:
        return self.get_attribute(self.get_key_name())

    def set_key(self, value: Any) -> None:
        self.set_attribute(self.get_key_name(), value)

    def get_connection(self):
        if not self._connection:
            from larapy.config import database
            from larapy.database.connection import Connection

            self._connection = Connection(**database.default_connection)
        return self._connection

    def fill(self, attributes: Dict[str, Any]) -> "Model":
        for key, value in attributes.items():
            if self.is_fillable(key):
                self.set_attribute(key, value)

        return self

    def is_fillable(self, key: str) -> bool:
        if self._fillable and key in self._fillable:
            return True

        if self._guarded == ["*"]:
            return False

        if key in self._guarded:
            return False

        return True

    def get_fillable(self) -> List[str]:
        return self._fillable

    def get_guarded(self) -> List[str]:
        return self._guarded

    def get_attribute(self, key: str) -> Any:
        if key in self._attributes:
            value = self._attributes[key]

            if key in self._casts:
                return self.cast_attribute(key, value)

            return value

        return None

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def cast_attribute(self, key: str, value: Any) -> Any:
        cast_type = self._casts.get(key)

        if not cast_type or value is None:
            return value

        if cast_type == "int":
            return int(value)
        elif cast_type == "float":
            return float(value)
        elif cast_type == "str":
            return str(value)
        elif cast_type == "bool":
            return bool(value)
        elif cast_type == "datetime":
            if isinstance(value, str):
                return datetime.strptime(value, self._date_format)
            return value

        return value
    
    def _serialize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        serialized = attributes.copy()
        
        for key, value in serialized.items():
            cast_type = self._casts.get(key)
            
            if cast_type == "json" and value is not None:
                if not isinstance(value, str):
                    import json
                    serialized[key] = json.dumps(value)
        
        return serialized

    def get_attributes(self) -> Dict[str, Any]:
        return self._attributes.copy()

    def get_original(self, key: Optional[str] = None) -> Any:
        if key:
            return self._original.get(key)
        return self._original.copy()

    def is_dirty(self, attributes: Optional[List[str]] = None) -> bool:
        if attributes:
            for attr in attributes:
                if self._attributes.get(attr) != self._original.get(attr):
                    return True
            return False

        return self._attributes != self._original

    def is_clean(self, attributes: Optional[List[str]] = None) -> bool:
        return not self.is_dirty(attributes)

    def was_changed(self, attributes: Optional[List[str]] = None) -> bool:
        if not self._exists:
            return False

        if attributes:
            for attr in attributes:
                if attr in self.get_changes():
                    return True
            return False

        return len(self.get_changes()) > 0

    def get_changes(self) -> Dict[str, Any]:
        changes = {}
        for key, value in self._attributes.items():
            if key not in self._original or self._original[key] != value:
                changes[key] = value
        return changes

    def sync_original(self) -> "Model":
        self._original = self._attributes.copy()
        return self

    def save(self) -> bool:
        if self._exists:
            return self._perform_update()
        else:
            return self._perform_insert()

    def _perform_insert(self) -> bool:
        if self._timestamps:
            self._update_timestamps()

        attributes = self._attributes.copy()

        if self._incrementing:
            attributes.pop(self.get_key_name(), None)
        
        attributes = self._serialize_attributes(attributes)

        connection = self.get_connection()
        query = connection.table(self.get_table())

        inserted_id = query.insert_get_id(attributes)

        if self._incrementing and inserted_id:
            self.set_key(self.cast_attribute(self.get_key_name(), inserted_id))

        self._exists = True
        self._was_recently_created = True

        self.sync_original()

        return True

    def _perform_update(self) -> bool:
        if not self.is_dirty():
            return True

        if self._timestamps:
            self._update_timestamps()

        attributes = self.get_dirty()
        attributes = self._serialize_attributes(attributes)

        connection = self.get_connection()
        query = connection.table(self.get_table())

        affected = query.where(self.get_key_name(), self.get_key()).update(attributes)

        self.sync_original()

        return affected > 0

    def get_dirty(self) -> Dict[str, Any]:
        dirty = {}
        for key, value in self._attributes.items():
            if key not in self._original or self._original[key] != value:
                dirty[key] = value
        return dirty

    def _update_timestamps(self) -> None:
        time = self._fresh_timestamp_string()

        if not self._exists and self.CREATED_AT:
            self.set_attribute(self.CREATED_AT, time)

        if self.UPDATED_AT:
            self.set_attribute(self.UPDATED_AT, time)

    def _fresh_timestamp_string(self) -> str:
        return datetime.now().strftime(self._date_format)

    def update(self, attributes: Dict[str, Any]) -> bool:
        return self.fill(attributes).save()

    def delete(self) -> bool:
        if not self._exists:
            return False

        connection = self.get_connection()
        query = connection.table(self.get_table())

        affected = query.where(self.get_key_name(), self.get_key()).delete()

        self._exists = False

        return affected > 0

    def fresh(self) -> Optional["Model"]:
        if not self._exists:
            return None

        return self.new_query().find(self.get_key())

    def refresh(self) -> "Model":
        if not self._exists:
            return self

        fresh = self.fresh()

        if fresh:
            self._attributes = fresh._attributes.copy()
            self._original = fresh._original.copy()

        return self

    def has_one(
        self,
        related_class: Type,
        foreign_key: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships import HasOne

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return HasOne(query, self, related_class, foreign_key, local_key)

    def has_many(
        self,
        related_class: Type,
        foreign_key: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships import HasMany

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return HasMany(query, self, related_class, foreign_key, local_key)
    
    def has_many_through(
        self,
        related_class: Type,
        through_class: Type,
        first_key: Optional[str] = None,
        second_key: Optional[str] = None,
        local_key: Optional[str] = None,
        second_local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.has_many_through import HasManyThrough

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return HasManyThrough(
            query,
            self,
            related_class,
            through_class,
            first_key,
            second_key,
            local_key,
            second_local_key,
        )
    
    def has_one_through(
        self,
        related_class: Type,
        through_class: Type,
        first_key: Optional[str] = None,
        second_key: Optional[str] = None,
        local_key: Optional[str] = None,
        second_local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.has_one_through import HasOneThrough

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return HasOneThrough(
            query,
            self,
            related_class,
            through_class,
            first_key,
            second_key,
            local_key,
            second_local_key,
        )

    def belongs_to(
        self,
        related_class: Type,
        foreign_key: Optional[str] = None,
        owner_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships import BelongsTo

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return BelongsTo(query, self, related_class, foreign_key, owner_key)

    def belongs_to_many(
        self,
        related_class: Type,
        table: Optional[str] = None,
        foreign_pivot_key: Optional[str] = None,
        related_pivot_key: Optional[str] = None,
        parent_key: Optional[str] = None,
        related_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships import BelongsToMany

        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())

        return BelongsToMany(
            query,
            self,
            related_class,
            table,
            foreign_pivot_key,
            related_pivot_key,
            parent_key,
            related_key,
        )
    
    def morph_to(
        self,
        morph_name: Optional[str] = None,
        morph_type: Optional[str] = None,
        morph_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.morph_to import MorphTo
        import inspect
        
        if morph_name is None:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                morph_name = frame.f_back.f_code.co_name
            else:
                morph_name = "morphable"
        
        connection = self.get_connection()
        query = None
        
        return MorphTo(query, self, morph_name, morph_type, morph_id, owner_key)
    
    def morph_one(
        self,
        related_class: Type,
        morph_name: str,
        morph_type: Optional[str] = None,
        morph_id: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.morph_one import MorphOne
        
        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())
        
        return MorphOne(
            query,
            self,
            related_class,
            morph_name,
            morph_type,
            morph_id,
            local_key
        )
    
    def morph_many(
        self,
        related_class: Type,
        morph_name: str,
        morph_type: Optional[str] = None,
        morph_id: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.morph_many import MorphMany
        
        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())
        
        return MorphMany(
            query,
            self,
            related_class,
            morph_name,
            morph_type,
            morph_id,
            local_key
        )
    
    def morph_to_many(
        self,
        related_class: Type,
        morph_name: str,
        table: Optional[str] = None,
        foreign_pivot_key: Optional[str] = None,
        related_pivot_key: Optional[str] = None,
        parent_key: Optional[str] = None,
        related_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.morph_to_many import MorphToMany
        
        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())
        
        return MorphToMany(
            query,
            self,
            related_class,
            morph_name,
            table,
            foreign_pivot_key,
            related_pivot_key,
            parent_key,
            related_key,
        )
    
    def morphed_by_many(
        self,
        related_class: Type,
        morph_name: str,
        table: Optional[str] = None,
        foreign_pivot_key: Optional[str] = None,
        related_pivot_key: Optional[str] = None,
        parent_key: Optional[str] = None,
        related_key: Optional[str] = None,
    ):
        from larapy.database.orm.relationships.morphed_by_many import MorphedByMany
        
        connection = self.get_connection()
        related_instance = related_class()
        query = connection.table(related_instance.get_table())
        
        return MorphedByMany(
            query,
            self,
            related_class,
            morph_name,
            table,
            foreign_pivot_key,
            related_pivot_key,
            parent_key,
            related_key,
        )

    def set_relation(self, relation: str, value: Any) -> "Model":
        self._relations[relation] = value
        return self

    def get_relation(self, relation: str) -> Any:
        return self._relations.get(relation)

    def relation_loaded(self, key: str) -> bool:
        return key in self._relations

    def load(self, *relations) -> "Model":
        if not relations:
            return self

        from larapy.database.orm.collection import Collection

        collection = Collection([self])

        for relation in relations:
            if isinstance(relation, str):
                self._load_relation(collection, relation)
            elif isinstance(relation, dict):
                for rel_name, callback in relation.items():
                    self._load_relation(collection, rel_name, callback)

        return self

    def load_missing(self, *relations) -> "Model":
        relations_to_load = [rel for rel in relations if not self.relation_loaded(rel)]
        if relations_to_load:
            return self.load(*relations_to_load)
        return self

    def _load_relation(self, collection, relation: str, callback=None):
        if not hasattr(self.__class__, relation):
            return

        relation_method = getattr(self.__class__, relation)
        if not callable(relation_method):
            return

        relation_instance = relation_method(self)

        if not hasattr(relation_instance, "add_eager_constraints"):
            return

        relation_instance.add_eager_constraints(collection.all())

        if callback:
            callback(relation_instance.get_query())

        results = relation_instance.get_eager()

        if hasattr(relation_instance, "match"):
            relation_instance.match(collection.all(), results, relation)

    def __getattribute__(self, key: str) -> Any:
        if (
            key.startswith("_")
            or key.isupper()
            or key
            in [
                "get_attribute",
                "set_attribute",
                "get_relation",
                "set_relation",
                "relation_loaded",
                "__dict__",
                "__class__",
            ]
        ):
            return super().__getattribute__(key)

        _relations = super().__getattribute__("_relations") if hasattr(self, "_relations") else {}
        if key in _relations:
            return _relations[key]

        return super().__getattribute__(key)

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

        if key in self._relations:
            return self._relations[key]

        if hasattr(self.__class__, key):
            method = getattr(self.__class__, key)
            if callable(method):
                result = method(self)
                if hasattr(result, "get_results"):
                    value = result.get_results()
                    self._relations[key] = value
                    return value

        return self.get_attribute(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_") or key.isupper():
            super().__setattr__(key, value)
        else:
            self.set_attribute(key, value)

    @classmethod
    def create(cls, attributes: Dict[str, Any]) -> "Model":
        model = cls(attributes)
        model.save()
        return model

    @classmethod
    def find(cls, id: Any) -> Optional["Model"]:
        return cls.new_query().find(id)

    @classmethod
    def find_or_fail(cls, id: Any) -> "Model":
        model = cls.find(id)
        if not model:
            raise Exception(f"Model not found with id: {id}")
        return model

    @classmethod
    def all(cls) -> "Collection":
        return cls.new_query().get()

    @classmethod
    def with_(cls, *relations):
        return cls.new_query().with_(*relations)

    @classmethod
    def where(cls, *args, **kwargs):
        return cls.new_query().where(*args, **kwargs)

    @classmethod
    def new_query(cls):
        from larapy.database.orm.builder import Builder

        instance = cls()
        connection = instance.get_connection()

        return Builder(connection.table(instance.get_table()), cls, connection)

    def instance_query(self):
        from larapy.database.orm.builder import Builder

        connection = self._connection if self._connection else self.get_connection()

        return Builder(connection.table(self.get_table()), self.__class__, connection)

    @classmethod
    def query(cls):
        return cls.new_query()

    def new_instance(
        self, attributes: Optional[Dict[str, Any]] = None, exists: bool = False
    ) -> "Model":
        model = self.__class__(attributes, self._connection)
        model._exists = exists

        if exists:
            model.sync_original()

        return model

    # Serialization Methods

    def toArray(self, include_relations: bool = True) -> dict:
        """
        Convert model to dictionary.

        Args:
            include_relations: Whether to include loaded relationships

        Returns:
            Dictionary representation of the model
        """
        attributes = self.attributesToArray()

        if include_relations:
            attributes.update(self.relationshipsToArray())

        return attributes

    def toDict(self) -> dict:
        """
        Alias for toArray (Python convention).

        Returns:
            Dictionary representation of the model
        """
        return self.toArray()

    def toJson(self, **json_kwargs) -> str:
        """
        Convert model to JSON string.

        Args:
            **json_kwargs: Arguments to pass to json.dumps()

        Returns:
            JSON string representation of the model
        """
        data = self.toArray()

        # Set default JSON encoding options
        if "indent" not in json_kwargs:
            json_kwargs["indent"] = None
        if "ensure_ascii" not in json_kwargs:
            json_kwargs["ensure_ascii"] = False
        if "default" not in json_kwargs:
            json_kwargs["default"] = str

        return json.dumps(data, **json_kwargs)

    def attributesToArray(self) -> dict:
        """
        Get model attributes as array with visibility rules applied.

        Returns:
            Dictionary of visible attributes
        """
        attributes = {}

        for key, value in self._attributes.items():
            # Skip hidden attributes
            if self._is_hidden(key):
                continue

            # Check visible list if defined
            if not self._is_visible(key):
                continue

            # Serialize the value
            attributes[key] = self._serialize_attribute(key, value)

        # Add appended attributes
        for accessor in self._get_appends():
            attributes[accessor] = self._mutate_attribute_for_array(accessor)

        return attributes

    def relationshipsToArray(self) -> dict:
        """
        Get loaded relationships as array.

        Returns:
            Dictionary of loaded relationships
        """
        relations = {}

        # Check for loaded relationships
        for relation_name in self._with_relations:
            if hasattr(self, f"_{relation_name}_relation"):
                relation_value = getattr(self, f"_{relation_name}_relation")

                # Serialize relation
                if isinstance(relation_value, Model):
                    relations[relation_name] = relation_value.toArray()
                elif isinstance(relation_value, list):
                    relations[relation_name] = [
                        item.toArray() if isinstance(item, Model) else item
                        for item in relation_value
                    ]
                else:
                    relations[relation_name] = relation_value

        return relations

    def _serialize_attribute(self, key: str, value: Any) -> Any:
        """
        Serialize a single attribute value.

        Args:
            key: Attribute key
            value: Attribute value

        Returns:
            Serialized value
        """
        if value is None:
            return None

        # Handle datetime serialization
        if isinstance(value, datetime):
            return self.serializeDate(value)

        # Apply casts if defined
        if key in self._casts:
            cast_type = self._casts[key]

            # Handle datetime casts with formats
            if ":" in cast_type:
                cast_base, cast_format = cast_type.split(":", 1)
                if cast_base == "datetime" and isinstance(value, datetime):
                    return value.strftime(cast_format)

            # Handle array/json casts
            if cast_type in ["array", "json"]:
                if isinstance(value, (list, dict)):
                    return value
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except:
                        return value

        return value

    def serializeDate(self, date: datetime) -> str:
        """
        Format date for serialization.

        Args:
            date: datetime object to serialize

        Returns:
            Formatted date string
        """
        if self._dateFormat == "iso8601":
            return date.isoformat()
        else:
            return date.strftime(self._dateFormat)

    def _is_hidden(self, key: str) -> bool:
        """
        Check if attribute is hidden.

        Args:
            key: Attribute key

        Returns:
            True if attribute should be hidden
        """
        # Check if made visible at runtime
        if key in self._runtime_visible:
            return False

        # Check runtime hidden
        if key in self._runtime_hidden:
            return True

        # Check class hidden list (only if runtime hidden not set)
        if not self._runtime_hidden:
            return key in self._hidden

        return False

    def _is_visible(self, key: str) -> bool:
        """
        Check if attribute is visible.

        Args:
            key: Attribute key

        Returns:
            True if attribute should be visible
        """
        # If visible list is not empty, only show attributes in the list
        visible_list = list(self._runtime_visible) if self._runtime_visible else self._visible

        if visible_list:
            return key in visible_list

        return True

    def _get_appends(self) -> List[str]:
        """
        Get list of attributes to append.

        Returns:
            List of accessor names to append
        """
        appends = self._appends.copy()
        appends.extend(self._runtime_appends)
        return appends

    def _mutate_attribute_for_array(self, key: str) -> Any:
        """
        Get accessor value for serialization.

        Args:
            key: Accessor name

        Returns:
            Accessor value
        """
        # Look for get_{key}_attribute method
        method_name = f"get_{key}_attribute"

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            if callable(method):
                return method()

        return None

    def makeVisible(self, attributes: List[str]) -> "Model":
        """
        Make attributes visible at runtime.

        Args:
            attributes: List of attribute names to make visible

        Returns:
            self for chaining
        """
        for attr in attributes:
            self._runtime_visible.add(attr)
            self._runtime_hidden.discard(attr)

        return self

    def makeHidden(self, attributes: List[str]) -> "Model":
        """
        Hide attributes at runtime.

        Args:
            attributes: List of attribute names to hide

        Returns:
            self for chaining
        """
        for attr in attributes:
            self._runtime_hidden.add(attr)
            self._runtime_visible.discard(attr)

        return self

    def setVisible(self, visible: List[str]) -> "Model":
        """
        Set visible attributes list.

        Args:
            visible: List of attribute names to show

        Returns:
            self for chaining
        """
        self._runtime_visible = set(visible)
        return self

    def setHidden(self, hidden: List[str]) -> "Model":
        """
        Set hidden attributes list.

        Args:
            hidden: List of attribute names to hide

        Returns:
            self for chaining
        """
        self._runtime_hidden = set(hidden)
        return self

    def append(self, attributes: List[str]) -> "Model":
        """
        Append attributes at runtime.

        Args:
            attributes: List of accessor names to append

        Returns:
            self for chaining
        """
        self._runtime_appends.extend(attributes)
        return self

    def getArrayableAttributes(self) -> Dict[str, Any]:
        """
        Get attributes that should be converted to array.

        Returns:
            Dictionary of arrayable attributes
        """
        return self.attributesToArray()

    def getHidden(self) -> List[str]:
        """
        Get hidden attributes.

        Returns:
            List of hidden attribute names
        """
        return list(self._runtime_hidden) if self._runtime_hidden else self._hidden

    def getVisible(self) -> List[str]:
        """
        Get visible attributes.

        Returns:
            List of visible attribute names
        """
        return list(self._runtime_visible) if self._runtime_visible else self._visible

    def getAppends(self) -> List[str]:
        """
        Get appended attributes.

        Returns:
            List of appended accessor names
        """
        return self._get_appends()

    def getRouteKeyName(self) -> str:
        """
        Get the route key name for model binding.

        Returns:
            Route key name (default: primary key)
        """
        return self.get_key_name()

    def resolveRouteBinding(self, value: Any, field: Optional[str] = None) -> Optional["Model"]:
        """
        Resolve route model binding.

        Args:
            value: Value to search for
            field: Field to search in (default: route key)

        Returns:
            Model instance or None
        """
        field = field or self.getRouteKeyName()

        return self.__class__.where(field, value).first()

    def resolveChildRouteBinding(
        self, childType: str, value: Any, field: Optional[str] = None
    ) -> Optional["Model"]:
        """
        Resolve child route binding for scoped bindings.

        Args:
            childType: Child model class name
            value: Value to search for
            field: Field to search in

        Returns:
            Child model instance or None
        """
        # This will be implemented when relationships are fully supported
        raise NotImplementedError("Child route binding requires relationship support")
