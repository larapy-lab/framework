from larapy.support.service_provider import ServiceProvider
from larapy.hashing import Hasher


class HashServiceProvider(ServiceProvider):
    def register(self) -> None:
        self.app.singleton("hasher", self._create_hasher)
        self.app.singleton(Hasher, self._create_hasher)

    def _create_hasher(self, app) -> Hasher:
        config = getattr(app, "_config", {})
        hashing_config = config.get("hashing", {})

        if not hashing_config:
            try:
                from config.hashing import HASHING

                hashing_config = HASHING
            except ImportError:
                pass

        driver = hashing_config.get("driver", "bcrypt")

        if driver == "bcrypt":
            bcrypt_config = hashing_config.get("bcrypt", {})
            return Hasher(driver="bcrypt", rounds=bcrypt_config.get("rounds", 12))
        elif driver in ["argon2", "argon2i", "argon2id"]:
            argon2_config = hashing_config.get("argon2", {})
            return Hasher(
                driver=driver,
                memory=argon2_config.get("memory", 65536),
                time=argon2_config.get("time", 4),
                threads=argon2_config.get("threads", 1),
            )

        return Hasher(driver=driver)

    def boot(self) -> None:
        pass
