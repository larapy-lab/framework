import unittest
import tempfile
import shutil
from pathlib import Path
from larapy.filesystem.drivers.local import LocalFilesystemAdapter


class TestComplexScenarios(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.adapter = LocalFilesystemAdapter(
            root=self.test_dir,
            url='/storage',
            visibility='public'
        )
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_large_file_streaming(self):
        large_content = b'x' * (10 * 1024 * 1024)
        
        self.adapter.put('large.bin', large_content)
        
        with self.adapter.read_stream('large.bin') as stream:
            chunk = stream.read(1024)
            self.assertEqual(len(chunk), 1024)
            self.assertEqual(chunk, b'x' * 1024)
    
    def test_nested_directory_creation(self):
        path = 'level1/level2/level3/file.txt'
        
        self.adapter.put(path, b'content')
        
        self.assertTrue(self.adapter.exists(path))
        self.assertEqual(self.adapter.get(path), b'content')
    
    def test_multiple_files_same_directory(self):
        files = [
            ('dir/file1.txt', b'content1'),
            ('dir/file2.txt', b'content2'),
            ('dir/file3.txt', b'content3'),
        ]
        
        for path, content in files:
            self.adapter.put(path, content)
        
        directory_files = self.adapter.files('dir')
        
        self.assertEqual(len(directory_files), 3)
        self.assertIn('dir/file1.txt', directory_files)
        self.assertIn('dir/file2.txt', directory_files)
        self.assertIn('dir/file3.txt', directory_files)
    
    def test_recursive_directory_listing(self):
        paths = [
            'root1.txt',
            'dir1/file1.txt',
            'dir1/subdir1/file2.txt',
            'dir2/file3.txt',
        ]
        
        for path in paths:
            self.adapter.put(path, b'content')
        
        all_files = self.adapter.all_files()
        
        self.assertGreaterEqual(len(all_files), len(paths))
        for path in paths:
            self.assertIn(path, all_files)
    
    def test_move_across_directories(self):
        self.adapter.put('source/file.txt', b'content')
        
        self.adapter.move('source/file.txt', 'dest/nested/file.txt')
        
        self.assertFalse(self.adapter.exists('source/file.txt'))
        self.assertTrue(self.adapter.exists('dest/nested/file.txt'))
        self.assertEqual(self.adapter.get('dest/nested/file.txt'), b'content')
    
    def test_copy_preserves_original(self):
        original_content = b'original content'
        self.adapter.put('original.txt', original_content)
        
        self.adapter.copy('original.txt', 'copy.txt')
        
        self.assertTrue(self.adapter.exists('original.txt'))
        self.assertTrue(self.adapter.exists('copy.txt'))
        self.assertEqual(self.adapter.get('original.txt'), original_content)
        self.assertEqual(self.adapter.get('copy.txt'), original_content)
    
    def test_delete_directory_with_nested_files(self):
        paths = [
            'delete_dir/file1.txt',
            'delete_dir/subdir/file2.txt',
            'delete_dir/subdir/nested/file3.txt',
        ]
        
        for path in paths:
            self.adapter.put(path, b'content')
        
        self.adapter.delete_directory('delete_dir')
        
        for path in paths:
            self.assertFalse(self.adapter.exists(path))
    
    def test_append_to_empty_file(self):
        self.adapter.put('empty.txt', b'')
        
        self.adapter.append('empty.txt', b'new content')
        
        self.assertEqual(self.adapter.get('empty.txt'), b'new content')
    
    def test_prepend_multiple_times(self):
        self.adapter.put('test.txt', b'original')
        
        self.adapter.prepend('test.txt', b'second ')
        self.adapter.prepend('test.txt', b'first ')
        
        result = self.adapter.get('test.txt')
        self.assertEqual(result, b'first second original')
    
    def test_overwrite_existing_file(self):
        self.adapter.put('file.txt', b'first content')
        
        self.adapter.put('file.txt', b'second content')
        
        result = self.adapter.get('file.txt')
        self.assertEqual(result, b'second content')
    
    def test_binary_content_preservation(self):
        binary_data = bytes(range(256))
        
        self.adapter.put('binary.dat', binary_data)
        
        result = self.adapter.get('binary.dat')
        self.assertEqual(result, binary_data)
    
    def test_empty_directory_operations(self):
        self.adapter.make_directory('empty_dir')
        
        files = self.adapter.files('empty_dir')
        directories = self.adapter.directories('empty_dir')
        
        self.assertEqual(len(files), 0)
        self.assertEqual(len(directories), 0)
    
    def test_special_characters_in_filenames(self):
        special_names = [
            'file with spaces.txt',
            'file-with-dashes.txt',
            'file_with_underscores.txt',
            'file.multiple.dots.txt',
        ]
        
        for name in special_names:
            self.adapter.put(name, b'content')
        
        for name in special_names:
            self.assertTrue(self.adapter.exists(name))
            self.assertEqual(self.adapter.get(name), b'content')
    
    def test_file_size_tracking(self):
        sizes = {
            'small.txt': b'x' * 100,
            'medium.txt': b'x' * 10000,
            'large.txt': b'x' * 1000000,
        }
        
        for path, content in sizes.items():
            self.adapter.put(path, content)
        
        for path, content in sizes.items():
            size = self.adapter.size(path)
            self.assertEqual(size, len(content))
    
    def test_last_modified_updates(self):
        import time
        
        self.adapter.put('test.txt', b'initial')
        first_modified = self.adapter.last_modified('test.txt')
        
        time.sleep(0.1)
        self.adapter.put('test.txt', b'updated')
        second_modified = self.adapter.last_modified('test.txt')
        
        self.assertGreaterEqual(second_modified, first_modified)
    
    def test_stream_write_large_content(self):
        large_content = b'y' * (5 * 1024 * 1024)
        
        import io
        with io.BytesIO(large_content) as stream:
            self.adapter.write_stream('stream_large.bin', stream)
        
        result_size = self.adapter.size('stream_large.bin')
        self.assertEqual(result_size, len(large_content))
    
    def test_missing_vs_exists(self):
        self.adapter.put('exists.txt', b'content')
        
        self.assertTrue(self.adapter.exists('exists.txt'))
        self.assertFalse(self.adapter.missing('exists.txt'))
        
        self.assertFalse(self.adapter.exists('missing.txt'))
        self.assertTrue(self.adapter.missing('missing.txt'))
    
    def test_delete_nonexistent_file(self):
        result = self.adapter.delete('nonexistent.txt')
        
        self.assertFalse(result)
    
    def test_get_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.adapter.get('nonexistent.txt')


if __name__ == '__main__':
    unittest.main()
