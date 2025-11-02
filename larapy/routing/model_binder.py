"""
Model Binder

Handles implicit and explicit route model binding resolution.
Integrates with the router to automatically resolve models from route parameters.
"""

from typing import Any, Callable, Dict, Optional, Type
from larapy.database.orm.model import Model
from larapy.container.container import Container


class ModelNotFoundException(Exception):
    """Exception raised when model cannot be found during binding"""

    def __init__(self, model_class: Type[Model], value: Any, field: str = "id"):
        self.model_class = model_class
        self.value = value
        self.field = field
        super().__init__(
            f"No query results for model [{model_class.__name__}] with {field} = {value}"
        )


class ModelBinder:
    """
    Resolves route model binding for automatic model injection.

    Supports:
    - Implicit binding by primary key or custom field
    - Explicit binding with custom resolution logic
    - Soft-deleted model support
    - Scoped bindings for parent-child relationships
    """

    def __init__(self, container: Optional[Container] = None):
        """
        Initialize model binder.

        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.bindings: Dict[str, Callable] = {}
        self.scoped_bindings: Dict[str, Dict[str, Any]] = {}

    def bind(self, key: str, callback: Callable):
        """
        Register custom binding callback for a parameter.

        Args:
            key: Parameter name
            callback: Callable that receives value and returns model

        Example:
            binder.bind('user', lambda value: User.where('name', value).first())
        """
        self.bindings[key] = callback

    def model(self, key: str, model_class: Type[Model], callback: Optional[Callable] = None):
        """
        Register a model binding (simplified version of bind).

        Args:
            key: Parameter name
            model_class: Model class to resolve
            callback: Optional custom resolution callback
        """
        # Store scoped binding metadata for router integration
        self.scoped_bindings[key] = {"model_class": model_class, "field": "id"}  # Default field

        if callback:
            self.bindings[key] = callback
        else:
            # Default to implicit binding by primary key
            def default_callback(value):
                return self.resolveImplicit(model_class, value)

            self.bindings[key] = default_callback

    def resolve(
        self,
        parameter_name: str,
        value: Any,
        model_class: Optional[Type[Model]] = None,
        field: Optional[str] = None,
        with_trashed: bool = False,
    ) -> Optional[Model]:
        """
        Resolve model from route parameter.

        Args:
            parameter_name: Route parameter name
            value: Parameter value from route
            model_class: Model class to resolve (for implicit binding)
            field: Field to search by (default: primary key)
            with_trashed: Include soft-deleted models

        Returns:
            Resolved model instance or None

        Raises:
            ModelNotFoundException: If model cannot be found
        """
        # If a specific field is provided, use implicit binding with that field
        # This allows route-specific binding like {post:slug} to override global binding
        if field and model_class:
            return self.resolveImplicit(model_class, value, field, with_trashed)

        # Check for explicit binding
        if parameter_name in self.bindings:
            return self.resolveExplicit(self.bindings[parameter_name], value)

        # Use implicit binding if model class provided
        if model_class:
            return self.resolveImplicit(model_class, value, field, with_trashed)

        return None

    def resolveImplicit(
        self,
        model_class: Type[Model],
        value: Any,
        field: Optional[str] = None,
        with_trashed: bool = False,
    ) -> Model:
        """
        Resolve model using implicit binding (by primary key or custom field).

        Args:
            model_class: Model class to resolve
            value: Value to search for
            field: Field to search by (default: route key name)
            with_trashed: Include soft-deleted models

        Returns:
            Resolved model instance

        Raises:
            ModelNotFoundException: If model not found
        """
        # Create model instance to access methods
        instance = model_class()

        # Use custom resolution if model supports it
        if hasattr(instance, "resolveRouteBinding"):
            result = instance.resolveRouteBinding(value, field)
            if result:
                return result

        # Default resolution
        if field is None:
            field = instance.getRouteKeyName() if hasattr(instance, "getRouteKeyName") else "id"

        # Build query
        query = model_class.where(field, value)

        # Include soft-deleted if requested
        if with_trashed and hasattr(query, "withTrashed"):
            query = query.withTrashed()

        # Get first result
        result = query.first()

        if not result:
            raise ModelNotFoundException(model_class, value, field)

        return result

    def resolveExplicit(self, callback: Callable, value: Any) -> Any:
        """
        Resolve model using explicit binding callback.

        Args:
            callback: Custom resolution callback
            value: Parameter value

        Returns:
            Result from callback (typically a model instance)

        Raises:
            ModelNotFoundException: If callback returns None
        """
        result = callback(value)

        if result is None:
            raise ModelNotFoundException(Model, value, "custom")

        return result

    def resolveScoped(
        self, parent_model: Model, child_type: str, value: Any, field: Optional[str] = None
    ) -> Model:
        """
        Resolve scoped (child) binding based on parent model.

        Used for nested routes like /users/{user}/posts/{post}
        where post should belong to user.

        Args:
            parent_model: Parent model instance
            child_type: Child model class name
            value: Child value to search for
            field: Field to search by

        Returns:
            Resolved child model

        Raises:
            ModelNotFoundException: If child not found or doesn't belong to parent
        """
        # Use model's custom scoped resolution if available
        if hasattr(parent_model, "resolveChildRouteBinding"):
            result = parent_model.resolveChildRouteBinding(child_type, value, field)
            if result:
                return result

        # This requires relationship support which will be implemented later
        raise NotImplementedError(
            "Scoped bindings require relationship support. "
            "Implement resolveChildRouteBinding on your model."
        )

    def getBindingCallback(self, key: str) -> Optional[Callable]:
        """
        Get binding callback for a parameter.

        Args:
            key: Parameter name

        Returns:
            Binding callback or None
        """
        return self.bindings.get(key)

    def hasBinding(self, key: str) -> bool:
        """
        Check if parameter has custom binding.

        Args:
            key: Parameter name

        Returns:
            True if binding exists
        """
        return key in self.bindings

    def clear(self):
        """Clear all bindings"""
        self.bindings.clear()
        self.scoped_bindings.clear()
