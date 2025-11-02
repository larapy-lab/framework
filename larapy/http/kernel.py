from typing import Any, Callable, List, Optional, Dict, Union
from larapy.pipeline.pipeline import Pipeline


class MiddlewareWithParameters:
    def __init__(self, middleware: Any, parameters: List[str]):
        self.middleware = middleware
        self.parameters = parameters

    def handle(self, request: Any, next_handler: Callable) -> Any:
        if hasattr(self.middleware, "handle"):
            return self.middleware.handle(request, next_handler, *self.parameters)
        elif callable(self.middleware):
            return self.middleware(request, next_handler, *self.parameters)
        raise ValueError(f"Middleware {self.middleware} is not callable")


class Kernel:
    def __init__(self, container=None):
        self._container = container
        self._middleware = []
        self._middleware_groups = {"web": [], "api": []}
        self._route_middleware = {}
        self._middleware_priority = []

    def handle(self, request: Any, handler: Callable) -> Any:
        pipeline = Pipeline(self._container)

        return pipeline.send(request).through(self._gather_route_middleware(request)).then(handler)

    def append(self, middleware: Union[str, type]) -> "Kernel":
        if middleware not in self._middleware:
            self._middleware.append(middleware)
        return self

    def prepend(self, middleware: Union[str, type]) -> "Kernel":
        if middleware not in self._middleware:
            self._middleware.insert(0, middleware)
        return self

    def use(self, middleware: List[Union[str, type]]) -> "Kernel":
        self._middleware = middleware
        return self

    def appendToGroup(self, group: str, middleware: List[Union[str, type]]) -> "Kernel":
        if group not in self._middleware_groups:
            self._middleware_groups[group] = []

        for m in middleware:
            if m not in self._middleware_groups[group]:
                self._middleware_groups[group].append(m)
        return self

    def prependToGroup(self, group: str, middleware: List[Union[str, type]]) -> "Kernel":
        if group not in self._middleware_groups:
            self._middleware_groups[group] = []

        for m in reversed(middleware):
            if m not in self._middleware_groups[group]:
                self._middleware_groups[group].insert(0, m)
        return self

    def group(self, name: str, middleware: List[Union[str, type]]) -> "Kernel":
        self._middleware_groups[name] = middleware
        return self

    def alias(self, aliases: Dict[str, Union[str, type]]) -> "Kernel":
        for alias_name, middleware in aliases.items():
            self._route_middleware[alias_name] = middleware
        return self

    def aliasMiddleware(self, name: str, middleware: Union[str, type]) -> "Kernel":
        self._route_middleware[name] = middleware
        return self

    def priority(self, middleware: List[Union[str, type]]) -> "Kernel":
        self._middleware_priority = middleware
        return self

    def hasMiddleware(self, middleware: Union[str, type]) -> bool:
        return middleware in self._middleware

    def getMiddleware(self) -> List[Union[str, type]]:
        return self._middleware.copy()

    def getMiddlewareGroups(self) -> Dict[str, List[Union[str, type]]]:
        return self._middleware_groups.copy()

    def getRouteMiddleware(self) -> Dict[str, Union[str, type]]:
        return self._route_middleware.copy()

    def _gather_route_middleware(self, request: Any) -> List[Union[str, type]]:
        middleware = self._middleware.copy()

        if hasattr(request, "_route_middleware"):
            route_middleware = self._expand_middleware(request._route_middleware)
            middleware.extend(route_middleware)

        return self._sort_middleware(middleware)

    def _expand_middleware(self, middleware: List[Union[str, type]]) -> List[Union[str, type]]:
        expanded = []

        for m in middleware:
            if isinstance(m, str):
                m_stripped = m.split(":")[0]

                if m_stripped in self._middleware_groups:
                    expanded.extend(self._middleware_groups[m_stripped])
                elif m_stripped in self._route_middleware:
                    base_middleware = self._route_middleware[m_stripped]
                    if ":" in m:
                        params = m.split(":", 1)[1].split(",")
                        params = [p.strip() for p in params]
                        expanded.append(MiddlewareWithParameters(base_middleware, params))
                    else:
                        expanded.append(base_middleware)
                else:
                    expanded.append(m)
            else:
                expanded.append(m)

        return expanded

    def _sort_middleware(self, middleware: List[Union[str, type]]) -> List[Union[str, type]]:
        if not self._middleware_priority:
            return middleware

        priority_map = {m: i for i, m in enumerate(self._middleware_priority)}

        def get_priority(m):
            if isinstance(m, str):
                m_class = m.split(":")[0]
            elif isinstance(m, type):
                m_class = m
            else:
                m_class = type(m)
            return priority_map.get(m_class, len(self._middleware_priority))

        return sorted(middleware, key=get_priority)

    def terminate(self, request: Any, response: Any) -> None:
        middleware_to_terminate = []

        middleware_list = self._gather_route_middleware(request)

        for m in middleware_list:
            if isinstance(m, str):
                if self._container:
                    instance = self._container.make(m.split(":")[0])
                else:
                    continue
            else:
                instance = m if callable(m) else (m() if isinstance(m, type) else m)

            if hasattr(instance, "terminate"):
                middleware_to_terminate.append(instance)

        for middleware_instance in middleware_to_terminate:
            middleware_instance.terminate(request, response)
