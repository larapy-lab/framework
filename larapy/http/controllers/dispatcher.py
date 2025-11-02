"""
Controller Dispatcher

Handles resolving and executing controller actions from routes.
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Union


class ControllerDispatcher:
    """
    Controller dispatcher for resolving and executing controller actions.

    Handles:
    - Parsing 'Controller@method' syntax
    - Resolving controllers from container
    - Dependency injection
    - Method parameter resolution
    - Controller middleware execution
    """

    def __init__(self, container: Optional[Any] = None) -> None:
        """
        Initialize dispatcher.

        Args:
            container: Service container for dependency injection
        """
        self.container = container

    def dispatch(
        self,
        route: Any,
        request: Any,
        controller: Union[str, Callable],
        method: Optional[str] = None,
    ) -> Any:
        """
        Dispatch request to controller.

        Args:
            route: Route instance
            request: HTTP request
            controller: Controller class name or instance
            method: Method name (optional for single action)

        Returns:
            Controller response
        """
        controller_instance = self.resolveController(controller)

        if method is None:
            if hasattr(controller_instance, "__invoke"):
                method = "__invoke"
            else:
                raise ValueError(
                    f"Controller {controller} must implement __invoke for single action"
                )

        if not hasattr(controller_instance, method):
            raise AttributeError(
                f"Method {method} does not exist on controller {controller_instance.__class__.__name__}"
            )

        parameters = self.resolveMethodParameters(controller_instance, method, route, request)

        return controller_instance.callAction(method, parameters)

    def resolveController(self, controller: Union[str, type, object]) -> Any:
        """
        Resolve controller instance.

        Args:
            controller: Controller class name, class, or instance

        Returns:
            Controller instance
        """
        if isinstance(controller, str):
            controller_class = self.resolveControllerClass(controller)
            return self.instantiateController(controller_class)
        elif inspect.isclass(controller):
            return self.instantiateController(controller)
        else:
            return controller

    def resolveControllerClass(self, controller: str) -> type:
        """
        Resolve controller class from string name.

        Args:
            controller: Controller class name (e.g., 'UserController' or 'App.Controllers.UserController')

        Returns:
            Controller class
        """
        parts = controller.split(".")

        try:
            module_parts = parts[:-1] if len(parts) > 1 else []
            class_name = parts[-1]

            if module_parts:
                module_name = ".".join(module_parts)
                module = __import__(module_name, fromlist=[class_name])
                return getattr(module, class_name)
            else:
                if self.container and hasattr(self.container, "make"):
                    return self.container.make(class_name)

                raise ImportError(f"Cannot resolve controller {controller}")

        except (ImportError, AttributeError) as e:
            raise ImportError(f"Controller {controller} not found: {e}")

    def instantiateController(self, controller: type) -> Any:
        """
        Instantiate controller with dependency injection.

        Args:
            controller: Controller class

        Returns:
            Controller instance
        """
        if self.container and hasattr(self.container, "make"):
            return self.container.make(controller)

        sig = inspect.signature(controller.__init__)
        params = list(sig.parameters.values())[1:]

        if not params:
            return controller()

        dependencies = []
        for param in params:
            if param.annotation != inspect.Parameter.empty:
                if self.container and hasattr(self.container, "make"):
                    dependencies.append(self.container.make(param.annotation))
                else:
                    dependencies.append(param.annotation())
            elif param.default != inspect.Parameter.empty:
                dependencies.append(param.default)
            else:
                dependencies.append(None)

        return controller(*dependencies)

    def resolveMethodParameters(
        self, controller: Any, method: str, route: Any, request: Any
    ) -> List[Any]:
        """
        Resolve method parameters from route and request.

        Args:
            controller: Controller instance
            method: Method name
            route: Route instance
            request: HTTP request

        Returns:
            List of resolved parameters
        """
        method_obj = getattr(controller, method)
        sig = inspect.signature(method_obj)
        params = list(sig.parameters.values())

        route_params = route.parameters() if hasattr(route, "parameters") else {}
        resolved = []

        for param in params:
            if param.name == "self":
                continue

            param_type = param.annotation

            if param_type != inspect.Parameter.empty:
                if self._is_request_type(param_type):
                    resolved.append(request)
                    continue

                if self.container and hasattr(self.container, "make"):
                    try:
                        resolved.append(self.container.make(param_type))
                        continue
                    except Exception:
                        pass

            if param.name in route_params:
                value = route_params[param.name]

                if param_type != inspect.Parameter.empty:
                    value = self._cast_parameter(value, param_type)

                resolved.append(value)
            elif param.default != inspect.Parameter.empty:
                resolved.append(param.default)
            else:
                resolved.append(None)

        return resolved

    def _is_request_type(self, param_type: type) -> bool:
        """
        Check if parameter type is a Request class.

        Args:
            param_type: Parameter type annotation

        Returns:
            True if Request type
        """
        if not inspect.isclass(param_type):
            return False

        type_name = param_type.__name__
        module_name = param_type.__module__ if hasattr(param_type, "__module__") else ""

        return type_name == "Request" or "request" in module_name.lower()

    def _cast_parameter(self, value: Any, param_type: type) -> Any:
        """
        Cast parameter to specified type.

        Args:
            value: Parameter value
            param_type: Target type

        Returns:
            Casted value
        """
        if param_type == int:
            return int(value)
        elif param_type == float:
            return float(value)
        elif param_type == bool:
            return str(value).lower() in ("1", "true", "yes", "on")
        elif param_type == str:
            return str(value)
        else:
            return value

    def parseAction(self, action: Union[str, Callable, Dict]) -> Dict[str, Any]:
        """
        Parse action into controller and method.

        Args:
            action: Action string ('Controller@method'), callable, or dict

        Returns:
            Dict with 'controller' and 'method' keys
        """
        if isinstance(action, str):
            if "@" in action:
                controller, method = action.split("@", 1)
                return {"controller": controller, "method": method}
            else:
                return {"controller": action, "method": None}

        elif callable(action):
            return {"uses": action}

        elif isinstance(action, dict):
            if "uses" in action and isinstance(action["uses"], str):
                if "@" in action["uses"]:
                    controller, method = action["uses"].split("@", 1)
                    return {**action, "controller": controller, "method": method}
            return action

        return {"uses": action}
