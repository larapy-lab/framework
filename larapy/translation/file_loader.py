from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path


class FileLoader:

    def __init__(self, paths: List[str]):
        self.paths: List[str] = paths if isinstance(paths, list) else [paths]
        self._cache: Dict[str, Any] = {}

    def load(self, locale: str, group: str, namespace: Optional[str] = None) -> Dict:
        key = self._get_cache_key(locale, group, namespace)

        if key in self._cache:
            return self._cache[key]

        translations = self._load_from_files(locale, group, namespace)
        self._cache[key] = translations

        return translations

    def _load_from_files(self, locale: str, group: str, namespace: Optional[str] = None) -> Dict:
        for path in self.paths:
            base_path = Path(path)

            if namespace:
                file_path = base_path / "vendor" / namespace / locale / f"{group}.json"
            else:
                file_path = base_path / locale / f"{group}.json"

            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        return content if isinstance(content, dict) else {}
                except (json.JSONDecodeError, IOError):
                    continue

            py_file = file_path.with_suffix(".py")
            if py_file.exists():
                loaded = self._load_python_file(str(py_file))
                if loaded:
                    return loaded

        return {}

    def _load_python_file(self, file_path: str) -> Dict:
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("translations", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                translations = getattr(module, "translations", {})
                return translations if isinstance(translations, dict) else {}
        except Exception:
            pass
        return {}

    def _get_cache_key(self, locale: str, group: str, namespace: Optional[str]) -> str:
        if namespace:
            return f"{namespace}::{locale}.{group}"
        return f"{locale}.{group}"

    def add_namespace(self, namespace: str, hint: str) -> None:
        if hint not in self.paths:
            self.paths.insert(0, hint)

    def add_json_path(self, path: str) -> None:
        if path not in self.paths:
            self.paths.append(path)

    def namespaces(self) -> List[str]:
        namespaces = []
        for path in self.paths:
            vendor_path = Path(path) / "vendor"
            if vendor_path.exists() and vendor_path.is_dir():
                for ns_dir in vendor_path.iterdir():
                    if ns_dir.is_dir() and ns_dir.name not in namespaces:
                        namespaces.append(ns_dir.name)
        return namespaces

    def flush(self, locale: Optional[str] = None) -> None:
        if locale:
            keys_to_remove = [
                k for k in self._cache.keys() if k.startswith(f"{locale}.") or f".{locale}." in k
            ]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache = {}
