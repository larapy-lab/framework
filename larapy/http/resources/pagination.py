from typing import Dict, Any, Optional


class PaginatedResourceResponse:
    def __init__(self, paginator, resource_class):
        self.paginator = paginator
        self.resource_class = resource_class

    def to_response(self, request=None) -> Dict[str, Any]:
        return {
            "data": [self.resource_class(item).to_dict(request) for item in self.paginator.items()],
            "links": self._get_links(),
            "meta": self._get_meta(),
        }

    def _get_links(self) -> Dict[str, Optional[str]]:
        return {
            "first": self.paginator.url(1) if hasattr(self.paginator, "url") else None,
            "last": (
                self.paginator.url(self.paginator.last_page())
                if hasattr(self.paginator, "url") and hasattr(self.paginator, "last_page")
                else None
            ),
            "prev": (
                self.paginator.previous_page_url()
                if hasattr(self.paginator, "previous_page_url")
                else None
            ),
            "next": (
                self.paginator.next_page_url() if hasattr(self.paginator, "next_page_url") else None
            ),
        }

    def _get_meta(self) -> Dict[str, Any]:
        meta = {}

        if hasattr(self.paginator, "current_page"):
            meta["current_page"] = self.paginator.current_page()

        if hasattr(self.paginator, "first_item"):
            meta["from"] = self.paginator.first_item()

        if hasattr(self.paginator, "last_page"):
            meta["last_page"] = self.paginator.last_page()

        if hasattr(self.paginator, "per_page"):
            meta["per_page"] = self.paginator.per_page()

        if hasattr(self.paginator, "last_item"):
            meta["to"] = self.paginator.last_item()

        if hasattr(self.paginator, "total"):
            meta["total"] = self.paginator.total()

        return meta
