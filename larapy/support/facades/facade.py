from typing import Any, Optional


class Facade:
    _app: Optional[Any] = None
    _resolved_instances: dict = {}

    @classmethod
    def set_facade_application(cls, app: Any) -> None:
        cls._app = app

    @classmethod
    def get_facade_application(cls) -> Any:
        return cls._app

    @classmethod
    def get_facade_accessor(cls) -> str:
        raise NotImplementedError(
            f"Facade {cls.__name__} has not implemented get_facade_accessor method"
        )

    @classmethod
    def get_facade_root(cls) -> Any:
        accessor = cls.get_facade_accessor()

        if accessor in cls._resolved_instances:
            return cls._resolved_instances[accessor]

        if cls._app is None:
            raise RuntimeError("A facade application has not been set")

        instance = cls._app.make(accessor)
        cls._resolved_instances[accessor] = instance

        return instance

    @classmethod
    def clear_resolved_instances(cls) -> None:
        cls._resolved_instances = {}

    @classmethod
    def __getattr__(cls, name: str) -> Any:
        instance = cls.get_facade_root()

        if not hasattr(instance, name):
            raise AttributeError(f"{cls.__name__} facade does not have attribute {name}")

        attr = getattr(instance, name)

        if callable(attr):

            def wrapper(*args, **kwargs):
                return attr(*args, **kwargs)

            return wrapper

        return attr
