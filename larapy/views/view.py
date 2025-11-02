"""
View Facade

High-level API for working with views and templates.
"""

import os
from typing import Any, Callable, Dict, List, Optional, Union

from .engine import Engine


class View:
    """
    View facade for template rendering.

    Provides static methods for creating and rendering views.
    """

    _engine: Optional[Engine] = None
    _shared_data: Dict[str, Any] = {}
    _composers: Dict[str, List[Callable]] = {}
    _creators: Dict[str, List[Callable]] = {}

    @classmethod
    def configure(
        cls,
        view_paths: Union[str, List[str]] = None,
        cache_path: Optional[str] = None,
        cache_enabled: bool = True,
    ) -> None:
        """
        Configure view system.

        Args:
            view_paths: Directory or list of directories containing views
            cache_path: Directory for compiled template cache
            cache_enabled: Whether to enable caching
        """
        if isinstance(view_paths, str):
            view_paths = [view_paths]

        cls._engine = Engine(
            view_paths=view_paths or [], cache_path=cache_path, cache_enabled=cache_enabled
        )

    @classmethod
    def make(cls, name: str, data: Dict[str, Any] = None) -> "ViewInstance":
        """
        Create view instance.

        Args:
            name: View name (e.g., 'posts.index')
            data: View data

        Returns:
            ViewInstance
        """
        if cls._engine is None:
            cls.configure()

        data = data or {}

        merged_data = {**cls._shared_data, **data}

        view = ViewInstance(cls._engine, name, merged_data)

        cls._call_creators(name, view)
        cls._call_composers(name, view)

        return view

    @classmethod
    def share(cls, key: str, value: Any = None) -> None:
        """
        Share data with all views.

        Args:
            key: Data key or dict of key-value pairs
            value: Data value
        """
        if isinstance(key, dict):
            cls._shared_data.update(key)
        else:
            cls._shared_data[key] = value

    @classmethod
    def composer(cls, views: Union[str, List[str]], callback: Callable) -> None:
        """
        Register view composer.

        Args:
            views: View name(s) to compose
            callback: Composer callback
        """
        if isinstance(views, str):
            views = [views]

        for view in views:
            if view not in cls._composers:
                cls._composers[view] = []
            cls._composers[view].append(callback)

    @classmethod
    def creator(cls, views: Union[str, List[str]], callback: Callable) -> None:
        """
        Register view creator.

        Args:
            views: View name(s) to create
            callback: Creator callback
        """
        if isinstance(views, str):
            views = [views]

        for view in views:
            if view not in cls._creators:
                cls._creators[view] = []
            cls._creators[view].append(callback)

    @classmethod
    def _call_composers(cls, name: str, view: "ViewInstance") -> None:
        """Call registered composers for view."""
        for pattern, composers in cls._composers.items():
            if cls._matches_pattern(name, pattern):
                for composer in composers:
                    if callable(composer):
                        composer(view)
                    elif hasattr(composer, "compose"):
                        composer.compose(view)

    @classmethod
    def _call_creators(cls, name: str, view: "ViewInstance") -> None:
        """Call registered creators for view."""
        for pattern, creators in cls._creators.items():
            if cls._matches_pattern(name, pattern):
                for creator in creators:
                    if callable(creator):
                        creator(view)
                    elif hasattr(creator, "create"):
                        creator.create(view)

    @classmethod
    def _matches_pattern(cls, name: str, pattern: str) -> bool:
        """Check if view name matches pattern."""
        if pattern == name:
            return True

        if "*" in pattern:
            pattern_parts = pattern.split(".")
            name_parts = name.split(".")

            if len(pattern_parts) != len(name_parts):
                if pattern.endswith(".*"):
                    pattern_prefix = pattern[:-2]
                    return name.startswith(pattern_prefix)
                return False

            for pattern_part, name_part in zip(pattern_parts, name_parts):
                if pattern_part != "*" and pattern_part != name_part:
                    return False

            return True

        return False

    @classmethod
    def clear_cache(cls) -> None:
        """Clear compiled template cache."""
        if cls._engine:
            cls._engine.clear_cache()

    @classmethod
    def add_path(cls, path: str) -> None:
        """Add view path."""
        if cls._engine is None:
            cls.configure()
        cls._engine.add_view_path(path)

    @classmethod
    def directive(cls, name: str, handler: Callable) -> None:
        """Register custom directive."""
        if cls._engine is None:
            cls.configure()
        cls._engine.directive(name, handler)


class ViewInstance:
    """
    Individual view instance.

    Represents a specific view with its data.
    """

    def __init__(self, engine: Engine, name: str, data: Dict[str, Any]) -> None:
        """
        Initialize view instance.

        Args:
            engine: Template engine
            name: View name
            data: View data
        """
        self.engine = engine
        self.name = name
        self.data = data

    def with_(self, key: str, value: Any = None) -> "ViewInstance":
        """
        Add data to view.

        Args:
            key: Data key or dict
            value: Data value

        Returns:
            Self for chaining
        """
        if isinstance(key, dict):
            self.data.update(key)
        else:
            self.data[key] = value
        return self

    def render(self) -> str:
        """
        Render view to string.

        Returns:
            Rendered template
        """
        return self.engine.render(self.name, self.data)

    def __str__(self) -> str:
        """String representation renders the view."""
        return self.render()
