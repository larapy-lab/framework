"""
IoC Container Implementation

The container provides dependency injection and service resolution capabilities,
inspired by Laravel's service container.
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from larapy.container.binding import Binding
from larapy.container.exceptions import (
    BindingResolutionException,
    CircularDependencyException,
)

T = TypeVar("T")


class Container:
    """
    IoC (Inversion of Control) Container.

    Provides dependency injection, service binding, and automatic resolution
    of class dependencies through reflection and type hints.

    Example:
        >>> container = Container()
        >>> container.bind('cache', RedisCache)
        >>> cache = container.make('cache')
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._bindings: Dict[str, Binding] = {}
        self._instances: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
        self._resolved: Dict[str, bool] = {}
        self._resolving_callbacks: Dict[str, List[Callable]] = {}
        self._rebinding_callbacks: Dict[str, List[Callable]] = {}
        self._tags: Dict[str, List[str]] = {}
        self._contextual: Dict[str, Dict[str, Any]] = {}
        self._build_stack: List[str] = []
        self._with: List[Dict[str, Any]] = []

    def bind(
        self,
        abstract: Union[str, Type[T]],
        concrete: Optional[Callable[..., T]] = None,
        shared: bool = False,
    ) -> None:
        """
        Register a binding with the container.

        Args:
            abstract: The abstract type or identifier (string or class)
            concrete: The concrete implementation (callable or class)
            shared: Whether this binding should be shared (singleton)

        Example:
            >>> container.bind('cache', RedisCache)
            >>> container.bind(CacheInterface, RedisCache)
            >>> container.bind('config', lambda c: Config.load())
        """
        # Convert abstract to string if it's a class
        abstract_key = self._get_abstract_key(abstract)

        # If no concrete provided, use abstract as concrete
        if concrete is None:
            if isinstance(abstract, type):
                concrete = abstract
            else:
                raise BindingResolutionException(
                    abstract_key,
                    "Concrete implementation must be provided for string abstracts",
                )

        # Drop stale instances and resolved markers
        self._drop_stale_instances(abstract_key)

        # Store the binding
        self._bindings[abstract_key] = Binding(concrete=concrete, shared=shared)

        # If this was resolved before, fire rebinding callbacks
        if abstract_key in self._resolved:
            self._rebound(abstract_key)

    def singleton(
        self,
        abstract: Union[str, Type[T]],
        concrete: Optional[Callable[..., T]] = None,
    ) -> None:
        """
        Register a shared binding (singleton) in the container.

        Args:
            abstract: The abstract type or identifier
            concrete: The concrete implementation

        Example:
            >>> container.singleton('db', DatabaseManager)
            >>> db1 = container.make('db')
            >>> db2 = container.make('db')
            >>> assert db1 is db2  # Same instance
        """
        self.bind(abstract, concrete, shared=True)

    def instance(self, abstract: Union[str, Type[T]], instance: T) -> T:
        """
        Register an existing instance as shared in the container.

        Args:
            abstract: The abstract type or identifier
            instance: The instance to register

        Returns:
            The registered instance

        Example:
            >>> config = Config({'app_name': 'Larapy'})
            >>> container.instance('config', config)
        """
        abstract_key = self._get_abstract_key(abstract)

        # Remove any existing bindings
        self._drop_stale_instances(abstract_key)

        # Store the instance
        self._instances[abstract_key] = instance

        return instance

    def make(
        self,
        abstract: Union[str, Type[T]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Resolve the given type from the container.

        Args:
            abstract: The abstract type or identifier to resolve
            parameters: Optional parameters to pass to the constructor

        Returns:
            The resolved instance

        Raises:
            BindingResolutionException: If the type cannot be resolved
            CircularDependencyException: If a circular dependency is detected

        Example:
            >>> user_service = container.make(UserService)
            >>> cache = container.make('cache')
        """
        return self.resolve(abstract, parameters)

    def resolve(
        self,
        abstract: Union[str, Type[T]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Resolve a type from the container.

        This is an alias for make() following Laravel's convention.

        Args:
            abstract: The abstract type to resolve
            parameters: Optional constructor parameters

        Returns:
            The resolved instance
        """
        # Keep original abstract for auto-wiring
        original_abstract = abstract
        abstract_key = self._get_abstract_key(abstract)
        abstract_key = self._get_alias(abstract_key)

        # Check if we already have a singleton instance
        if abstract_key in self._instances:
            return self._instances[abstract_key]

        # Get parameters from contextual binding if available
        if parameters is None:
            parameters = {}

        # Merge with contextual parameters
        if self._with:
            parameters = {**self._with[-1], **parameters}

        # Get concrete implementation
        concrete = self._get_concrete(abstract_key, original_abstract)

        # Build the instance
        if self._is_buildable(concrete, abstract_key):
            instance = self._build(concrete, parameters)
        else:
            instance = self.make(concrete, parameters)

        # Call resolving callbacks
        self._call_resolving_callbacks(abstract_key, instance)

        # Mark as resolved
        self._resolved[abstract_key] = True

        # If this is a shared binding, store the instance
        if self._is_shared(abstract_key):
            self._instances[abstract_key] = instance

        return instance

    def call(
        self,
        callback: Callable[..., T],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Call the given callable, injecting its dependencies.

        Enables method injection by resolving dependencies from type hints.

        Args:
            callback: The callable to invoke
            parameters: Optional parameters to pass

        Returns:
            The result of the callable

        Example:
            >>> def send_email(user: User, mailer: MailManager):
            ...     mailer.send(user.email, 'Welcome!')
            >>> container.call(send_email, {'user': current_user})
        """
        if parameters is None:
            parameters = {}

        # Get the signature
        sig = inspect.signature(callback)

        # Resolve dependencies
        dependencies = self._resolve_dependencies(sig, parameters)

        # Call the callback
        return callback(**dependencies)

    def _build(self, concrete: Union[Type[T], Callable], parameters: Dict[str, Any]) -> T:
        """
        Instantiate a concrete instance of the given type.

        Args:
            concrete: The concrete class or callable
            parameters: Constructor parameters

        Returns:
            The instantiated object

        Raises:
            CircularDependencyException: If circular dependency detected
            BindingResolutionException: If unable to build
        """
        # If concrete is a callable (not a class), just call it
        if callable(concrete) and not inspect.isclass(concrete):
            return concrete(self, **parameters)

        # Check if it's a class
        if not inspect.isclass(concrete):
            raise BindingResolutionException(
                str(concrete),
                f"Target '{concrete}' is not instantiable",
            )

        # Check for circular dependencies
        concrete_key = self._get_abstract_key(concrete)
        if concrete_key in self._build_stack:
            chain = self._build_stack + [concrete_key]
            raise CircularDependencyException(chain)

        # Add to build stack
        self._build_stack.append(concrete_key)

        try:
            # Get constructor
            constructor = concrete.__init__

            # Check if this class has its own __init__ or inherits from object
            # If it inherits from object and has no custom __init__, just instantiate
            if constructor is object.__init__:
                # No custom constructor, just create instance
                instance = concrete()
            else:
                # Custom constructor, resolve dependencies
                sig = inspect.signature(constructor)
                dependencies = self._resolve_dependencies(sig, parameters)
                instance = concrete(**dependencies)

            # Remove from build stack
            self._build_stack.pop()

            return instance

        except Exception as e:
            # Clean up build stack on error
            if concrete_key in self._build_stack:
                self._build_stack.pop()
            raise

    def _resolve_dependencies(
        self,
        signature: inspect.Signature,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve all dependencies for a given signature.

        Uses type hints to automatically resolve dependencies from the container.

        Args:
            signature: The function/method signature
            parameters: Already provided parameters

        Returns:
            Dictionary of parameter names to resolved values
        """
        # Builtins that should not be auto-wired
        BUILTINS = (str, int, float, bool, list, dict, set, tuple, bytes, bytearray)

        dependencies = {}

        for param_name, param in signature.parameters.items():
            # Skip 'self' and 'cls'
            if param_name in ("self", "cls"):
                continue

            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Use provided parameter if available
            if param_name in parameters:
                dependencies[param_name] = parameters[param_name]
                continue

            # Try to resolve from type hint
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation

                # Skip forward references (strings) for now
                # They can't be easily resolved without the module context
                if isinstance(annotation, str):
                    if param.default != inspect.Parameter.empty:
                        # Don't add to dependencies, let Python use the default
                        continue
                    else:
                        raise BindingResolutionException(
                            param_name,
                            f"Unable to resolve forward reference '{annotation}'. Consider using actual class references.",
                        )

                # Skip builtin types - they should use defaults or be explicitly provided
                if annotation in BUILTINS:
                    if param.default != inspect.Parameter.empty:
                        continue
                    else:
                        raise BindingResolutionException(
                            param_name,
                            f"Cannot auto-wire builtin type '{annotation.__name__}' for parameter '{param_name}'. Provide a default or pass it explicitly.",
                        )

                # Check for contextual binding first
                contextual = self._get_contextual_concrete(annotation)
                if contextual is not None:
                    dependencies[param_name] = self.make(contextual)
                else:
                    # Try to resolve the type hint
                    try:
                        dependencies[param_name] = self.make(annotation)
                    except BindingResolutionException:
                        # If can't resolve and has default, don't add to dependencies
                        # Let Python use the default value
                        if param.default != inspect.Parameter.empty:
                            continue
                        else:
                            raise BindingResolutionException(
                                param_name,
                                f"Unable to resolve dependency '{param_name}' of type '{annotation}'",
                            )
            elif param.default != inspect.Parameter.empty:
                # Has default value, don't add to dependencies
                # Let Python use the default
                continue
            else:
                raise BindingResolutionException(
                    param_name,
                    f"Unresolvable dependency '{param_name}' with no type hint or default",
                )

        return dependencies

    def _get_concrete(self, abstract_key: str, original_abstract: Union[str, Type] = None) -> Any:
        """Get the concrete implementation for an abstract type."""
        if abstract_key in self._bindings:
            return self._bindings[abstract_key].get_concrete()

        # If no binding, return the original abstract if it's a class (for auto-wiring)
        # Otherwise return the abstract key
        if original_abstract is not None and inspect.isclass(original_abstract):
            return original_abstract
        return abstract_key

    def _is_buildable(self, concrete: Any, abstract: str) -> bool:
        """Check if the concrete type is buildable."""
        return concrete == abstract or inspect.isclass(concrete) or callable(concrete)

    def _is_shared(self, abstract: str) -> bool:
        """Check if an abstract type is shared (singleton)."""
        if abstract in self._bindings:
            return self._bindings[abstract].is_shared()
        return False

    def _get_abstract_key(self, abstract: Union[str, Type]) -> str:
        """Convert abstract to string key."""
        if isinstance(abstract, str):
            return abstract
        return f"{abstract.__module__}.{abstract.__qualname__}"

    def _get_alias(self, abstract: str) -> str:
        """Get the alias for an abstract type."""
        return self._aliases.get(abstract, abstract)

    def _drop_stale_instances(self, abstract: str) -> None:
        """Remove stale instances and bindings."""
        self._instances.pop(abstract, None)
        self._resolved.pop(abstract, None)

    def _rebound(self, abstract: str) -> None:
        """Fire rebinding callbacks for an abstract type."""
        instance = self.make(abstract)
        for callback in self._rebinding_callbacks.get(abstract, []):
            callback(self, instance)

    def _call_resolving_callbacks(self, abstract: str, instance: Any) -> None:
        """Call all resolving callbacks for an abstract type."""
        for callback in self._resolving_callbacks.get(abstract, []):
            callback(instance, self)

    def _get_contextual_concrete(self, abstract: Any) -> Optional[Any]:
        """Get contextual concrete implementation if available."""
        if not self._build_stack:
            return None

        # Get the current class being built
        current = self._build_stack[-1]

        # Check for contextual binding
        if current in self._contextual:
            abstract_key = self._get_abstract_key(abstract)
            return self._contextual[current].get(abstract_key)

        return None

    def bound(self, abstract: Union[str, Type]) -> bool:
        """
        Check if an abstract type is bound in the container.

        Args:
            abstract: The abstract type to check

        Returns:
            True if bound, False otherwise
        """
        abstract_key = self._get_abstract_key(abstract)
        return (
            abstract_key in self._bindings
            or abstract_key in self._instances
            or abstract_key in self._aliases
        )

    def has(self, abstract: Union[str, Type]) -> bool:
        """
        Alias for bound().

        Args:
            abstract: The abstract type to check

        Returns:
            True if bound, False otherwise
        """
        return self.bound(abstract)

    def alias(self, abstract: str, alias: str) -> None:
        """
        Alias an abstract type to another name.

        Args:
            abstract: The original abstract type
            alias: The alias name

        Example:
            >>> container.bind('app.cache', RedisCache)
            >>> container.alias('app.cache', 'cache')
            >>> cache = container.make('cache')  # Resolves 'app.cache'
        """
        self._aliases[alias] = abstract

    def tag(self, abstracts: List[Union[str, Type]], tags: List[str]) -> None:
        """
        Assign a set of tags to a given binding.

        Args:
            abstracts: List of abstract types to tag
            tags: List of tags to assign

        Example:
            >>> container.tag([RedisCache, FileCache], ['cache', 'storage'])
            >>> caches = container.tagged('cache')
        """
        for tag in tags:
            if tag not in self._tags:
                self._tags[tag] = []

            for abstract in abstracts:
                abstract_key = self._get_abstract_key(abstract)
                if abstract_key not in self._tags[tag]:
                    self._tags[tag].append(abstract_key)

    def tagged(self, tag: str) -> List[Any]:
        """
        Resolve all bindings for a given tag.

        Args:
            tag: The tag name

        Returns:
            List of resolved instances

        Example:
            >>> container.tag([SlackNotifier, EmailNotifier], ['notifiers'])
            >>> notifiers = container.tagged('notifiers')
            >>> for notifier in notifiers:
            ...     notifier.send('Hello!')
        """
        if tag not in self._tags:
            return []

        return [self.make(abstract) for abstract in self._tags[tag]]

    def flush(self) -> None:
        """
        Flush the container of all bindings and resolved instances.

        Useful for testing or resetting the container state.
        """
        self._bindings.clear()
        self._instances.clear()
        self._aliases.clear()
        self._resolved.clear()
        self._resolving_callbacks.clear()
        self._rebinding_callbacks.clear()
        self._tags.clear()
        self._contextual.clear()
        self._build_stack.clear()
        self._with.clear()

    def __repr__(self) -> str:
        """String representation of the container."""
        return (
            f"<Container bindings={len(self._bindings)} "
            f"instances={len(self._instances)} "
            f"aliases={len(self._aliases)}>"
        )
