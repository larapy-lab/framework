from typing import Callable, List, Dict, Any
from larapy.http.resources.resource_collection import ResourceCollection


class AnonymousResourceCollection(ResourceCollection):
    def __init__(self, resources, callback: Callable):
        super().__init__(resources)
        self.callback = callback

    def to_dict(self, request=None) -> List[Dict[str, Any]]:
        if not self.resources:
            return []

        return [self.callback(resource, request) for resource in self.resources]
