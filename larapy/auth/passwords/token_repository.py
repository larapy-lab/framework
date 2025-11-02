from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets
import hashlib


class TokenRepository:

    def __init__(self, connection, table: str = "password_resets", expires: int = 3600):
        self.connection = connection
        self.table = table
        self.expires = expires
        self._tokens: Dict[str, Dict[str, Any]] = {}

    async def create(self, email: str) -> str:
        await self.delete_existing(email)

        token = self._create_new_token()

        hashed_token = self._hash_token(token)

        await self.connection.execute(
            f"INSERT INTO {self.table} (email, token, created_at) VALUES (?, ?, ?)",
            (email, hashed_token, datetime.utcnow()),
        )

        return token

    async def exists(self, email: str, token: str) -> bool:
        record = await self.get_record(email, token)
        return record is not None

    async def recently_created_token(self, email: str) -> bool:
        record = await self._get_record_by_email(email)

        if not record:
            return False

        created_at = record["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return (datetime.utcnow() - created_at).total_seconds() < 60

    async def get_record(self, email: str, token: str) -> Optional[Dict[str, Any]]:
        record = await self._get_record_by_email(email)

        if not record:
            return None

        if not self._token_matches(token, record["token"]):
            return None

        return record

    async def _get_record_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        result = await self.connection.execute(
            f"SELECT * FROM {self.table} WHERE email = ? ORDER BY created_at DESC LIMIT 1", (email,)
        )

        row = await result.fetchone()

        if not row:
            return None

        return {"email": row[0], "token": row[1], "created_at": row[2]}

    def _token_matches(self, token: str, hashed_token: str) -> bool:
        return self._hash_token(token) == hashed_token

    async def delete(self, email: str) -> None:
        await self.connection.execute(f"DELETE FROM {self.table} WHERE email = ?", (email,))

    async def delete_existing(self, email: str) -> None:
        await self.delete(email)

    async def delete_expired(self) -> None:
        expires_at = datetime.utcnow() - timedelta(seconds=self.expires)

        await self.connection.execute(
            f"DELETE FROM {self.table} WHERE created_at < ?", (expires_at,)
        )

    def _create_new_token(self) -> str:
        return secrets.token_urlsafe(40)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def create_sync(self, email: str) -> str:
        self.delete_existing_sync(email)

        token = self._create_new_token()

        self._tokens[email] = {"token": self._hash_token(token), "created_at": datetime.utcnow()}

        return token

    def exists_sync(self, email: str, token: str) -> bool:
        if email not in self._tokens:
            return False

        record = self._tokens[email]
        return self._token_matches(token, record["token"])

    def delete_existing_sync(self, email: str) -> None:
        if email in self._tokens:
            del self._tokens[email]

    def recently_created_token_sync(self, email: str) -> bool:
        if email not in self._tokens:
            return False

        created_at = self._tokens[email]["created_at"]
        return (datetime.utcnow() - created_at).total_seconds() < 60
