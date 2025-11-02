import unittest
import tempfile
import shutil
from pathlib import Path
from io import StringIO
from larapy.logging import Logger, LogManager, Log, LogLevel
from larapy.logging.handlers import FileHandler, StreamHandler, NullHandler
from larapy.logging.formatters import LineFormatter


class TestLogger(unittest.TestCase):
    
    def setUp(self):
        self.stream = StringIO()
        self.handler = StreamHandler(self.stream)
        self.logger = Logger('test', [self.handler])
    
    def test_emergency_logs_message(self):
        self.logger.emergency('Emergency message')
        
        output = self.stream.getvalue()
        self.assertIn('EMERGENCY', output)
        self.assertIn('Emergency message', output)
    
    def test_alert_logs_message(self):
        self.logger.alert('Alert message')
        
        output = self.stream.getvalue()
        self.assertIn('ALERT', output)
        self.assertIn('Alert message', output)
    
    def test_critical_logs_message(self):
        self.logger.critical('Critical message')
        
        output = self.stream.getvalue()
        self.assertIn('CRITICAL', output)
        self.assertIn('Critical message', output)
    
    def test_error_logs_message(self):
        self.logger.error('Error message')
        
        output = self.stream.getvalue()
        self.assertIn('ERROR', output)
        self.assertIn('Error message', output)
    
    def test_warning_logs_message(self):
        self.logger.warning('Warning message')
        
        output = self.stream.getvalue()
        self.assertIn('WARNING', output)
        self.assertIn('Warning message', output)
    
    def test_notice_logs_message(self):
        self.logger.notice('Notice message')
        
        output = self.stream.getvalue()
        self.assertIn('NOTICE', output)
        self.assertIn('Notice message', output)
    
    def test_info_logs_message(self):
        self.logger.info('Info message')
        
        output = self.stream.getvalue()
        self.assertIn('INFO', output)
        self.assertIn('Info message', output)
    
    def test_debug_logs_message(self):
        self.logger.debug('Debug message')
        
        output = self.stream.getvalue()
        self.assertIn('DEBUG', output)
        self.assertIn('Debug message', output)
    
    def test_logs_with_context(self):
        self.logger.info('User action', {'user_id': 123, 'action': 'login'})
        
        output = self.stream.getvalue()
        self.assertIn('user_id=123', output)
        self.assertIn('action=login', output)
    
    def test_logs_with_exception(self):
        try:
            raise ValueError('Test error')
        except ValueError as e:
            self.logger.error('Error occurred', exception=e)
        
        output = self.stream.getvalue()
        self.assertIn('ValueError', output)
        self.assertIn('Test error', output)
    
    def test_share_context(self):
        self.logger.share_context({'request_id': 'abc123'})
        
        self.logger.info('First message')
        self.logger.info('Second message')
        
        output = self.stream.getvalue()
        self.assertEqual(output.count('request_id=abc123'), 2)
    
    def test_with_context_creates_new_logger(self):
        logger2 = self.logger.with_context({'temp': 'value'})
        
        self.assertIsNot(logger2, self.logger)
        self.assertIn('temp', logger2.shared_context)
        self.assertNotIn('temp', self.logger.shared_context)
    
    def test_listen_receives_log_records(self):
        records = []
        self.logger.listen(lambda record: records.append(record))
        
        self.logger.info('Test message')
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].message, 'Test message')


class TestLogManager(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        self.config = {
            'default': 'single',
            'channels': {
                'single': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'single.log'),
                    'level': 'debug',
                },
                'daily': {
                    'driver': 'daily',
                    'path': str(Path(self.test_dir) / 'daily.log'),
                    'level': 'info',
                    'days': 7,
                },
                'null': {
                    'driver': 'null',
                },
            }
        }
        
        self.manager = LogManager(self.config)
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_channel_returns_logger(self):
        logger = self.manager.channel('single')
        
        self.assertIsInstance(logger, Logger)
        self.assertEqual(logger.name, 'single')
    
    def test_channel_caches_instances(self):
        logger1 = self.manager.channel('single')
        logger2 = self.manager.channel('single')
        
        self.assertIs(logger1, logger2)
    
    def test_channel_uses_default_when_none_specified(self):
        logger = self.manager.channel()
        
        self.assertEqual(logger.name, 'single')
    
    def test_stack_combines_multiple_channels(self):
        logger = self.manager.stack(['single', 'daily'])
        
        logger.info('Test message')
        
        for handler in logger.handlers:
            handler.close()
        
        single_file = Path(self.test_dir) / 'single.log'
        self.assertTrue(single_file.exists())
    
    def test_build_creates_custom_logger(self):
        logger = self.manager.build({
            'driver': 'file',
            'path': str(Path(self.test_dir) / 'custom.log'),
            'level': 'warning'
        })
        
        logger.warning('Custom message')
        
        for handler in logger.handlers:
            handler.close()
        
        custom_file = Path(self.test_dir) / 'custom.log'
        self.assertTrue(custom_file.exists())
        self.assertIn('Custom message', custom_file.read_text())


class TestLogFacade(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        config = {
            'default': 'test',
            'channels': {
                'test': {
                    'driver': 'file',
                    'path': str(Path(self.test_dir) / 'test.log'),
                    'level': 'debug',
                },
            }
        }
        
        manager = LogManager(config)
        Log.set_manager(manager)
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_info_logs_via_facade(self):
        Log.info('Facade message')
        
        log_file = Path(self.test_dir) / 'test.log'
        self.assertTrue(log_file.exists())
        self.assertIn('Facade message', log_file.read_text())
    
    def test_all_log_levels_work(self):
        Log.emergency('Emergency')
        Log.alert('Alert')
        Log.critical('Critical')
        Log.error('Error')
        Log.warning('Warning')
        Log.notice('Notice')
        Log.info('Info')
        Log.debug('Debug')
        
        content = (Path(self.test_dir) / 'test.log').read_text()
        
        self.assertIn('Emergency', content)
        self.assertIn('Alert', content)
        self.assertIn('Critical', content)
        self.assertIn('Error', content)
        self.assertIn('Warning', content)
        self.assertIn('Notice', content)
        self.assertIn('Info', content)
        self.assertIn('Debug', content)
    
    def test_channel_selection(self):
        logger = Log.channel('test')
        
        self.assertIsInstance(logger, Logger)
    
    def test_share_context(self):
        Log.share_context({'shared': 'value'})
        Log.info('Message with shared context')
        
        content = (Path(self.test_dir) / 'test.log').read_text()
        self.assertIn('shared=value', content)


if __name__ == '__main__':
    unittest.main()
