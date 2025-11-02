from typing import Any, Dict, Optional, List


class ResourceCollection:
    wrap = "data"

    def __init__(self, resources, resource_class=None):
        self.resources = resources if resources is not None else []
        self.resource_class = resource_class
        self.with_data = {}
        self.additional_data = {}

    def to_dict(self, request=None) -> List[Dict[str, Any]]:
        if not self.resources:
            return []

        if self.resource_class:
            return [self.resource_class(resource).to_dict(request) for resource in self.resources]

        return [
            resource if isinstance(resource, dict) else resource.__dict__
            for resource in self.resources
        ]

    def with_info(self, key: str, value: Any):
        self.with_data[key] = value
        return self

    def additional(self, data: Dict[str, Any]):
        self.additional_data.update(data)
        return self

    def to_response(self, request=None) -> Dict[str, Any]:
        data = self.to_dict(request)

        if self.__class__.wrap:
            response_data = {self.__class__.wrap: data}
        else:
            response_data = {"data": data}

        response_data.update(self.with_data)
        response_data.update(self.additional_data)

        return response_data

    @classmethod
    def without_wrapping(cls):
        cls.wrap = None

    @classmethod
    def wrap_with(cls, key: str):
        cls.wrap = key

    def count(self) -> int:
        return len(self.resources) if self.resources else 0

    def is_empty(self) -> bool:
        return self.count() == 0
