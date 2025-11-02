from typing import Any


class AuthorizesRequests:
    """Mixin for controllers to add authorization methods."""

    def authorize(self, ability: str, arguments: Any = None):
        """Authorize the request or throw exception."""
        gate = self.container.make("gate")
        gate.authorize(ability, arguments)

    def authorize_for_user(self, user, ability: str, arguments: Any = None):
        """Authorize for a specific user."""
        gate = self.container.make("gate")
        gate.for_user(user).authorize(ability, arguments)

    def can(self, ability: str, arguments: Any = None) -> bool:
        """Check if current user can perform ability."""
        gate = self.container.make("gate")
        return gate.allows(ability, arguments)

    def cannot(self, ability: str, arguments: Any = None) -> bool:
        """Check if current user cannot perform ability."""
        gate = self.container.make("gate")
        return gate.denies(ability, arguments)
