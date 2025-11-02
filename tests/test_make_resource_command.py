import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_resource_command import MakeResourceCommand


class TestMakeResourceCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'resources': {'path': os.path.join(self.temp_dir, 'resources')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_resource_file(self):
        command = MakeResourceCommand(self.config)
        command.set_arguments(['UserResource'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'resources', 'UserResource.py'))
    
    def test_resource_content(self):
        command = MakeResourceCommand(self.config)
        command.set_arguments(['PostResource'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'resources', 'PostResource.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'from larapy.http.resources import JsonResource' in content
        assert 'class PostResource(JsonResource)' in content
        assert 'def to_array(self, request=None)' in content
    
    def test_collection_resource(self):
        command = MakeResourceCommand(self.config)
        command.set_arguments(['UserCollection'])
        command.set_options({'collection': True})
        
        result = command.handle()
        
        assert result == 0
        
        filepath = os.path.join(self.temp_dir, 'resources', 'UserCollection.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'from larapy.http.resources import ResourceCollection' in content
        assert 'class UserCollection(ResourceCollection)' in content
    
    def test_fails_without_name(self):
        command = MakeResourceCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_resource_exists(self):
        command1 = MakeResourceCommand(self.config)
        command1.set_arguments(['TestResource'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeResourceCommand(self.config)
        command2.set_arguments(['TestResource'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_creates_directory_if_not_exists(self):
        resources_path = os.path.join(self.temp_dir, 'resources')
        
        assert not os.path.exists(resources_path)
        
        command = MakeResourceCommand(self.config)
        command.set_arguments(['ItemResource'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(resources_path)
