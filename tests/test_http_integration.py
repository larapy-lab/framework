import unittest
from larapy.http.client.http_facade import Http
from larapy.http.client.client import HttpClient
from larapy.http.client.exceptions import RequestException, TimeoutException


class TestHttpIntegration(unittest.TestCase):
    
    def test_get_request_with_httpbin(self):
        response = Http.get('https://httpbin.org/get')
        
        self.assertTrue(response.successful())
        self.assertEqual(response.status(), 200)
        
        data = response.json()
        self.assertIn('url', data)
    
    def test_get_with_query_parameters(self):
        response = Http.get('https://httpbin.org/get', {'foo': 'bar', 'test': '123'})
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['args']['foo'], 'bar')
        self.assertEqual(data['args']['test'], '123')
    
    def test_post_with_json_data(self):
        payload = {'name': 'John Doe', 'age': 30}
        response = Http.as_json().post('https://httpbin.org/post', payload)
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['json']['name'], 'John Doe')
        self.assertEqual(data['json']['age'], 30)
    
    def test_headers_sent_correctly(self):
        response = Http.with_headers({
            'X-Custom-Header': 'test-value',
            'X-Another': 'another-value'
        }).get('https://httpbin.org/headers')
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['headers']['X-Custom-Header'], 'test-value')
        self.assertEqual(data['headers']['X-Another'], 'another-value')
    
    def test_basic_auth(self):
        response = Http.with_basic_auth('user', 'pass').get('https://httpbin.org/basic-auth/user/pass')
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['user'], 'user')
    
    def test_bearer_token(self):
        response = Http.with_token('test-token-123').get('https://httpbin.org/bearer')
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['token'], 'test-token-123')
    
    def test_put_request(self):
        payload = {'updated': True}
        response = Http.as_json().put('https://httpbin.org/put', payload)
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['json']['updated'], True)
    
    def test_patch_request(self):
        payload = {'patched': True}
        response = Http.as_json().patch('https://httpbin.org/patch', payload)
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['json']['patched'], True)
    
    def test_delete_request(self):
        response = Http.delete('https://httpbin.org/delete')
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertIn('url', data)
    
    def test_response_status_codes(self):
        response = Http.get('https://httpbin.org/status/404')
        
        self.assertFalse(response.successful())
        self.assertTrue(response.client_error())
        self.assertEqual(response.status(), 404)
    
    def test_response_throw_on_error(self):
        with self.assertRaises(RequestException):
            Http.get('https://httpbin.org/status/500').throw()
    
    def test_redirect_following(self):
        response = Http.get('https://httpbin.org/redirect/2')
        
        self.assertTrue(response.successful())
        self.assertEqual(response.status(), 200)
    
    def test_without_redirecting(self):
        response = Http.without_redirecting().get('https://httpbin.org/redirect/1')
        
        self.assertTrue(response.redirect())
        self.assertIn(response.status(), [301, 302, 303, 307, 308])
    
    def test_accept_json_header(self):
        response = Http.accept_json().get('https://httpbin.org/headers')
        
        self.assertTrue(response.successful())
        
        data = response.json()
        self.assertEqual(data['headers']['Accept'], 'application/json')
    
    def test_timeout_configuration(self):
        client = HttpClient({'timeout': 10})
        self.assertEqual(client._timeout, 10)
    
    def test_base_url_concatenation(self):
        response = Http.base_url('https://httpbin.org').get('/get')
        
        self.assertTrue(response.successful())
        self.assertEqual(response.status(), 200)
    
    def test_response_cookies(self):
        response = Http.get('https://httpbin.org/cookies/set?test=value')
        
        self.assertTrue(response.successful())
        cookies = response.cookies()
        self.assertIsInstance(cookies, dict)


if __name__ == '__main__':
    unittest.main()
