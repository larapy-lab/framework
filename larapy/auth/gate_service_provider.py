from larapy.support import ServiceProvider
from larapy.auth.gate import Gate


class GateServiceProvider(ServiceProvider):
    """Service provider for authorization gate."""

    @property
    def singletons(self):
        return {"gate": lambda c: self._create_gate(c)}

    def _create_gate(self, container):
        """Create and configure the gate instance."""
        gate = Gate(container)
        gate.user_resolver = lambda: self._get_current_user()
        return gate

    def _get_current_user(self):
        """Get the current authenticated user."""
        try:
            request = self.app.make("request")
            if hasattr(request, "user"):
                user_method = getattr(request, "user")
                if callable(user_method):
                    return user_method()
                return user_method
            return None
        except:
            return None
