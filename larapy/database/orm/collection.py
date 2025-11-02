from typing import Any, Callable, Dict, List, Optional, Union
from larapy.support.macroable import Macroable


class Collection(Macroable):

    def __init__(self, items: Optional[List[Any]] = None):
        self._items = items if items is not None else []

    def all(self) -> List[Any]:
        return self._items

    def first(self) -> Optional[Any]:
        return self._items[0] if self._items else None

    def last(self) -> Optional[Any]:
        return self._items[-1] if self._items else None

    def count(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def is_not_empty(self) -> bool:
        return len(self._items) > 0

    def contains(self, item: Any) -> bool:
        if callable(item):
            for model in self._items:
                if item(model):
                    return True
            return False

        return item in self._items

    def find(self, key: Any) -> Optional[Any]:
        for model in self._items:
            if hasattr(model, "get_key") and model.get_key() == key:
                return model
        return None

    def pluck(self, column: str) -> List[Any]:
        result = []
        for model in self._items:
            if hasattr(model, "get_attribute"):
                result.append(model.get_attribute(column))
            elif isinstance(model, dict):
                result.append(model.get(column))
        return result

    def sum(self, key: Optional[str] = None) -> Union[int, float]:
        if key:
            total = 0
            for item in self._items:
                if hasattr(item, "get_attribute"):
                    total += item.get_attribute(key)
                elif isinstance(item, dict):
                    total += item.get(key, 0)
                else:
                    total += getattr(item, key, 0)
            return total
        return sum(self._items) if self._items else 0

    def model_keys(self) -> List[Any]:
        keys = []
        for model in self._items:
            if hasattr(model, "get_key"):
                keys.append(model.get_key())
        return keys

    def unique(self, key: Optional[str] = None) -> "Collection":
        if key:
            seen = set()
            unique_items = []
            for model in self._items:
                value = model.get_attribute(key) if hasattr(model, "get_attribute") else None
                if value not in seen:
                    seen.add(value)
                    unique_items.append(model)
            return Collection(unique_items)
        else:
            return Collection(list(dict.fromkeys(self._items)))

    def filter(self, callback: Callable[[Any], bool]) -> "Collection":
        filtered = [item for item in self._items if callback(item)]
        return Collection(filtered)

    def map(self, callback: Callable[[Any], Any]) -> "Collection":
        mapped = [callback(item) for item in self._items]
        return Collection(mapped)

    def each(self, callback: Callable[[Any], None]) -> "Collection":
        for item in self._items:
            callback(item)
        return self

    def push(self, item: Any) -> "Collection":
        self._items.append(item)
        return self

    def pop(self) -> Optional[Any]:
        return self._items.pop() if self._items else None

    def shift(self) -> Optional[Any]:
        return self._items.pop(0) if self._items else None

    def slice(self, start: int, length: Optional[int] = None) -> "Collection":
        if length is None:
            return Collection(self._items[start:])
        return Collection(self._items[start : start + length])

    def take(self, limit: int) -> "Collection":
        if limit < 0:
            return Collection(self._items[limit:])
        return Collection(self._items[:limit])

    def sort(self, callback: Optional[Callable] = None, reverse: bool = False) -> "Collection":
        if callback:
            sorted_items = sorted(self._items, key=callback, reverse=reverse)
        else:
            sorted_items = sorted(self._items, reverse=reverse)
        return Collection(sorted_items)

    def sort_by(self, key: Union[str, Callable], reverse: bool = False) -> "Collection":
        if callable(key):
            sorted_items = sorted(self._items, key=key, reverse=reverse)
        else:
            sorted_items = sorted(
                self._items,
                key=lambda model: (
                    model.get_attribute(key) if hasattr(model, "get_attribute") else None
                ),
                reverse=reverse,
            )
        return Collection(sorted_items)

    def reverse(self) -> "Collection":
        return Collection(list(reversed(self._items)))

    def fresh(self) -> "Collection":
        fresh_models = []
        for model in self._items:
            if hasattr(model, "fresh"):
                fresh_model = model.fresh()
                if fresh_model:
                    fresh_models.append(fresh_model)
        return Collection(fresh_models)

    def to_list(self) -> List[Any]:
        return self._items.copy()

    def to_dict(self) -> List[Dict[str, Any]]:
        result = []
        for model in self._items:
            if hasattr(model, "get_attributes"):
                result.append(model.get_attributes())
            elif isinstance(model, dict):
                result.append(model)
        return result

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key):
        return self._items[key]

    def __bool__(self):
        return len(self._items) > 0

    def __repr__(self):
        return f"Collection({self._items})"

    def tap(self, callback: Callable) -> "Collection":
        callback(self)
        return self

    def pipe(self, callback: Callable) -> Any:
        return callback(self)

    def pipe_through(self, callbacks: List[Callable]) -> Any:
        result = self
        for callback in callbacks:
            result = callback(result)
        return result

    def when(
        self,
        condition: Union[bool, Callable],
        callback: Callable,
        default: Optional[Callable] = None,
    ) -> "Collection":
        if callable(condition):
            condition = condition(self)

        if condition:
            result = callback(self)
        elif default:
            result = default(self)
        else:
            result = self

        return result if isinstance(result, Collection) else self

    def unless(
        self,
        condition: Union[bool, Callable],
        callback: Callable,
        default: Optional[Callable] = None,
    ) -> "Collection":
        if callable(condition):
            condition = condition(self)

        return self.when(not condition, callback, default)

    def when_empty(self, callback: Callable) -> "Collection":
        return self.when(self.is_empty(), callback)

    def when_not_empty(self, callback: Callable) -> "Collection":
        return self.when(self.is_not_empty(), callback)

    def sole(self, key: Optional[str] = None, value: Any = None) -> Any:
        if key is not None:
            filtered = self.filter(
                lambda item: (
                    item.get_attribute(key) == value
                    if hasattr(item, "get_attribute")
                    else (
                        item.get(key) == value
                        if isinstance(item, dict)
                        else getattr(item, key, None) == value
                    )
                )
            )
        else:
            filtered = self

        count = filtered.count()

        if count == 0:
            raise ValueError("No items found matching criteria")
        elif count > 1:
            raise ValueError(f"Multiple items found ({count}), expected exactly one")

        return filtered.first()

    def ensure(self, type_or_types: Union[type, tuple]) -> "Collection":
        if not isinstance(type_or_types, tuple):
            type_or_types = (type_or_types,)

        for item in self._items:
            if not isinstance(item, type_or_types):
                raise TypeError(f"Item {item} is not of type {type_or_types}")

        return self

    def dot(self) -> "Collection":
        def flatten(data, prefix=""):
            result = {}
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    result.update(flatten(value, new_key))
                else:
                    result[new_key] = value
            return result

        if not self._items:
            return Collection([])

        if isinstance(self._items[0], dict):
            return Collection([flatten(item) for item in self._items])

        return self

    def undot(self) -> "Collection":
        def expand(data):
            result = {}
            for key, value in data.items():
                parts = key.split(".")
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            return result

        if not self._items:
            return Collection([])

        if isinstance(self._items[0], dict):
            return Collection([expand(item) for item in self._items])

        return self

    def sliding(self, size: int = 2, step: int = 1) -> "Collection":
        windows = []
        for i in range(0, len(self._items) - size + 1, step):
            windows.append(self._items[i : i + size])
        return Collection(windows)

    def chunk_while(self, callback: Callable) -> "Collection":
        if not self._items:
            return Collection([])

        chunks = []
        current_chunk = [self._items[0]]

        for i in range(1, len(self._items)):
            if callback(self._items[i], self._items[i - 1]):
                current_chunk.append(self._items[i])
            else:
                chunks.append(current_chunk)
                current_chunk = [self._items[i]]

        chunks.append(current_chunk)
        return Collection(chunks)

    def take_until(self, callback: Callable) -> "Collection":
        result = []
        for item in self._items:
            if callback(item):
                break
            result.append(item)
        return Collection(result)

    def take_while(self, callback: Callable) -> "Collection":
        result = []
        for item in self._items:
            if not callback(item):
                break
            result.append(item)
        return Collection(result)

    def skip_until(self, callback: Callable) -> "Collection":
        result = []
        skipping = True
        for item in self._items:
            if skipping and callback(item):
                skipping = False
            if not skipping:
                result.append(item)
        return Collection(result)

    def skip_while(self, callback: Callable) -> "Collection":
        result = []
        skipping = True
        for item in self._items:
            if skipping and not callback(item):
                skipping = False
            if not skipping:
                result.append(item)
        return Collection(result)

    def lazy(self) -> "LazyCollection":
        from larapy.support.lazy_collection import LazyCollection

        return LazyCollection(iter(self._items))

    def flatten(self, depth: int = 1) -> "Collection":
        def flatten_recursive(items, current_depth):
            result = []
            for item in items:
                if isinstance(item, (list, tuple, Collection)) and current_depth > 0:
                    if isinstance(item, Collection):
                        item = item.all()
                    result.extend(flatten_recursive(item, current_depth - 1))
                else:
                    result.append(item)
            return result

        return Collection(flatten_recursive(self._items, depth))

    def chunk(self, size: int) -> "Collection":
        chunks = []
        for i in range(0, len(self._items), size):
            chunks.append(self._items[i : i + size])
        return Collection(chunks)

    def split(self, number_of_groups: int) -> "Collection":
        if number_of_groups <= 0:
            return Collection([])

        group_size = len(self._items) // number_of_groups
        remainder = len(self._items) % number_of_groups

        groups = []
        start = 0

        for i in range(number_of_groups):
            extra = 1 if i < remainder else 0
            end = start + group_size + extra
            groups.append(self._items[start:end])
            start = end

        return Collection(groups)

    def where(self, key: str, operator: Any = None, value: Any = None) -> "Collection":
        if operator is None:
            return self.filter(
                lambda item: bool(
                    item.get_attribute(key)
                    if hasattr(item, "get_attribute")
                    else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
                )
            )

        if value is None:
            value = operator
            operator = "="

        operators = {
            "=": lambda a, b: a == b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<>": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }

        if operator not in operators:
            raise ValueError(f"Operator {operator} is not supported")

        compare = operators[operator]

        return self.filter(
            lambda item: compare(
                (
                    item.get_attribute(key)
                    if hasattr(item, "get_attribute")
                    else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
                ),
                value,
            )
        )

    def where_in(self, key: str, values: List[Any]) -> "Collection":
        return self.filter(
            lambda item: (
                item.get_attribute(key)
                if hasattr(item, "get_attribute")
                else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            )
            in values
        )

    def where_not_in(self, key: str, values: List[Any]) -> "Collection":
        return self.filter(
            lambda item: (
                item.get_attribute(key)
                if hasattr(item, "get_attribute")
                else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            )
            not in values
        )

    def where_null(self, key: str) -> "Collection":
        return self.filter(
            lambda item: (
                item.get_attribute(key)
                if hasattr(item, "get_attribute")
                else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            )
            is None
        )

    def where_not_null(self, key: str) -> "Collection":
        return self.filter(
            lambda item: (
                item.get_attribute(key)
                if hasattr(item, "get_attribute")
                else item.get(key) if isinstance(item, dict) else getattr(item, key, None)
            )
            is not None
        )

    def load(self, *relations) -> "Collection":
        """
        Eager load relationships on the collection models.
        
        This method allows you to load relationships after the models have been
        retrieved, preventing N+1 query problems when accessing relationships.
        
        Args:
            *relations: Variable number of relationship names to load.
                       Can be strings or dicts with constraints.
        
        Returns:
            self for method chaining
            
        Example:
            # Load a single relationship
            users = User.all()
            users.load('posts')
            
            # Load multiple relationships
            users.load('posts', 'comments')
            
            # Load nested relationships
            users.load('posts.comments')
            
            # Load with constraints
            users.load({'posts': lambda q: q.where('published', True)})
        """
        if not self._items or not relations:
            return self
        
        # Check if items are models (have load capability)
        first_item = self.first()
        if not first_item or not hasattr(first_item, 'load'):
            return self
        
        # Process each relation
        for relation in relations:
            self._load_relation(relation)
        
        return self
    
    def _load_relation(self, relation: Union[str, Dict[str, Callable]]):
        """
        Load a single relationship on all models in the collection.
        
        Args:
            relation: Either a string relation name or dict with constraints
        """
        if not self._items:
            return
        
        # Handle dict format: {'posts': lambda q: q.where('published', True)}
        if isinstance(relation, dict):
            for rel_name, callback in relation.items():
                self._load_relation_with_callback(rel_name, callback)
            return
        
        # Handle string format: 'posts' or 'posts.comments'
        self._load_relation_string(relation)
    
    def _load_relation_string(self, relation: str, callback: Optional[Callable] = None):
        """
        Load a relationship by name on all models.
        
        Args:
            relation: The relationship name (can be nested like 'posts.comments')
            callback: Optional callback to constrain the relationship query
        """
        if not self._items:
            return
        
        # Check if this is a nested relation (e.g., 'posts.comments')
        if '.' in relation:
            parts = relation.split('.', 1)
            base_relation = parts[0]
            nested_relation = parts[1]
            
            # Load the base relation first
            self._load_relation_string(base_relation)
            
            # Then load the nested relation on the loaded models
            for model in self._items:
                if hasattr(model, 'get_relation') and model.relation_loaded(base_relation):
                    related = model.get_relation(base_relation)
                    if related:
                        if hasattr(related, 'load'):
                            # Single model
                            related.load(nested_relation)
                        elif isinstance(related, Collection):
                            # Collection of models
                            related.load(nested_relation)
            return
        
        # Get the first model to check for relation method
        first_model = self.first()
        if not hasattr(first_model.__class__, relation):
            return
        
        relation_method = getattr(first_model.__class__, relation)
        if not callable(relation_method):
            return
        
        # Get the relation instance from first model
        relation_instance = relation_method(first_model)
        
        # Check if this relation supports eager loading
        if not hasattr(relation_instance, 'add_eager_constraints'):
            return
        
        # Add eager constraints for all models in collection
        relation_instance.add_eager_constraints(self._items)
        
        # Apply callback if provided
        if callback:
            callback(relation_instance.get_query())
        
        # Execute the eager load query
        results = relation_instance.get_eager()
        
        # Match results to models
        if hasattr(relation_instance, 'match'):
            relation_instance.match(self._items, results, relation)
    
    def _load_relation_with_callback(self, relation: str, callback: Callable):
        """
        Load a relationship with a query constraint callback.
        
        Args:
            relation: The relationship name
            callback: Callback function to constrain the query
        """
        self._load_relation_string(relation, callback)
    
    def load_missing(self, *relations) -> "Collection":
        """
        Load relationships that haven't been loaded yet.
        
        Only loads relationships that are not already loaded on the models.
        
        Args:
            *relations: Variable number of relationship names
            
        Returns:
            self for method chaining
            
        Example:
            users.load('posts')
            users.load_missing('posts', 'comments')  # Only loads 'comments'
        """
        if not self._items or not relations:
            return self
        
        first_item = self.first()
        if not first_item or not hasattr(first_item, 'relation_loaded'):
            return self
        
        # Filter to only relations not already loaded
        relations_to_load = []
        for relation in relations:
            # Handle dict format
            if isinstance(relation, dict):
                relations_to_load.append(relation)
            # Handle string format
            elif isinstance(relation, str):
                # Check if any model doesn't have this relation loaded
                needs_load = any(
                    not model.relation_loaded(relation) 
                    for model in self._items 
                    if hasattr(model, 'relation_loaded')
                )
                if needs_load:
                    relations_to_load.append(relation)
        
        if relations_to_load:
            return self.load(*relations_to_load)
        
        return self
