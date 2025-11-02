from larapy.console.command import Command
import os


class MakeControllerCommand(Command):

    signature = "make:controller {name} {--resource} {--api} {--model=}"
    description = "Create a new controller class"

    def __init__(self, config: dict = None):
        super().__init__()
        self._config = config or {}

    def handle(self) -> int:
        name = self.argument("name")

        if not name:
            self.error("Controller name is required")
            return 1

        controller_path = self._config.get("controllers", {}).get("path", "app/http/controllers")
        os.makedirs(controller_path, exist_ok=True)

        filename = f"{name}.py"
        filepath = os.path.join(controller_path, filename)

        if os.path.exists(filepath):
            self.error(f"Controller {name} already exists")
            return 1

        model_name = self.option("model", None)
        is_resource = self.option("resource", False)
        is_api = self.option("api", False)

        if is_resource or is_api:
            stub = self._get_resource_stub(name, model_name, is_api)
        else:
            stub = self._get_basic_stub(name)

        with open(filepath, "w") as f:
            f.write(stub)

        self.info(f"Controller created: {filepath}")

        return 0

    def _get_basic_stub(self, name: str) -> str:
        return f"""from larapy.routing.controller import Controller


class {name}(Controller):

    def __init__(self):
        pass
"""

    def _get_resource_stub(self, name: str, model_name: str = None, is_api: bool = False) -> str:
        model_import = f"from app.models.{model_name} import {model_name}\n" if model_name else ""
        model_hint = f"{model_name}" if model_name else "Model"

        if is_api:
            return f"""{model_import}from larapy.routing.controller import Controller


class {name}(Controller):

    def index(self, request):
        items = {model_hint}.query.all()
        return {{'data': [item.to_dict() for item in items]}}

    def store(self, request):
        data = request.all()
        item = {model_hint}.create(data)
        return {{'data': item.to_dict()}}, 201

    def show(self, request, id):
        item = {model_hint}.query.find(id)
        if not item:
            return {{'error': 'Not found'}}, 404
        return {{'data': item.to_dict()}}

    def update(self, request, id):
        item = {model_hint}.query.find(id)
        if not item:
            return {{'error': 'Not found'}}, 404
        item.update(request.all())
        return {{'data': item.to_dict()}}

    def destroy(self, request, id):
        item = {model_hint}.query.find(id)
        if not item:
            return {{'error': 'Not found'}}, 404
        item.delete()
        return {{'message': 'Deleted successfully'}}, 204
"""
        else:
            return f"""{model_import}from larapy.routing.controller import Controller


class {name}(Controller):

    def index(self, request):
        items = {model_hint}.query.all()
        return {{'items': items}}

    def create(self, request):
        return {{'view': 'create'}}

    def store(self, request):
        data = request.all()
        item = {model_hint}.create(data)
        return {{'redirect': f'/{{item.id}}'}}

    def show(self, request, id):
        item = {model_hint}.query.find(id)
        return {{'item': item}}

    def edit(self, request, id):
        item = {model_hint}.query.find(id)
        return {{'item': item, 'view': 'edit'}}

    def update(self, request, id):
        item = {model_hint}.query.find(id)
        item.update(request.all())
        return {{'redirect': f'/{{item.id}}'}}

    def destroy(self, request, id):
        item = {model_hint}.query.find(id)
        item.delete()
        return {{'redirect': '/'}}
"""
