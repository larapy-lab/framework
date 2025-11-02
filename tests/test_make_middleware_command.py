import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_middleware_command import MakeMiddlewareCommand


class TestMakeMiddlewareCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'middleware': {'path': os.path.join(self.temp_dir, 'middleware')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_middleware_file(self):
        command = MakeMiddlewareCommand(self.config)
        command.set_arguments(['AuthMiddleware'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'middleware', 'AuthMiddleware.py'))
    
    def test_middleware_content(self):
        command = MakeMiddlewareCommand(self.config)
        command.set_arguments(['CorsMiddleware'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'middleware', 'CorsMiddleware.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'from larapy.http.middleware import Middleware' in content
        assert 'class CorsMiddleware(Middleware)' in content
        assert 'def handle(self, request, next)' in content
        assert 'response = next(request)' in content
    
    def test_fails_without_name(self):
        command = MakeMiddlewareCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_middleware_exists(self):
        command1 = MakeMiddlewareCommand(self.config)
        command1.set_arguments(['TestMiddleware'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeMiddlewareCommand(self.config)
        command2.set_arguments(['TestMiddleware'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_creates_directory_if_not_exists(self):
        middleware_path = os.path.join(self.temp_dir, 'middleware')
        
        assert not os.path.exists(middleware_path)
        
        command = MakeMiddlewareCommand(self.config)
        command.set_arguments(['LogMiddleware'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(middleware_path)
    
    def test_middleware_stub_has_next_pattern(self):
        command = MakeMiddlewareCommand(self.config)
        command.set_arguments(['ThrottleMiddleware'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'middleware', 'ThrottleMiddleware.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'next(request)' in content
        assert 'return response' in content
