import pytest
import base64
import json

from larapy.encryption import Encrypter
from larapy.encryption.exceptions import (
    DecryptionException,
    InvalidKeyException,
    InvalidPayloadException,
)


class TestEncrypter:
    def test_constructor_validates_key_length(self):
        with pytest.raises(InvalidKeyException):
            Encrypter('short_key')

    def test_constructor_validates_cipher(self):
        key = base64.b64encode(b'0' * 32).decode('utf-8')
        with pytest.raises(InvalidKeyException):
            Encrypter(f'base64:{key}', cipher='invalid')

    def test_constructor_accepts_base64_key(self):
        key = base64.b64encode(b'0' * 32).decode('utf-8')
        encrypter = Encrypter(f'base64:{key}')
        assert encrypter.get_key() == b'0' * 32

    def test_constructor_accepts_raw_key(self):
        key = '0' * 32
        encrypter = Encrypter(key)
        assert encrypter.get_key() == key.encode('utf-8')

    def test_encrypt_and_decrypt_with_serialization(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        data = {'name': 'John', 'age': 30, 'active': True}
        encrypted = encrypter.encrypt(data)
        decrypted = encrypter.decrypt(encrypted)
        
        assert decrypted == data

    def test_encrypt_and_decrypt_without_serialization(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        data = 'Hello World'
        encrypted = encrypter.encrypt(data, serialize=False)
        decrypted = encrypter.decrypt(encrypted, unserialize=False)
        
        assert decrypted == data

    def test_encrypt_string(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        original = 'Secret Message'
        encrypted = encrypter.encrypt_string(original)
        decrypted = encrypter.decrypt_string(encrypted)
        
        assert decrypted == original

    def test_encrypted_payloads_are_different(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        data = 'Same Data'
        encrypted1 = encrypter.encrypt(data, serialize=False)
        encrypted2 = encrypter.encrypt(data, serialize=False)
        
        assert encrypted1 != encrypted2

    def test_decrypt_validates_mac(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        encrypted = encrypter.encrypt('data', serialize=False)
        
        decoded = json.loads(base64.b64decode(encrypted).decode('utf-8'))
        decoded['mac'] = 'invalid_mac'
        tampered = base64.b64encode(
            json.dumps(decoded).encode('utf-8')
        ).decode('utf-8')
        
        with pytest.raises(DecryptionException):
            encrypter.decrypt(tampered, unserialize=False)

    def test_decrypt_validates_payload_structure(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        invalid_payload = base64.b64encode(b'invalid').decode('utf-8')
        
        with pytest.raises(InvalidPayloadException):
            encrypter.decrypt(invalid_payload)

    def test_decrypt_requires_iv(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        payload = {'value': 'test'}
        invalid = base64.b64encode(
            json.dumps(payload).encode('utf-8')
        ).decode('utf-8')
        
        with pytest.raises(InvalidPayloadException):
            encrypter.decrypt(invalid)

    def test_aes_256_gcm_encryption(self):
        key = Encrypter.generate_key('aes-256-gcm')
        encrypter = Encrypter(f'base64:{key}', cipher='aes-256-gcm')
        
        data = {'secure': 'data'}
        encrypted = encrypter.encrypt(data)
        decrypted = encrypter.decrypt(encrypted)
        
        assert decrypted == data

    def test_gcm_no_mac_in_payload(self):
        key = Encrypter.generate_key('aes-256-gcm')
        encrypter = Encrypter(f'base64:{key}', cipher='aes-256-gcm')
        
        encrypted = encrypter.encrypt('test', serialize=False)
        decoded = json.loads(base64.b64decode(encrypted).decode('utf-8'))
        
        assert decoded['mac'] == ''

    def test_generate_key_produces_valid_key(self):
        key = Encrypter.generate_key()
        decoded = base64.b64decode(key)
        
        assert len(decoded) == 32

    def test_generate_key_supports_different_ciphers(self):
        key_cbc = Encrypter.generate_key('aes-256-cbc')
        key_gcm = Encrypter.generate_key('aes-256-gcm')
        
        assert len(base64.b64decode(key_cbc)) == 32
        assert len(base64.b64decode(key_gcm)) == 32

    def test_generate_key_invalid_cipher(self):
        with pytest.raises(InvalidKeyException):
            Encrypter.generate_key('invalid')

    def test_encrypt_list(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        data = [1, 2, 3, 'four', True]
        encrypted = encrypter.encrypt(data)
        decrypted = encrypter.decrypt(encrypted)
        
        assert decrypted == data

    def test_encrypt_nested_dict(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        data = {
            'user': {
                'name': 'John',
                'address': {
                    'city': 'NYC',
                    'zip': 10001
                }
            }
        }
        encrypted = encrypter.encrypt(data)
        decrypted = encrypter.decrypt(encrypted)
        
        assert decrypted == data

    def test_encrypt_empty_string(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        encrypted = encrypter.encrypt_string('')
        decrypted = encrypter.decrypt_string(encrypted)
        
        assert decrypted == ''

    def test_different_keys_cannot_decrypt(self):
        key1 = Encrypter.generate_key()
        key2 = Encrypter.generate_key()
        
        encrypter1 = Encrypter(f'base64:{key1}')
        encrypter2 = Encrypter(f'base64:{key2}')
        
        encrypted = encrypter1.encrypt('data', serialize=False)
        
        with pytest.raises(DecryptionException):
            encrypter2.decrypt(encrypted, unserialize=False)

    def test_decrypt_invalid_base64(self):
        key = Encrypter.generate_key()
        encrypter = Encrypter(f'base64:{key}')
        
        with pytest.raises(InvalidPayloadException):
            encrypter.decrypt('not_valid_base64!@#')
