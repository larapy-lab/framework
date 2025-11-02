import pytest
from unittest.mock import Mock, patch
from larapy.console.progress_bar import ProgressBar
from larapy.console.command import Command


class MockCommand(Command):
    signature = 'mock'
    description = 'Mock command'
    
    def handle(self) -> int:
        return 0


class TestProgressBar:
    
    def test_progress_bar_initialization(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        assert progress.max_steps == 100
        assert progress.current == 0
        assert progress.started is False
    
    def test_start_initializes_progress(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        with patch('sys.stdout.write'):
            progress.start()
        
        assert progress.started is True
        assert progress.current == 0
    
    def test_advance_increments_progress(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        with patch('sys.stdout.write'), patch('sys.stdout.flush'):
            progress.start()
            progress.advance(10)
        
        assert progress.current == 10
    
    def test_advance_multiple_steps(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        with patch('sys.stdout.write'), patch('sys.stdout.flush'):
            progress.start()
            progress.advance(25)
            progress.advance(25)
        
        assert progress.current == 50
    
    def test_finish_completes_progress(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        with patch('sys.stdout.write'), patch('sys.stdout.flush'):
            progress.start()
            progress.advance(50)
            progress.finish()
        
        assert progress.current == 100
    
    def test_set_message(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        progress.set_message('Processing...')
        
        assert progress.message == 'Processing...'
    
    def test_progress_percentage_calculation(self):
        command = MockCommand()
        progress = ProgressBar(command, 100)
        
        with patch('sys.stdout.write'), patch('sys.stdout.flush'):
            progress.start()
            progress.advance(50)
        
        percentage = int((progress.current / progress.max_steps) * 100)
        assert percentage == 50
    
    def test_with_progress_bar_iteration(self):
        command = MockCommand()
        items = list(range(10))
        
        results = command.with_progress_bar(items, lambda x: x * 2)
        
        assert len(results) == 10
        assert results[0] == 0
        assert results[5] == 10
        assert results[9] == 18
