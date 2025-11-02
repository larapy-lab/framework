from abc import ABC
from typing import Any, Dict, Optional, List


class JsonResource(ABC):
    wrap = "data"

    def __init__(self, resource):
        self.resource = resource
        self.with_data = {}
        self.additional_data = {}

    def to_dict(self, request=None) -> Dict[str, Any]:
        if hasattr(self, "to_array"):
            data = self.to_array(request)
        else:
            data = self._default_to_array()

        return self._filter_missing_values(data)

    def _default_to_array(self) -> Dict[str, Any]:
        if self.resource is None:
            return {}

        if hasattr(self.resource, "__dict__"):
            return {k: v for k, v in self.resource.__dict__.items() if not k.startswith("_")}

        return {}

    def _filter_missing_values(self, data: Any) -> Any:
        from larapy.http.resources.conditional_attributes import MissingValue

        if isinstance(data, dict):
            return {
                k: self._filter_missing_values(v)
                for k, v in data.items()
                if not isinstance(v, MissingValue)
            }
        elif isinstance(data, list):
            return [
                self._filter_missing_values(item)
                for item in data
                if not isinstance(item, MissingValue)
            ]

        return data

    def with_info(self, key: str, value: Any):
        self.with_data[key] = value
        return self

    def additional(self, data: Dict[str, Any]):
        self.additional_data.update(data)
        return self

    def when(self, condition: bool, value: Any, default=None):
        from larapy.http.resources.conditional_attributes import MissingValue

        if callable(condition):
            condition = condition()

        if condition:
            return value() if callable(value) else value

        if default is None:
            return MissingValue()

        return default() if callable(default) else default

    def when_loaded(self, relationship: str, value: Any = None, default=None):
        from larapy.http.resources.conditional_attributes import MissingValue

        if not hasattr(self.resource, relationship):
            if default is None:
                return MissingValue()
            return default() if callable(default) else default

        attr = getattr(self.resource, relationship)

        if attr is None:
            if default is None:
                return MissingValue()
            return default() if callable(default) else default

        if value is not None:
            return value() if callable(value) else value

        return attr

    def when_pivot_loaded(self, table: str, value: Any = None, default=None):
        if not hasattr(self.resource, "pivot"):
            from larapy.http.resources.conditional_attributes import MissingValue

            if default is None:
                return MissingValue()
            return default() if callable(default) else default

        pivot = self.resource.pivot

        if pivot is None:
            from larapy.http.resources.conditional_attributes import MissingValue

            if default is None:
                return MissingValue()
            return default() if callable(default) else default

        if value is not None:
            return value() if callable(value) else value

        return pivot

    def merge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {**self.to_dict(), **data}

    def merge_when(self, condition: bool, data: Dict[str, Any]) -> Dict[str, Any]:
        if callable(condition):
            condition = condition()

        if condition:
            return self.merge(data)

        return self.to_dict()

    @classmethod
    def collection(cls, resources):
        from larapy.http.resources.resource_collection import ResourceCollection

        return ResourceCollection(resources, cls)

    def to_response(self, request=None) -> Dict[str, Any]:
        data = self.to_dict(request)

        if self.__class__.wrap:
            response_data = {self.__class__.wrap: data}
        else:
            response_data = data

        response_data.update(self.with_data)
        response_data.update(self.additional_data)

        return response_data

    @classmethod
    def without_wrapping(cls):
        cls.wrap = None

    @classmethod
    def wrap_with(cls, key: str):
        cls.wrap = key
