import pytest

from larapy.foundation.application import Application
from larapy.encryption.encryption_service_provider import EncryptionServiceProvider
from larapy.hashing.hash_service_provider import HashServiceProvider
from larapy.support.facades.crypt import Crypt
from larapy.support.facades.hash import Hash
from larapy.encryption import Encrypter


class TestCryptFacade:
    @pytest.fixture
    def app(self):
        app = Application()
        app._config = {
            'encryption': {
                'key': f'base64:{Encrypter.generate_key()}',
                'cipher': 'aes-256-cbc'
            }
        }
        
        provider = EncryptionServiceProvider(app)
        provider.register()
        
        Crypt.set_facade_application(app)
        
        return app

    def test_encrypt_and_decrypt(self, app):
        data = {'message': 'secret data'}
        
        encrypted = Crypt.encrypt(data)
        decrypted = Crypt.decrypt(encrypted)
        
        assert decrypted == data

    def test_encrypt_string(self, app):
        original = 'Hello World'
        
        encrypted = Crypt.encrypt_string(original)
        decrypted = Crypt.decrypt_string(encrypted)
        
        assert decrypted == original

    def test_generate_key(self, app):
        key = Crypt.generate_key()
        
        assert len(key) > 0

    def test_encrypt_without_serialization(self, app):
        data = 'plain text'
        
        encrypted = Crypt.encrypt(data, serialize=False)
        decrypted = Crypt.decrypt(encrypted, unserialize=False)
        
        assert decrypted == data


class TestHashFacade:
    @pytest.fixture
    def app(self):
        app = Application()
        app._config = {
            'hashing': {
                'driver': 'bcrypt',
                'bcrypt': {
                    'rounds': 10
                }
            }
        }
        
        provider = HashServiceProvider(app)
        provider.register()
        
        Hash.set_facade_application(app)
        
        return app

    def test_make_and_check(self, app):
        password = 'secret_password'
        
        hashed = Hash.make(password)
        
        assert Hash.check(password, hashed)
        assert not Hash.check('wrong_password', hashed)

    def test_needs_rehash(self, app):
        password = 'test_password'
        hashed = Hash.make(password)
        
        needs_rehash = Hash.needs_rehash(hashed)
        
        assert isinstance(needs_rehash, bool)

    def test_info(self, app):
        password = 'test_password'
        hashed = Hash.make(password)
        
        info = Hash.info(hashed)
        
        assert 'algo' in info
        assert 'algoName' in info
        assert 'options' in info


class TestEncryptionServiceProvider:
    def test_registers_encrypter(self):
        app = Application()
        app._config = {
            'encryption': {
                'key': f'base64:{Encrypter.generate_key()}',
                'cipher': 'aes-256-cbc'
            }
        }
        
        provider = EncryptionServiceProvider(app)
        provider.register()
        
        encrypter = app.make('encrypter')
        
        assert isinstance(encrypter, Encrypter)

    def test_encrypter_works(self):
        app = Application()
        app._config = {
            'encryption': {
                'key': f'base64:{Encrypter.generate_key()}',
                'cipher': 'aes-256-cbc'
            }
        }
        
        provider = EncryptionServiceProvider(app)
        provider.register()
        
        encrypter = app.make('encrypter')
        
        encrypted = encrypter.encrypt('test')
        decrypted = encrypter.decrypt(encrypted)
        
        assert decrypted == 'test'


class TestHashServiceProvider:
    def test_registers_hasher(self):
        app = Application()
        app._config = {
            'hashing': {
                'driver': 'bcrypt',
                'bcrypt': {'rounds': 10}
            }
        }
        
        provider = HashServiceProvider(app)
        provider.register()
        
        hasher = app.make('hasher')
        
        from larapy.hashing import Hasher
        assert isinstance(hasher, Hasher)

    def test_hasher_works(self):
        app = Application()
        app._config = {
            'hashing': {
                'driver': 'bcrypt',
                'bcrypt': {'rounds': 10}
            }
        }
        
        provider = HashServiceProvider(app)
        provider.register()
        
        hasher = app.make('hasher')
        
        hashed = hasher.make('password')
        
        assert hasher.check('password', hashed)
