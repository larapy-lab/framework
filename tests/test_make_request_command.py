import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_request_command import MakeRequestCommand


class TestMakeRequestCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'requests': {'path': os.path.join(self.temp_dir, 'requests')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_request_file(self):
        command = MakeRequestCommand(self.config)
        command.set_arguments(['StorePost'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'requests', 'StorePostRequest.py'))
    
    def test_request_content_structure(self):
        command = MakeRequestCommand(self.config)
        command.set_arguments(['StorePost'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'requests', 'StorePostRequest.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'class StorePostRequest(FormRequest)' in content
        assert 'def authorize(self)' in content
        assert 'def rules(self)' in content
        assert 'def messages(self)' in content
        assert 'def attributes(self)' in content
        assert 'from larapy.validation.form_request import FormRequest' in content
    
    def test_fails_without_name(self):
        command = MakeRequestCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_exists(self):
        command1 = MakeRequestCommand(self.config)
        command1.set_arguments(['StorePost'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeRequestCommand(self.config)
        command2.set_arguments(['StorePost'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_adds_request_suffix(self):
        command = MakeRequestCommand(self.config)
        command.set_arguments(['StorePost'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(os.path.join(self.temp_dir, 'requests', 'StorePostRequest.py'))
    
    def test_handles_name_with_request_suffix(self):
        command = MakeRequestCommand(self.config)
        command.set_arguments(['UpdateUserRequest'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'requests', 'UpdateUserRequest.py')
        assert os.path.exists(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
        assert 'class UpdateUserRequest(FormRequest)' in content
    
    def test_creates_directory_if_not_exists(self):
        requests_path = os.path.join(self.temp_dir, 'requests')
        
        assert not os.path.exists(requests_path)
        
        command = MakeRequestCommand(self.config)
        command.set_arguments(['StorePost'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(requests_path)
