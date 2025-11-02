import bcrypt
from typing import Optional


class Hash:
    @staticmethod
    def make(value: str, rounds: int = 10) -> str:
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(value.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def check(value: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def needsRehash(hashed: str, rounds: int = 10) -> bool:
        try:
            salt = hashed.encode("utf-8")
            cost = bcrypt.gensalt(rounds=rounds)
            return bcrypt.gensalt(rounds=rounds) != salt[:29]
        except (ValueError, AttributeError):
            return True

    @staticmethod
    def info(hashed: str) -> Optional[dict]:
        try:
            if hashed.startswith("$2y$"):
                hashed = "$2b$" + hashed[4:]

            parts = hashed.split("$")
            if len(parts) >= 4:
                return {"algo": parts[1], "algoName": "bcrypt", "options": {"cost": int(parts[2])}}
        except (ValueError, IndexError, AttributeError):
            pass

        return None
