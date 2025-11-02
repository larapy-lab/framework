import unittest
import json
from larapy.exceptions import ErrorRenderer


class TestErrorRenderer(unittest.TestCase):
    
    def setUp(self):
        self.renderer = ErrorRenderer(debug=True)
        self.production_renderer = ErrorRenderer(debug=False)
    
    def test_render_json_debug_mode(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_json(e, 500)
        
        data = json.loads(result)
        
        self.assertEqual(data['message'], 'Test error')
        self.assertEqual(data['status_code'], 500)
        self.assertEqual(data['exception'], 'ValueError')
        self.assertIn('file', data)
        self.assertIn('line', data)
        self.assertIn('trace', data)
    
    def test_render_json_production_mode(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.production_renderer.render_json(e, 500)
        
        data = json.loads(result)
        
        self.assertEqual(data['message'], 'Test error')
        self.assertEqual(data['status_code'], 500)
        self.assertNotIn('exception', data)
        self.assertNotIn('trace', data)
    
    def test_render_json_with_context(self):
        exception = ValueError('Test error')
        context = {'request': {'method': 'POST', 'path': '/api/test'}}
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_json(e, 500, context)
        
        data = json.loads(result)
        
        self.assertIn('context', data)
        self.assertEqual(data['context']['request']['method'], 'POST')
    
    def test_render_html_debug_mode(self):
        exception = ValueError('Test error message')
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_html(e, 500)
        
        self.assertIn('<!DOCTYPE html>', result)
        self.assertIn('ValueError', result)
        self.assertIn('Test error message', result)
        self.assertIn('Stack Trace', result)
    
    def test_render_html_production_mode(self):
        result = self.production_renderer.render_html(
            Exception('Test'), 
            404
        )
        
        self.assertIn('<!DOCTYPE html>', result)
        self.assertIn('404', result)
        self.assertIn('Not Found', result)
        self.assertNotIn('Stack Trace', result)
    
    def test_render_html_production_500(self):
        result = self.production_renderer.render_html(
            Exception('Internal error'),
            500
        )
        
        self.assertIn('500', result)
        self.assertIn('Server Error', result)
    
    def test_render_html_production_403(self):
        result = self.production_renderer.render_html(
            Exception('Forbidden'),
            403
        )
        
        self.assertIn('403', result)
        self.assertIn('Forbidden', result)
    
    def test_render_text_debug_mode(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_text(e, 500)
        
        self.assertIn('ValueError', result)
        self.assertIn('Test error', result)
        self.assertIn('Traceback', result)
    
    def test_render_text_production_mode(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.production_renderer.render_text(e, 500)
        
        self.assertEqual(result, 'Error 500: Test error')
    
    def test_debug_html_includes_code_snippet(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_html(e, 500)
        
        self.assertIn('Code Snippet', result)
    
    def test_debug_html_includes_context(self):
        exception = ValueError('Test error')
        context = {
            'request': {'method': 'GET', 'path': '/test'},
            'user': {'id': 123, 'email': 'test@example.com'}
        }
        
        try:
            raise exception
        except ValueError as e:
            result = self.renderer.render_html(e, 500, context)
        
        self.assertIn('Context', result)
        self.assertIn('request', result.lower())
        self.assertIn('GET', result)
    
    def test_get_stack_trace(self):
        exception = ValueError('Test')
        
        try:
            raise exception
        except ValueError as e:
            trace = self.renderer._get_stack_trace(e)
        
        self.assertIsInstance(trace, list)
        self.assertGreater(len(trace), 0)
        self.assertIn('file', trace[0])
        self.assertIn('line', trace[0])
        self.assertIn('function', trace[0])
    
    def test_get_exception_file_and_line(self):
        exception = ValueError('Test')
        
        try:
            raise exception
        except ValueError as e:
            file_path = self.renderer._get_exception_file(e)
            line_number = self.renderer._get_exception_line(e)
        
        self.assertIsNotNone(file_path)
        self.assertIn('test_error_renderer.py', file_path)
        self.assertIsInstance(line_number, int)
        self.assertGreater(line_number, 0)


if __name__ == '__main__':
    unittest.main()
