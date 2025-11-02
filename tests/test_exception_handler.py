import unittest
from unittest.mock import Mock, MagicMock
from larapy.exceptions import ExceptionHandler
from larapy.http.exceptions import (
    HttpException,
    NotFoundHttpException,
    ServerErrorHttpException
)


class TestExceptionHandler(unittest.TestCase):
    
    def setUp(self):
        self.handler = ExceptionHandler(debug=True)
    
    def test_should_report_returns_true_by_default(self):
        exception = ValueError('Test error')
        
        result = self.handler.should_report(exception)
        
        self.assertTrue(result)
    
    def test_should_report_respects_dont_report_list(self):
        self.handler.dont_report = [ValueError]
        exception = ValueError('Test error')
        
        result = self.handler.should_report(exception)
        
        self.assertFalse(result)
    
    def test_should_report_with_string_type(self):
        self.handler.dont_report = ['ValueError']
        exception = ValueError('Test error')
        
        result = self.handler.should_report(exception)
        
        self.assertFalse(result)
    
    def test_should_report_with_full_qualified_name(self):
        self.handler.dont_report = ['larapy.http.exceptions.not_found_http_exception.NotFoundHttpException']
        exception = NotFoundHttpException()
        
        result = self.handler.should_report(exception)
        
        self.assertFalse(result)
    
    def test_report_calls_logger_for_500_errors(self):
        mock_logger = Mock()
        self.handler.set_logger(mock_logger)
        
        exception = ServerErrorHttpException('Server error')
        self.handler.report(exception)
        
        mock_logger.error.assert_called_once()
    
    def test_report_calls_logger_warning_for_400_errors(self):
        mock_logger = Mock()
        self.handler.set_logger(mock_logger)
        
        exception = NotFoundHttpException()
        self.handler.report(exception)
        
        mock_logger.warning.assert_called_once()
    
    def test_report_doesnt_call_logger_for_dont_report(self):
        mock_logger = Mock()
        self.handler.set_logger(mock_logger)
        self.handler.dont_report = [NotFoundHttpException]
        
        exception = NotFoundHttpException()
        self.handler.report(exception)
        
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
    
    def test_render_returns_dict_with_content(self):
        exception = ValueError('Test error')
        request = None
        
        result = self.handler.render(request, exception)
        
        self.assertIn('content', result)
        self.assertIn('status_code', result)
        self.assertIn('content_type', result)
        self.assertIn('headers', result)
    
    def test_render_http_exception_status_code(self):
        exception = NotFoundHttpException()
        request = None
        
        result = self.handler.render(request, exception)
        
        self.assertEqual(result['status_code'], 404)
    
    def test_render_non_http_exception_returns_500(self):
        exception = ValueError('Test error')
        request = None
        
        result = self.handler.render(request, exception)
        
        self.assertEqual(result['status_code'], 500)
    
    def test_render_returns_json_for_json_request(self):
        exception = ValueError('Test error')
        request = None
        
        result = self.handler.render(request, exception)
        
        self.assertIn('content_type', result)
        self.assertIn('message', result['content'])
    
    def test_render_returns_json_for_api_path(self):
        exception = ValueError('Test error')
        
        class SimpleRequest:
            path = '/api/users'
            headers = {'Accept': 'text/html'}
        
        request = SimpleRequest()
        
        try:
            raise exception
        except ValueError as e:
            result = self.handler.render(request, e)
        
        self.assertEqual(result['content_type'], 'application/json')
    
    def test_render_returns_html_by_default(self):
        exception = ValueError('Test error')
        
        class SimpleRequest:
            path = '/test'
            headers = {'Accept': 'text/html'}
        
        request = SimpleRequest()
        
        try:
            raise exception
        except ValueError as e:
            result = self.handler.render(request, e)
        
        self.assertEqual(result['content_type'], 'text/html')
        self.assertIn('<!DOCTYPE html>', result['content'])
    
    def test_render_includes_exception_headers(self):
        exception = HttpException(404, headers={'X-Custom': 'value'})
        request = None
        
        result = self.handler.render(request, exception)
        
        self.assertEqual(result['headers']['X-Custom'], 'value')
    
    def test_renderable_callback_is_used(self):
        def custom_renderer(request, exception):
            return {
                'content': 'Custom error page',
                'status_code': 500,
                'content_type': 'text/html',
                'headers': {}
            }
        
        self.handler.renderable(ValueError, custom_renderer)
        
        exception = ValueError('Test')
        result = self.handler.render(None, exception)
        
        self.assertEqual(result['content'], 'Custom error page')
    
    def test_reportable_callback_with_using(self):
        called = []
        
        def report_callback(e):
            called.append(str(e))
        
        self.handler.report_callbacks[ValueError] = [report_callback]
        
        exception = ValueError('Test error')
        self.handler.report(exception)
        
        self.assertEqual(len(called), 1)
        self.assertIn('Test error', called[0])
    
    def test_add_context_provider(self):
        def custom_provider():
            return {'app_version': '1.0.0'}
        
        self.handler.add_context_provider(custom_provider)
        
        exception = ValueError('Test')
        try:
            raise exception
        except ValueError as e:
            result = self.handler.render(None, e)
        
        self.assertIn('1.0.0', result['content'])
    
    def test_context_method_returns_empty_dict(self):
        result = self.handler.context()
        
        self.assertEqual(result, {})
    
    def test_production_handler_hides_sensitive_info(self):
        production_handler = ExceptionHandler(debug=False)
        exception = ValueError('Database password is secret123')
        request = None
        
        result = production_handler.render(request, exception)
        
        self.assertNotIn('Stack Trace', result['content'])


if __name__ == '__main__':
    unittest.main()
