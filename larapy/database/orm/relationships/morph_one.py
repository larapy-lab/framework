from typing import List, Optional
from larapy.database.orm.relationships.morph_relation import MorphRelation


class MorphOne(MorphRelation):
    
    def __init__(
        self,
        query,
        parent,
        related_class,
        morph_name: str,
        morph_type: Optional[str] = None,
        morph_id: Optional[str] = None,
        local_key: Optional[str] = None,
    ):
        super().__init__(
            query,
            parent,
            related_class,
            morph_name,
            morph_type,
            morph_id,
            local_key
        )
    
    def add_constraints(self):
        if self._constraints_applied:
            return
        
        if self._parent._exists:
            morph_class = self.get_morph_class()
            local_key = self.get_local_key()
            local_value = self._parent.get_attribute(local_key)
            
            if local_value is not None:
                self._query.where(self._morph_type, morph_class)
                self._query.where(self._morph_id, local_value)
        
        self._constraints_applied = True
    
    def add_eager_constraints(self, models: List):
        morph_class = self.get_morph_class()
        local_key = self.get_local_key()
        
        keys = [
            model.get_attribute(local_key)
            for model in models
            if model.get_attribute(local_key) is not None
        ]
        
        if keys:
            self._query.where(self._morph_type, morph_class)
            self._query.where_in(self._morph_id, keys)
    
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
        
        results = self._query.get()
        
        if not results:
            return None
        
        return self._hydrate_model(results[0])
    
    def get_eager(self):
        """Get eager loaded results for MorphOne relationship."""
        results = self._query.get()
        models = []
        for row in results:
            models.append(self._hydrate_model(row))
        return models
    
    def _build_dictionary(self, results: List):
        return {self._get_dictionary_key(result): result for result in results}
    
    def _get_dictionary_key(self, result):
        return result.get_attribute(self._morph_id)
    
    def create(self, attributes: dict):
        instance = self._related_class(attributes, self._parent.get_connection())
        
        morph_class = self.get_morph_class()
        local_key = self.get_local_key()
        
        instance.set_attribute(self._morph_type, morph_class)
        instance.set_attribute(self._morph_id, self._parent.get_attribute(local_key))
        
        instance.save()
        return instance
    
    def save(self, model):
        morph_class = self.get_morph_class()
        local_key = self.get_local_key()
        
        model.set_attribute(self._morph_type, morph_class)
        model.set_attribute(self._morph_id, self._parent.get_attribute(local_key))
        
        model.save()
        return model
