import unittest
from unittest.mock import Mock, patch, MagicMock
from larapy.http.client.client import HttpClient
from larapy.http.client.response import Response


class TestHttpClient(unittest.TestCase):
    
    def setUp(self):
        self.client = HttpClient()
    
    def test_initialization(self):
        config = {
            'base_url': 'https://api.example.com',
            'timeout': 60,
            'verify': False
        }
        client = HttpClient(config)
        
        self.assertEqual(client.base_url, 'https://api.example.com')
        self.assertEqual(client._timeout, 60)
        self.assertEqual(client.verify, False)
    
    def test_with_headers(self):
        new_client = self.client.with_headers({'X-Custom': 'value'})
        
        self.assertIn('X-Custom', new_client.headers)
        self.assertEqual(new_client.headers['X-Custom'], 'value')
        self.assertNotIn('X-Custom', self.client.headers)
    
    def test_with_header(self):
        new_client = self.client.with_header('Authorization', 'Bearer token123')
        
        self.assertEqual(new_client.headers['Authorization'], 'Bearer token123')
        self.assertNotIn('Authorization', self.client.headers)
    
    def test_with_basic_auth(self):
        new_client = self.client.with_basic_auth('user', 'pass')
        
        self.assertIn('Authorization', new_client.headers)
        self.assertTrue(new_client.headers['Authorization'].startswith('Basic '))
    
    def test_with_digest_auth(self):
        new_client = self.client.with_digest_auth('user', 'pass')
        
        self.assertIn('auth', new_client.config)
        self.assertIsNotNone(new_client.config['auth'])
    
    def test_with_token(self):
        new_client = self.client.with_token('abc123')
        
        self.assertEqual(new_client.headers['Authorization'], 'Bearer abc123')
        
        new_client = self.client.with_token('xyz789', 'Token')
        self.assertEqual(new_client.headers['Authorization'], 'Token xyz789')
    
    def test_accept_json(self):
        new_client = self.client.accept_json()
        
        self.assertEqual(new_client.headers['Accept'], 'application/json')
    
    def test_as_json(self):
        new_client = self.client.as_json()
        
        self.assertEqual(new_client.headers['Content-Type'], 'application/json')
        self.assertEqual(new_client.headers['Accept'], 'application/json')
    
    def test_as_form(self):
        new_client = self.client.as_form()
        
        self.assertEqual(new_client.headers['Content-Type'], 'application/x-www-form-urlencoded')
    
    def test_timeout(self):
        new_client = self.client.timeout(120)
        
        self.assertEqual(new_client._timeout, 120)
        self.assertEqual(self.client._timeout, 30)
    
    def test_without_redirecting(self):
        new_client = self.client.without_redirecting()
        
        self.assertFalse(new_client.allow_redirects)
        self.assertTrue(self.client.allow_redirects)
    
    def test_without_verifying(self):
        new_client = self.client.without_verifying()
        
        self.assertFalse(new_client.verify)
        self.assertTrue(self.client.verify)
    
    def test_with_cookies(self):
        cookies = {'session': 'abc123'}
        new_client = self.client.with_cookies(cookies)
        
        self.assertEqual(new_client.config.get('cookies'), cookies)
    
    def test_retry_configuration(self):
        new_client = self.client.retry(times=5, sleep=1)
        
        self.assertIsNotNone(new_client._retry_config)
        self.assertEqual(new_client._retry_config.get('total'), 5)
    
    def test_middleware(self):
        def middleware(request):
            request['headers']['X-Middleware'] = 'applied'
            return request
        
        new_client = self.client.with_middleware(middleware)
        
        self.assertEqual(len(new_client._middleware), 1)
        self.assertEqual(len(self.client._middleware), 0)
    
    def test_before_sending(self):
        callback_called = []
        
        def callback(request):
            callback_called.append(request)
        
        new_client = self.client.before_sending(callback)
        
        self.assertEqual(len(new_client._before_sending_callbacks), 1)
        self.assertEqual(len(self.client._before_sending_callbacks), 0)
    
    def test_build_url_without_base(self):
        url = self.client._build_url('https://api.example.com/users')
        self.assertEqual(url, 'https://api.example.com/users')
    
    def test_build_url_with_base(self):
        client = HttpClient({'base_url': 'https://api.example.com'})
        url = client._build_url('/users')
        self.assertEqual(url, 'https://api.example.com/users')
    
    def test_clone_creates_independent_copy(self):
        new_client = self.client._clone()
        
        new_client.headers['X-Test'] = 'value'
        self.assertNotIn('X-Test', self.client.headers)
        
        new_client._timeout = 100
        self.assertEqual(self.client._timeout, 30)
    
    @patch('requests.Session.request')
    def test_get_request(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'response body'
        mock_request.return_value = mock_response
        
        response = self.client.get('https://api.example.com/users')
        
        mock_request.assert_called_once()
        self.assertIsInstance(response, Response)
    
    @patch('requests.Session.request')
    def test_post_request(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        response = self.client.post('https://api.example.com/users', {'name': 'John'})
        
        mock_request.assert_called_once()
        self.assertIsInstance(response, Response)


if __name__ == '__main__':
    unittest.main()
