from typing import Optional, Dict, Any, Callable
from larapy.auth.guard import Guard, SessionGuard
from larapy.auth.user_provider import UserProvider, DatabaseUserProvider
from larapy.auth.authenticatable import Authenticatable


class AuthManager:
    def __init__(self, session_manager=None):
        self._guards: Dict[str, Guard] = {}
        self._providers: Dict[str, UserProvider] = {}
        self._custom_guards: Dict[str, Callable] = {}
        self._custom_providers: Dict[str, Callable] = {}
        self._config: Dict[str, Any] = {}
        self._session_manager = session_manager
        self._default_guard: Optional[str] = None

    def guard(self, name: Optional[str] = None) -> Guard:
        name = name or self.getDefaultDriver()

        if name in self._guards:
            return self._guards[name]

        self._guards[name] = self._createGuard(name)
        return self._guards[name]

    def _createGuard(self, name: str) -> Guard:
        config = self._config.get("guards", {}).get(name, {})

        driver = config.get("driver", "session")

        if driver in self._custom_guards:
            return self._custom_guards[driver](name, config)

        if driver == "session":
            return self._createSessionGuard(name, config)

        raise ValueError(f"Auth driver [{driver}] is not supported")

    def _createSessionGuard(self, name: str, config: Dict[str, Any]) -> SessionGuard:
        provider_name = config.get("provider", "users")
        provider = self.createUserProvider(provider_name)

        session = None
        if self._session_manager:
            session = self._session_manager.driver()

        return SessionGuard(name, provider, session)

    def createUserProvider(self, name: str) -> UserProvider:
        if name in self._providers:
            return self._providers[name]

        config = self._config.get("providers", {}).get(name, {})

        driver = config.get("driver", "database")

        if driver in self._custom_providers:
            provider = self._custom_providers[driver](config)
        elif driver == "database":
            provider = DatabaseUserProvider(
                connection=config.get("connection"), table=config.get("table", "users")
            )
        else:
            raise ValueError(f"User provider driver [{driver}] is not supported")

        self._providers[name] = provider
        return provider

    def extend(self, driver: str, callback: Callable) -> None:
        self._custom_guards[driver] = callback

    def provider(self, driver: str, callback: Callable) -> None:
        self._custom_providers[driver] = callback

    def viaRequest(self, driver: str, callback: Callable) -> None:
        def request_guard(name: str, config: Dict[str, Any]) -> Guard:
            from larapy.auth.request_guard import RequestGuard

            provider_name = config.get("provider", "users")
            provider = self.createUserProvider(provider_name)
            return RequestGuard(callback, provider, name)

        self.extend(driver, request_guard)

    def setDefaultDriver(self, name: str) -> None:
        self._default_guard = name

    def getDefaultDriver(self) -> str:
        return self._default_guard or self._config.get("defaults", {}).get("guard", "web")

    def set_config(self, config: Dict[str, Any]) -> None:
        self._config = config

    def check(self) -> bool:
        return self.guard().check()

    def guest(self) -> bool:
        return self.guard().guest()

    def user(self) -> Optional[Authenticatable]:
        return self.guard().user()

    def id(self):
        return self.guard().id()

    def validate(self, credentials: Dict[str, Any]) -> bool:
        return self.guard().validate(credentials)

    def attempt(self, credentials: Dict[str, Any], remember: bool = False) -> bool:
        return self.guard().attempt(credentials, remember)

    def attemptWhen(self, credentials: Dict[str, Any], callback, remember: bool = False) -> bool:
        return self.guard().attemptWhen(credentials, callback, remember)

    def once(self, credentials: Dict[str, Any]) -> bool:
        return self.guard().once(credentials)

    def login(self, user: Authenticatable, remember: bool = False) -> None:
        self.guard().login(user, remember)

    def loginUsingId(self, user_id, remember: bool = False) -> Optional[Authenticatable]:
        return self.guard().loginUsingId(user_id, remember)

    def viaRemember(self) -> bool:
        return self.guard().viaRemember()

    def logout(self) -> None:
        self.guard().logout()

    def logoutOtherDevices(self, password: str) -> bool:
        return self.guard().logoutOtherDevices(password)

    def __call__(self, name: Optional[str] = None) -> Guard:
        return self.guard(name)
