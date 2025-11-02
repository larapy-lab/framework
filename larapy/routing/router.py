"""
HTTP Router

Main router class matching Laravel's Router.
"""

from typing import Any, Callable, Dict, List, Optional, Union, Type
from larapy.routing.route import Route
from larapy.routing.route_collection import RouteCollection


class Router:
    """
    HTTP Router matching Laravel's Router class.

    Manages route registration, grouping, and dispatching.
    """

    def __init__(self, container: Optional[Any] = None) -> None:
        """
        Initialize the router.

        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.routes = RouteCollection()
        self._group_stack: List[Dict[str, Any]] = []
        self._patterns: Dict[str, str] = {}
        self._middleware: Dict[str, str] = {}
        self._middleware_groups: Dict[str, List[str]] = {}
        self._dispatcher: Optional[Any] = None
        self._binder: Optional[Any] = None

    def get(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register GET route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute(["GET", "HEAD"], uri, action)

    def post(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register POST route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute("POST", uri, action)

    def put(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register PUT route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute("PUT", uri, action)

    def patch(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register PATCH route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute("PATCH", uri, action)

    def delete(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register DELETE route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute("DELETE", uri, action)

    def options(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register OPTIONS route.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute("OPTIONS", uri, action)

    def any(self, uri: str, action: Union[Callable, str, Dict[str, Any]]) -> Route:
        """
        Register route for all HTTP methods.

        Args:
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute(
            ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], uri, action
        )

    def match(
        self, methods: List[str], uri: str, action: Union[Callable, str, Dict[str, Any]]
    ) -> Route:
        """
        Register route for specific HTTP methods.

        Args:
            methods: List of HTTP methods
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        return self.addRoute(methods, uri, action)

    def addRoute(
        self, methods: Union[str, List[str]], uri: str, action: Union[Callable, str, Dict[str, Any]]
    ) -> Route:
        """
        Add a route to the collection.

        Args:
            methods: HTTP method(s)
            uri: Route URI
            action: Route action

        Returns:
            Created route
        """
        route = Route(methods, self._prefix(uri), action)

        if self._group_stack:
            self._mergeGroupAttributes(route)

        if self._patterns:
            route.where(self._patterns)

        # Apply global model bindings to route parameters
        if self._binder:
            route_bindings = route.getBindings()

            for param_name in route._parameter_names:
                # Get existing binding from URI syntax (e.g., {post:slug})
                existing_binding = route_bindings.get(param_name, {})

                # Check scoped_bindings first (from model() calls - has metadata)
                if param_name in self._binder.scoped_bindings:
                    # Merge global binding with URI syntax binding
                    # URI syntax 'field' takes precedence over global binding field
                    global_binding = self._binder.scoped_bindings[param_name].copy()
                    if existing_binding.get("field"):
                        global_binding["field"] = existing_binding["field"]
                    route_bindings[param_name] = global_binding
                # Then check regular bindings (from bind() calls - just callback)
                elif param_name in self._binder.bindings and param_name not in route_bindings:
                    route_bindings[param_name] = {"callback": self._binder.bindings[param_name]}

        return self.routes.add(route)

    def group(
        self, attributes: Union[Dict[str, Any], List], routes: Optional[Callable] = None
    ) -> "Router":
        """
        Create a route group.

        Args:
            attributes: Group attributes (prefix, middleware, name, etc.) or middleware list
            routes: Routes callback

        Returns:
            Self for chaining
        """
        if isinstance(attributes, list):
            attributes = {"middleware": attributes}

        if routes is None:
            return RouteGroup(self, attributes)

        self._group_stack.append(attributes)
        routes(self)
        self._group_stack.pop()

        return self

    def prefix(self, prefix: str) -> "RouteGroup":
        """
        Create a route group with URI prefix.

        Args:
            prefix: URI prefix

        Returns:
            Route group
        """
        return RouteGroup(self, {"prefix": prefix})

    def name(self, name: str) -> "RouteGroup":
        """
        Create a route group with name prefix.

        Args:
            name: Name prefix

        Returns:
            Route group
        """
        return RouteGroup(self, {"name": name})

    def middleware(self, *middleware: str) -> "RouteGroup":
        """
        Create a route group with middleware.

        Args:
            middleware: Middleware names

        Returns:
            Route group
        """
        return RouteGroup(self, {"middleware": list(middleware)})

    def _prefix(self, uri: str) -> str:
        """
        Get the full URI with group prefixes.

        Args:
            uri: Route URI

        Returns:
            Prefixed URI
        """
        prefix_parts = []

        for group in self._group_stack:
            if "prefix" in group:
                prefix_parts.append(group["prefix"].strip("/"))

        if prefix_parts:
            prefix = "/".join(prefix_parts)
            uri = uri.strip("/")
            return f"{prefix}/{uri}" if uri else prefix

        return uri

    def _mergeGroupAttributes(self, route: Route) -> None:
        """
        Merge group attributes into route.

        Args:
            route: Route to merge attributes into
        """
        middleware = []
        name_parts = []

        for group in self._group_stack:
            if "middleware" in group:
                group_middleware = group["middleware"]
                if isinstance(group_middleware, str):
                    middleware.append(group_middleware)
                else:
                    middleware.extend(group_middleware)

            if "name" in group:
                name_parts.append(group["name"])

        if middleware:
            route.middleware(*middleware)

        if name_parts:
            name_prefix = ".".join([n.rstrip(".") for n in name_parts])
            original_name = route.getName()
            if original_name:
                route.name(f"{name_prefix}.{original_name}")
            else:
                route._name_prefix = name_prefix

    def pattern(self, key: str, pattern: str) -> "Router":
        """
        Set global parameter constraint.

        Args:
            key: Parameter name
            pattern: Regex pattern

        Returns:
            Self for chaining
        """
        self._patterns[key] = pattern
        return self

    def patterns(self, patterns: Dict[str, str]) -> "Router":
        """
        Set multiple global parameter constraints.

        Args:
            patterns: Dict of parameter:pattern

        Returns:
            Self for chaining
        """
        self._patterns.update(patterns)
        return self

    def bind(self, key: str, callback: Callable) -> "Router":
        """
        Register a custom route model binding.

        Args:
            key: Parameter name
            callback: Callback to resolve model

        Returns:
            Self for chaining
        """
        if self._binder is None:
            from larapy.routing.model_binder import ModelBinder

            self._binder = ModelBinder(self.container)

        self._binder.bind(key, callback)
        return self

    def model(self, key: str, model_class: Type, callback: Optional[Callable] = None) -> "Router":
        """
        Register a model binding.

        Args:
            key: Parameter name
            model_class: Model class to bind
            callback: Optional custom resolution callback

        Returns:
            Self for chaining
        """
        if self._binder is None:
            from larapy.routing.model_binder import ModelBinder

            self._binder = ModelBinder(self.container)

        self._binder.model(key, model_class, callback)
        return self

    def getBindings(self) -> Dict[str, Callable]:
        """
        Get all registered model bindings.

        Returns:
            Dictionary of bindings
        """
        if self._binder is None:
            return {}
        return self._binder.bindings

    def getBinder(self):
        """
        Get the model binder instance.

        Returns:
            ModelBinder instance or None
        """
        if self._binder is None:
            from larapy.routing.model_binder import ModelBinder

            self._binder = ModelBinder(self.container)
        return self._binder

    def aliasMiddleware(self, name: str, middleware: str) -> "Router":
        """
        Register middleware alias.

        Args:
            name: Middleware alias
            middleware: Middleware class name

        Returns:
            Self for chaining
        """
        self._middleware[name] = middleware
        return self

    def middlewareGroup(self, name: str, middleware: List[str]) -> "Router":
        """
        Register middleware group.

        Args:
            name: Group name
            middleware: List of middleware

        Returns:
            Self for chaining
        """
        self._middleware_groups[name] = middleware
        return self

    def resource(self, name: str, controller: str, **options: Any) -> List[Route]:
        """
        Register resource routes for a controller.

        Creates 7 RESTful routes:
        - GET /resource -> index
        - GET /resource/create -> create
        - POST /resource -> store
        - GET /resource/{id} -> show
        - GET /resource/{id}/edit -> edit
        - PUT/PATCH /resource/{id} -> update
        - DELETE /resource/{id} -> destroy

        Args:
            name: Resource name (e.g., 'users', 'posts')
            controller: Controller class name
            **options: Route options (only, except, names, parameters)

        Returns:
            List of created routes

        Example:
            router.resource('posts', 'PostController')
            router.resource('users', 'UserController', only=['index', 'show'])
            router.resource('photos', 'PhotoController', except_=['destroy'])
        """
        only = options.get("only", [])
        except_ = options.get("except_", options.get("except", []))
        names = options.get("names", {})
        parameters = options.get("parameters", {})

        param_name = parameters.get(name, name.rstrip("s") if name.endswith("s") else name)
        param_name = f"{{{param_name}}}"

        resource_routes = []
        route_definitions = [
            ("index", "GET", f"/{name}", None),
            ("create", "GET", f"/{name}/create", None),
            ("store", "POST", f"/{name}", None),
            ("show", "GET", f"/{name}/{param_name}", None),
            ("edit", "GET", f"/{name}/{param_name}/edit", None),
            ("update", ["PUT", "PATCH"], f"/{name}/{param_name}", None),
            ("destroy", "DELETE", f"/{name}/{param_name}", None),
        ]

        for method_name, http_method, uri, _ in route_definitions:
            if only and method_name not in only:
                continue

            if except_ and method_name in except_:
                continue

            action = f"{controller}@{method_name}"
            route = self.addRoute(http_method, uri, action)

            route_name = names.get(method_name, f"{name}.{method_name}")
            route.name(route_name)

            resource_routes.append(route)

        return resource_routes

    def apiResource(self, name: str, controller: str, **options: Any) -> List[Route]:
        """
        Register API resource routes (without create/edit).

        Creates 5 RESTful routes:
        - GET /resource -> index
        - POST /resource -> store
        - GET /resource/{id} -> show
        - PUT/PATCH /resource/{id} -> update
        - DELETE /resource/{id} -> destroy

        Args:
            name: Resource name
            controller: Controller class name
            **options: Route options

        Returns:
            List of created routes
        """
        options["except_"] = options.get("except_", []) + ["create", "edit"]
        return self.resource(name, controller, **options)

    def resources(self, resources: Dict[str, str], **options: Any) -> Dict[str, List[Route]]:
        """
        Register multiple resource controllers.

        Args:
            resources: Dict of name:controller pairs
            **options: Route options to apply to all resources

        Returns:
            Dict of name:routes pairs
        """
        all_routes = {}
        for name, controller in resources.items():
            all_routes[name] = self.resource(name, controller, **options)
        return all_routes

    def apiResources(self, resources: Dict[str, str], **options: Any) -> Dict[str, List[Route]]:
        """
        Register multiple API resource controllers.

        Args:
            resources: Dict of name:controller pairs
            **options: Route options to apply to all resources

        Returns:
            Dict of name:routes pairs
        """
        all_routes = {}
        for name, controller in resources.items():
            all_routes[name] = self.apiResource(name, controller, **options)
        return all_routes

    def getRoutes(self) -> RouteCollection:
        """Get the route collection."""
        return self.routes

    def dispatch(self, request: Any) -> Any:
        """
        Dispatch request to matching route.

        Args:
            request: HTTP request

        Returns:
            Route response
        """
        route = self.findRoute(request)

        if route is None:
            from larapy.http.response import Response

            return Response("Not Found", 404)

        request.setRouteParameters(route.parameters())

        if hasattr(route, "_name") and route._name:
            request.setRouteParameters({**route.parameters(), "_route_name": route._name})

        return self.runRoute(request, route)

    def findRoute(self, request: Any) -> Optional[Route]:
        """
        Find matching route for request.

        Args:
            request: HTTP request

        Returns:
            Matching route or None
        """
        path = request.path()
        method = request.method()

        return self.routes.match(path, method)

    def runRoute(self, request: Any, route: Route) -> Any:
        """
        Execute route action.

        Args:
            request: HTTP request
            route: Matched route

        Returns:
            Route response
        """
        action = route.getAction()

        if "uses" in action:
            uses = action["uses"]

            if callable(uses):
                return uses(request)

            elif isinstance(uses, str) and "@" in uses:
                return self.dispatchToController(request, route, uses)

        return None

    def dispatchToController(self, request: Any, route: Route, action: str) -> Any:
        """
        Dispatch request to controller.

        Args:
            request: HTTP request
            route: Matched route
            action: Controller action string (e.g., 'UserController@index')

        Returns:
            Controller response
        """
        if self._dispatcher is None:
            from larapy.http.controllers import ControllerDispatcher

            self._dispatcher = ControllerDispatcher(self.container)

        controller, method = action.split("@", 1)

        return self._dispatcher.dispatch(route, request, controller, method)


class RouteGroup:
    """
    Route group builder for fluent route registration.
    """

    def __init__(self, router: Router, attributes: Dict[str, Any]) -> None:
        """
        Initialize route group.

        Args:
            router: Parent router
            attributes: Group attributes
        """
        self.router = router
        self.attributes = attributes

    def group(self, routes: Callable) -> Router:
        """
        Execute the route group.

        Args:
            routes: Routes callback

        Returns:
            Router instance
        """
        return self.router.group(self.attributes, routes)

    def prefix(self, prefix: str) -> "RouteGroup":
        """Add prefix to group."""
        self.attributes["prefix"] = prefix
        return self

    def name(self, name: str) -> "RouteGroup":
        """Add name prefix to group."""
        self.attributes["name"] = name
        return self

    def middleware(self, *middleware: str) -> "RouteGroup":
        """Add middleware to group."""
        if "middleware" not in self.attributes:
            self.attributes["middleware"] = []
        self.attributes["middleware"].extend(middleware)
        return self
