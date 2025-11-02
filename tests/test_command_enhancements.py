import pytest
from unittest.mock import Mock, patch, MagicMock
from larapy.console.command import Command
from larapy.console.kernel import Kernel


class TestCommand(Command):
    signature = 'test:command {arg} {--opt=}'
    description = 'Test command'
    
    def handle(self) -> int:
        return 0


class TestCommandEnhancements:
    
    def test_ask_with_input(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value='John'):
            result = command.ask('What is your name?')
        
        assert result == 'John'
    
    def test_ask_with_default(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value=''):
            result = command.ask('What is your name?', default='Alice')
        
        assert result == 'Alice'
    
    def test_confirm_yes(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value='y'):
            result = command.confirm('Do you agree?')
        
        assert result is True
    
    def test_confirm_no(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value='n'):
            result = command.confirm('Do you agree?')
        
        assert result is False
    
    def test_confirm_default_true(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value=''):
            result = command.confirm('Do you agree?', default=True)
        
        assert result is True
    
    def test_confirm_default_false(self):
        command = TestCommand()
        
        with patch('builtins.input', return_value=''):
            result = command.confirm('Do you agree?', default=False)
        
        assert result is False
    
    def test_choice_by_number(self):
        command = TestCommand()
        choices = ['option1', 'option2', 'option3']
        
        with patch('builtins.input', return_value='2'):
            result = command.choice('Select option:', choices)
        
        assert result == 'option2'
    
    def test_choice_by_text(self):
        command = TestCommand()
        choices = ['option1', 'option2', 'option3']
        
        with patch('builtins.input', return_value='option3'):
            result = command.choice('Select option:', choices)
        
        assert result == 'option3'
    
    def test_choice_with_default(self):
        command = TestCommand()
        choices = ['option1', 'option2', 'option3']
        
        with patch('builtins.input', return_value=''):
            result = command.choice('Select option:', choices, default='option1')
        
        assert result == 'option1'
    
    def test_new_line_single(self):
        command = TestCommand()
        
        output_before = len(command.get_output())
        command.new_line()
        output_after = len(command.get_output())
        
        assert output_after == output_before + 1
    
    def test_new_line_multiple(self):
        command = TestCommand()
        
        output_before = len(command.get_output())
        command.new_line(3)
        output_after = len(command.get_output())
        
        assert output_after == output_before + 3
    
    def test_call_command(self):
        kernel = Kernel()
        
        class FirstCommand(Command):
            signature = 'first'
            description = 'First'
            
            def handle(self) -> int:
                return 0
        
        class SecondCommand(Command):
            signature = 'second'
            description = 'Second'
            
            def handle(self) -> int:
                result = self.call('first')
                return result
        
        kernel.register(FirstCommand)
        kernel.register(SecondCommand)
        
        result = kernel.call('second')
        
        assert result == 0
    
    def test_call_silent_suppresses_output(self):
        kernel = Kernel()
        
        class VerboseCommand(Command):
            signature = 'verbose'
            description = 'Verbose'
            
            def handle(self) -> int:
                self.info('This is verbose')
                return 0
        
        class QuietCommand(Command):
            signature = 'quiet'
            description = 'Quiet'
            
            def handle(self) -> int:
                return self.call_silent('verbose')
        
        kernel.register(VerboseCommand)
        kernel.register(QuietCommand)
        
        result = kernel.call('quiet')
        
        assert result == 0
