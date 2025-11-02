from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import secrets
from larapy.auth.authenticatable import Authenticatable
from larapy.auth.user_provider import UserProvider


class Guard(ABC):
    @abstractmethod
    def check(self) -> bool:
        pass

    @abstractmethod
    def guest(self) -> bool:
        pass

    @abstractmethod
    def user(self) -> Optional[Authenticatable]:
        pass

    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def validate(self, credentials: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        pass


class SessionGuard(Guard):
    def __init__(self, name: str, provider: UserProvider, session=None, request=None):
        self._name = name
        self._provider = provider
        self._session = session
        self._request = request
        self._user: Optional[Authenticatable] = None
        self._logout_other_devices = False

    def check(self) -> bool:
        return self.user() is not None

    def guest(self) -> bool:
        return not self.check()

    def user(self) -> Optional[Authenticatable]:
        if self._user is not None:
            return self._user

        user_id = self._getUserFromSession()

        if user_id:
            self._user = self._provider.retrieveById(user_id)

        if self._user is None:
            remember_token = self._getRememberToken()
            if remember_token:
                self._user = self._getUserByRememberToken(remember_token)

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
        user = self._provider.retrieveByCredentials(credentials)

        if user and self._provider.validateCredentials(user, credentials):
            self.login(user, remember)

            self._provider.rehashPasswordIfRequired(user, credentials)

            return True

        return False

    def attemptWhen(self, credentials: Dict[str, Any], callback, remember: bool = False) -> bool:
        user = self._provider.retrieveByCredentials(credentials)

        if user and self._provider.validateCredentials(user, credentials):
            if callable(callback) and callback(user):
                self.login(user, remember)
                self._provider.rehashPasswordIfRequired(user, credentials)
                return True

        return False

    def once(self, credentials: Dict[str, Any]) -> bool:
        if self.validate(credentials):
            self._user = self._provider.retrieveByCredentials(credentials)
            return True

        return False

    def login(self, user: Authenticatable, remember: bool = False) -> None:
        self._updateSession(user.getAuthIdentifier())

        if remember:
            self._queueRememberCookie(user)

        self._user = user

    def loginUsingId(self, user_id, remember: bool = False) -> Optional[Authenticatable]:
        user = self._provider.retrieveById(user_id)

        if user:
            self.login(user, remember)
            return user

        return None

    def viaRemember(self) -> bool:
        return self._getUserFromSession() is None and self.user() is not None

    def logout(self) -> None:
        user = self.user()

        self._clearUserSession()

        if user and user.getRememberToken():
            self._provider.updateRememberToken(user, "")

        self._user = None

    def logoutOtherDevices(self, password: str) -> bool:
        if not self._session:
            return False

        user = self.user()
        if not user:
            return False

        credentials = {user.getAuthIdentifierName(): user.getAuthIdentifier(), "password": password}

        if not self._provider.validateCredentials(user, credentials):
            return False

        self._logout_other_devices = True
        return True

    def _getUserFromSession(self):
        if self._session:
            return self._session.get(f"auth_{self._name}")
        return None

    def _updateSession(self, user_id) -> None:
        if self._session:
            self._session.put(f"auth_{self._name}", user_id)
            self._session.regenerate()

    def _clearUserSession(self) -> None:
        if self._session:
            self._session.forget(f"auth_{self._name}")

    def _queueRememberCookie(self, user: Authenticatable) -> None:
        token = secrets.token_urlsafe(60)
        self._provider.updateRememberToken(user, token)

        if self._request:
            cookie_name = f"remember_{self._name}_{user.getAuthIdentifierName()}"
            self._request._remember_cookie = {
                "name": cookie_name,
                "value": f"{user.getAuthIdentifier()}|{token}",
                "minutes": 43200,
            }

    def _getRememberToken(self) -> Optional[str]:
        if self._request:
            cookie_name = f"remember_{self._name}_id"
            cookie_value = self._request.cookie(cookie_name)
            if cookie_value and "|" in cookie_value:
                return cookie_value
        return None

    def _getUserByRememberToken(self, remember_cookie: str) -> Optional[Authenticatable]:
        parts = remember_cookie.split("|", 1)
        if len(parts) == 2:
            user_id, token = parts
            return self._provider.retrieveByToken(user_id, token)
        return None

    def setSession(self, session) -> None:
        self._session = session

    def setRequest(self, request) -> None:
        self._request = request

    def getName(self) -> str:
        return self._name
