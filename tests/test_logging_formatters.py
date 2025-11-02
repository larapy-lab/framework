import unittest
import json
from datetime import datetime as dt
from larapy.logging.log_level import LogLevel
from larapy.logging.log_record import LogRecord
from larapy.logging.formatters import LineFormatter, JsonFormatter


class TestLineFormatter(unittest.TestCase):
    
    def setUp(self):
        self.formatter = LineFormatter()
    
    def test_format_simple_message(self):
        record = LogRecord(
            level=LogLevel.INFO,
            message='Test message',
            channel='test',
            datetime=dt(2025, 1, 27, 10, 30, 0)
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('[2025-01-27 10:30:00]', result)
        self.assertIn('test.INFO', result)
        self.assertIn('Test message', result)
    
    def test_format_with_context(self):
        record = LogRecord(
            level=LogLevel.ERROR,
            message='Error occurred',
            context={'user_id': 123, 'action': 'login'},
            channel='app',
            datetime=dt(2025, 1, 27, 10, 30, 0)
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('user_id=123', result)
        self.assertIn('action=login', result)
    
    def test_format_with_exception(self):
        try:
            raise ValueError('Test error')
        except ValueError as e:
            record = LogRecord(
                level=LogLevel.CRITICAL,
                message='Exception caught',
                channel='test',
                datetime=dt.now(),
                exception=e
            )
            
            result = self.formatter.format(record)
            
            self.assertIn('ValueError', result)
            self.assertIn('Test error', result)
    
    def test_custom_format_string(self):
        formatter = LineFormatter(format_string='{level}: {message}')
        record = LogRecord(
            level=LogLevel.DEBUG,
            message='Debug info',
            channel='test'
        )
        
        result = formatter.format(record)
        
        self.assertIn('DEBUG: Debug info', result)
    
    def test_custom_date_format(self):
        formatter = LineFormatter(date_format='%Y/%m/%d')
        record = LogRecord(
            level=LogLevel.INFO,
            message='Test',
            channel='test',
            datetime=dt(2025, 1, 27, 10, 30, 0)
        )
        
        result = formatter.format(record)
        
        self.assertIn('[2025/01/27]', result)


class TestJsonFormatter(unittest.TestCase):
    
    def setUp(self):
        self.formatter = JsonFormatter()
    
    def test_format_simple_message(self):
        record = LogRecord(
            level=LogLevel.INFO,
            message='Test message',
            channel='test',
            datetime=dt(2025, 1, 27, 10, 30, 0)
        )
        
        result = self.formatter.format(record)
        data = json.loads(result)
        
        self.assertEqual(data['level'], 'info')
        self.assertEqual(data['message'], 'Test message')
        self.assertEqual(data['channel'], 'test')
    
    def test_format_with_context(self):
        record = LogRecord(
            level=LogLevel.WARNING,
            message='Warning message',
            context={'key': 'value', 'number': 42},
            channel='app'
        )
        
        result = self.formatter.format(record)
        data = json.loads(result)
        
        self.assertEqual(data['context']['key'], 'value')
        self.assertEqual(data['context']['number'], 42)
    
    def test_format_with_exception(self):
        try:
            raise RuntimeError('Test exception')
        except RuntimeError as e:
            record = LogRecord(
                level=LogLevel.ERROR,
                message='Error with exception',
                channel='test',
                exception=e
            )
            
            result = self.formatter.format(record)
            data = json.loads(result)
            
            self.assertIn('exception', data)
            self.assertEqual(data['exception']['class'], 'RuntimeError')
            self.assertEqual(data['exception']['message'], 'Test exception')
    
    def test_pretty_format(self):
        formatter = JsonFormatter(pretty=True)
        record = LogRecord(
            level=LogLevel.DEBUG,
            message='Test',
            channel='test'
        )
        
        result = formatter.format(record)
        
        self.assertIn('\n', result)
        self.assertIn('  ', result)


if __name__ == '__main__':
    unittest.main()
