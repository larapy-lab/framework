"""
Container Exceptions

Custom exceptions for the IoC container.
"""


class ContainerException(Exception):
    """Base exception for all container-related errors."""

    pass


class BindingResolutionException(ContainerException):
    """Raised when a binding cannot be resolved from the container."""

    def __init__(self, abstract: str, message: str = "") -> None:
        self.abstract = abstract
        if not message:
            message = f"Unable to resolve '{abstract}' from container"
        super().__init__(message)


class CircularDependencyException(ContainerException):
    """Raised when a circular dependency is detected during resolution."""

    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        message = f"Circular dependency detected: {' -> '.join(chain)}"
        super().__init__(message)
