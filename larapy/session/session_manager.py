from typing import Any, Dict, Optional, Callable
from larapy.session.store import Store
from larapy.session.array_session_handler import ArraySessionHandler
from larapy.session.file_session_handler import FileSessionHandler


class SessionManager:
    def __init__(self, container: Optional[Any] = None):
        self._container = container
        self._drivers: Dict[str, Store] = {}
        self._custom_creators: Dict[str, Callable] = {}
        self._config = {}

    def driver(self, name: Optional[str] = None) -> Store:
        name = name or self._get_default_driver()

        if name not in self._drivers:
            self._drivers[name] = self._create_driver(name)

        return self._drivers[name]

    def _create_driver(self, name: str) -> Store:
        if name in self._custom_creators:
            return self._call_custom_creator(name)

        method_name = f"_create_{name}_driver"
        if hasattr(self, method_name):
            return getattr(self, method_name)()

        raise ValueError(f"Driver [{name}] not supported.")

    def _create_array_driver(self) -> Store:
        return Store(
            name=self._config.get("cookie", "larapy_session"), handler=ArraySessionHandler()
        )

    def _create_file_driver(self) -> Store:
        path = self._config.get("files", "/tmp/sessions")
        lifetime = self._config.get("lifetime", 120)

        return Store(
            name=self._config.get("cookie", "larapy_session"),
            handler=FileSessionHandler(path, lifetime),
        )

    def extend(self, driver: str, callback: Callable):
        self._custom_creators[driver] = callback

    def _call_custom_creator(self, driver: str) -> Store:
        return self._custom_creators[driver](self._container)

    def _get_default_driver(self) -> str:
        return self._config.get("driver", "array")

    def get_default_driver(self) -> str:
        return self._get_default_driver()

    def set_default_driver(self, name: str):
        self._config["driver"] = name

    def set_config(self, config: Dict[str, Any]):
        self._config = config

    def __call__(self, driver: Optional[str] = None) -> Store:
        return self.driver(driver)
