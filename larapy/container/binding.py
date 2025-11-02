"""
Binding Class

Represents a binding in the container with its concrete implementation
and configuration options.
"""

from typing import Any, Callable, Optional


class Binding:
    """
    Represents a service binding in the container.

    A binding defines how a service should be resolved, including whether
    it should be shared (singleton) and its concrete implementation.
    """

    def __init__(
        self,
        concrete: Callable[..., Any],
        shared: bool = False,
        alias: Optional[str] = None,
    ) -> None:
        """
        Initialize a binding.

        Args:
            concrete: The concrete implementation (callable or class)
            shared: Whether this binding should be shared (singleton)
            alias: Optional alias for this binding
        """
        self.concrete = concrete
        self.shared = shared
        self.alias = alias

    def is_shared(self) -> bool:
        """Check if this binding is shared (singleton)."""
        return self.shared

    def get_concrete(self) -> Callable[..., Any]:
        """Get the concrete implementation."""
        return self.concrete

    def __repr__(self) -> str:
        """String representation of the binding."""
        shared_str = "shared" if self.shared else "not shared"
        return f"<Binding concrete={self.concrete.__name__} {shared_str}>"
