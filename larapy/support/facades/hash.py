from typing import Dict, Optional

from larapy.support.facades.facade import Facade


class Hash(Facade):
    @staticmethod
    def get_facade_accessor() -> str:
        return "hasher"

    @classmethod
    def make(cls, value: str) -> str:
        return cls.get_facade_root().make(value)

    @classmethod
    def check(cls, value: str, hashed: str) -> bool:
        return cls.get_facade_root().check(value, hashed)

    @classmethod
    def needs_rehash(cls, hashed: str, options: Optional[Dict] = None) -> bool:
        return cls.get_facade_root().needs_rehash(hashed, options)

    @classmethod
    def info(cls, hashed: str) -> Dict:
        return cls.get_facade_root().info(hashed)
