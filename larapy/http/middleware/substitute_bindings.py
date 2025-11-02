"""
Substitute Bindings Middleware

Performs route model binding by substituting route parameters with resolved models.
This middleware runs in the middleware pipeline before controllers are executed.
"""

from typing import Callable
from larapy.http.request import Request
from larapy.http.response import Response
from larapy.routing.model_binder import ModelBinder, ModelNotFoundException


class SubstituteBindings:
    """
    Middleware that performs route model binding.

    Substitutes route parameters with bound model instances
    based on implicit or explicit binding rules.
    """

    def __init__(self, binder: ModelBinder):
        """
        Initialize middleware.

        Args:
            binder: Model binder instance
        """
        self.binder = binder

    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the request and substitute route bindings.

        Args:
            request: HTTP request
            next_handler: Next middleware handler

        Returns:
            HTTP response

        Raises:
            ModelNotFoundException: Converted to 404 response
        """
        # Get route from request
        route = getattr(request, "route", None)

        if route:
            try:
                # Perform model binding substitution
                self._substituteBindings(request, route)
            except ModelNotFoundException as e:
                # Convert to 404 response
                from larapy.http.response import JsonResponse

                return JsonResponse(
                    {
                        "message": str(e),
                        "model": e.model_class.__name__ if hasattr(e, "model_class") else "Model",
                        "value": e.value if hasattr(e, "value") else None,
                    },
                    status=404,
                )

        # Continue to next middleware
        return next_handler(request)

    def _substituteBindings(self, request: Request, route):
        """
        Substitute route parameters with bound models.

        Args:
            request: HTTP request
            route: Route object with parameters
        """
        # Get route parameters - handle both method and property
        # Check if parameters is callable (method) or a property/attribute
        params_attr = getattr(route, "parameters", None)
        if callable(params_attr):
            # It's a method - call it
            parameters = params_attr()
        elif params_attr is not None:
            # It's a property or attribute - access it directly
            parameters = params_attr
        else:
            parameters = {}

        parameter_names = getattr(route, "parameter_names", [])

        # Get binding configuration from route
        bindings = getattr(route, "bindings", {})
        with_trashed = getattr(route, "with_trashed", False)

        # Process each parameter
        for param_name in parameter_names:
            if param_name in parameters:
                value = parameters[param_name]

                # Skip if already a model instance
                if self._isModel(value):
                    continue

                # Get binding configuration
                binding_config = bindings.get(param_name, {})
                model_class = binding_config.get("model_class")
                field = binding_config.get("field")

                # Resolve model
                if model_class or self.binder.hasBinding(param_name):
                    try:
                        model = self.binder.resolve(
                            param_name, value, model_class, field, with_trashed
                        )

                        # Replace parameter value with model
                        parameters[param_name] = model

                        # Also set as request attribute for easy access
                        setattr(request, param_name, model)

                    except ModelNotFoundException:
                        # Re-raise to be caught by handle method
                        raise

    def _isModel(self, value) -> bool:
        """
        Check if value is a model instance.

        Args:
            value: Value to check

        Returns:
            True if value is a model instance
        """
        try:
            from larapy.database.orm.model import Model

            return isinstance(value, Model)
        except ImportError:
            return False
