from typing import Optional


class Policy:
    """Base class for authorization policies."""

    def before(self, user, ability: str) -> Optional[bool]:
        """
        Optional before hook that runs before all checks.
        Return True to allow, False to deny, None to continue to ability check.
        """
        return None
