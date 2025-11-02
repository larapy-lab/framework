"""
HTTP Route

Represents an individual route with URI pattern, HTTP methods, and action.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Union


class Route:
    """
    HTTP Route matching Laravel's Route class.

    Handles route matching, parameter extraction, and action execution.
    """

    def __init__(
        self, methods: Union[str, List[str]], uri: str, action: Union[Callable, str, Dict[str, Any]]
    ) -> None:
        """
        Initialize a route.

        Args:
            methods: HTTP method(s) (GET, POST, PUT, etc.)
            uri: URI pattern with optional parameters
            action: Route action (callable, controller string, or dict)
        """
        self._methods = [methods] if isinstance(methods, str) else methods
        self._methods = [m.upper() for m in self._methods]

        if "GET" in self._methods and "HEAD" not in self._methods:
            self._methods.append("HEAD")

        self._uri = uri if uri.startswith("/") else "/" + uri
        self._action = self._parse_action(action)
        self._parameters: Dict[str, Any] = {}
        self._parameter_names: List[str] = []
        self._where: Dict[str, str] = {}
        self._compiled_pattern: Optional[re.Pattern] = None
        self._name: Optional[str] = None
        self._name_prefix: Optional[str] = None
        self._middleware: List[str] = []
        self._bindings: Dict[str, Dict[str, Any]] = {}
        self._with_trashed: bool = False

        self._compile()

    def _parse_action(self, action: Union[Callable, str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse action into standardized dictionary format."""
        if callable(action):
            return {"uses": action}
        elif isinstance(action, str):
            return {"uses": action}
        elif isinstance(action, dict):
            return action
        else:
            return {"uses": action}

    def _compile(self) -> None:
        """Compile the route URI pattern to a regex."""
        uri = self._uri.strip("/")

        if not uri:
            self._compiled_pattern = re.compile("^/$")
            return

        pattern = uri
        # Match {param} or {param?} or {param:field} or {param:field?}
        param_pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z_][a-zA-Z0-9_]*))?\??}"

        segments = []
        last_end = 0

        for match in re.finditer(param_pattern, uri):
            param_name = match.group(1)
            binding_field = match.group(2)  # Will be None if no :field specified
            is_optional = match.group(0).endswith("?}")

            self._parameter_names.append(param_name)

            # If binding field specified, store it in bindings config
            # The model class will be set later by Router.model() or bind()
            if binding_field and param_name not in self._bindings:
                self._bindings[param_name] = {"field": binding_field}

            if param_name in self._where:
                constraint = self._where[param_name]
            else:
                constraint = "[^/]+"

            segment_before = uri[last_end : match.start()]

            if is_optional and segment_before.endswith("/"):
                segments.append(segment_before[:-1])
                segments.append(f"(?:/(?P<{param_name}>{constraint}))?")
            else:
                segments.append(segment_before)
                if is_optional:
                    segments.append(f"(?:(?P<{param_name}>{constraint}))?")
                else:
                    segments.append(f"(?P<{param_name}>{constraint})")

            last_end = match.end()

        segments.append(uri[last_end:])
        pattern = "".join(segments)

        pattern = f"^/{pattern}$"
        self._compiled_pattern = re.compile(pattern)

    def matches(self, uri: str, method: str) -> bool:
        """
        Check if route matches the given URI and method.

        Args:
            uri: Request URI
            method: HTTP method

        Returns:
            True if route matches
        """
        if method.upper() not in self._methods:
            return False

        uri = uri.strip("/") if uri != "/" else "/"
        uri = "/" + uri if uri and not uri.startswith("/") else uri

        if self._compiled_pattern is None:
            return False

        match = self._compiled_pattern.match(uri)
        if match:
            self._parameters = {k: v for k, v in match.groupdict().items() if v is not None}
            return True

        return False

    def bind(self, container: Any) -> "Route":
        """
        Bind route to container for dependency injection.

        Args:
            container: Service container

        Returns:
            Self for chaining
        """
        self._action["container"] = container
        return self

    def run(self) -> Any:
        """
        Execute the route action.

        Returns:
            Action result
        """
        action = self._action.get("uses")

        if callable(action):
            container = self._action.get("container")
            if container:
                return container.call(action, self._parameters)
            else:
                return action(**self._parameters)

        return None

    def name(self, name: str) -> "Route":
        """
        Set the route name.

        Args:
            name: Route name

        Returns:
            Self for chaining
        """
        if hasattr(self, "_name_prefix") and self._name_prefix:
            prefix = self._name_prefix.rstrip(".")
            name = name.lstrip(".")
            self._name = f"{prefix}.{name}"
        else:
            self._name = name

        if hasattr(self, "_collection"):
            self._collection.refreshNamedRoute(self)

        return self

    def getName(self) -> Optional[str]:
        """Get the route name."""
        return self._name

    def where(
        self, parameter: Union[str, Dict[str, str]], pattern: Optional[str] = None
    ) -> "Route":
        """
        Add parameter constraints.

        Args:
            parameter: Parameter name or dict of name:pattern
            pattern: Regex pattern (if parameter is string)

        Returns:
            Self for chaining
        """
        if isinstance(parameter, dict):
            self._where.update(parameter)
        else:
            if pattern is not None:
                self._where[parameter] = pattern

        self._compile()
        return self

    def whereNumber(self, parameter: str) -> "Route":
        """Constrain parameter to numbers."""
        return self.where(parameter, r"[0-9]+")

    def whereAlpha(self, parameter: str) -> "Route":
        """Constrain parameter to alphabetic characters."""
        return self.where(parameter, r"[a-zA-Z]+")

    def whereAlphaNumeric(self, parameter: str) -> "Route":
        """Constrain parameter to alphanumeric characters."""
        return self.where(parameter, r"[a-zA-Z0-9]+")

    def whereUuid(self, parameter: str) -> "Route":
        """Constrain parameter to UUID format."""
        return self.where(
            parameter, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        )

    def whereIn(self, parameter: str, values: List[str]) -> "Route":
        """Constrain parameter to specific values."""
        escaped_values = [re.escape(v) for v in values]
        pattern = "|".join(escaped_values)
        return self.where(parameter, pattern)

    def withTrashed(self) -> "Route":
        """
        Allow soft-deleted models to be resolved in route model binding.

        Returns:
            Self for chaining
        """
        self._with_trashed = True
        return self

    def getBindings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the binding configuration for this route.

        Returns:
            Dict mapping parameter names to binding config
        """
        return self._bindings

    def shouldIncludeTrashed(self) -> bool:
        """
        Check if soft-deleted models should be included in binding resolution.

        Returns:
            True if trashed models should be included
        """
        return self._with_trashed

    def middleware(self, *middleware: str) -> "Route":
        """
        Add middleware to the route.

        Args:
            middleware: Middleware names

        Returns:
            Self for chaining
        """
        self._middleware.extend(middleware)
        return self

    def getMiddleware(self) -> List[str]:
        """Get route middleware."""
        return self._middleware

    def methods(self) -> List[str]:
        """Get route HTTP methods."""
        return self._methods

    def getParameters(self) -> Dict[str, Any]:
        """Get extracted parameters."""
        return self._parameters

    def parameter(self, name: str, default: Any = None) -> Any:
        """Get a specific parameter."""
        return self._parameters.get(name, default)

    def setParameter(self, name: str, value: Any) -> "Route":
        """
        Set a parameter value.

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            Self for chaining
        """
        self._parameters[name] = value
        return self

    def uri(self) -> str:
        """Get the route URI."""
        return self._uri

    def getUri(self) -> str:
        """Get the route URI."""
        return self._uri

    def getMethods(self) -> List[str]:
        """Get allowed HTTP methods."""
        return self._methods

    def getAction(self, key: Optional[str] = None) -> Any:
        """Get route action or specific action attribute."""
        if key:
            return self._action.get(key)
        return self._action

    def setAction(self, action: Dict[str, Any]) -> "Route":
        """
        Set the route action.

        Args:
            action: Action dictionary

        Returns:
            Self for chaining
        """
        self._action = action
        return self

    def named(self, name: str) -> bool:
        """Check if route has the given name."""
        return self._name == name

    def parameters(self) -> Dict[str, Any]:
        """Get route parameters as dict."""
        return self._parameters

    @property
    def parameter_names(self):
        """Get parameter names (for middleware access)."""
        return self._parameter_names

    @property
    def bindings(self):
        """Get binding configuration (for middleware access)."""
        return self._bindings

    @property
    def with_trashed(self):
        """Get with_trashed flag (for middleware access)."""
        return self._with_trashed

    def __repr__(self) -> str:
        """String representation."""
        methods = "|".join(self._methods)
        return f"<Route [{methods}] {self._uri}>"
