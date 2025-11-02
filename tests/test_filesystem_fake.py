import unittest
from datetime import datetime, timedelta
from io import BytesIO
from larapy.filesystem.fake import FakeStorage


class TestFakeStorage(unittest.TestCase):
    
    def setUp(self):
        self.fake = FakeStorage()
    
    def test_put_and_get(self):
        self.fake.put('test.txt', b'content')
        
        result = self.fake.get('test.txt')
        self.assertEqual(result, b'content')
    
    def test_exists(self):
        self.assertFalse(self.fake.exists('test.txt'))
        
        self.fake.put('test.txt', b'content')
        self.assertTrue(self.fake.exists('test.txt'))
    
    def test_missing(self):
        self.assertTrue(self.fake.missing('test.txt'))
        
        self.fake.put('test.txt', b'content')
        self.assertFalse(self.fake.missing('test.txt'))
    
    def test_delete(self):
        self.fake.put('test.txt', b'content')
        
        result = self.fake.delete('test.txt')
        self.assertTrue(result)
        self.assertFalse(self.fake.exists('test.txt'))
    
    def test_copy(self):
        self.fake.put('original.txt', b'content')
        
        self.fake.copy('original.txt', 'copy.txt')
        
        self.assertTrue(self.fake.exists('original.txt'))
        self.assertTrue(self.fake.exists('copy.txt'))
        self.assertEqual(self.fake.get('copy.txt'), b'content')
    
    def test_move(self):
        self.fake.put('source.txt', b'content')
        
        self.fake.move('source.txt', 'dest.txt')
        
        self.assertFalse(self.fake.exists('source.txt'))
        self.assertTrue(self.fake.exists('dest.txt'))
    
    def test_size(self):
        content = b'12345'
        self.fake.put('test.txt', content)
        
        size = self.fake.size('test.txt')
        self.assertEqual(size, len(content))
    
    def test_files(self):
        self.fake.put('file1.txt', b'a')
        self.fake.put('file2.txt', b'b')
        self.fake.put('dir/file3.txt', b'c')
        
        files = self.fake.files()
        
        self.assertIn('file1.txt', files)
        self.assertIn('file2.txt', files)
        self.assertNotIn('dir/file3.txt', files)
    
    def test_directories(self):
        self.fake.put('dir1/file.txt', b'a')
        self.fake.put('dir2/file.txt', b'b')
        self.fake.put('dir1/subdir/file.txt', b'c')
        
        dirs = self.fake.directories()
        
        self.assertIn('dir1', dirs)
        self.assertIn('dir2', dirs)
    
    def test_delete_directory(self):
        self.fake.put('dir/file1.txt', b'a')
        self.fake.put('dir/file2.txt', b'b')
        
        result = self.fake.delete_directory('dir')
        self.assertTrue(result)
        self.assertFalse(self.fake.exists('dir/file1.txt'))
    
    def test_url(self):
        url = self.fake.url('path/file.txt')
        
        self.assertIn('path/file.txt', url)
        self.assertTrue(url.startswith('https://'))
    
    def test_temporary_url(self):
        expiration = datetime.now() + timedelta(hours=1)
        url = self.fake.temporary_url('path/file.txt', expiration)
        
        self.assertIn('path/file.txt', url)
        self.assertIn('expires=', url)
    
    def test_read_stream(self):
        content = b'stream content'
        self.fake.put('test.txt', content)
        
        stream = self.fake.read_stream('test.txt')
        data = stream.read()
        
        self.assertEqual(data, content)
    
    def test_write_stream(self):
        content = b'stream write'
        stream = BytesIO(content)
        
        self.fake.write_stream('test.txt', stream)
        
        self.assertEqual(self.fake.get('test.txt'), content)
    
    def test_append(self):
        self.fake.put('test.txt', b'First ')
        self.fake.append('test.txt', b'Second')
        
        result = self.fake.get('test.txt')
        self.assertEqual(result, b'First Second')
    
    def test_prepend(self):
        self.fake.put('test.txt', b'Second')
        self.fake.prepend('test.txt', b'First ')
        
        result = self.fake.get('test.txt')
        self.assertEqual(result, b'First Second')
    
    def test_assert_exists(self):
        self.fake.put('test.txt', b'content')
        
        self.fake.assert_exists('test.txt')
    
    def test_assert_exists_fails(self):
        with self.assertRaises(AssertionError):
            self.fake.assert_exists('nonexistent.txt')
    
    def test_assert_missing(self):
        self.fake.assert_missing('nonexistent.txt')
    
    def test_assert_missing_fails(self):
        self.fake.put('test.txt', b'content')
        
        with self.assertRaises(AssertionError):
            self.fake.assert_missing('test.txt')
    
    def test_assert_created(self):
        self.fake.put('test.txt', b'content')
        
        self.fake.assert_created('test.txt')
    
    def test_assert_created_fails(self):
        with self.assertRaises(AssertionError):
            self.fake.assert_created('never_created.txt')
    
    def test_assert_deleted(self):
        self.fake.put('test.txt', b'content')
        self.fake.delete('test.txt')
        
        self.fake.assert_deleted('test.txt')
    
    def test_assert_deleted_fails(self):
        with self.assertRaises(AssertionError):
            self.fake.assert_deleted('never_deleted.txt')
    
    def test_operations_recorded(self):
        self.fake.put('test.txt', b'content')
        self.fake.get('test.txt')
        self.fake.delete('test.txt')
        
        self.assertEqual(len(self.fake.operations), 3)
        self.assertEqual(self.fake.operations[0]['operation'], 'put')
        self.assertEqual(self.fake.operations[1]['operation'], 'get')
        self.assertEqual(self.fake.operations[2]['operation'], 'delete')
    
    def test_reset(self):
        self.fake.put('test.txt', b'content')
        self.fake.get('test.txt')
        
        self.fake.reset()
        
        self.assertEqual(len(self.fake._storage), 0)
        self.assertEqual(len(self.fake.operations), 0)


if __name__ == '__main__':
    unittest.main()
