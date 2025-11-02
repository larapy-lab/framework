from typing import Any

from larapy.support.facades.facade import Facade


class Crypt(Facade):
    @staticmethod
    def get_facade_accessor() -> str:
        return "encrypter"

    @classmethod
    def encrypt(cls, value: Any, serialize: bool = True) -> str:
        return cls.get_facade_root().encrypt(value, serialize)

    @classmethod
    def decrypt(cls, payload: str, unserialize: bool = True) -> Any:
        return cls.get_facade_root().decrypt(payload, unserialize)

    @classmethod
    def encrypt_string(cls, value: str) -> str:
        return cls.get_facade_root().encrypt_string(value)

    @classmethod
    def decrypt_string(cls, payload: str) -> str:
        return cls.get_facade_root().decrypt_string(payload)

    @classmethod
    def generate_key(cls, cipher: str = "aes-256-cbc") -> str:
        from larapy.encryption import Encrypter

        return Encrypter.generate_key(cipher)
