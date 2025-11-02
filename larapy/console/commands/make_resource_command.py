from larapy.console.command import Command
import os


class MakeResourceCommand(Command):

    signature = "make:resource {name} {--collection}"
    description = "Create a new API resource class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Resource name is required")
            return 1

        resource_path = self._config.get("resources", {}).get("path", "app/http/resources")
        os.makedirs(resource_path, exist_ok=True)

        filename = f"{name}.py"
        filepath = os.path.join(resource_path, filename)

        if os.path.exists(filepath):
            self.error(f"Resource {name} already exists")
            return 1

        is_collection = self.option("collection", False)

        if is_collection:
            stub = self._get_collection_stub(name)
        else:
            stub = self._get_resource_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Resource created: {filepath}")

        return 0

    def _get_resource_stub(self, name: str) -> str:
        return f"""from larapy.http.resources import JsonResource


class {name}(JsonResource):

    def to_array(self, request=None):
        return {{
            'id': self.resource.id,
        }}
"""

    def _get_collection_stub(self, name: str) -> str:
        base_name = name.replace("Collection", "")
        if not base_name:
            base_name = "Item"

        return f"""from larapy.http.resources import ResourceCollection


class {name}(ResourceCollection):

    def to_array(self, request=None):
        from app.http.resources.{base_name} import {base_name}

        return [
            {base_name}(item).to_dict(request)
            for item in self.collection
        ]
"""
