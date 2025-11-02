import pytest
import os
import json
import tempfile
from pathlib import Path
from larapy.translation.file_loader import FileLoader


class TestFileLoaderBasics:
    
    def test_loads_json_file(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        translations = {'welcome': 'Welcome!', 'hello': 'Hello, :name!'}
        messages_file = locale_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f)
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'messages')
        
        assert result == translations
    
    def test_loads_python_file(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        messages_file = locale_dir / 'messages.py'
        with open(messages_file, 'w', encoding='utf-8') as f:
            f.write("translations = {'welcome': 'Welcome!', 'hello': 'Hello!'}")
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'messages')
        
        assert result == {'welcome': 'Welcome!', 'hello': 'Hello!'}
    
    def test_returns_empty_dict_when_file_not_found(self, tmp_path):
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'nonexistent')
        
        assert result == {}
    
    def test_caches_loaded_translations(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        translations = {'welcome': 'Welcome!'}
        messages_file = locale_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f)
        
        loader = FileLoader([str(tmp_path)])
        
        result1 = loader.load('en', 'messages')
        
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump({'changed': 'Changed!'}, f)
        
        result2 = loader.load('en', 'messages')
        
        assert result1 == result2
        assert result2 == {'welcome': 'Welcome!'}
    
    def test_searches_multiple_paths(self, tmp_path):
        path1 = tmp_path / 'path1'
        path2 = tmp_path / 'path2'
        path1.mkdir()
        path2.mkdir()
        
        locale1 = path1 / 'en'
        locale2 = path2 / 'en'
        locale1.mkdir()
        locale2.mkdir()
        
        messages1 = locale1 / 'messages.json'
        with open(messages1, 'w', encoding='utf-8') as f:
            json.dump({'from': 'path1'}, f)
        
        loader = FileLoader([str(path1), str(path2)])
        result = loader.load('en', 'messages')
        
        assert result == {'from': 'path1'}
    
    def test_uses_second_path_when_first_not_found(self, tmp_path):
        path1 = tmp_path / 'path1'
        path2 = tmp_path / 'path2'
        path1.mkdir()
        path2.mkdir()
        
        locale2 = path2 / 'en'
        locale2.mkdir()
        
        messages2 = locale2 / 'messages.json'
        with open(messages2, 'w', encoding='utf-8') as f:
            json.dump({'from': 'path2'}, f)
        
        loader = FileLoader([str(path1), str(path2)])
        result = loader.load('en', 'messages')
        
        assert result == {'from': 'path2'}


class TestFileLoaderNamespaces:
    
    def test_loads_namespaced_translations(self, tmp_path):
        vendor_dir = tmp_path / 'vendor' / 'my-package' / 'en'
        vendor_dir.mkdir(parents=True)
        
        translations = {'package': 'value'}
        package_file = vendor_dir / 'package.json'
        with open(package_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f)
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'package', 'my-package')
        
        assert result == translations
    
    def test_add_namespace(self, tmp_path):
        ns_path = tmp_path / 'custom'
        ns_path.mkdir()
        
        loader = FileLoader([str(tmp_path)])
        loader.add_namespace('custom-ns', str(ns_path))
        
        assert str(ns_path) in loader.paths
    
    def test_namespaces_method_returns_list(self, tmp_path):
        vendor_dir = tmp_path / 'vendor'
        vendor_dir.mkdir()
        
        ns1 = vendor_dir / 'package1'
        ns2 = vendor_dir / 'package2'
        ns1.mkdir()
        ns2.mkdir()
        
        loader = FileLoader([str(tmp_path)])
        namespaces = loader.namespaces()
        
        assert 'package1' in namespaces
        assert 'package2' in namespaces


class TestFileLoaderCaching:
    
    def test_flush_clears_all_cache(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        translations = {'welcome': 'Welcome!'}
        messages_file = locale_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f)
        
        loader = FileLoader([str(tmp_path)])
        loader.load('en', 'messages')
        
        assert len(loader._cache) > 0
        
        loader.flush()
        
        assert len(loader._cache) == 0
    
    def test_flush_with_locale_clears_specific_locale(self, tmp_path):
        en_dir = tmp_path / 'en'
        es_dir = tmp_path / 'es'
        en_dir.mkdir()
        es_dir.mkdir()
        
        en_file = en_dir / 'messages.json'
        es_file = es_dir / 'messages.json'
        
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump({'lang': 'en'}, f)
        with open(es_file, 'w', encoding='utf-8') as f:
            json.dump({'lang': 'es'}, f)
        
        loader = FileLoader([str(tmp_path)])
        loader.load('en', 'messages')
        loader.load('es', 'messages')
        
        assert len(loader._cache) == 2
        
        loader.flush('en')
        
        assert len(loader._cache) == 1
        assert 'es.messages' in loader._cache
    
    def test_cache_key_format(self, tmp_path):
        loader = FileLoader([str(tmp_path)])
        
        key1 = loader._get_cache_key('en', 'messages', None)
        assert key1 == 'en.messages'
        
        key2 = loader._get_cache_key('en', 'messages', 'my-package')
        assert key2 == 'my-package::en.messages'


class TestFileLoaderErrorHandling:
    
    def test_handles_invalid_json(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        messages_file = locale_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            f.write('invalid json {')
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'messages')
        
        assert result == {}
    
    def test_handles_invalid_python_file(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        messages_file = locale_dir / 'messages.py'
        with open(messages_file, 'w', encoding='utf-8') as f:
            f.write('invalid python syntax !!!!')
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'messages')
        
        assert result == {}
    
    def test_handles_python_file_without_translations(self, tmp_path):
        locale_dir = tmp_path / 'en'
        locale_dir.mkdir()
        
        messages_file = locale_dir / 'messages.py'
        with open(messages_file, 'w', encoding='utf-8') as f:
            f.write('some_variable = 123')
        
        loader = FileLoader([str(tmp_path)])
        result = loader.load('en', 'messages')
        
        assert result == {}
    
    def test_add_json_path(self, tmp_path):
        new_path = tmp_path / 'new'
        new_path.mkdir()
        
        loader = FileLoader([str(tmp_path)])
        loader.add_json_path(str(new_path))
        
        assert str(new_path) in loader.paths
