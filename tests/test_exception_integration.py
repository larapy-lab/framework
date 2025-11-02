import unittest
from unittest.mock import Mock
from larapy.exceptions import ExceptionHandler, ErrorRenderer, ExceptionContext
from larapy.http.exceptions import NotFoundHttpException, ServerErrorHttpException
from larapy.logging import Logger, LogManager, LogLevel
import tempfile
import os


class TestExceptionIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'exceptions.log')
        
        config = {
            'channels': {
                'file': {
                    'driver': 'file',
                    'path': self.log_file,
                    'level': 'debug',
                }
            }
        }
        
        manager = LogManager(config)
        self.logger = manager.channel('file')
        
        self.handler = ExceptionHandler(debug=True)
        self.handler.set_logger(self.logger)
    
    def test_exception_handler_with_logging_integration(self):
        exception = ValueError('Test error')
        
        self.handler.report(exception)
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('Test error', log_content)
        self.assertIn('ValueError', log_content)
    
    def test_http_exception_logs_warning_not_error(self):
        exception = NotFoundHttpException('Page not found')
        
        self.handler.report(exception)
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('Page not found', log_content)
        self.assertIn('WARNING', log_content)
    
    def test_server_error_logs_as_error(self):
        exception = ServerErrorHttpException('Database error')
        
        self.handler.report(exception)
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('Database error', log_content)
        self.assertIn('ERROR', log_content)
    
    def test_end_to_end_error_handling(self):
        class SimpleRequest:
            method = 'POST'
            path = '/api/users'
            headers = {'Accept': 'application/json'}
            query_params = {'page': '1'}
        
        exception = ValueError('Invalid user data')
        request = SimpleRequest()
        
        try:
            raise exception
        except ValueError as e:
            self.handler.report(e)
            result = self.handler.render(request, e)
        
        self.assertEqual(result['status_code'], 500)
        self.assertEqual(result['content_type'], 'application/json')
        self.assertIn('Invalid user data', result['content'])
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        self.assertIn('Invalid user data', log_content)
    
    def test_debug_mode_includes_stack_trace(self):
        exception = ValueError('Debug test')
        
        try:
            raise exception
        except ValueError as e:
            result = self.handler.render(None, e)
        
        self.assertIn('Stack Trace', result['content'])
        self.assertIn('ValueError', result['content'])
    
    def test_production_mode_hides_details(self):
        production_handler = ExceptionHandler(debug=False)
        exception = ValueError('Secret information')
        
        result = production_handler.render(None, exception)
        
        self.assertNotIn('Stack Trace', result['content'])
        self.assertIn('500', result['content'])
    
    def test_context_collection_with_real_data(self):
        class SimpleRequest:
            method = 'POST'
            path = '/login'
            headers = {'Content-Type': 'application/json'}
            query_params = {}
            form = {'email': 'test@example.com', 'password': 'secret'}
        
        class SimpleUser:
            id = 123
            email = 'test@example.com'
        
        context_collector = ExceptionContext()
        exception = ValueError('Login failed')
        
        try:
            raise exception
        except ValueError as e:
            context = context_collector.collect(e, request=SimpleRequest(), user=SimpleUser())
        
        self.assertEqual(context['request']['method'], 'POST')
        self.assertEqual(context['request']['path'], '/login')
        self.assertEqual(context['request']['body']['email'], 'test@example.com')
        self.assertEqual(context['request']['body']['password'], '***FILTERED***')
        self.assertEqual(context['user']['id'], 123)
    
    def test_custom_exception_renderer(self):
        def custom_renderer(request, exception):
            return {
                'content': f'Custom error: {str(exception)}',
                'status_code': 418,
                'content_type': 'text/plain',
                'headers': {'X-Custom': 'Error'}
            }
        
        self.handler.renderable(ValueError, custom_renderer)
        exception = ValueError('Custom error test')
        
        result = self.handler.render(None, exception)
        
        self.assertEqual(result['status_code'], 418)
        self.assertEqual(result['content'], 'Custom error: Custom error test')
        self.assertEqual(result['headers']['X-Custom'], 'Error')
    
    def test_dont_report_prevents_logging(self):
        self.handler.dont_report = [NotFoundHttpException]
        exception = NotFoundHttpException()
        
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        
        self.handler.report(exception)
        
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                content = f.read()
            self.assertEqual(content.strip(), '')
    
    def test_json_rendering_for_api_endpoints(self):
        class ApiRequest:
            path = '/api/v1/users'
            headers = {}
        
        exception = ValueError('API error')
        request = ApiRequest()
        
        try:
            raise exception
        except ValueError as e:
            result = self.handler.render(request, e)
        
        self.assertEqual(result['content_type'], 'application/json')
        
        import json
        data = json.loads(result['content'])
        self.assertEqual(data['message'], 'API error')
        self.assertEqual(data['status_code'], 500)


if __name__ == '__main__':
    unittest.main()
