from typing import Dict, Optional


class MorphMap:
    
    _map: Dict[str, str] = {}
    _reverse_map: Dict[str, str] = {}
    
    @classmethod
    def set(cls, morph_map: Dict[str, str]) -> None:
        cls._map = morph_map.copy()
        cls._reverse_map = {v: k for k, v in morph_map.items()}
    
    @classmethod
    def get_map(cls) -> Dict[str, str]:
        return cls._map.copy()
    
    @classmethod
    def get_alias(cls, class_name: str) -> Optional[str]:
        return cls._reverse_map.get(class_name)
    
    @classmethod
    def get_class(cls, alias: str) -> Optional[str]:
        return cls._map.get(alias)
    
    @classmethod
    def resolve_type(cls, morph_type: str) -> str:
        if morph_type in cls._map:
            return cls._map[morph_type]
        return morph_type
    
    @classmethod
    def get_morph_alias(cls, class_name: str) -> str:
        if class_name in cls._reverse_map:
            return cls._reverse_map[class_name]
        return class_name
    
    @classmethod
    def clear(cls) -> None:
        cls._map = {}
        cls._reverse_map = {}
