from typing import Optional, Dict, Any, Callable
from larapy.auth.guard import Guard
from larapy.auth.user_provider import UserProvider
from larapy.auth.authenticatable import Authenticatable


class RequestGuard(Guard):
    def __init__(self, callback: Callable, provider: UserProvider, name: str = "api"):
        self._callback = callback
        self._provider = provider
        self._name = name
        self._user: Optional[Authenticatable] = None
        self._request = None

    def check(self) -> bool:
        return self.user() is not None

    def guest(self) -> bool:
        return not self.check()

    def user(self) -> Optional[Authenticatable]:
        if self._user is not None:
            return self._user

        if self._request:
            self._user = self._callback(self._request)

        return self._user

    def id(self):
        if self.user():
            return self._user.getAuthIdentifier()
        return None

    def validate(self, credentials: Dict[str, Any]) -> bool:
        user = self._provider.retrieveByCredentials(credentials)

        if user is None:
            return False

        return self._provider.validateCredentials(user, credentials)

    def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        return False

    def setRequest(self, request) -> None:
        self._request = request
        self._user = None
