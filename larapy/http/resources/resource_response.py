from typing import Dict, Any, Optional
import json


class ResourceResponse:
    def __init__(self, resource, status: int = 200, headers: Optional[Dict[str, str]] = None):
        self.resource = resource
        self.status = status
        self.headers = headers or {}

    def to_response(self, request=None) -> Dict[str, Any]:
        data = self.resource.to_response(request)

        return {
            "body": json.dumps(data),
            "status": self.status,
            "headers": {"Content-Type": "application/json", **self.headers},
        }

    def with_status(self, status: int):
        self.status = status
        return self

    def with_headers(self, headers: Dict[str, str]):
        self.headers.update(headers)
        return self
