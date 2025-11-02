import pytest
from larapy.translation import helpers
from larapy.translation.translator import Translator
from larapy.translation.file_loader import FileLoader
from larapy.translation.translation_service_provider import TranslationServiceProvider
from larapy.foundation.application import Application
import tempfile
import json
from pathlib import Path


class TestTranslationHelpers:
    
    def setup_method(self):
        helpers._translator = None
    
    def test_trans_without_translator_returns_key(self):
        result = helpers.trans('messages.welcome')
        assert result == 'messages.welcome'
    
    def test_trans_with_translator(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        result = helpers.trans('messages.welcome')
        assert result == 'Welcome!'
    
    def test_double_underscore_alias(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'hello': 'Hello!'})
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        result = helpers.__('messages.hello')
        assert result == 'Hello!'
    
    def test_trans_with_replacements(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'greeting': 'Hello, :name!'})
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        result = helpers.trans('messages.greeting', {'name': 'John'})
        assert result == 'Hello, John!'
    
    def test_trans_choice(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'items': '{0} No items|{1} One item|[2,*] :count items'
        })
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        assert helpers.trans_choice('messages.items', 0) == 'No items'
        assert helpers.trans_choice('messages.items', 1) == 'One item'
        assert '5 items' in helpers.trans_choice('messages.items', 5)
    
    def test_get_locale(self):
        loader = MockLoader()
        translator = Translator(loader, 'es')
        helpers.set_translator(translator)
        
        assert helpers.get_locale() == 'es'
    
    def test_get_locale_without_translator(self):
        result = helpers.get_locale()
        assert result == 'en'
    
    def test_set_locale(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        helpers.set_locale('fr')
        
        assert translator.get_locale() == 'fr'
    
    def test_has_trans(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        assert helpers.has_trans('messages.welcome') is True
        assert helpers.has_trans('messages.nonexistent') is False
    
    def test_has_trans_without_translator(self):
        result = helpers.has_trans('messages.welcome')
        assert result is False
    
    def test_get_fallback(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        translator.set_fallback('es')
        helpers.set_translator(translator)
        
        assert helpers.get_fallback() == 'es'
    
    def test_set_fallback(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        helpers.set_translator(translator)
        
        helpers.set_fallback('fr')
        
        assert translator.get_fallback() == 'fr'


class TestTranslationServiceProvider:
    
    def test_registers_loader(self, tmp_path):
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        
        loader = app.make('translation.loader')
        assert isinstance(loader, FileLoader)
    
    def test_registers_translator(self, tmp_path):
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        
        translator = app.make('translator')
        assert isinstance(translator, Translator)
    
    def test_sets_default_locale(self, tmp_path):
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        
        translator = app.make('translator')
        assert translator.get_locale() == 'en'
    
    def test_sets_helper_translator(self, tmp_path):
        helpers._translator = None
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        app.make('translator')
        
        assert helpers._translator is not None
    
    def test_loader_searches_lang_directory(self, tmp_path):
        lang_dir = tmp_path / 'lang'
        lang_dir.mkdir()
        
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        
        loader = app.make('translation.loader')
        assert str(lang_dir) in loader.paths
    
    def test_loader_searches_resources_lang_directory(self, tmp_path):
        resources_lang_dir = tmp_path / 'resources' / 'lang'
        resources_lang_dir.mkdir(parents=True)
        
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        
        provider.register()
        
        loader = app.make('translation.loader')
        assert str(resources_lang_dir) in loader.paths


class TestIntegrationWithRealFiles:
    
    def test_loads_translations_from_files(self, tmp_path):
        lang_dir = tmp_path / 'lang'
        en_dir = lang_dir / 'en'
        en_dir.mkdir(parents=True)
        
        messages_file = en_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump({'welcome': 'Welcome to our app!'}, f)
        
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        provider.register()
        
        translator = app.make('translator')
        result = translator.get('messages.welcome')
        
        assert result == 'Welcome to our app!'
    
    def test_uses_multiple_locales(self, tmp_path):
        lang_dir = tmp_path / 'lang'
        
        en_dir = lang_dir / 'en'
        es_dir = lang_dir / 'es'
        en_dir.mkdir(parents=True)
        es_dir.mkdir(parents=True)
        
        en_file = en_dir / 'messages.json'
        es_file = es_dir / 'messages.json'
        
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump({'greeting': 'Hello!'}, f)
        with open(es_file, 'w', encoding='utf-8') as f:
            json.dump({'greeting': '¡Hola!'}, f)
        
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        provider.register()
        
        translator = app.make('translator')
        
        translator.set_locale('en')
        assert translator.get('messages.greeting') == 'Hello!'
        
        translator.set_locale('es')
        assert translator.get('messages.greeting') == '¡Hola!'
    
    def test_falls_back_to_default_locale(self, tmp_path):
        lang_dir = tmp_path / 'lang'
        en_dir = lang_dir / 'en'
        en_dir.mkdir(parents=True)
        
        messages_file = en_dir / 'messages.json'
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump({'welcome': 'Welcome!'}, f)
        
        app = Application(str(tmp_path))
        provider = TranslationServiceProvider(app)
        provider.register()
        
        translator = app.make('translator')
        translator.set_locale('fr')
        translator.set_fallback('en')
        
        result = translator.get('messages.welcome')
        
        assert result == 'Welcome!'


class MockLoader:
    
    def __init__(self):
        self._translations = {}
        self._cache = {}
        self.paths = []
    
    def load(self, locale, group, namespace=None):
        key = f"{namespace}::{locale}.{group}" if namespace else f"{locale}.{group}"
        return self._translations.get(key, {})
    
    def set_translations(self, locale, group, translations, namespace=None):
        key = f"{namespace}::{locale}.{group}" if namespace else f"{locale}.{group}"
        self._translations[key] = translations
    
    def _get_cache_key(self, locale, group, namespace=None):
        if namespace:
            return f'{namespace}::{locale}.{group}'
        return f'{locale}.{group}'
    
    def add_namespace(self, namespace, hint):
        self.paths.append(hint)
