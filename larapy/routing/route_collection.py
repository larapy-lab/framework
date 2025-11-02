"""
Route Collection

Manages collection of routes and provides route matching capabilities.
"""

from typing import Dict, List, Optional
from larapy.routing.route import Route


class RouteCollection:
    """
    Collection of routes matching Laravel's RouteCollection.

    Handles route storage, lookup by name/method, and route matching.
    """

    def __init__(self) -> None:
        """Initialize empty route collection."""
        self._routes: List[Route] = []
        self._named_routes: Dict[str, Route] = {}
        self._method_routes: Dict[str, List[Route]] = {}

    def add(self, route: Route) -> Route:
        """
        Add a route to the collection.

        Args:
            route: Route to add

        Returns:
            The added route
        """
        self._routes.append(route)

        route._collection = self

        if route.getName():
            self._named_routes[route.getName()] = route

        for method in route.getMethods():
            if method not in self._method_routes:
                self._method_routes[method] = []
            self._method_routes[method].append(route)

        return route

    def match(self, uri: str, method: str) -> Optional[Route]:
        """
        Find first route matching the given URI and method.

        Args:
            uri: Request URI
            method: HTTP method

        Returns:
            Matching route or None
        """
        method = method.upper()

        if method not in self._method_routes:
            return None

        for route in self._method_routes[method]:
            if route.matches(uri, method):
                return route

        return None

    def getByName(self, name: str) -> Optional[Route]:
        """
        Get route by name.

        Args:
            name: Route name

        Returns:
            Named route or None
        """
        return self._named_routes.get(name)

    def getByMethod(self, method: str) -> List[Route]:
        """
        Get all routes for a specific HTTP method.

        Args:
            method: HTTP method

        Returns:
            List of routes
        """
        return self._method_routes.get(method.upper(), [])

    def getRoutes(self) -> List[Route]:
        """Get all routes."""
        return self._routes

    def count(self) -> int:
        """Get total number of routes."""
        return len(self._routes)

    def hasNamedRoute(self, name: str) -> bool:
        """Check if named route exists."""
        return name in self._named_routes

    def refreshNamedRoute(self, route: Route) -> None:
        """Refresh a specific route's named route index."""
        if route.getName():
            self._named_routes[route.getName()] = route

    def refresh(self) -> None:
        """Refresh named and method route indexes."""
        self._named_routes.clear()
        self._method_routes.clear()

        for route in self._routes:
            if route.getName():
                self._named_routes[route.getName()] = route

            for method in route.getMethods():
                if method not in self._method_routes:
                    self._method_routes[method] = []
                self._method_routes[method].append(route)

    def __len__(self) -> int:
        """Get collection length."""
        return len(self._routes)

    def __iter__(self):
        """Iterate over routes."""
        return iter(self._routes)

    def __repr__(self) -> str:
        """String representation."""
        return f"<RouteCollection routes={len(self._routes)}>"
