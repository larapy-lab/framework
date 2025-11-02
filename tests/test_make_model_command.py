import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_model_command import MakeModelCommand
from larapy.console.kernel import Kernel


class TestMakeModelCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'models': {'path': os.path.join(self.temp_dir, 'models')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_model_file(self):
        command = MakeModelCommand(self.config)
        command.set_arguments(['User'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'models', 'User.py'))
    
    def test_model_content_includes_class(self):
        command = MakeModelCommand(self.config)
        command.set_arguments(['User'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'models', 'User.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'class User(Model)' in content
        assert 'table = \'users\'' in content
    
    def test_fails_without_name(self):
        command = MakeModelCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_model_exists(self):
        command1 = MakeModelCommand(self.config)
        command1.set_arguments(['User'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeModelCommand(self.config)
        command2.set_arguments(['User'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_with_migration_option(self):
        kernel = Kernel()
        
        from larapy.console.commands.make_migration_command import MakeMigrationCommand
        
        migration_config = {
            'migrations': {'path': os.path.join(self.temp_dir, 'migrations')}
        }
        kernel.register(lambda: MakeMigrationCommand(migration_config))
        
        command = MakeModelCommand(self.config)
        command.set_kernel(kernel)
        command.set_arguments(['Post'])
        command.set_options({'migration': True})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'models', 'Post.py'))
    
    def test_table_name_conversion(self):
        command = MakeModelCommand(self.config)
        
        assert command._get_table_name('User') == 'users'
        assert command._get_table_name('BlogPost') == 'blog_posts'
        assert command._get_table_name('UserProfile') == 'user_profiles'
    
    def test_model_stub_includes_fillable(self):
        command = MakeModelCommand(self.config)
        command.set_arguments(['Product'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'models', 'Product.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'fillable = []' in content
        assert 'hidden = []' in content
        assert 'casts = {}' in content
    
    def test_creates_directory_if_not_exists(self):
        models_path = os.path.join(self.temp_dir, 'models')
        
        assert not os.path.exists(models_path)
        
        command = MakeModelCommand(self.config)
        command.set_arguments(['User'])
        command.set_options({})
        
        command.handle()
        
        assert os.path.exists(models_path)
    
    def test_all_option_triggers_multiple_generations(self):
        kernel = Kernel()
        
        from larapy.console.commands.make_migration_command import MakeMigrationCommand
        from larapy.console.commands.make_factory_command import MakeFactoryCommand
        from larapy.console.commands.make_resource_command import MakeResourceCommand
        
        migration_config = {'migrations': {'path': os.path.join(self.temp_dir, 'migrations')}}
        factory_config = {'factories': {'path': os.path.join(self.temp_dir, 'factories')}}
        resource_config = {'resources': {'path': os.path.join(self.temp_dir, 'resources')}}
        
        kernel.register(lambda: MakeMigrationCommand(migration_config))
        kernel.register(lambda: MakeFactoryCommand(factory_config))
        kernel.register(lambda: MakeResourceCommand(resource_config))
        
        command = MakeModelCommand(self.config)
        command.set_kernel(kernel)
        command.set_arguments(['Article'])
        command.set_options({'all': True})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'models', 'Article.py'))
