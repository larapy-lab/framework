from __future__ import annotations
from typing import Dict, Any, Optional, Callable, Union, TYPE_CHECKING
from .token_repository import TokenRepository
from ...mail.mailable import Mailable

if TYPE_CHECKING:
    from ..user_provider import UserProvider
    from ..user import User


class PasswordBroker:

    RESET_LINK_SENT = "passwords.sent"
    PASSWORD_RESET = "passwords.reset"
    INVALID_USER = "passwords.user"
    INVALID_TOKEN = "passwords.token"
    THROTTLED = "passwords.throttled"

    def __init__(
        self,
        tokens: TokenRepository,
        users: UserProvider,
        reset_view: str = "emails.password-reset",
        mail_callback: Optional[Callable] = None,
    ):
        self.tokens = tokens
        self.users = users
        self.reset_view = reset_view
        self.mail_callback = mail_callback

    async def send_reset_link(self, credentials: Dict[str, Any]) -> str:
        user = await self.get_user(credentials)

        if not user:
            return self.INVALID_USER

        user_email = user.get("email") if isinstance(user, User) else None
        if not user_email:
            return self.INVALID_USER

        if await self.tokens.recently_created_token(user_email):
            return self.THROTTLED

        token = await self.tokens.create(user_email)

        if self.mail_callback:
            await self.mail_callback(user, token)

        return self.RESET_LINK_SENT

    async def reset(self, credentials: Dict[str, Any], callback: Callable) -> str:
        user = await self.validate_reset(credentials)

        if isinstance(user, str):
            return user

        password = credentials.get("password")

        await callback(user, password)

        user_email = user.get("email") if isinstance(user, User) else None
        if user_email:
            await self.tokens.delete(user_email)

        return self.PASSWORD_RESET

    async def validate_reset(self, credentials: Dict[str, Any]) -> Union[User, str]:
        user = await self.get_user(credentials)

        if not user:
            return self.INVALID_USER

        token = credentials.get("token", "")
        user_email = user.get("email") if isinstance(user, User) else None

        if not user_email or not await self.tokens.exists(user_email, token):
            return self.INVALID_TOKEN

        return user

    async def get_user(self, credentials: Dict[str, Any]):
        email = credentials.get("email")

        if not email:
            return None

        user = self.users.retrieveByCredentials({"email": email})

        if user and self.validate_new_password(user, credentials):
            return user

        return None

    def validate_new_password(self, user, credentials: Dict[str, Any]) -> bool:
        password = credentials.get("password")
        password_confirmation = credentials.get("password_confirmation")

        if not password or not password_confirmation:
            return False

        return password == password_confirmation and len(password) >= 8

    def send_reset_link_sync(self, credentials: Dict[str, Any]) -> str:
        user = self.get_user_sync(credentials)

        if not user:
            return self.INVALID_USER

        user_email = user.get("email") if isinstance(user, User) else None
        if not user_email:
            return self.INVALID_USER

        if self.tokens.recently_created_token_sync(user_email):
            return self.THROTTLED

        token = self.tokens.create_sync(user_email)

        return self.RESET_LINK_SENT

    def get_user_sync(self, credentials: Dict[str, Any]):
        email = credentials.get("email")

        if not email:
            return None

        user = self.users.retrieveByCredentials({"email": email})

        if user:
            return user

        return None

    def reset_sync(self, credentials: Dict[str, Any], callback: Callable) -> str:
        user = self.validate_reset_sync(credentials)

        if isinstance(user, str):
            return user

        password = credentials.get("password")

        callback(user, password)

        user_email = user.get("email") if isinstance(user, User) else None
        if user_email:
            self.tokens.delete_existing_sync(user_email)

        return self.PASSWORD_RESET

    def validate_reset_sync(self, credentials: Dict[str, Any]) -> Union[User, str]:
        user = self.get_user_sync(credentials)

        if not user:
            return self.INVALID_USER

        token = credentials.get("token", "")
        user_email = user.get("email") if isinstance(user, User) else None

        if not user_email or not self.tokens.exists_sync(user_email, token):
            return self.INVALID_TOKEN

        return user
