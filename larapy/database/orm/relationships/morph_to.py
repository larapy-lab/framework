from typing import List, Optional, Type
from larapy.database.orm.relationships.morph_relation import MorphRelation
from larapy.database.orm.morph_map import MorphMap


class MorphTo(MorphRelation):
    
    def __init__(
        self,
        query,
        parent,
        morph_name: str,
        morph_type: Optional[str] = None,
        morph_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ):
        self._morph_name = morph_name
        self._morph_type_field = morph_type or f"{morph_name}_type"
        self._morph_id_field = morph_id or f"{morph_name}_id"
        self._owner_key = owner_key
        self._loaded_parent = None
        
        super().__init__(
            query,
            parent,
            None,
            morph_name,
            self._morph_type_field,
            self._morph_id_field,
            owner_key
        )
    
    def add_constraints(self):
        pass
    
    def add_eager_constraints(self, models: List):
        """
        Set constraints for eager loading MorphTo relationships.
        Groups models by morph type and loads each type separately.
        """
        pass
    
    def get_eager(self):
        """
        Get eager loaded results for MorphTo relationship.
        This groups parent models by morph type and executes separate queries for each type.
        Note: MorphTo eager loading is handled via morphWith() instead.
        """
        return None
    
    def morph_with(self, models: List):
        """
        Load morphTo relationships for a collection of models.
        Groups by morph type and executes one query per type.
        """
        from larapy.database.query.builder import QueryBuilder
        
        # Group models by morph type
        grouped = {}
        for model in models:
            morph_type = model.get_attribute(self._morph_type_field)
            morph_id = model.get_attribute(self._morph_id_field)
            
            if morph_type and morph_id:
                if morph_type not in grouped:
                    grouped[morph_type] = {'ids': [], 'models': []}
                grouped[morph_type]['ids'].append(morph_id)
                grouped[morph_type]['models'].append(model)
        
        # Load each morph type separately
        results_by_type = {}
        for morph_type, data in grouped.items():
            related_class = self._resolve_related_class(morph_type)
            if not related_class:
                continue
            
            related_instance = related_class(connection=self._parent.get_connection())
            owner_key = self._owner_key or related_instance.get_key_name()
            
            query = QueryBuilder(
                connection=self._parent.get_connection(),
                table_name=related_instance.get_table()
            )
            
            results = query.where_in(owner_key, data['ids']).get()
            
            # Build dictionary for this type
            results_dict = {}
            for row in results:
                key_value = row.get(owner_key)
                model = self._hydrate_related_model(related_class, row)
                results_dict[key_value] = model
            
            results_by_type[morph_type] = results_dict
        
        return results_by_type
    
    def match(self, models: List, results: List, relation: str) -> List:
        dictionary = {}
        
        for result in results:
            morph_type = result.get('_morph_type')
            morph_id = result.get('_morph_id')
            key = f"{morph_type}_{morph_id}"
            dictionary[key] = result.get('model')
        
        for model in models:
            morph_type = model.get_attribute(self._morph_type_field)
            morph_id = model.get_attribute(self._morph_id_field)
            
            if morph_type and morph_id:
                key = f"{morph_type}_{morph_id}"
                if key in dictionary:
                    model.set_relation(relation, dictionary[key])
                else:
                    model.set_relation(relation, None)
            else:
                model.set_relation(relation, None)
        
        return models
    
    def get_results(self):
        if self._loaded_parent is not None:
            return self._loaded_parent
        
        morph_type = self._parent.get_attribute(self._morph_type_field)
        morph_id = self._parent.get_attribute(self._morph_id_field)
        
        if not morph_type or not morph_id:
            return None
        
        related_class = self._resolve_related_class(morph_type)
        if not related_class:
            return None
        
        related_instance = related_class(connection=self._parent.get_connection())
        owner_key = self._owner_key or related_instance.get_key_name()
        
        from larapy.database.query.builder import QueryBuilder
        query = QueryBuilder(
            connection=self._parent.get_connection(),
            table_name=related_instance.get_table()
        )
        
        results = query.where(owner_key, morph_id).get()
        
        if not results:
            return None
        
        self._loaded_parent = self._hydrate_related_model(related_class, results[0])
        return self._loaded_parent
    
    def _resolve_related_class(self, morph_type: str) -> Optional[Type]:
        resolved_type = MorphMap.resolve_type(morph_type)
        
        try:
            parts = resolved_type.rsplit('.', 1)
            if len(parts) == 2:
                module_name, class_name = parts
                import importlib
                module = importlib.import_module(module_name)
                return getattr(module, class_name)
            else:
                return None
        except (ImportError, AttributeError):
            return None
    
    def _hydrate_related_model(self, related_class: Type, attributes: dict):
        instance = related_class(connection=self._parent.get_connection())
        instance._attributes = attributes.copy()
        instance._original = attributes.copy()
        instance._exists = True
        instance._was_recently_created = False
        return instance
    
    def associate(self, model):
        morph_class = self._get_morph_class_for_model(model)
        
        self._parent.set_attribute(self._morph_type_field, morph_class)
        self._parent.set_attribute(
            self._morph_id_field,
            model.get_attribute(self._owner_key or model.get_key_name())
        )
        
        self._loaded_parent = model
        return self._parent
    
    def dissociate(self):
        self._parent.set_attribute(self._morph_type_field, None)
        self._parent.set_attribute(self._morph_id_field, None)
        self._loaded_parent = None
        return self._parent
    
    def _get_morph_class_for_model(self, model) -> str:
        model_class = model.__class__
        module = model_class.__module__
        name = model_class.__name__
        full_class = f"{module}.{name}"
        
        return MorphMap.get_morph_alias(full_class)
