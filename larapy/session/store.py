import time
import secrets
from typing import Any, Optional, Dict, List, Callable


class Store:
    def __init__(self, name: str, handler: Any, session_id: Optional[str] = None):
        self._name = name
        self._handler = handler
        self._id = session_id
        self._attributes = {}
        self._started = False

    def start(self) -> bool:
        if not self._id:
            self._id = self._generate_session_id()

        self._load_session()

        if not self.has("_token"):
            self.regenerateToken()

        self._started = True
        return self._started

    def _load_session(self):
        if self._id:
            data = self._handler.read(self._id)
            if data:
                self._attributes = self._unserialize(data)
                return

        self._attributes = {}

    def save(self):
        self._age_flash_data()

        data = self._serialize(self._attributes)
        self._handler.write(self._id, data)

        self._started = False

    def getId(self) -> Optional[str]:
        return self._id

    def setId(self, session_id: str):
        self._id = session_id

    def isStarted(self) -> bool:
        return self._started

    def getName(self) -> str:
        return self._name

    def setName(self, name: str):
        self._name = name

    def invalidate(self) -> bool:
        self.flush()
        return self.migrate(True)

    def migrate(self, destroy: bool = False) -> bool:
        if destroy:
            self._handler.destroy(self._id)

        self.setId(self._generate_session_id())
        self._started = True

        return True

    def regenerate(self, destroy: bool = False) -> bool:
        return self.migrate(destroy)

    def _generate_session_id(self) -> str:
        return secrets.token_hex(20)

    def all(self) -> Dict[str, Any]:
        return self._attributes.copy()

    def exists(self, key: str) -> bool:
        return key in self._attributes

    def has(self, key: str) -> bool:
        return self.exists(key) and self._attributes[key] is not None

    def missing(self, key: str) -> bool:
        return not self.has(key)

    def get(self, key: str, default: Any = None) -> Any:
        if callable(default):
            return self._attributes.get(key, default())
        return self._attributes.get(key, default)

    def pull(self, key: str, default: Any = None) -> Any:
        value = self.get(key, default)
        self.forget(key)
        return value

    def put(self, key: str, value: Any = None):
        if isinstance(key, dict):
            for k, v in key.items():
                self._attributes[k] = v
        else:
            self._attributes[key] = value

    def push(self, key: str, value: Any):
        array = self.get(key, [])
        if not isinstance(array, list):
            array = [array]
        array.append(value)
        self.put(key, array)

    def increment(self, key: str, amount: int = 1) -> int:
        value = self.get(key, 0)
        self.put(key, value + amount)
        return value + amount

    def decrement(self, key: str, amount: int = 1) -> int:
        return self.increment(key, -amount)

    def flash(self, key: str, value: Any = True):
        self.put(key, value)
        self.push("_flash.new", key)
        self._remove_from_old_flash_data([key])

    def now(self, key: str, value: Any):
        self.put(key, value)
        self.push("_flash.old", key)

    def reflash(self):
        self._merge_new_flashes(self.get("_flash.old", []))
        self.put("_flash.old", [])

    def keep(self, keys: Optional[List[str]] = None):
        if keys is None:
            keys = []
        elif isinstance(keys, str):
            keys = [keys]

        self._merge_new_flashes(keys)
        self._remove_from_old_flash_data(keys)

    def _merge_new_flashes(self, keys: List[str]):
        new_flash = self.get("_flash.new", [])
        for key in keys:
            if key not in new_flash:
                new_flash.append(key)
        self.put("_flash.new", new_flash)

    def _remove_from_old_flash_data(self, keys: List[str]):
        old_flash = self.get("_flash.old", [])
        self.put("_flash.old", [k for k in old_flash if k not in keys])

    def _age_flash_data(self):
        for key in self.get("_flash.old", []):
            self.forget(key)

        self.put("_flash.old", self.get("_flash.new", []))
        self.put("_flash.new", [])

    def forget(self, keys: Optional[List[str]] = None):
        if keys is None:
            return

        if isinstance(keys, str):
            keys = [keys]

        for key in keys:
            if key in self._attributes:
                del self._attributes[key]

    def flush(self):
        self._attributes = {}

    def regenerateToken(self):
        self.put("_token", secrets.token_hex(20))

    def token(self) -> Optional[str]:
        return self.get("_token")

    def only(self, keys: List[str]) -> Dict[str, Any]:
        return {k: self.get(k) for k in keys if self.has(k)}

    def except_(self, keys: List[str]) -> Dict[str, Any]:
        return {k: v for k, v in self._attributes.items() if k not in keys}

    def _serialize(self, data: Dict[str, Any]) -> str:
        import json

        return json.dumps(data)

    def _unserialize(self, data: str) -> Dict[str, Any]:
        import json

        try:
            return json.loads(data)
        except:
            return {}

    def getHandler(self):
        return self._handler
