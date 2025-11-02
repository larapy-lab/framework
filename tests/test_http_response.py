import unittest
import json
import requests
from larapy.http.client.response import Response
from larapy.http.client.exceptions import RequestException


class TestResponse(unittest.TestCase):
    
    def _create_mock_response(self, body='', status=200, headers=None):
        mock_response = requests.Response()
        mock_response.status_code = status
        mock_response._content = body if isinstance(body, bytes) else body.encode('utf-8')
        
        if headers:
            mock_response.headers.update(headers)
        
        return mock_response
    
    def test_json_parsing(self):
        data = {'name': 'John', 'age': 30}
        mock_response = self._create_mock_response(json.dumps(data))
        response = Response(mock_response)
        
        self.assertEqual(response.json(), data)
        self.assertEqual(response.json('name'), 'John')
        self.assertEqual(response.json('age'), 30)
    
    def test_json_with_nested_keys(self):
        data = {'user': {'name': 'John', 'profile': {'age': 30}}}
        mock_response = self._create_mock_response(json.dumps(data))
        response = Response(mock_response)
        
        self.assertEqual(response.json('user.name'), 'John')
        self.assertEqual(response.json('user.profile.age'), 30)
    
    def test_json_with_default(self):
        mock_response = self._create_mock_response('not json')
        response = Response(mock_response)
        
        self.assertEqual(response.json(default={'error': True}), {'error': True})
        self.assertEqual(response.json('missing.key', 'default_value'), 'default_value')
    
    def test_body(self):
        text = 'Hello, World!'
        mock_response = self._create_mock_response(text)
        response = Response(mock_response)
        
        self.assertEqual(response.body(), text)
    
    def test_status(self):
        mock_response = self._create_mock_response('', 404)
        response = Response(mock_response)
        
        self.assertEqual(response.status(), 404)
    
    def test_headers(self):
        headers = {'Content-Type': 'application/json', 'X-Custom': 'value'}
        mock_response = self._create_mock_response('', headers=headers)
        response = Response(mock_response)
        
        self.assertEqual(response.headers(), headers)
        self.assertEqual(response.header('Content-Type'), 'application/json')
        self.assertEqual(response.header('X-Custom'), 'value')
        self.assertIsNone(response.header('Missing'))
    
    def test_successful(self):
        for status in [200, 201, 204, 299]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertTrue(response.successful())
            self.assertTrue(response.ok())
        
        for status in [199, 300, 400, 500]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertFalse(response.successful())
            self.assertFalse(response.ok())
    
    def test_failed(self):
        for status in [400, 404, 500, 503]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertTrue(response.failed())
        
        for status in [200, 201, 299]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertFalse(response.failed())
    
    def test_client_error(self):
        for status in [400, 404, 429, 499]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertTrue(response.client_error())
        
        mock_response = self._create_mock_response('', 200)
        response = Response(mock_response)
        self.assertFalse(response.client_error())
    
    def test_server_error(self):
        for status in [500, 502, 503, 599]:
            mock_response = self._create_mock_response('', status)
            response = Response(mock_response)
            self.assertTrue(response.server_error())
        
        mock_response = self._create_mock_response('', 200)
        response = Response(mock_response)
        self.assertFalse(response.server_error())
    
    def test_throw(self):
        mock_response = self._create_mock_response('', 404)
        response = Response(mock_response)
        
        with self.assertRaises(RequestException) as context:
            response.throw()
        
        self.assertIn('404', str(context.exception))
    
    def test_throw_successful_does_not_raise(self):
        mock_response = self._create_mock_response('', 200)
        response = Response(mock_response)
        
        result = response.throw()
        self.assertEqual(result, response)
    
    def test_throw_if(self):
        mock_response = self._create_mock_response('', 404)
        response = Response(mock_response)
        
        with self.assertRaises(RequestException):
            response.throw_if(True)
        
        result = response.throw_if(False)
        self.assertEqual(result, response)
    
    def test_throw_unless(self):
        mock_response = self._create_mock_response('', 404)
        response = Response(mock_response)
        
        with self.assertRaises(RequestException):
            response.throw_unless(False)
        
        result = response.throw_unless(True)
        self.assertEqual(result, response)
    
    def test_on_error(self):
        mock_response = self._create_mock_response('', 404)
        response = Response(mock_response)
        
        callback_called = []
        
        def callback(r):
            callback_called.append(r)
        
        response.on_error(callback)
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], response)
    
    def test_dict_access(self):
        data = {'name': 'John', 'age': 30}
        mock_response = self._create_mock_response(json.dumps(data))
        response = Response(mock_response)
        
        self.assertEqual(response['name'], 'John')
        self.assertEqual(response['age'], 30)


if __name__ == '__main__':
    unittest.main()
