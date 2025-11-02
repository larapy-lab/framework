"""
Template Engine

Manages template compilation, caching, and execution.
"""

import hashlib
import html
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .compiler import Compiler


class Engine:
    """
    Template engine for rendering Blade-like templates.

    Handles template loading, compilation, caching, and execution.
    """

    def __init__(
        self, view_paths: list = None, cache_path: Optional[str] = None, cache_enabled: bool = True
    ) -> None:
        """
        Initialize engine.

        Args:
            view_paths: List of directories to search for templates
            cache_path: Directory to store compiled templates
            cache_enabled: Whether to cache compiled templates
        """
        self.view_paths = view_paths or []
        self.cache_path = cache_path
        self.cache_enabled = cache_enabled and cache_path is not None
        self.compiler = Compiler()
        self.compiled_cache: Dict[str, Any] = {}

    def render(self, template: str, context: Dict[str, Any] = None) -> str:
        """
        Render template with context data.

        Args:
            template: Template name or path
            context: Context data dictionary

        Returns:
            Rendered template string
        """
        context = context or {}

        template_path = self.find_template(template)
        if not template_path:
            raise FileNotFoundError(f"Template not found: {template}")

        compiled_function = self.get_compiled(template_path)

        try:
            return compiled_function(context)
        except Exception as e:
            raise RuntimeError(f"Error rendering template {template}: {str(e)}")

    def find_template(self, name: str) -> Optional[str]:
        """
        Find template file by name.

        Args:
            name: Template name (e.g., 'posts.index')

        Returns:
            Full path to template file or None
        """
        name = name.replace(".", os.sep)

        extensions = [".blade.py", ".blade.html", ".blade", ".html"]

        for view_path in self.view_paths:
            for ext in extensions:
                template_path = os.path.join(view_path, name + ext)
                if os.path.exists(template_path):
                    return template_path

        return None

    def get_compiled(self, template_path: str) -> callable:
        """
        Get compiled template function.

        Args:
            template_path: Full path to template file

        Returns:
            Compiled template function
        """
        cache_key = self._get_cache_key(template_path)

        if cache_key in self.compiled_cache:
            return self.compiled_cache[cache_key]

        if self.cache_enabled:
            cached = self._load_from_cache(cache_key, template_path)
            if cached:
                self.compiled_cache[cache_key] = cached
                return cached

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        compiled_code = self.compiler.compile(template_content)

        namespace = {"html": html}
        exec(compiled_code, namespace)
        compiled_function = namespace["render"]

        self.compiled_cache[cache_key] = compiled_function

        if self.cache_enabled:
            self._save_to_cache(cache_key, compiled_code, template_path)

        return compiled_function

    def _get_cache_key(self, template_path: str) -> str:
        """Generate cache key for template."""
        return hashlib.md5(template_path.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> str:
        """Get cache file path for key."""
        return os.path.join(self.cache_path, f"{cache_key}.py")

    def _load_from_cache(self, cache_key: str, template_path: str) -> Optional[callable]:
        """Load compiled template from cache."""
        cache_file = self._get_cache_file(cache_key)

        if not os.path.exists(cache_file):
            return None

        template_mtime = os.path.getmtime(template_path)
        cache_mtime = os.path.getmtime(cache_file)

        if template_mtime > cache_mtime:
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                compiled_code = f.read()

            namespace = {"html": html}
            exec(compiled_code, namespace)
            return namespace["render"]
        except Exception:
            return None

    def _save_to_cache(self, cache_key: str, compiled_code: str, template_path: str) -> None:
        """Save compiled template to cache."""
        cache_file = self._get_cache_file(cache_key)

        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(f"# Compiled from: {template_path}\n")
            f.write(compiled_code)

    def clear_cache(self) -> None:
        """Clear all cached templates."""
        self.compiled_cache.clear()

        if self.cache_enabled and os.path.exists(self.cache_path):
            for file in os.listdir(self.cache_path):
                if file.endswith(".py"):
                    os.remove(os.path.join(self.cache_path, file))

    def add_view_path(self, path: str) -> None:
        """Add view path to search list."""
        if path not in self.view_paths:
            self.view_paths.append(path)

    def directive(self, name: str, handler: callable) -> None:
        """
        Register custom directive.

        Args:
            name: Directive name (without @)
            handler: Callable that takes args and returns string
        """
        self.compiler.directive(name, handler)
