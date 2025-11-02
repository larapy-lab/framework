import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime as dt, timedelta
from io import StringIO
from larapy.logging.log_level import LogLevel
from larapy.logging.log_record import LogRecord
from larapy.logging.handlers import (
    FileHandler, StreamHandler, NullHandler,
    DailyFileHandler, StackHandler
)
from larapy.logging.formatters import LineFormatter


class TestFileHandler(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = Path(self.test_dir) / 'test.log'
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_writes_to_file(self):
        handler = FileHandler(str(self.log_path))
        record = LogRecord(
            level=LogLevel.INFO,
            message='Test message',
            channel='test'
        )
        
        handler.handle(record)
        handler.close()
        
        content = self.log_path.read_text()
        self.assertIn('Test message', content)
    
    def test_creates_directory_if_not_exists(self):
        nested_path = Path(self.test_dir) / 'nested' / 'dir' / 'test.log'
        handler = FileHandler(str(nested_path))
        
        record = LogRecord(level=LogLevel.INFO, message='Test', channel='test')
        handler.handle(record)
        handler.close()
        
        self.assertTrue(nested_path.exists())
    
    def test_respects_log_level(self):
        handler = FileHandler(str(self.log_path), level=LogLevel.ERROR)
        
        handler.handle(LogRecord(level=LogLevel.DEBUG, message='Debug message', channel='test'))
        handler.handle(LogRecord(level=LogLevel.ERROR, message='Error message', channel='test'))
        handler.close()
        
        content = self.log_path.read_text()
        self.assertNotIn('Debug message', content)
        self.assertIn('Error message', content)


class TestStreamHandler(unittest.TestCase):
    
    def test_writes_to_stream(self):
        stream = StringIO()
        handler = StreamHandler(stream)
        
        record = LogRecord(level=LogLevel.INFO, message='Test message', channel='test')
        handler.handle(record)
        
        output = stream.getvalue()
        self.assertIn('Test message', output)
    
    def test_respects_log_level(self):
        stream = StringIO()
        handler = StreamHandler(stream, level=LogLevel.WARNING)
        
        handler.handle(LogRecord(level=LogLevel.DEBUG, message='Debug message', channel='test'))
        handler.handle(LogRecord(level=LogLevel.WARNING, message='Warning message', channel='test'))
        
        output = stream.getvalue()
        self.assertNotIn('Debug message', output)
        self.assertIn('Warning message', output)


class TestNullHandler(unittest.TestCase):
    
    def test_discards_all_messages(self):
        handler = NullHandler()
        
        record = LogRecord(level=LogLevel.EMERGENCY, message='Critical message', channel='test')
        handler.handle(record)


class TestDailyFileHandler(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = Path(self.test_dir) / 'app.log'
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_creates_daily_file(self):
        handler = DailyFileHandler(str(self.log_path))
        
        record = LogRecord(
            level=LogLevel.INFO,
            message='Test message',
            channel='test',
            datetime=dt(2025, 1, 27, 10, 0, 0)
        )
        handler.handle(record)
        handler.close()
        
        daily_file = Path(self.test_dir) / 'app-2025-01-27.log'
        self.assertTrue(daily_file.exists())
        self.assertIn('Test message', daily_file.read_text())
    
    def test_rotates_on_different_day(self):
        handler = DailyFileHandler(str(self.log_path))
        
        record1 = LogRecord(
            level=LogLevel.INFO,
            message='Day 1 message',
            channel='test',
            datetime=dt(2025, 1, 27, 10, 0, 0)
        )
        handler.handle(record1)
        
        record2 = LogRecord(
            level=LogLevel.INFO,
            message='Day 2 message',
            channel='test',
            datetime=dt(2025, 1, 28, 10, 0, 0)
        )
        handler.handle(record2)
        handler.close()
        
        file1 = Path(self.test_dir) / 'app-2025-01-27.log'
        file2 = Path(self.test_dir) / 'app-2025-01-28.log'
        
        self.assertTrue(file1.exists())
        self.assertTrue(file2.exists())
        self.assertIn('Day 1 message', file1.read_text())
        self.assertIn('Day 2 message', file2.read_text())
    
    def test_cleans_up_old_files(self):
        handler = DailyFileHandler(str(self.log_path), days=2)
        
        dates = [
            dt(2025, 1, 24, 10, 0, 0),
            dt(2025, 1, 25, 10, 0, 0),
            dt(2025, 1, 27, 10, 0, 0),
        ]
        
        for date in dates:
            record = LogRecord(
                level=LogLevel.INFO,
                message=f'Message {date.day}',
                channel='test',
                datetime=date
            )
            handler.handle(record)
        
        handler.close()
        
        old_file = Path(self.test_dir) / 'app-2025-01-24.log'
        self.assertFalse(old_file.exists())


class TestStackHandler(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_delegates_to_multiple_handlers(self):
        file1 = Path(self.test_dir) / 'log1.log'
        file2 = Path(self.test_dir) / 'log2.log'
        
        handler1 = FileHandler(str(file1))
        handler2 = FileHandler(str(file2))
        stack = StackHandler([handler1, handler2])
        
        record = LogRecord(level=LogLevel.INFO, message='Test message', channel='test')
        stack.handle(record)
        
        handler1.close()
        handler2.close()
        
        self.assertIn('Test message', file1.read_text())
        self.assertIn('Test message', file2.read_text())
    
    def test_ignores_exceptions_when_configured(self):
        failing_handler = FailingHandler(str(Path(self.test_dir) / 'fail.log'))
        stream = StringIO()
        working_handler = StreamHandler(stream)
        
        stack = StackHandler([failing_handler, working_handler], ignore_exceptions=True)
        
        record = LogRecord(level=LogLevel.INFO, message='Test message', channel='test')
        stack.handle(record)
        
        self.assertIn('Test message', stream.getvalue())


class FailingHandler(FileHandler):
    def write(self, formatted_message: str, record: LogRecord):
        raise RuntimeError('Handler failed')


if __name__ == '__main__':
    unittest.main()
