from typing import Callable, Any, Dict


class Macroable:

    _macros: Dict[str, Callable] = {}

    @classmethod
    def macro(cls, name: str, callback: Callable) -> None:
        if not hasattr(cls, "_macros"):
            cls._macros = {}
        cls._macros[name] = callback

    @classmethod
    def mixin(cls, mixin_class: type) -> None:
        if not hasattr(cls, "_macros"):
            cls._macros = {}

        for name in dir(mixin_class):
            if not name.startswith("_"):
                attr = getattr(mixin_class, name)
                if callable(attr):
                    cls._macros[name] = attr

    @classmethod
    def has_macro(cls, name: str) -> bool:
        if not hasattr(cls, "_macros"):
            return False
        return name in cls._macros

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.__class__, "_macros") and name in self.__class__._macros:
            macro = self.__class__._macros[name]

            def wrapper(*args, **kwargs):
                return macro(self, *args, **kwargs)

            return wrapper

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
