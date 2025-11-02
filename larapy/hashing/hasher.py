from typing import Dict, Optional

import bcrypt

from larapy.hashing.exceptions import HashingException


class Hasher:
    def __init__(
        self,
        driver: str = "bcrypt",
        rounds: Optional[int] = None,
        memory: Optional[int] = None,
        time: Optional[int] = None,
        threads: Optional[int] = None,
    ):
        self.driver = driver.lower()
        self.rounds = rounds or 12
        self.memory = memory or 65536
        self.time = time or 4
        self.threads = threads or 1

        if self.driver not in ["bcrypt", "argon2", "argon2i", "argon2id"]:
            raise HashingException(f"Unsupported hashing driver: {driver}")

    def make(self, value: str) -> str:
        if self.driver == "bcrypt":
            return self._make_bcrypt(value)
        elif self.driver in ["argon2", "argon2i", "argon2id"]:
            return self._make_argon2(value)

        raise HashingException(f"Driver {self.driver} not implemented")

    def check(self, value: str, hashed: str) -> bool:
        if not value or not hashed:
            return False

        try:
            if hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"):
                return self._check_bcrypt(value, hashed)
            elif hashed.startswith("$argon2"):
                return self._check_argon2(value, hashed)

            return False
        except Exception:
            return False

    def needs_rehash(self, hashed: str, options: Optional[Dict] = None) -> bool:
        try:
            if hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"):
                return self._needs_rehash_bcrypt(hashed, options)
            elif hashed.startswith("$argon2"):
                return self._needs_rehash_argon2(hashed, options)

            return True
        except Exception:
            return True

    def info(self, hashed: str) -> Dict:
        try:
            if hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"):
                parts = hashed.split("$")
                if len(parts) >= 3:
                    return {
                        "algo": "bcrypt",
                        "algoName": "bcrypt",
                        "options": {"cost": int(parts[2])},
                    }
            elif hashed.startswith("$argon2"):
                parts = hashed.split("$")
                if len(parts) >= 4:
                    params = {}
                    for param in parts[3].split(","):
                        if "=" in param:
                            key, val = param.split("=")
                            params[key] = int(val)

                    return {"algo": "argon2", "algoName": parts[1], "options": params}
        except Exception:
            pass

        return {"algo": None, "algoName": "unknown", "options": {}}

    def _make_bcrypt(self, value: str) -> str:
        hashed = bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt(rounds=self.rounds))
        return hashed.decode("utf-8")

    def _check_bcrypt(self, value: str, hashed: str) -> bool:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))

    def _needs_rehash_bcrypt(self, hashed: str, options: Optional[Dict] = None) -> bool:
        rounds = (options or {}).get("rounds", self.rounds)

        parts = hashed.split("$")
        if len(parts) < 3:
            return True

        try:
            current_rounds = int(parts[2])
            return current_rounds != rounds
        except (ValueError, IndexError):
            return True

    def _make_argon2(self, value: str) -> str:
        try:
            from argon2 import PasswordHasher
            from argon2.profiles import RFC_9106_LOW_MEMORY
        except ImportError:
            raise HashingException(
                "argon2-cffi package is required for Argon2 hashing. "
                "Install it with: pip install argon2-cffi"
            )

        hasher_type = self._get_argon2_type()

        ph = PasswordHasher(
            time_cost=self.time,
            memory_cost=self.memory,
            parallelism=self.threads,
            hash_len=32,
            salt_len=16,
            type=hasher_type,
        )

        return ph.hash(value)

    def _check_argon2(self, value: str, hashed: str) -> bool:
        try:
            from argon2 import PasswordHasher
            from argon2.exceptions import VerifyMismatchError
        except ImportError:
            raise HashingException("argon2-cffi package is required for Argon2 hashing")

        ph = PasswordHasher()

        try:
            ph.verify(hashed, value)
            return True
        except VerifyMismatchError:
            return False

    def _needs_rehash_argon2(self, hashed: str, options: Optional[Dict] = None) -> bool:
        try:
            from argon2 import PasswordHasher
        except ImportError:
            return True

        time = (options or {}).get("time", self.time)
        memory = (options or {}).get("memory", self.memory)
        threads = (options or {}).get("threads", self.threads)

        ph = PasswordHasher(time_cost=time, memory_cost=memory, parallelism=threads)

        try:
            return ph.check_needs_rehash(hashed)
        except Exception:
            return True

    def _get_argon2_type(self):
        try:
            from argon2 import Type
        except ImportError:
            raise HashingException("argon2-cffi package is required")

        if self.driver == "argon2i":
            return Type.I
        elif self.driver == "argon2id":
            return Type.ID
        else:
            return Type.ID
