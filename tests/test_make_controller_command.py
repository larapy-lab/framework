import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_controller_command import MakeControllerCommand


class TestMakeControllerCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'controllers': {'path': os.path.join(self.temp_dir, 'controllers')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_basic_controller(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['UserController'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'controllers', 'UserController.py'))
    
    def test_basic_controller_content(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['UserController'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'controllers', 'UserController.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'class UserController(Controller)' in content
        assert 'def __init__(self)' in content
    
    def test_resource_controller(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['PostController'])
        command.set_options({'resource': True})
        
        result = command.handle()
        
        assert result == 0
        
        filepath = os.path.join(self.temp_dir, 'controllers', 'PostController.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'def index(self, request)' in content
        assert 'def create(self, request)' in content
        assert 'def store(self, request)' in content
        assert 'def show(self, request, id)' in content
        assert 'def edit(self, request, id)' in content
        assert 'def update(self, request, id)' in content
        assert 'def destroy(self, request, id)' in content
    
    def test_api_controller(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['ApiController'])
        command.set_options({'api': True})
        
        result = command.handle()
        
        assert result == 0
        
        filepath = os.path.join(self.temp_dir, 'controllers', 'ApiController.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'def index(self, request)' in content
        assert 'def store(self, request)' in content
        assert 'def show(self, request, id)' in content
        assert 'def update(self, request, id)' in content
        assert 'def destroy(self, request, id)' in content
        assert 'def create(self, request)' not in content
        assert 'def edit(self, request, id)' not in content
    
    def test_controller_with_model(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['ProductController'])
        command.set_options({'resource': True, 'model': 'Product'})
        
        result = command.handle()
        
        assert result == 0
        
        filepath = os.path.join(self.temp_dir, 'controllers', 'ProductController.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'from app.models.Product import Product' in content
        assert 'Product.query' in content
    
    def test_fails_without_name(self):
        command = MakeControllerCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_controller_exists(self):
        command1 = MakeControllerCommand(self.config)
        command1.set_arguments(['TestController'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeControllerCommand(self.config)
        command2.set_arguments(['TestController'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_creates_directory_if_not_exists(self):
        controllers_path = os.path.join(self.temp_dir, 'controllers')
        
        assert not os.path.exists(controllers_path)
        
        command = MakeControllerCommand(self.config)
        command.set_arguments(['HomeController'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(controllers_path)
    
    def test_api_controller_returns_json(self):
        command = MakeControllerCommand(self.config)
        command.set_arguments(['CommentController'])
        command.set_options({'api': True, 'model': 'Comment'})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'controllers', 'CommentController.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'to_dict()' in content
        assert 'return {' in content
