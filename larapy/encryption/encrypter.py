import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from larapy.encryption.exceptions import (
    DecryptionException,
    InvalidKeyException,
    InvalidPayloadException,
)


class Encrypter:
    def __init__(self, key: str, cipher: str = "aes-256-cbc"):
        self.key = self._parse_key(key)
        self.cipher = cipher.lower()

        if self.cipher not in ["aes-256-cbc", "aes-256-gcm"]:
            raise InvalidKeyException(f"Unsupported cipher: {cipher}")

        if len(self.key) != 32:
            raise InvalidKeyException(f"Invalid key length. Expected 32 bytes, got {len(self.key)}")

    def encrypt(self, value: Any, serialize: bool = True) -> str:
        if serialize:
            value = json.dumps(value, separators=(",", ":"))
        else:
            value = str(value)

        iv = secrets.token_bytes(16)

        if self.cipher == "aes-256-cbc":
            encrypted = self._encrypt_cbc(value.encode("utf-8"), iv)
        else:
            encrypted = self._encrypt_gcm(value.encode("utf-8"), iv)

        payload = {
            "iv": base64.b64encode(iv).decode("utf-8"),
            "value": base64.b64encode(encrypted).decode("utf-8"),
            "mac": "",
        }

        if self.cipher == "aes-256-cbc":
            payload["mac"] = self._hash(payload["iv"], payload["value"])

        json_payload = json.dumps(payload, separators=(",", ":"))
        return base64.b64encode(json_payload.encode("utf-8")).decode("utf-8")

    def decrypt(self, payload: str, unserialize: bool = True) -> Any:
        payload_dict = self._get_json_payload(payload)

        iv = base64.b64decode(payload_dict["iv"])
        value = base64.b64decode(payload_dict["value"])

        if self.cipher == "aes-256-cbc":
            if not self._valid_mac(payload_dict):
                raise DecryptionException("MAC verification failed")

            decrypted = self._decrypt_cbc(value, iv)
        else:
            decrypted = self._decrypt_gcm(value, iv)

        decrypted_str = decrypted.decode("utf-8")

        if unserialize:
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str

        return decrypted_str

    def encrypt_string(self, value: str) -> str:
        return self.encrypt(value, serialize=False)

    def decrypt_string(self, payload: str) -> str:
        return self.decrypt(payload, unserialize=False)

    def _encrypt_cbc(self, data: bytes, iv: bytes) -> bytes:
        padded = self._pad(data)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    def _decrypt_cbc(self, data: bytes, iv: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()
        return self._unpad(padded)

    def _encrypt_gcm(self, data: bytes, iv: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return ciphertext + encryptor.tag

    def _decrypt_gcm(self, data: bytes, iv: bytes) -> bytes:
        if len(data) < 16:
            raise DecryptionException("Invalid encrypted data length")

        tag = data[-16:]
        ciphertext = data[:-16]

        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def _pad(self, data: bytes) -> bytes:
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding

    def _unpad(self, data: bytes) -> bytes:
        if not data:
            raise DecryptionException("Invalid padded data")

        padding_length = data[-1]

        if padding_length > 16 or padding_length == 0:
            raise DecryptionException("Invalid padding length")

        for byte in data[-padding_length:]:
            if byte != padding_length:
                raise DecryptionException("Invalid padding")

        return data[:-padding_length]

    def _hash(self, iv: str, value: str) -> str:
        payload = f"{iv}{value}"
        mac = hmac.new(self.key, payload.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(mac).decode("utf-8")

    def _valid_mac(self, payload: Dict[str, str]) -> bool:
        expected_mac = self._hash(payload["iv"], payload["value"])
        return hmac.compare_digest(
            payload.get("mac", "").encode("utf-8"), expected_mac.encode("utf-8")
        )

    def _get_json_payload(self, payload: str) -> Dict[str, str]:
        try:
            decoded = base64.b64decode(payload).decode("utf-8")
            parsed = json.loads(decoded)

            if not isinstance(parsed, dict):
                raise InvalidPayloadException("Invalid payload structure")

            if "iv" not in parsed or "value" not in parsed:
                raise InvalidPayloadException("Missing required payload fields")

            return parsed
        except (ValueError, json.JSONDecodeError) as e:
            raise InvalidPayloadException(f"Invalid payload: {str(e)}")

    def _parse_key(self, key: str) -> bytes:
        if key.startswith("base64:"):
            try:
                return base64.b64decode(key[7:])
            except Exception:
                raise InvalidKeyException("Invalid base64-encoded key")

        return key.encode("utf-8")

    @staticmethod
    def generate_key(cipher: str = "aes-256-cbc") -> str:
        if cipher.lower() in ["aes-256-cbc", "aes-256-gcm"]:
            key = secrets.token_bytes(32)
            return base64.b64encode(key).decode("utf-8")

        raise InvalidKeyException(f"Unsupported cipher: {cipher}")

    def get_key(self) -> bytes:
        return self.key
