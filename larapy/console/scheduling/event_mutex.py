import hashlib
from typing import Optional


class EventMutex:
    def __init__(self, cache):
        self.cache = cache

    def create(self, event) -> bool:
        key = self._get_mutex_key(event)
        expires_at = event.overlapping_expires_at

        try:
            return self.cache.add(key, "locked", expires_at * 60)
        except AttributeError:
            return self.cache.put(key, "locked", expires_at * 60)

    def exists(self, event) -> bool:
        key = self._get_mutex_key(event)
        try:
            return self.cache.has(key)
        except AttributeError:
            value = self.cache.get(key)
            return value is not None

    def forget(self, event):
        key = self._get_mutex_key(event)
        try:
            self.cache.forget(key)
        except AttributeError:
            self.cache.delete(key)

    def _get_mutex_key(self, event) -> str:
        description = event.get_description()
        hash_str = hashlib.md5(description.encode()).hexdigest()
        return f"framework:schedule:mutex:{hash_str}"
