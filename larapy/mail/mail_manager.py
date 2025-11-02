from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
from .mailer import Mailer
from .mailable import Address
from .transports import SmtpTransport

if TYPE_CHECKING:
    from ..views.engine import Engine


class MailManager:

    def __init__(self, config: Dict[str, Any], view_engine: Optional["Engine"] = None):
        self.config = config
        self.view_engine = view_engine
        self._mailers: Dict[str, Mailer] = {}
        self._custom_creators: Dict[str, Callable] = {}

    def mailer(self, name: Optional[str] = None) -> Mailer:
        name = name or self.get_default_driver()

        if name not in self._mailers:
            self._mailers[name] = self._resolve(name)

        return self._mailers[name]

    def _resolve(self, name: str) -> Mailer:
        config = self.get_config(name)

        if name in self._custom_creators:
            return self._custom_creators[name](config)

        driver = config.get("transport", "smtp")

        if driver == "smtp":
            transport = SmtpTransport(config)
        else:
            raise ValueError(f"Unsupported mail driver: {driver}")

        from_config = self.config.get("from", {})
        from_address = None
        if from_config.get("address"):
            from_address = Address(from_config["address"], from_config.get("name"))

        return Mailer(transport, from_address, self.view_engine)

    def get_config(self, name: str) -> Dict[str, Any]:
        mailers = self.config.get("mailers", {})

        if name not in mailers:
            raise ValueError(f"Mail configuration for '{name}' not found")

        return mailers[name]

    def get_default_driver(self) -> str:
        return self.config.get("default", "smtp")

    def extend(self, name: str, creator: Callable[[Dict[str, Any]], Mailer]) -> "MailManager":
        self._custom_creators[name] = creator
        return self

    def purge(self, name: Optional[str] = None) -> "MailManager":
        if name:
            if name in self._mailers:
                del self._mailers[name]
        else:
            self._mailers.clear()

        return self
