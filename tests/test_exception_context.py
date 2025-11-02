import unittest
from unittest.mock import Mock
from larapy.exceptions import ExceptionContext


class TestExceptionContext(unittest.TestCase):
    
    def setUp(self):
        self.context = ExceptionContext()
    
    def test_collect_exception_context(self):
        exception = ValueError('Test error')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e)
        
        self.assertIn('exception', result)
        self.assertEqual(result['exception']['type'], 'ValueError')
        self.assertEqual(result['exception']['message'], 'Test error')
        self.assertIn('file', result['exception'])
        self.assertIn('line', result['exception'])
    
    def test_collect_environment_context(self):
        exception = ValueError('Test')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e)
        
        self.assertIn('environment', result)
        self.assertIn('python_version', result['environment'])
        self.assertIn('platform', result['environment'])
        self.assertIn('cwd', result['environment'])
    
    def test_collect_request_context_with_method_and_path(self):
        exception = ValueError('Test')
        request = Mock()
        request.method = 'POST'
        request.path = '/api/users'
        request.configure_mock(**{
            'query_params': {},
            'headers': {},
            'form': None
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e, request=request)
        
        self.assertIn('request', result)
        self.assertEqual(result['request']['method'], 'POST')
        self.assertEqual(result['request']['path'], '/api/users')
    
    def test_collect_request_context_with_query_params(self):
        exception = ValueError('Test')
        request = Mock()
        request.method = 'GET'
        request.path = '/search'
        request.configure_mock(**{
            'query_params': {'q': 'test', 'page': '1'},
            'headers': {},
            'form': None
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e, request=request)
        
        self.assertIn('query', result['request'])
        self.assertEqual(result['request']['query']['q'], 'test')
        self.assertEqual(result['request']['query']['page'], '1')
    
    def test_collect_user_context(self):
        exception = ValueError('Test')
        user = Mock()
        user.id = 123
        user.email = 'test@example.com'
        user.name = 'Test User'
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e, user=user)
        
        self.assertIn('user', result)
        self.assertEqual(result['user']['id'], 123)
        self.assertEqual(result['user']['email'], 'test@example.com')
        self.assertEqual(result['user']['name'], 'Test User')
    
    def test_filter_sensitive_data_in_body(self):
        exception = ValueError('Test')
        request = Mock()
        request.method = 'POST'
        request.path = '/login'
        request.configure_mock(**{
            'query_params': {},
            'form': {
                'email': 'test@example.com',
                'password': 'secret123',
                'token': 'abc123'
            },
            'headers': {}
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e, request=request)
        
        self.assertEqual(result['request']['body']['email'], 'test@example.com')
        self.assertEqual(result['request']['body']['password'], '***FILTERED***')
        self.assertEqual(result['request']['body']['token'], '***FILTERED***')
    
    def test_filter_sensitive_headers(self):
        exception = ValueError('Test')
        request = Mock()
        request.method = 'GET'
        request.path = '/api/data'
        request.configure_mock(**{
            'query_params': {},
            'headers': {
                'Authorization': 'Bearer token123',
                'Content-Type': 'application/json',
                'Cookie': 'session=abc123',
                'X-Api-Key': 'key123'
            },
            'form': None
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e, request=request)
        
        self.assertEqual(result['request']['headers']['Authorization'], '***FILTERED***')
        self.assertEqual(result['request']['headers']['Content-Type'], 'application/json')
        self.assertEqual(result['request']['headers']['Cookie'], '***FILTERED***')
        self.assertEqual(result['request']['headers']['X-Api-Key'], '***FILTERED***')
    
    def test_truncate_long_strings(self):
        context = ExceptionContext(max_string_length=50)
        exception = ValueError('Test')
        request = Mock()
        request.method = 'POST'
        request.path = '/test'
        request.configure_mock(**{
            'query_params': {},
            'headers': {},
            'form': {
                'long_text': 'a' * 100
            }
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = context.collect(e, request=request)
        
        self.assertEqual(len(result['request']['body']['long_text']), 53)
        self.assertTrue(result['request']['body']['long_text'].endswith('...'))
    
    def test_truncate_large_arrays(self):
        context = ExceptionContext(max_array_items=10)
        exception = ValueError('Test')
        request = Mock()
        request.method = 'POST'
        request.path = '/test'
        request.configure_mock(**{
            'query_params': {},
            'headers': {},
            'form': {
                'items': list(range(50))
            }
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = context.collect(e, request=request)
        
        self.assertEqual(len(result['request']['body']['items']), 11)
        self.assertEqual(result['request']['body']['items'][-1], '...')
    
    def test_add_custom_provider(self):
        def custom_provider():
            return {'custom_data': 'test_value', 'app_version': '1.0.0'}
        
        self.context.add_provider(custom_provider)
        exception = ValueError('Test')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e)
        
        self.assertEqual(result['custom_data'], 'test_value')
        self.assertEqual(result['app_version'], '1.0.0')
    
    def test_custom_provider_exception_doesnt_break_collection(self):
        def failing_provider():
            raise RuntimeError('Provider failed')
        
        self.context.add_provider(failing_provider)
        exception = ValueError('Test')
        
        try:
            raise exception
        except ValueError as e:
            result = self.context.collect(e)
        
        self.assertIn('exception', result)
        self.assertIn('environment', result)
    
    def test_custom_dont_flash_list(self):
        context = ExceptionContext(dont_flash=['email', 'custom_field'])
        exception = ValueError('Test')
        request = Mock()
        request.method = 'POST'
        request.path = '/test'
        request.configure_mock(**{
            'query_params': {},
            'headers': {},
            'form': {
                'email': 'test@example.com',
                'custom_field': 'sensitive',
                'name': 'John'
            }
        })
        delattr(request, 'json')
        
        try:
            raise exception
        except ValueError as e:
            result = context.collect(e, request=request)
        
        self.assertEqual(result['request']['body']['email'], '***FILTERED***')
        self.assertEqual(result['request']['body']['custom_field'], '***FILTERED***')
        self.assertEqual(result['request']['body']['name'], 'John')


if __name__ == '__main__':
    unittest.main()
