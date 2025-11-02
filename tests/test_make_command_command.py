import pytest
import os
import tempfile
import shutil
from larapy.console.commands.make_command_command import MakeCommandCommand


class TestMakeCommandCommand:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'commands': {'path': os.path.join(self.temp_dir, 'commands')}
        }
    
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_creates_command_file(self):
        command = MakeCommandCommand(self.config)
        command.set_arguments(['SendEmailCommand'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert os.path.exists(os.path.join(self.temp_dir, 'commands', 'send_email_command.py'))
    
    def test_command_content_includes_class(self):
        command = MakeCommandCommand(self.config)
        command.set_arguments(['ProcessDataCommand'])
        command.set_options({})
        
        command.handle()
        
        filepath = os.path.join(self.temp_dir, 'commands', 'process_data_command.py')
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'class ProcessDataCommand(Command)' in content
        assert 'signature =' in content
        assert 'description =' in content
        assert 'def handle(self) -> int:' in content
    
    def test_fails_without_name(self):
        command = MakeCommandCommand(self.config)
        
        with pytest.raises(ValueError, match="Missing required argument"):
            command.set_arguments([])
            command.set_options({})
            command.handle()
    
    def test_fails_if_command_exists(self):
        command1 = MakeCommandCommand(self.config)
        command1.set_arguments(['TestCommand'])
        command1.set_options({})
        command1.handle()
        
        command2 = MakeCommandCommand(self.config)
        command2.set_arguments(['TestCommand'])
        command2.set_options({})
        
        result = command2.handle()
        
        assert result == 1
    
    def test_command_name_conversion(self):
        command = MakeCommandCommand(self.config)
        
        assert command._command_name('SendEmailCommand') == 'send:email'
        assert command._command_name('ProcessDataCommand') == 'process:data'
    
    def test_snake_case_conversion(self):
        command = MakeCommandCommand(self.config)
        
        assert command._snake_case('SendEmail') == 'send_email'
        assert command._snake_case('ProcessDataCommand') == 'process_data_command'
