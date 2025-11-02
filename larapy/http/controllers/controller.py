"""
Controller Base Class

Base controller providing middleware management and helper methods.
"""

from typing import Any, Callable, Dict, List, Optional, Union


class Controller:
    """
    Base controller class matching Laravel's Controller.

    Provides middleware management and helper methods for controllers.
    """

    _middleware: List[Dict[str, Any]] = []

    def __init__(self) -> None:
        """Initialize controller."""
        self._middleware = []

    @classmethod
    def middleware(cls, middleware: Union[str, List[str], Callable], **options: Any) -> None:
        """
        Register middleware for controller.

        Args:
            middleware: Middleware name(s) or callable
            **options: Middleware options (only, except)

        Example:
            class UserController(Controller):
                def __init__(self):
                    super().__init__()
                    self.middleware('auth')
                    self.middleware('admin', only=['destroy'])
                    self.middleware('throttle:60,1', except_=['index', 'show'])
        """
        if not hasattr(cls, "_middleware_stack"):
            cls._middleware_stack = []

        middleware_list = [middleware] if isinstance(middleware, (str, Callable)) else middleware

        for m in middleware_list:
            middleware_config = {"middleware": m}

            if "only" in options:
                middleware_config["only"] = (
                    options["only"] if isinstance(options["only"], list) else [options["only"]]
                )

            if "except_" in options:
                middleware_config["except"] = (
                    options["except_"]
                    if isinstance(options["except_"], list)
                    else [options["except_"]]
                )
            elif "except" in options:
                middleware_config["except"] = (
                    options["except"]
                    if isinstance(options["except"], list)
                    else [options["except"]]
                )

            cls._middleware_stack.append(middleware_config)

    def getMiddleware(self) -> List[Dict[str, Any]]:
        """
        Get controller middleware.

        Returns:
            List of middleware configurations
        """
        if hasattr(self.__class__, "_middleware_stack"):
            return self.__class__._middleware_stack
        return []

    def getMiddlewareForMethod(self, method: str) -> List[str]:
        """
        Get middleware for specific method.

        Args:
            method: Method name

        Returns:
            List of middleware names
        """
        middleware_list = []

        for config in self.getMiddleware():
            if "only" in config and method not in config["only"]:
                continue

            if "except" in config and method in config["except"]:
                continue

            middleware_list.append(config["middleware"])

        return middleware_list

    def callAction(self, method: str, parameters: List[Any]) -> Any:
        """
        Call controller method with parameters.

        Args:
            method: Method name
            parameters: Method parameters

        Returns:
            Method result
        """
        if not hasattr(self, method):
            raise AttributeError(f"Method {method} does not exist on {self.__class__.__name__}")

        return getattr(self, method)(*parameters)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Handle controller invocation for single action controllers.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Action result
        """
        if hasattr(self, "__invoke"):
            return self.__invoke(*args, **kwargs)

        raise NotImplementedError(f"{self.__class__.__name__} does not implement __invoke method")


class ResourceController(Controller):
    """
    Resource controller base class for RESTful operations.

    Provides standard CRUD methods:
    - index: Display a listing
    - create: Show creation form
    - store: Store new resource
    - show: Display resource
    - edit: Show edit form
    - update: Update resource
    - destroy: Delete resource
    """

    def index(self):
        """
        Display a listing of the resource.

        Returns:
            Response with resource listing
        """
        raise NotImplementedError("Method index not implemented")

    def create(self):
        """
        Show the form for creating a new resource.

        Returns:
            Response with creation form
        """
        raise NotImplementedError("Method create not implemented")

    def store(self, request):
        """
        Store a newly created resource in storage.

        Args:
            request: HTTP request

        Returns:
            Response with created resource
        """
        raise NotImplementedError("Method store not implemented")

    def show(self, id):
        """
        Display the specified resource.

        Args:
            id: Resource identifier

        Returns:
            Response with resource
        """
        raise NotImplementedError("Method show not implemented")

    def edit(self, id):
        """
        Show the form for editing the specified resource.

        Args:
            id: Resource identifier

        Returns:
            Response with edit form
        """
        raise NotImplementedError("Method edit not implemented")

    def update(self, request, id):
        """
        Update the specified resource in storage.

        Args:
            request: HTTP request
            id: Resource identifier

        Returns:
            Response with updated resource
        """
        raise NotImplementedError("Method update not implemented")

    def destroy(self, id):
        """
        Remove the specified resource from storage.

        Args:
            id: Resource identifier

        Returns:
            Response confirming deletion
        """
        raise NotImplementedError("Method destroy not implemented")


class ApiResourceController(Controller):
    """
    API resource controller for RESTful APIs (without create/edit views).

    Provides API-focused CRUD methods:
    - index: List resources
    - store: Create resource
    - show: Display resource
    - update: Update resource
    - destroy: Delete resource
    """

    def index(self):
        """Display a listing of the resource."""
        raise NotImplementedError("Method index not implemented")

    def store(self, request):
        """Store a newly created resource."""
        raise NotImplementedError("Method store not implemented")

    def show(self, id):
        """Display the specified resource."""
        raise NotImplementedError("Method show not implemented")

    def update(self, request, id):
        """Update the specified resource."""
        raise NotImplementedError("Method update not implemented")

    def destroy(self, id):
        """Remove the specified resource."""
        raise NotImplementedError("Method destroy not implemented")
