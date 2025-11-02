import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime as dt
from larapy.logging import Log, LogManager, LogLevel
from larapy.logging.formatters import JsonFormatter


class TestComplexScenarios(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_stack_channel_logs_to_multiple_files(self):
        config = {
            'default': 'stack',
            'channels': {
                'stack': {
                    'driver': 'stack',
                    'channels': ['file1', 'file2', 'file3'],
                },
                'file1': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'app1.log'),
                },
                'file2': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'app2.log'),
                },
                'file3': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'app3.log'),
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('stack')
        
        logger.info('Multi-channel message')
        
        for handler in logger.handlers:
            handler.close()
        
        for i in range(1, 4):
            log_file = Path(self.test_dir) / f'app{i}.log'
            self.assertTrue(log_file.exists())
            self.assertIn('Multi-channel message', log_file.read_text())
    
    def test_different_log_levels_per_channel(self):
        config = {
            'channels': {
                'debug_channel': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'debug.log'),
                    'level': 'debug',
                },
                'error_channel': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'error.log'),
                    'level': 'error',
                },
            }
        }
        
        manager = LogManager(config)
        
        debug_logger = manager.channel('debug_channel')
        debug_logger.debug('Debug message')
        debug_logger.error('Error message')
        
        error_logger = manager.channel('error_channel')
        error_logger.debug('Should not appear')
        error_logger.error('Error only')
        
        for logger in [debug_logger, error_logger]:
            for handler in logger.handlers:
                handler.close()
        
        debug_content = (Path(self.test_dir) / 'debug.log').read_text()
        self.assertIn('Debug message', debug_content)
        self.assertIn('Error message', debug_content)
        
        error_content = (Path(self.test_dir) / 'error.log').read_text()
        self.assertNotIn('Should not appear', error_content)
        self.assertIn('Error only', error_content)
    
    def test_json_formatted_logs(self):
        config = {
            'channels': {
                'json': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'app.log'),
                    'formatter': 'json',
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('json')
        
        logger.info('Structured log', {'user_id': 123, 'action': 'purchase', 'amount': 99.99})
        
        for handler in logger.handlers:
            handler.close()
        
        import json
        content = (Path(self.test_dir) / 'app.log').read_text()
        data = json.loads(content.strip())
        
        self.assertEqual(data['level'], 'info')
        self.assertEqual(data['message'], 'Structured log')
        self.assertEqual(data['context']['user_id'], 123)
        self.assertEqual(data['context']['action'], 'purchase')
        self.assertEqual(data['context']['amount'], 99.99)
    
    def test_daily_rotation_with_multiple_days(self):
        config = {
            'channels': {
                'daily': {
                    'driver': 'daily',
                    'path': str(Path(self.test_dir) / 'app.log'),
                    'days': 2,
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('daily')
        
        dates = [
            dt(2025, 1, 25, 10, 0, 0),
            dt(2025, 1, 26, 10, 0, 0),
            dt(2025, 1, 27, 10, 0, 0),
            dt(2025, 1, 28, 10, 0, 0),
        ]
        
        for date in dates:
            from larapy.logging.log_record import LogRecord
            record = LogRecord(
                level=LogLevel.INFO,
                message=f'Log for {date.date()}',
                channel='daily',
                datetime=date
            )
            logger.handlers[0].handle(record)
        
        logger.handlers[0].close()
        
        file_28 = Path(self.test_dir) / 'app-2025-01-28.log'
        file_27 = Path(self.test_dir) / 'app-2025-01-27.log'
        self.assertTrue(file_28.exists())
        self.assertTrue(file_27.exists())
        
        old_file_25 = Path(self.test_dir) / 'app-2025-01-25.log'
        self.assertFalse(old_file_25.exists(), "File older than 2 days should be cleaned up")
    
    def test_context_persists_across_logs(self):
        config = {
            'channels': {
                'test': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'context.log'),
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('test')
        
        logger.share_context({
            'request_id': 'req-123',
            'user_id': 456,
            'ip': '192.168.1.1'
        })
        
        logger.info('First action', {'action': 'login'})
        logger.info('Second action', {'action': 'purchase'})
        logger.info('Third action', {'action': 'logout'})
        
        for handler in logger.handlers:
            handler.close()
        
        content = (Path(self.test_dir) / 'context.log').read_text()
        
        self.assertEqual(content.count('request_id=req-123'), 3)
        self.assertEqual(content.count('user_id=456'), 3)
        self.assertEqual(content.count('ip=192.168.1.1'), 3)
        
        self.assertIn('action=login', content)
        self.assertIn('action=purchase', content)
        self.assertIn('action=logout', content)
    
    def test_exception_logging_with_stack_trace(self):
        config = {
            'channels': {
                'errors': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'errors.log'),
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('errors')
        
        def failing_function():
            raise ValueError('Something went wrong')
        
        try:
            failing_function()
        except ValueError as e:
            logger.error('Caught exception', exception=e)
        
        for handler in logger.handlers:
            handler.close()
        
        content = (Path(self.test_dir) / 'errors.log').read_text()
        
        self.assertIn('ValueError', content)
        self.assertIn('Something went wrong', content)
        self.assertIn('failing_function', content)
    
    def test_listener_called_for_all_logs(self):
        config = {
            'channels': {
                'test': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'test.log'),
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('test')
        
        logged_records = []
        logger.listen(lambda record: logged_records.append(record))
        
        logger.debug('Debug')
        logger.info('Info')
        logger.warning('Warning')
        logger.error('Error')
        logger.critical('Critical')
        
        self.assertEqual(len(logged_records), 5)
        self.assertEqual(logged_records[0].level, LogLevel.DEBUG)
        self.assertEqual(logged_records[1].level, LogLevel.INFO)
        self.assertEqual(logged_records[2].level, LogLevel.WARNING)
        self.assertEqual(logged_records[3].level, LogLevel.ERROR)
        self.assertEqual(logged_records[4].level, LogLevel.CRITICAL)
    
    def test_build_custom_channel_on_the_fly(self):
        config = {'channels': {}}
        manager = LogManager(config)
        
        logger = manager.build({
            'driver': 'file',
            'path': str(Path(self.test_dir) / 'custom.log'),
            'level': 'warning'
        })
        
        logger.debug('Should not appear')
        logger.info('Should not appear either')
        logger.warning('Warning appears')
        logger.error('Error appears')
        
        for handler in logger.handlers:
            handler.close()
        
        content = (Path(self.test_dir) / 'custom.log').read_text()
        
        self.assertNotIn('Should not appear', content)
        self.assertIn('Warning appears', content)
        self.assertIn('Error appears', content)
    
    def test_null_channel_discards_all_logs(self):
        config = {
            'channels': {
                'null': {
                    'driver': 'null',
                },
            }
        }
        
        manager = LogManager(config)
        logger = manager.channel('null')
        
        logger.emergency('Emergency')
        logger.critical('Critical')
        logger.error('Error')
        
        files = list(Path(self.test_dir).glob('*'))
        self.assertEqual(len(files), 0)


if __name__ == '__main__':
    unittest.main()
