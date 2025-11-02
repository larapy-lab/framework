from typing import List, Optional, Type, Dict, Any
from larapy.database.orm.relationships.relation import Relation


class HasManyThrough(Relation):
    
    def __init__(
        self,
        query,
        parent,
        related_class: Type,
        through_class: Type,
        first_key: Optional[str] = None,
        second_key: Optional[str] = None,
        local_key: Optional[str] = None,
        second_local_key: Optional[str] = None,
    ):
        super().__init__(query, parent, related_class)
        
        self._through_class = through_class
        self._first_key = first_key
        self._second_key = second_key
        self._local_key = local_key
        self._second_local_key = second_local_key
        
    def add_constraints(self):
        if self._constraints_applied:
            return
            
        if self._parent._exists:
            self._set_join()
            self._set_where()
            
        self._constraints_applied = True
        
    def add_eager_constraints(self, models: List):
        table = self._get_qualified_parent_key_name()
        
        keys = [
            model.get_attribute(self._get_local_key())
            for model in models
            if model.get_attribute(self._get_local_key()) is not None
        ]
        
        if keys:
            self._set_join()
            self._query.where_in(table, keys)
    
    def match(self, models: List, results: List, relation: str) -> List:
        dictionary = self._build_dictionary_collection(results)
        
        for model in models:
            key = model.get_attribute(self._get_local_key())
            if key in dictionary:
                model.set_relation(relation, dictionary[key])
            else:
                from larapy.database.orm.collection import Collection
                model.set_relation(relation, Collection([]))
                
        return models
    
    def get_results(self):
        if not self._constraints_applied:
            self.add_constraints()
            
        results = self._query.get()
        
        if not results:
            from larapy.database.orm.collection import Collection
            return Collection([])
            
        models = [self._hydrate_model(row) for row in results]
        from larapy.database.orm.collection import Collection
        return Collection(models)
    
    def get_eager(self):
        results = self._query.get()
        
        if not results:
            return []
            
        return [self._hydrate_model(row) for row in results]
    
    def _set_join(self):
        parent_table = self._parent.get_table()
        through_table = self._get_through_table()
        final_table = self._get_related_table()
        
        self._query._table = parent_table
        
        first_key = self._get_first_key()
        local_key = self._get_local_key()
        self._query.join(through_table, f'{through_table}.{first_key}', '=', f'{parent_table}.{local_key}')
        
        second_key = self._get_second_key()
        second_local_key = self._get_second_local_key()
        self._query.join(final_table, f'{final_table}.{second_key}', '=', f'{through_table}.{second_local_key}')
        
        self._query.select(f'{final_table}.*')
        
    def _set_where(self):
        local_key = self._get_local_key()
        local_value = self._parent.get_attribute(local_key)
        
        if local_value is not None:
            qualified_key = self._get_qualified_parent_key_name()
            self._query.where(qualified_key, local_value)
    
    def _build_dictionary_collection(self, results: List):
        from larapy.database.orm.collection import Collection
        
        dictionary = {}
        first_key = self._get_first_key()
        
        for result in results:
            pivot_data = getattr(result, '_pivot_data', {})
            key = pivot_data.get(first_key)
            
            if key is None:
                continue
                
            if key not in dictionary:
                dictionary[key] = []
            dictionary[key].append(result)
        
        return {key: Collection(models) for key, models in dictionary.items()}
    
    def _hydrate_model(self, row: Dict):
        from larapy.database.orm.collection import Collection
        
        related_instance = self._related_class()
        attributes = {}
        pivot_data = {}
        
        for key, value in row.items():
            if '.' in key:
                table_name, column_name = key.split('.', 1)
                
                if table_name == self._get_through_table():
                    pivot_data[column_name] = value
                elif table_name == self._get_related_table():
                    attributes[column_name] = value
            else:
                attributes[key] = value
        
        model = self._related_class(connection=self._parent.get_connection())
        model._attributes = attributes.copy()
        model._original = attributes.copy()
        model._exists = True
        
        if pivot_data:
            model._pivot_data = pivot_data
        
        return model
    
    def _get_first_key(self) -> str:
        if self._first_key:
            return self._first_key
            
        parent_table = self._parent.get_table()
        return f"{parent_table.rstrip('s')}_id"
    
    def _get_second_key(self) -> str:
        if self._second_key:
            return self._second_key
            
        through_table = self._get_through_table()
        return f"{through_table.rstrip('s')}_id"
    
    def _get_local_key(self) -> str:
        if self._local_key:
            return self._local_key
            
        return self._parent.get_key_name()
    
    def _get_second_local_key(self) -> str:
        if self._second_local_key:
            return self._second_local_key
            
        through_instance = self._through_class()
        return through_instance.get_key_name()
    
    def _get_through_table(self) -> str:
        through_instance = self._through_class()
        return through_instance.get_table()
    
    def _get_related_table(self) -> str:
        related_instance = self._related_class()
        return related_instance.get_table()
    
    def _get_qualified_first_key_name(self) -> str:
        through_table = self._get_through_table()
        first_key = self._get_first_key()
        return f"{through_table}.{first_key}"
    
    def _get_qualified_second_key_name(self) -> str:
        related_table = self._get_related_table()
        second_key = self._get_second_key()
        return f"{related_table}.{second_key}"
    
    def _get_qualified_parent_key_name(self) -> str:
        parent_table = self._parent.get_table()
        local_key = self._get_local_key()
        return f"{parent_table}.{local_key}"
    
    def limit(self, value: int):
        self._query.limit(value)
        return self
    
    def offset(self, value: int):
        self._query.offset(value)
        return self
    
    def take(self, value: int):
        return self.limit(value)
    
    def where_in(self, column: str, values: list):
        final_table = self._get_related_table()
        qualified_column = f'{final_table}.{column}'
        self._query.where_in(qualified_column, values)
        return self
    
    def first(self):
        results = self.limit(1).get_results()
        if results and results.count() > 0:
            return results[0]
        return None
