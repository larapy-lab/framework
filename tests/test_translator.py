import pytest
from larapy.translation.translator import Translator, MessageSelector
from larapy.translation.file_loader import FileLoader
import tempfile
import json
from pathlib import Path


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


class TestTranslatorBasics:
    
    def test_get_translation(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.welcome')
        
        assert result == 'Welcome!'
    
    def test_get_nested_translation(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'user': {
                'profile': 'User Profile',
                'settings': 'Settings'
            }
        })
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.user.profile')
        
        assert result == 'User Profile'
    
    def test_returns_key_when_translation_not_found(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        
        result = translator.get('messages.nonexistent')
        
        assert result == 'messages.nonexistent'
    
    def test_replaces_placeholders(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'hello': 'Hello, :name!'})
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.hello', {'name': 'John'})
        
        assert result == 'Hello, John!'
    
    def test_replaces_multiple_placeholders(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'greeting': 'Hello, :name! You are :age years old.'
        })
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.greeting', {'name': 'John', 'age': 25})
        
        assert result == 'Hello, John! You are 25 years old.'
    
    def test_fallback_locale(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        
        translator = Translator(loader, 'es')
        translator.set_fallback('en')
        
        result = translator.get('messages.welcome')
        
        assert result == 'Welcome!'
    
    def test_prefers_current_locale_over_fallback(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        loader.set_translations('es', 'messages', {'welcome': '¡Bienvenido!'})
        
        translator = Translator(loader, 'es')
        translator.set_fallback('en')
        
        result = translator.get('messages.welcome')
        
        assert result == '¡Bienvenido!'
    
    def test_has_checks_translation_existence(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        
        translator = Translator(loader, 'en')
        
        assert translator.has('messages.welcome') is True
        assert translator.has('messages.nonexistent') is False
    
    def test_has_with_fallback(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'welcome': 'Welcome!'})
        
        translator = Translator(loader, 'es')
        translator.set_fallback('en')
        
        assert translator.has('messages.welcome', fallback=True) is True
        assert translator.has('messages.welcome', fallback=False) is False


class TestTranslatorLocale:
    
    def test_get_locale(self):
        loader = MockLoader()
        translator = Translator(loader, 'es')
        
        assert translator.get_locale() == 'es'
    
    def test_set_locale(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        
        translator.set_locale('fr')
        
        assert translator.get_locale() == 'fr'
    
    def test_get_fallback(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        translator.set_fallback('es')
        
        assert translator.get_fallback() == 'es'
    
    def test_set_fallback(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        
        translator.set_fallback('fr')
        
        assert translator.get_fallback() == 'fr'


class TestTranslatorNamespaces:
    
    def test_get_namespaced_translation(self):
        loader = MockLoader()
        loader.set_translations('en', 'package', {'key': 'value'}, 'my-package')
        
        translator = Translator(loader, 'en')
        result = translator.get('my-package::package.key')
        
        assert result == 'value'
    
    def test_add_namespace(self):
        loader = MockLoader()
        translator = Translator(loader, 'en')
        
        translator.add_namespace('custom', '/path/to/custom')
        
        assert '/path/to/custom' in loader.paths


class TestTranslatorPlaceholders:
    
    def test_case_sensitive_placeholders(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'text': ':NAME is :age years old'})
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.text', {'NAME': 'JOHN', 'name': 'john', 'age': 25})
        
        assert 'JOHN' in result
        assert result == 'JOHN is 25 years old'
    
    def test_numeric_placeholder_values(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {'count': 'You have :count items'})
        
        translator = Translator(loader, 'en')
        result = translator.get('messages.count', {'count': 42})
        
        assert result == 'You have 42 items'


class TestMessageSelectorBasics:
    
    def test_simple_singular_plural(self):
        selector = MessageSelector()
        
        result = selector.choose('{1} One item|[2,*] Many items', 1, 'en')
        assert result == 'One item'
        
        result = selector.choose('{1} One item|[2,*] Many items', 5, 'en')
        assert result == 'Many items'
    
    def test_zero_one_many(self):
        selector = MessageSelector()
        
        line = '{0} No items|{1} One item|[2,*] :count items'
        
        assert selector.choose(line, 0, 'en') == 'No items'
        assert selector.choose(line, 1, 'en') == 'One item'
        assert selector.choose(line, 5, 'en') == ':count items'
    
    def test_range_matching(self):
        selector = MessageSelector()
        
        line = '[1,19] Few items|[20,*] Many items'
        
        assert selector.choose(line, 10, 'en') == 'Few items'
        assert selector.choose(line, 25, 'en') == 'Many items'
    
    def test_without_conditions(self):
        selector = MessageSelector()
        
        line = 'One|Two|Three'
        
        assert selector.choose(line, 1, 'en') == 'One'
        assert selector.choose(line, 2, 'en') == 'Two'
        assert selector.choose(line, 10, 'en') == 'Two'


class TestPluralization:
    
    def test_english_pluralization(self):
        selector = MessageSelector()
        
        assert selector._get_plural_index(0, 'en') == 1
        assert selector._get_plural_index(1, 'en') == 0
        assert selector._get_plural_index(2, 'en') == 1
        assert selector._get_plural_index(100, 'en') == 1
    
    def test_french_pluralization(self):
        selector = MessageSelector()
        
        assert selector._get_plural_index(0, 'fr') == 0
        assert selector._get_plural_index(1, 'fr') == 0
        assert selector._get_plural_index(2, 'fr') == 1
        assert selector._get_plural_index(100, 'fr') == 1
    
    def test_russian_pluralization(self):
        selector = MessageSelector()
        
        assert selector._get_plural_index(1, 'ru') == 0
        assert selector._get_plural_index(2, 'ru') == 1
        assert selector._get_plural_index(5, 'ru') == 2
        assert selector._get_plural_index(21, 'ru') == 0
        assert selector._get_plural_index(22, 'ru') == 1
        assert selector._get_plural_index(25, 'ru') == 2
        assert selector._get_plural_index(11, 'ru') == 2
    
    def test_polish_pluralization(self):
        selector = MessageSelector()
        
        assert selector._get_plural_index(1, 'pl') == 0
        assert selector._get_plural_index(2, 'pl') == 1
        assert selector._get_plural_index(5, 'pl') == 2
        assert selector._get_plural_index(22, 'pl') == 1
        assert selector._get_plural_index(25, 'pl') == 2
    
    def test_arabic_pluralization(self):
        selector = MessageSelector()
        
        assert selector._get_plural_index(0, 'ar') == 0
        assert selector._get_plural_index(1, 'ar') == 1
        assert selector._get_plural_index(2, 'ar') == 2
        assert selector._get_plural_index(5, 'ar') == 3
        assert selector._get_plural_index(15, 'ar') == 4
        assert selector._get_plural_index(100, 'ar') == 5


class TestTranslatorChoice:
    
    def test_choice_with_count(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'items': '{0} No items|{1} One item|[2,*] :count items'
        })
        
        translator = Translator(loader, 'en')
        
        assert translator.choice('messages.items', 0) == 'No items'
        assert translator.choice('messages.items', 1) == 'One item'
        assert 'items' in translator.choice('messages.items', 5, {'count': 5})
    
    def test_choice_replaces_count_placeholder(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'items': '{1} One item|[2,*] :count items'
        })
        
        translator = Translator(loader, 'en')
        result = translator.choice('messages.items', 5)
        
        assert result == '5 items'
    
    def test_choice_with_additional_replacements(self):
        loader = MockLoader()
        loader.set_translations('en', 'messages', {
            'items': '{1} :name has one item|[2,*] :name has :count items'
        })
        
        translator = Translator(loader, 'en')
        result = translator.choice('messages.items', 5, {'name': 'John'})
        
        assert result == 'John has 5 items'
