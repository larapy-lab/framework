import pytest

from larapy.hashing import Hasher
from larapy.hashing.exceptions import HashingException


class TestHasher:
    def test_bcrypt_make_and_check(self):
        hasher = Hasher(driver='bcrypt', rounds=10)
        
        password = 'secret_password_123'
        hashed = hasher.make(password)
        
        assert hashed.startswith('$2b$')
        assert hasher.check(password, hashed)

    def test_bcrypt_check_fails_with_wrong_password(self):
        hasher = Hasher(driver='bcrypt', rounds=10)
        
        hashed = hasher.make('correct_password')
        
        assert not hasher.check('wrong_password', hashed)

    def test_bcrypt_check_handles_empty_values(self):
        hasher = Hasher(driver='bcrypt')
        
        assert not hasher.check('', '')
        assert not hasher.check('password', '')
        assert not hasher.check('', 'hash')

    def test_bcrypt_different_hashes_for_same_password(self):
        hasher = Hasher(driver='bcrypt', rounds=10)
        
        password = 'same_password'
        hash1 = hasher.make(password)
        hash2 = hasher.make(password)
        
        assert hash1 != hash2
        assert hasher.check(password, hash1)
        assert hasher.check(password, hash2)

    def test_bcrypt_needs_rehash_with_different_rounds(self):
        hasher_10 = Hasher(driver='bcrypt', rounds=10)
        hasher_12 = Hasher(driver='bcrypt', rounds=12)
        
        hashed = hasher_10.make('password')
        
        assert hasher_12.needs_rehash(hashed)
        assert not hasher_10.needs_rehash(hashed)

    def test_bcrypt_needs_rehash_with_same_rounds(self):
        hasher = Hasher(driver='bcrypt', rounds=12)
        
        hashed = hasher.make('password')
        
        assert not hasher.needs_rehash(hashed)

    def test_bcrypt_info(self):
        hasher = Hasher(driver='bcrypt', rounds=12)
        
        hashed = hasher.make('password')
        info = hasher.info(hashed)
        
        assert info['algo'] == 'bcrypt'
        assert info['algoName'] == 'bcrypt'
        assert info['options']['cost'] == 12

    def test_argon2_make_and_check(self):
        try:
            hasher = Hasher(
                driver='argon2id',
                memory=65536,
                time=3,
                threads=1
            )
            
            password = 'secure_password'
            hashed = hasher.make(password)
            
            assert hashed.startswith('$argon2')
            assert hasher.check(password, hashed)
        except HashingException as e:
            if 'argon2-cffi package is required' in str(e):
                pytest.skip('argon2-cffi not installed')
            raise

    def test_argon2_check_fails_with_wrong_password(self):
        try:
            hasher = Hasher(driver='argon2id')
            
            hashed = hasher.make('correct_password')
            
            assert not hasher.check('wrong_password', hashed)
        except HashingException as e:
            if 'argon2-cffi package is required' in str(e):
                pytest.skip('argon2-cffi not installed')
            raise

    def test_argon2i_type(self):
        try:
            hasher = Hasher(driver='argon2i')
            
            hashed = hasher.make('password')
            
            assert hasher.check('password', hashed)
        except HashingException as e:
            if 'argon2-cffi package is required' in str(e):
                pytest.skip('argon2-cffi not installed')
            raise

    def test_argon2id_type(self):
        try:
            hasher = Hasher(driver='argon2id')
            
            hashed = hasher.make('password')
            
            assert hasher.check('password', hashed)
        except HashingException as e:
            if 'argon2-cffi package is required' in str(e):
                pytest.skip('argon2-cffi not installed')
            raise

    def test_unsupported_driver_raises_exception(self):
        with pytest.raises(HashingException):
            Hasher(driver='invalid_driver')

    def test_check_handles_invalid_hash_format(self):
        hasher = Hasher(driver='bcrypt')
        
        assert not hasher.check('password', 'invalid_hash')

    def test_needs_rehash_with_invalid_hash(self):
        hasher = Hasher(driver='bcrypt')
        
        assert hasher.needs_rehash('invalid_hash')

    def test_info_with_invalid_hash(self):
        hasher = Hasher(driver='bcrypt')
        
        info = hasher.info('invalid_hash')
        
        assert info['algo'] is None
        assert info['algoName'] == 'unknown'

    def test_bcrypt_with_custom_rounds(self):
        hasher = Hasher(driver='bcrypt', rounds=8)
        
        password = 'test_password'
        hashed = hasher.make(password)
        
        info = hasher.info(hashed)
        assert info['options']['cost'] == 8

    def test_check_exception_returns_false(self):
        hasher = Hasher(driver='bcrypt')
        
        result = hasher.check('password', None)
        
        assert result is False

    def test_argon2_info(self):
        try:
            hasher = Hasher(driver='argon2id', memory=65536, time=4, threads=1)
            
            hashed = hasher.make('password')
            info = hasher.info(hashed)
            
            assert info['algo'] == 'argon2'
            assert 'argon2' in info['algoName']
        except HashingException as e:
            if 'argon2-cffi package is required' in str(e):
                pytest.skip('argon2-cffi not installed')
            raise
