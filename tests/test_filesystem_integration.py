import unittest
import tempfile
import shutil
from pathlib import Path
from larapy.filesystem.storage_manager import StorageManager
from larapy.filesystem.storage import Storage
from larapy.filesystem.fake import FakeStorage


class MockApp:
    def __init__(self, config):
        self.config = config


class TestStorageManager(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        self.app = MockApp({
            'filesystems': {
                'default': 'local',
                'disks': {
                    'local': {
                        'driver': 'local',
                        'root': self.test_dir,
                        'url': '/storage',
                        'visibility': 'public'
                    },
                    'test': {
                        'driver': 'local',
                        'root': self.test_dir + '/test',
                        'url': '/test',
                    }
                }
            }
        })
        
        self.manager = StorageManager(self.app)
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_disk_returns_default(self):
        disk = self.manager.disk()
        
        self.assertIsNotNone(disk)
    
    def test_disk_returns_named_disk(self):
        disk = self.manager.disk('test')
        
        self.assertIsNotNone(disk)
    
    def test_disk_caches_instances(self):
        disk1 = self.manager.disk('local')
        disk2 = self.manager.disk('local')
        
        self.assertIs(disk1, disk2)
    
    def test_get_default_driver(self):
        default = self.manager.get_default_driver()
        
        self.assertEqual(default, 'local')
    
    def test_purge_single_disk(self):
        self.manager.disk('local')
        self.manager.purge('local')
        
        self.assertNotIn('local', self.manager.disks)
    
    def test_purge_all_disks(self):
        self.manager.disk('local')
        self.manager.disk('test')
        self.manager.purge()
        
        self.assertEqual(len(self.manager.disks), 0)
    
    def test_extend_custom_driver(self):
        def create_fake_driver(config):
            return FakeStorage()
        
        self.manager.extend('fake', create_fake_driver)
        
        self.app.config['filesystems']['disks']['custom'] = {'driver': 'fake'}
        
        disk = self.manager.disk('custom')
        self.assertIsInstance(disk, FakeStorage)


class TestStorageFacade(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        app = MockApp({
            'filesystems': {
                'default': 'local',
                'disks': {
                    'local': {
                        'driver': 'local',
                        'root': self.test_dir,
                        'url': '/storage',
                    }
                }
            }
        })
        
        manager = StorageManager(app)
        Storage.set_manager(manager)
    
    def tearDown(self):
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_facade_put_and_get(self):
        Storage.put('test.txt', b'content')
        
        result = Storage.get('test.txt')
        self.assertEqual(result, b'content')
    
    def test_facade_exists(self):
        Storage.put('test.txt', b'content')
        
        self.assertTrue(Storage.exists('test.txt'))
        self.assertFalse(Storage.exists('nonexistent.txt'))
    
    def test_facade_delete(self):
        Storage.put('test.txt', b'content')
        
        result = Storage.delete('test.txt')
        self.assertTrue(result)
        self.assertFalse(Storage.exists('test.txt'))
    
    def test_facade_copy(self):
        Storage.put('original.txt', b'content')
        
        Storage.copy('original.txt', 'copy.txt')
        
        self.assertTrue(Storage.exists('original.txt'))
        self.assertTrue(Storage.exists('copy.txt'))
    
    def test_facade_move(self):
        Storage.put('source.txt', b'content')
        
        Storage.move('source.txt', 'dest.txt')
        
        self.assertFalse(Storage.exists('source.txt'))
        self.assertTrue(Storage.exists('dest.txt'))
    
    def test_facade_size(self):
        content = b'12345'
        Storage.put('test.txt', content)
        
        size = Storage.size('test.txt')
        self.assertEqual(size, len(content))
    
    def test_facade_files(self):
        Storage.put('file1.txt', b'a')
        Storage.put('file2.txt', b'b')
        
        files = Storage.files()
        
        self.assertIn('file1.txt', files)
        self.assertIn('file2.txt', files)
    
    def test_facade_make_directory(self):
        result = Storage.make_directory('new_dir')
        
        self.assertTrue(result)
    
    def test_facade_append(self):
        Storage.put('test.txt', b'First ')
        Storage.append('test.txt', b'Second')
        
        result = Storage.get('test.txt')
        self.assertEqual(result, b'First Second')


if __name__ == '__main__':
    unittest.main()
