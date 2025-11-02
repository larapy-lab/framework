import pytest
import secrets
import hashlib
from datetime import datetime, timedelta
from larapy.database.connection import Connection
from larapy.auth.personal_access_token import PersonalAccessToken
from larapy.auth.has_api_tokens import HasApiTokens
from larapy.auth.token_guard import TokenGuard
from larapy.database.orm.model import Model


class UserWithApiTokens(Model, HasApiTokens):
    _table = 'users'
    _fillable = ['id', 'name', 'email', 'password']


@pytest.fixture
def connection():
    config = {
        'driver': 'sqlite',
        'database': ':memory:'
    }
    
    conn = Connection(config)
    conn.connect()
    
    conn.statement('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.statement('''
        CREATE TABLE personal_access_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tokenable_type TEXT NOT NULL,
            tokenable_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            abilities TEXT,
            last_used_at TEXT,
            expires_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.statement('''
        CREATE INDEX idx_tokenable ON personal_access_tokens(tokenable_type, tokenable_id)
    ''')
    
    yield conn
    
    conn.disconnect()


class TestApiTokenIntegration:
    
    def test_complete_token_lifecycle(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Lifecycle User',
            'email': 'lifecycle@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Lifecycle User', 'email': 'lifecycle@example.com'}, connection)
        
        new_token = user.create_token('Mobile App', abilities=['posts:read', 'posts:create'])
        plain_token = str(new_token)
        
        assert plain_token is not None
        assert '|' in plain_token
        
        token_parts = plain_token.split('|')
        assert len(token_parts) == 2
        assert token_parts[0].isdigit()
        assert len(token_parts[1]) > 0
        
        db_token = PersonalAccessToken.find_token(plain_token, connection)
        assert db_token is not None
        assert db_token.get_attribute('name') == 'Mobile App'
        assert db_token.can('posts:read')
        assert db_token.can('posts:create')
        assert not db_token.can('posts:delete')
        
        initial_last_used = db_token.get_attribute('last_used_at')
        
        db_token.set_attribute('last_used_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db_token.save()
        
        updated_token = PersonalAccessToken.find_token(plain_token, connection)
        assert updated_token.get_attribute('last_used_at') != initial_last_used
        
        token_id = db_token.get_attribute('id')
        deleted = connection.table('personal_access_tokens').where('id', token_id).delete()
        assert deleted > 0
        
        revoked_token = PersonalAccessToken.find_token(plain_token, connection)
        assert revoked_token is None
    
    def test_multiple_tokens_per_user(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Multi Token User',
            'email': 'multi@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Multi Token User', 'email': 'multi@example.com'}, connection)
        
        mobile_token = user.create_token('Mobile App', abilities=['posts:read', 'posts:create'])
        web_token = user.create_token('Web Dashboard', abilities=['*'])
        cli_token = user.create_token('CLI Tool', abilities=['posts:read'])
        
        mobile_plain = str(mobile_token)
        web_plain = str(web_token)
        cli_plain = str(cli_token)
        
        mobile_db = PersonalAccessToken.find_token(mobile_plain, connection)
        web_db = PersonalAccessToken.find_token(web_plain, connection)
        cli_db = PersonalAccessToken.find_token(cli_plain, connection)
        
        assert mobile_db is not None
        assert web_db is not None
        assert cli_db is not None
        
        assert mobile_db.can('posts:read')
        assert mobile_db.can('posts:create')
        assert not mobile_db.can('posts:delete')
        
        assert web_db.can('posts:read')
        assert web_db.can('posts:create')
        assert web_db.can('posts:delete')
        assert web_db.can('any:ability')
        
        assert cli_db.can('posts:read')
        assert not cli_db.can('posts:create')
        assert not cli_db.can('posts:delete')
        
        tokens = connection.table('personal_access_tokens').where('tokenable_id', user_id).get()
        assert len(list(tokens)) == 3
    
    def test_token_abilities_enforcement(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Restricted User',
            'email': 'restricted@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Restricted User', 'email': 'restricted@example.com'}, connection)
        
        read_only_token = user.create_token('Read Only', abilities=['posts:read', 'comments:read'])
        read_plain = str(read_only_token)
        
        token = PersonalAccessToken.find_token(read_plain, connection)
        
        assert token.can('posts:read')
        assert token.can('comments:read')
        assert not token.can('posts:create')
        assert not token.can('posts:update')
        assert not token.can('posts:delete')
        assert not token.can('comments:create')
        
        user.with_access_token(token)
        
        assert user.token_can('posts:read')
        assert user.token_can('comments:read')
        assert user.token_cant('posts:create')
        assert user.token_cant('posts:delete')
    
    def test_token_expiration_enforcement(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Temp User',
            'email': 'temp@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Temp User', 'email': 'temp@example.com'}, connection)
        
        expires_future = datetime.now() + timedelta(hours=1)
        valid_token = user.create_token('Valid Token', expires_at=expires_future)
        valid_plain = str(valid_token)
        
        token = PersonalAccessToken.find_token(valid_plain, connection)
        assert token is not None
        assert not token.is_expired()
        
        expires_past = datetime.now() - timedelta(hours=1)
        expired_token = user.create_token('Expired Token', expires_at=expires_past)
        expired_plain = str(expired_token)
        
        exp_token = PersonalAccessToken.find_token(expired_plain, connection)
        assert exp_token is not None
        assert exp_token.is_expired()
    
    def test_token_hash_security(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Security User',
            'email': 'security@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Security User', 'email': 'security@example.com'}, connection)
        
        new_token = user.create_token('Secure Token')
        plain_token = str(new_token)
        
        token_parts = plain_token.split('|')
        token_id = token_parts[0]
        token_secret = token_parts[1]
        
        db_record = connection.table('personal_access_tokens').where('id', token_id).first()
        stored_hash = db_record['token']
        
        assert stored_hash != plain_token
        assert stored_hash != token_secret
        
        expected_hash = hashlib.sha256(token_secret.encode()).hexdigest()
        assert stored_hash == expected_hash
        
        wrong_token = f"{token_id}|{secrets.token_urlsafe(40)}"
        not_found = PersonalAccessToken.find_token(wrong_token, connection)
        assert not_found is None
    
    def test_invalid_tokens_rejected(self, connection):
        invalid_formats = [
            'invalid_token',
            '123',
            'abc|',
            '|token',
            '999|' + 'x' * 40,
            ''
        ]
        
        for invalid in invalid_formats:
            if invalid and '|' in invalid:
                token = PersonalAccessToken.find_token(invalid, connection)
                assert token is None
    
    def test_token_revocation_immediate_invalidation(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Revoke User',
            'email': 'revoke@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Revoke User', 'email': 'revoke@example.com'}, connection)
        
        token = user.create_token('Revokable Token')
        plain_token = str(token)
        
        found = PersonalAccessToken.find_token(plain_token, connection)
        assert found is not None
        
        token_id = found.get_attribute('id')
        deleted = connection.table('personal_access_tokens').where('id', token_id).delete()
        assert deleted > 0
        
        not_found = PersonalAccessToken.find_token(plain_token, connection)
        assert not_found is None
    
    def test_wildcard_ability_grants_all(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Admin User',
            'email': 'admin@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Admin User', 'email': 'admin@example.com'}, connection)
        
        admin_token = user.create_token('Admin Token', abilities=['*'])
        plain_token = str(admin_token)
        
        token = PersonalAccessToken.find_token(plain_token, connection)
        
        abilities_to_test = [
            'posts:read', 'posts:create', 'posts:update', 'posts:delete',
            'users:read', 'users:create', 'users:update', 'users:delete',
            'comments:moderate', 'settings:change', 'any:random:ability'
        ]
        
        for ability in abilities_to_test:
            assert token.can(ability), f"Token should have {ability} with wildcard"
    
    def test_token_last_used_tracking(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Track User',
            'email': 'track@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Track User', 'email': 'track@example.com'}, connection)
        
        token = user.create_token('Tracked Token')
        plain_token = str(token)
        
        db_token = PersonalAccessToken.find_token(plain_token, connection)
        initial_last_used = db_token.get_attribute('last_used_at')
        
        db_token.set_attribute('last_used_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db_token.save()
        
        updated_token = PersonalAccessToken.find_token(plain_token, connection)
        new_last_used = updated_token.get_attribute('last_used_at')
        
        assert new_last_used != initial_last_used
        assert new_last_used is not None
    
    def test_specific_abilities_combination(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Combo User',
            'email': 'combo@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Combo User', 'email': 'combo@example.com'}, connection)
        
        token = user.create_token('Mixed Token', abilities=[
            'posts:read',
            'posts:create',
            'comments:read',
            'profile:update'
        ])
        plain_token = str(token)
        
        db_token = PersonalAccessToken.find_token(plain_token, connection)
        
        assert db_token.can('posts:read')
        assert db_token.can('posts:create')
        assert db_token.can('comments:read')
        assert db_token.can('profile:update')
        
        assert not db_token.can('posts:update')
        assert not db_token.can('posts:delete')
        assert not db_token.can('comments:create')
        assert not db_token.can('comments:delete')
        assert not db_token.can('users:admin')
    
    def test_empty_abilities_denies_all(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Empty User',
            'email': 'empty@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Empty User', 'email': 'empty@example.com'}, connection)
        
        token = user.create_token('Empty Token', abilities=[])
        plain_token = str(token)
        
        db_token = PersonalAccessToken.find_token(plain_token, connection)
        
        assert not db_token.can('posts:read')
        assert not db_token.can('posts:create')
        assert not db_token.can('any:ability')
    
    def test_token_format_validation(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Format User',
            'email': 'format@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Format User', 'email': 'format@example.com'}, connection)
        
        token = user.create_token('Format Token')
        plain_token = str(token)
        
        assert isinstance(plain_token, str)
        assert '|' in plain_token
        
        parts = plain_token.split('|')
        assert len(parts) == 2
        
        token_id, token_secret = parts
        assert token_id.isdigit()
        assert int(token_id) > 0
        assert len(token_secret) > 30
    
    def test_token_abilities_stored_as_json(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'JSON User',
            'email': 'json@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'JSON User', 'email': 'json@example.com'}, connection)
        
        abilities = ['read:posts', 'create:posts', 'update:own:posts']
        token = user.create_token('JSON Token', abilities=abilities)
        plain_token = str(token)
        
        token_parts = plain_token.split('|')
        token_id = token_parts[0]
        
        db_record = connection.table('personal_access_tokens').where('id', token_id).first()
        stored_abilities = db_record['abilities']
        
        assert isinstance(stored_abilities, str)
        
        import json
        parsed = json.loads(stored_abilities)
        assert isinstance(parsed, list)
        assert set(parsed) == set(abilities)
    
    def test_polymorphic_tokenable_relationship(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Polymorphic User',
            'email': 'poly@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Polymorphic User', 'email': 'poly@example.com'}, connection)
        
        token = user.create_token('Poly Token')
        plain_token = str(token)
        
        token_parts = plain_token.split('|')
        token_id = token_parts[0]
        
        db_record = connection.table('personal_access_tokens').where('id', token_id).first()
        
        assert db_record['tokenable_type'] == 'UserWithApiTokens'
        assert db_record['tokenable_id'] == user_id
    
    def test_concurrent_token_usage(self, connection):
        user_id = connection.table('users').insert_get_id({
            'name': 'Concurrent User',
            'email': 'concurrent@example.com',
            'password': 'hashed_password'
        })
        
        user = UserWithApiTokens({'id': user_id, 'name': 'Concurrent User', 'email': 'concurrent@example.com'}, connection)
        
        token1 = user.create_token('Token 1', abilities=['posts:read'])
        token2 = user.create_token('Token 2', abilities=['posts:write'])
        token3 = user.create_token('Token 3', abilities=['*'])
        
        plain1 = str(token1)
        plain2 = str(token2)
        plain3 = str(token3)
        
        db_token1 = PersonalAccessToken.find_token(plain1, connection)
        db_token2 = PersonalAccessToken.find_token(plain2, connection)
        db_token3 = PersonalAccessToken.find_token(plain3, connection)
        
        assert db_token1.can('posts:read')
        assert not db_token1.can('posts:write')
        
        assert not db_token2.can('posts:read')
        assert db_token2.can('posts:write')
        
        assert db_token3.can('posts:read')
        assert db_token3.can('posts:write')
        assert db_token3.can('posts:delete')
