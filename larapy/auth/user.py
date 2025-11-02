from typing import Optional, Dict, Any
from larapy.auth.authenticatable import Authenticatable


class User(Authenticatable):
    def __init__(self, attributes: Optional[Dict[str, Any]] = None):
        self._attributes = attributes or {}
        self._remember_token: Optional[str] = self._attributes.get("remember_token")

    def getAuthIdentifierName(self) -> str:
        return "id"

    def getAuthIdentifier(self):
        return self._attributes.get(self.getAuthIdentifierName())

    def getAuthPasswordName(self) -> str:
        return "password"

    def getAuthPassword(self) -> str:
        return self._attributes.get(self.getAuthPasswordName(), "")

    def getRememberToken(self) -> Optional[str]:
        return self._remember_token

    def setRememberToken(self, value: Optional[str]) -> None:
        self._remember_token = value
        self._attributes["remember_token"] = value

    def getRememberTokenName(self) -> str:
        return "remember_token"

    def get(self, key: str, default=None):
        return self._attributes.get(key, default)

    def __getattr__(self, key: str):
        if key.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        return self._attributes.get(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            if not hasattr(self, "_attributes"):
                super().__setattr__("_attributes", {})
            self._attributes[key] = value

    def toDict(self) -> Dict[str, Any]:
        return self._attributes.copy()
