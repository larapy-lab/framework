from larapy.support.service_provider import ServiceProvider
from larapy.encryption import Encrypter
from larapy.encryption.exceptions import InvalidKeyException


class EncryptionServiceProvider(ServiceProvider):
    def register(self) -> None:
        self.app.singleton("encrypter", self._create_encrypter)
        self.app.singleton(Encrypter, self._create_encrypter)

    def _create_encrypter(self, app) -> Encrypter:
        config = getattr(app, "_config", {})
        encryption_config = config.get("encryption", {})

        if not encryption_config:
            try:
                from config.encryption import ENCRYPTION

                encryption_config = ENCRYPTION
            except ImportError:
                pass

        key = encryption_config.get("key", "")
        cipher = encryption_config.get("cipher", "aes-256-cbc")

        if not key:
            raise InvalidKeyException(
                "No encryption key found. Please set APP_KEY in your .env file or "
                'generate one using: python -c "from larapy.encryption import Encrypter; '
                "print(f'base64:{Encrypter.generate_key()}')\""
            )

        return Encrypter(key, cipher)

    def boot(self) -> None:
        pass
