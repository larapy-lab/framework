from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from larapy.auth.authenticatable import Authenticatable
from larapy.auth.user import User
from larapy.auth.passwords.hash import Hash


class UserProvider(ABC):
    @abstractmethod
    def retrieveById(self, identifier) -> Optional[Authenticatable]:
        pass

    @abstractmethod
    def retrieveByToken(self, identifier, token: str) -> Optional[Authenticatable]:
        pass

    @abstractmethod
    def updateRememberToken(self, user: Authenticatable, token: str) -> None:
        pass

    @abstractmethod
    def retrieveByCredentials(self, credentials: Dict[str, Any]) -> Optional[Authenticatable]:
        pass

    @abstractmethod
    def validateCredentials(self, user: Authenticatable, credentials: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def rehashPasswordIfRequired(
        self, user: Authenticatable, credentials: Dict[str, Any], force: bool = False
    ) -> None:
        pass


class DatabaseUserProvider(UserProvider):
    def __init__(
        self, connection: Optional[Any] = None, table: str = "users", hasher: Optional[Any] = None
    ):
        self._connection = connection
        self._table = table
        self._hasher = hasher or Hash
        self._users: Dict[Any, Dict[str, Any]] = {}

    def retrieveById(self, identifier) -> Optional[Authenticatable]:
        user_data = self._users.get(identifier)
        if user_data:
            return User(user_data)
        return None

    def retrieveByToken(self, identifier, token: str) -> Optional[Authenticatable]:
        user_data = self._users.get(identifier)
        if user_data and user_data.get("remember_token") == token:
            return User(user_data)
        return None

    def updateRememberToken(self, user: Authenticatable, token: str) -> None:
        user_id = user.getAuthIdentifier()
        if user_id in self._users:
            self._users[user_id]["remember_token"] = token
            user.setRememberToken(token)

    def retrieveByCredentials(self, credentials: Dict[str, Any]) -> Optional[Authenticatable]:
        query_credentials = {k: v for k, v in credentials.items() if k != "password"}

        if not query_credentials:
            return None

        for user_id, user_data in self._users.items():
            match = True
            for key, value in query_credentials.items():
                if callable(value):
                    continue
                if user_data.get(key) != value:
                    match = False
                    break

            if match:
                return User(user_data)

        return None

    def validateCredentials(self, user: Authenticatable, credentials: Dict[str, Any]) -> bool:
        password = credentials.get("password", "")
        return self._hasher.check(password, user.getAuthPassword())

    def rehashPasswordIfRequired(
        self, user: Authenticatable, credentials: Dict[str, Any], force: bool = False
    ) -> None:
        password = credentials.get("password", "")

        if force or self._hasher.needsRehash(user.getAuthPassword()):
            user_id = user.getAuthIdentifier()
            if user_id in self._users:
                new_hash = self._hasher.make(password)
                self._users[user_id][user.getAuthPasswordName()] = new_hash

    def createUser(self, attributes: Dict[str, Any]) -> Authenticatable:
        if "password" in attributes and not attributes["password"].startswith("$2"):
            attributes["password"] = self._hasher.make(attributes["password"])

        if "id" not in attributes:
            attributes["id"] = len(self._users) + 1

        self._users[attributes["id"]] = attributes
        return User(attributes)

    def getUsers(self) -> Dict[Any, Dict[str, Any]]:
        return self._users
