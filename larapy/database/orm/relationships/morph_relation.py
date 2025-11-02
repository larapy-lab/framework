from abc import abstractmethod
from typing import List, Optional
from larapy.database.orm.relationships.relation import Relation


class MorphRelation(Relation):
    
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
        super().__init__(query, parent, related_class, None, local_key)
        self._morph_name = morph_name
        self._morph_type = morph_type or f"{morph_name}_type"
        self._morph_id = morph_id or f"{morph_name}_id"
    
    def get_morph_type(self) -> str:
        return self._morph_type
    
    def get_morph_id(self) -> str:
        return self._morph_id
    
    def get_morph_name(self) -> str:
        return self._morph_name
    
    def get_morph_class(self) -> str:
        from larapy.database.orm.morph_map import MorphMap
        
        parent_class = self._parent.__class__
        module = parent_class.__module__
        name = parent_class.__name__
        full_class = f"{module}.{name}"
        
        return MorphMap.get_morph_alias(full_class)
    
    @abstractmethod
    def add_constraints(self):
        pass
    
    @abstractmethod
    def add_eager_constraints(self, models: List):
        pass
    
    @abstractmethod
    def match(self, models: List, results: List, relation: str) -> List:
        pass
    
    @abstractmethod
    def get_results(self):
        pass
