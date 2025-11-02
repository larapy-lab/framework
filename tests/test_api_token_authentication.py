import pytest
import hashlib
import secrets
from datetime import datetime, timedelta
from larapy.auth.personal_access_token import PersonalAccessToken
from larapy.auth.has_api_tokens import HasApiTokens
from larapy.database.orm.model import Model
from larapy.database.connection import Connection


class UserWithTokens(Model, HasApiTokens):
    _table = 'users'
    _fillable = ['id', 'name', 'email', 'password']


class TestPersonalAccessToken:
    
    @pytest.fixture
    def connection(self):
        config = {
            'driver': 'sqlite',
            'database': ':memory:',
            'foreign_keys': True
        }
        conn = Connection(config)
        conn.connect()
        
        conn.statement('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        conn.statement('''
            CREATE TABLE personal_access_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tokenable_type VARCHAR(255),
                tokenable_id INTEGER,
                name VARCHAR(255),
                token VARCHAR(64) UNIQUE,
                abilities TEXT,
                last_used_at DATETIME NULL,
                expires_at DATETIME NULL,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        return conn
    
    def test_token_abilities_wildcard(self, connection):
        token = PersonalAccessToken({
            'abilities': ['*'],
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert token.can('read')
        assert token.can('write')
        assert token.can('delete')
        assert token.can('any_ability')
    
    def test_token_abilities_specific(self, connection):
        token = PersonalAccessToken({
            'abilities': ['read', 'write'],
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert token.can('read')
        assert token.can('write')
        assert not token.can('delete')
        assert token.cant('delete')
    
    def test_token_abilities_json_string(self, connection):
        import json
        token = PersonalAccessToken({
            'abilities': json.dumps(['read', 'write']),
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert token.can('read')
        assert token.can('write')
        assert not token.can('delete')
    
    def test_token_abilities_none(self, connection):
        token = PersonalAccessToken({
            'abilities': None,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert not token.can('read')
        assert token.cant('read')
    
    def test_token_abilities_empty_list(self, connection):
        token = PersonalAccessToken({
            'abilities': [],
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert not token.can('read')
        assert token.cant('write')
    
    def test_token_not_expired_no_expiry(self, connection):
        token = PersonalAccessToken({
            'expires_at': None,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert not token.is_expired()
    
    def test_token_expired(self, connection):
        past_time = datetime.now() - timedelta(hours=1)
        token = PersonalAccessToken({
            'expires_at': past_time,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert token.is_expired()
    
    def test_token_not_expired_yet(self, connection):
        future_time = datetime.now() + timedelta(hours=1)
        token = PersonalAccessToken({
            'expires_at': future_time,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert not token.is_expired()
    
    def test_token_expiry_string_format(self, connection):
        past_time_str = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        token = PersonalAccessToken({
            'expires_at': past_time_str,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        assert token.is_expired()
    
    def test_find_token_by_hash(self, connection):
        plain_token = secrets.token_urlsafe(40)
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        
        token_data = {
            'name': 'Test Token',
            'token': hashed_token,
            'abilities': ['*'],
            'tokenable_type': 'User',
            'tokenable_id': 1
        }
        
        token = PersonalAccessToken(token_data, connection)
        token.save()
        
        # Token format is {id}|{secret}, so we need to prepend the token ID
        token_id = token.get_key()
        full_token = f"{token_id}|{plain_token}"
        
        found = PersonalAccessToken.find_token(full_token, connection)
        
        assert found is not None
        assert found.get_attribute('name') == 'Test Token'
        assert found.can('read')
    
    def test_find_token_not_found(self, connection):
        # Invalid token with proper format {id}|{secret}
        invalid_token = "999|" + secrets.token_urlsafe(40)
        found = PersonalAccessToken.find_token(invalid_token, connection)
        
        assert found is None
    
    def test_find_token_wrong_hash(self, connection):
        plain_token = secrets.token_urlsafe(40)
        wrong_token = secrets.token_urlsafe(40)
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        
        token_data = {
            'name': 'Test Token',
            'token': hashed_token,
            'abilities': ['*'],
            'tokenable_type': 'User',
            'tokenable_id': 1
        }
        
        token = PersonalAccessToken(token_data, connection)
        token.save()
        
        # Use wrong token with correct format {id}|{secret}
        token_id = token.get_key()
        full_wrong_token = f"{token_id}|{wrong_token}"
        
        found = PersonalAccessToken.find_token(full_wrong_token, connection)
        
        assert found is None
    
    def test_token_model_fillable(self, connection):
        token = PersonalAccessToken({
            'name': 'API Token',
            'token': 'hashed_value',
            'abilities': ['read'],
            'tokenable_type': 'User',
            'tokenable_id': 1,
            'last_used_at': datetime.now()
        }, connection)
        
        assert token.get_attribute('name') == 'API Token'
        assert token.get_attribute('token') == 'hashed_value'
        assert token.get_attribute('tokenable_type') == 'User'
        assert token.get_attribute('tokenable_id') == 1
    
    def test_token_casts_datetime(self, connection):
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        token = PersonalAccessToken({
            'last_used_at': now_str,
            'tokenable_type': 'User',
            'tokenable_id': 1
        }, connection)
        
        last_used = token.get_attribute('last_used_at')
        assert isinstance(last_used, datetime)


class TestHasApiTokens:
    
    @pytest.fixture
    def connection(self):
        config = {
            'driver': 'sqlite',
            'database': ':memory:',
            'foreign_keys': True
        }
        conn = Connection(config)
        conn.connect()
        
        conn.statement('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        conn.statement('''
            CREATE TABLE personal_access_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tokenable_type VARCHAR(255),
                tokenable_id INTEGER,
                name VARCHAR(255),
                token VARCHAR(64) UNIQUE,
                abilities TEXT,
                last_used_at DATETIME NULL,
                expires_at DATETIME NULL,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        return conn
    
    def test_create_token_default_abilities(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'John Doe', 'email': 'john@example.com'}, connection)
        
        new_token = user.create_token('Test Token')
        
        assert new_token is not None
        assert str(new_token).startswith(str(new_token.access_token.get_key()))
        assert '|' in str(new_token)
        assert new_token.access_token.can('read')
        assert new_token.access_token.can('anything')
    
    def test_create_token_specific_abilities(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Jane Doe', 'email': 'jane@example.com'}, connection)
        
        new_token = user.create_token('Limited Token', abilities=['read', 'list'])
        
        assert new_token.access_token.can('read')
        assert new_token.access_token.can('list')
        assert not new_token.access_token.can('write')
        assert not new_token.access_token.can('delete')
    
    def test_create_token_with_expiration(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Bob Smith',
            'email': 'bob@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Bob Smith', 'email': 'bob@example.com'}, connection)
        
        expires = datetime.now() + timedelta(days=7)
        new_token = user.create_token('Expiring Token', abilities=['*'], expires_at=expires)
        
        assert new_token.access_token.get_attribute('expires_at') is not None
        assert not new_token.access_token.is_expired()
    
    def test_token_hash_stored_not_plain(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Alice',
            'email': 'alice@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Alice', 'email': 'alice@example.com'}, connection)
        
        new_token = user.create_token('Secure Token')
        plain_token_str = str(new_token)
        
        token_part = plain_token_str.split('|')[1]
        stored_hash = new_token.access_token.get_attribute('token')
        
        assert stored_hash != plain_token_str
        assert stored_hash != token_part
        
        expected_hash = hashlib.sha256(token_part.encode()).hexdigest()
        assert stored_hash == expected_hash
    
    def test_current_access_token(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Charlie',
            'email': 'charlie@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Charlie', 'email': 'charlie@example.com'}, connection)
        
        assert user.current_access_token() is None
        
        new_token = user.create_token('Token 1')
        user.with_access_token(new_token.access_token)
        
        assert user.current_access_token() is not None
        assert user.current_access_token() == new_token.access_token
    
    def test_token_can(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'David',
            'email': 'david@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'David', 'email': 'david@example.com'}, connection)
        
        new_token = user.create_token('Read Token', abilities=['read'])
        user.with_access_token(new_token.access_token)
        
        assert user.token_can('read')
        assert not user.token_can('write')
        assert user.token_cant('write')
    
    def test_token_can_no_token(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Eve',
            'email': 'eve@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Eve', 'email': 'eve@example.com'}, connection)
        
        assert not user.token_can('read')
        assert user.token_cant('read')
    
    def test_tokens_relation_get(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Frank',
            'email': 'frank@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Frank', 'email': 'frank@example.com'}, connection)
        
        user.create_token('Token 1')
        user.create_token('Token 2')
        user.create_token('Token 3')
        
        tokens = user.tokens().get()
        
        assert len(tokens) == 3
    
    def test_tokens_relation_first(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Grace',
            'email': 'grace@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Grace', 'email': 'grace@example.com'}, connection)
        
        user.create_token('First Token')
        user.create_token('Second Token')
        
        first_token = user.tokens().first()
        
        assert first_token is not None
        assert first_token.get_attribute('name') == 'First Token'
    
    def test_tokens_relation_where(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Henry',
            'email': 'henry@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Henry', 'email': 'henry@example.com'}, connection)
        
        user.create_token('Mobile App')
        user.create_token('Web App')
        user.create_token('CLI Tool')
        
        mobile_tokens = user.tokens().where('name', 'Mobile App').get()
        
        assert len(mobile_tokens) == 1
        assert mobile_tokens[0].get_attribute('name') == 'Mobile App'
    
    def test_new_access_token_to_dict(self, connection):
        UserWithTokens._connection = connection
        
        user_id = connection.table('users').insert_get_id({
            'name': 'Ivy',
            'email': 'ivy@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithTokens({'id': user_id, 'name': 'Ivy', 'email': 'ivy@example.com'}, connection)
        
        new_token = user.create_token('API Token')
        token_dict = new_token.to_dict()
        
        assert 'access_token' in token_dict
        assert 'token_type' in token_dict
        assert 'token' in token_dict
        assert token_dict['token_type'] == 'Bearer'
        assert token_dict['access_token'] == str(new_token)
