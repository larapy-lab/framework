import unittest
from larapy.http.client.fake import FakeHttpClient, FakeResponse


class TestFakeHttpClient(unittest.TestCase):
    
    def setUp(self):
        self.fake = FakeHttpClient()
    
    def test_fake_basic_response(self):
        self.fake.fake({
            'users': FakeResponse({'id': 1, 'name': 'John'}, 200)
        })
        
        response = self.fake.get('https://api.example.com/users')
        
        self.assertEqual(response.status(), 200)
        self.assertEqual(response.json(), {'id': 1, 'name': 'John'})
    
    def test_fake_with_dict_response(self):
        self.fake.fake({
            'posts': {'title': 'Hello World', 'content': 'Lorem ipsum'}
        })
        
        response = self.fake.get('https://api.example.com/posts')
        
        self.assertEqual(response.json('title'), 'Hello World')
        self.assertEqual(response.json('content'), 'Lorem ipsum')
    
    def test_fake_sequence(self):
        self.fake.sequence('users', [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'},
            {'id': 3, 'name': 'Bob'}
        ])
        
        response1 = self.fake.get('https://api.example.com/users')
        self.assertEqual(response1.json('id'), 1)
        
        response2 = self.fake.get('https://api.example.com/users')
        self.assertEqual(response2.json('id'), 2)
        
        response3 = self.fake.get('https://api.example.com/users')
        self.assertEqual(response3.json('id'), 3)
        
        response4 = self.fake.get('https://api.example.com/users')
        self.assertEqual(response4.json('id'), 3)
    
    def test_record_requests(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        self.fake.post('https://api.example.com/users', {'name': 'John'})
        
        recorded = self.fake.recorded()
        
        self.assertEqual(len(recorded), 2)
        self.assertEqual(recorded[0]['method'], 'GET')
        self.assertEqual(recorded[1]['method'], 'POST')
    
    def test_assert_sent(self):
        self.fake.fake()
        
        self.fake.post('https://api.example.com/users', {'name': 'John'})
        
        self.fake.assert_sent(lambda req: req['method'] == 'POST' and 'users' in req['url'])
    
    def test_assert_sent_fails(self):
        self.fake.fake()
        
        with self.assertRaises(AssertionError):
            self.fake.assert_sent(lambda req: req['method'] == 'POST')
    
    def test_assert_sent_count(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        self.fake.get('https://api.example.com/users')
        self.fake.get('https://api.example.com/posts')
        
        self.fake.assert_sent_count('users', 2)
        self.fake.assert_sent_count('posts', 1)
    
    def test_assert_sent_count_fails(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        
        with self.assertRaises(AssertionError):
            self.fake.assert_sent_count('users', 2)
    
    def test_assert_not_sent(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        
        self.fake.assert_not_sent(lambda req: req['method'] == 'POST')
    
    def test_assert_not_sent_fails(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        
        with self.assertRaises(AssertionError):
            self.fake.assert_not_sent(lambda req: req['method'] == 'GET')
    
    def test_wildcard_response(self):
        self.fake.fake({
            '*': FakeResponse({'default': True}, 200)
        })
        
        response1 = self.fake.get('https://api.example.com/anything')
        response2 = self.fake.post('https://api.example.com/other')
        
        self.assertEqual(response1.json('default'), True)
        self.assertEqual(response2.json('default'), True)
    
    def test_multiple_http_methods(self):
        self.fake.fake()
        
        self.fake.get('https://api.example.com/users')
        self.fake.post('https://api.example.com/users', {'name': 'John'})
        self.fake.put('https://api.example.com/users/1', {'name': 'Jane'})
        self.fake.patch('https://api.example.com/users/1', {'status': 'active'})
        self.fake.delete('https://api.example.com/users/1')
        self.fake.head('https://api.example.com/users')
        
        recorded = self.fake.recorded()
        
        self.assertEqual(len(recorded), 6)
        self.assertEqual(recorded[0]['method'], 'GET')
        self.assertEqual(recorded[1]['method'], 'POST')
        self.assertEqual(recorded[2]['method'], 'PUT')
        self.assertEqual(recorded[3]['method'], 'PATCH')
        self.assertEqual(recorded[4]['method'], 'DELETE')
        self.assertEqual(recorded[5]['method'], 'HEAD')


if __name__ == '__main__':
    unittest.main()
