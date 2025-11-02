import unittest
import tempfile
import shutil
from pathlib import Path
from larapy.filesystem.drivers.local import LocalFilesystemAdapter


class TestLocalFilesystemAdapter(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.adapter = LocalFilesystemAdapter(self.test_dir)
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_put_and_get(self):
        content = b'Hello, World!'
        self.adapter.put('test.txt', content)
        
        retrieved = self.adapter.get('test.txt')
        self.assertEqual(retrieved, content)
    
    def test_put_creates_directories(self):
        content = b'Nested file'
        self.adapter.put('dir1/dir2/file.txt', content)
        
        self.assertTrue(self.adapter.exists('dir1/dir2/file.txt'))
        self.assertEqual(self.adapter.get('dir1/dir2/file.txt'), content)
    
    def test_exists(self):
        self.assertFalse(self.adapter.exists('nonexistent.txt'))
        
        self.adapter.put('exists.txt', b'content')
        self.assertTrue(self.adapter.exists('exists.txt'))
    
    def test_missing(self):
        self.assertTrue(self.adapter.missing('nonexistent.txt'))
        
        self.adapter.put('exists.txt', b'content')
        self.assertFalse(self.adapter.missing('exists.txt'))
    
    def test_delete(self):
        self.adapter.put('delete_me.txt', b'content')
        self.assertTrue(self.adapter.exists('delete_me.txt'))
        
        result = self.adapter.delete('delete_me.txt')
        self.assertTrue(result)
        self.assertFalse(self.adapter.exists('delete_me.txt'))
    
    def test_delete_nonexistent_returns_false(self):
        result = self.adapter.delete('nonexistent.txt')
        self.assertFalse(result)
    
    def test_copy(self):
        content = b'Original content'
        self.adapter.put('original.txt', content)
        
        self.adapter.copy('original.txt', 'copied.txt')
        
        self.assertTrue(self.adapter.exists('original.txt'))
        self.assertTrue(self.adapter.exists('copied.txt'))
        self.assertEqual(self.adapter.get('copied.txt'), content)
    
    def test_move(self):
        content = b'Move me'
        self.adapter.put('source.txt', content)
        
        self.adapter.move('source.txt', 'destination.txt')
        
        self.assertFalse(self.adapter.exists('source.txt'))
        self.assertTrue(self.adapter.exists('destination.txt'))
        self.assertEqual(self.adapter.get('destination.txt'), content)
    
    def test_size(self):
        content = b'12345'
        self.adapter.put('size_test.txt', content)
        
        size = self.adapter.size('size_test.txt')
        self.assertEqual(size, len(content))
    
    def test_last_modified(self):
        self.adapter.put('timestamp.txt', b'content')
        
        timestamp = self.adapter.last_modified('timestamp.txt')
        self.assertIsInstance(timestamp, int)
        self.assertGreater(timestamp, 0)
    
    def test_files(self):
        self.adapter.put('file1.txt', b'a')
        self.adapter.put('file2.txt', b'b')
        self.adapter.put('dir/file3.txt', b'c')
        
        files = self.adapter.files()
        
        self.assertIn('file1.txt', files)
        self.assertIn('file2.txt', files)
        self.assertNotIn('dir/file3.txt', files)
    
    def test_files_recursive(self):
        self.adapter.put('file1.txt', b'a')
        self.adapter.put('dir/file2.txt', b'b')
        self.adapter.put('dir/subdir/file3.txt', b'c')
        
        files = self.adapter.files(recursive=True)
        
        self.assertIn('file1.txt', files)
        self.assertIn('dir/file2.txt', files)
        self.assertIn('dir/subdir/file3.txt', files)
    
    def test_all_files(self):
        self.adapter.put('file1.txt', b'a')
        self.adapter.put('dir/file2.txt', b'b')
        
        all_files = self.adapter.all_files()
        
        self.assertIn('file1.txt', all_files)
        self.assertIn('dir/file2.txt', all_files)
    
    def test_directories(self):
        self.adapter.put('dir1/file.txt', b'a')
        self.adapter.put('dir2/file.txt', b'b')
        self.adapter.put('dir1/subdir/file.txt', b'c')
        
        dirs = self.adapter.directories()
        
        self.assertIn('dir1', dirs)
        self.assertIn('dir2', dirs)
        self.assertNotIn('dir1/subdir', dirs)
    
    def test_make_directory(self):
        self.adapter.make_directory('new_dir')
        
        dir_path = Path(self.test_dir) / 'new_dir'
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())
    
    def test_delete_directory(self):
        self.adapter.put('del_dir/file1.txt', b'a')
        self.adapter.put('del_dir/file2.txt', b'b')
        
        result = self.adapter.delete_directory('del_dir')
        self.assertTrue(result)
        self.assertFalse(self.adapter.exists('del_dir'))
    
    def test_url(self):
        url = self.adapter.url('path/to/file.txt')
        
        self.assertIn('path/to/file.txt', url)
    
    def test_read_stream(self):
        content = b'Stream content'
        self.adapter.put('stream.txt', content)
        
        stream = self.adapter.read_stream('stream.txt')
        data = stream.read()
        stream.close()
        
        self.assertEqual(data, content)
    
    def test_write_stream(self):
        from io import BytesIO
        
        content = b'Stream write test'
        stream = BytesIO(content)
        
        self.adapter.write_stream('written.txt', stream)
        
        self.assertEqual(self.adapter.get('written.txt'), content)
    
    def test_append(self):
        self.adapter.put('append.txt', b'First ')
        self.adapter.append('append.txt', b'Second')
        
        result = self.adapter.get('append.txt')
        self.assertEqual(result, b'First Second')
    
    def test_prepend(self):
        self.adapter.put('prepend.txt', b'Second')
        self.adapter.prepend('prepend.txt', b'First ')
        
        result = self.adapter.get('prepend.txt')
        self.assertEqual(result, b'First Second')
    
    def test_path_traversal_protection(self):
        with self.assertRaises(ValueError):
            self.adapter.get('../../../etc/passwd')
    
    def test_visibility_public(self):
        self.adapter.put('public.txt', b'content', {'visibility': 'public'})
        
        file_path = Path(self.test_dir) / 'public.txt'
        mode = file_path.stat().st_mode & 0o777
        
        self.assertTrue(mode & 0o400)
    
    def test_visibility_private(self):
        self.adapter.put('private.txt', b'content', {'visibility': 'private'})
        
        file_path = Path(self.test_dir) / 'private.txt'
        mode = file_path.stat().st_mode & 0o777
        
        self.assertTrue(mode & 0o600)


if __name__ == '__main__':
    unittest.main()
