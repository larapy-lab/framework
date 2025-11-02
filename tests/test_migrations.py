import pytest
import os
import tempfile
import shutil
from larapy.database.connection import Connection
from larapy.database.migrations.migration import Migration
from larapy.database.migrations.migration_repository import MigrationRepository
from larapy.database.migrations.migrator import Migrator
from larapy.database.migrations.migration_creator import MigrationCreator


@pytest.fixture
def connection():
    conn = Connection({
        'driver': 'sqlite',
        'database': ':memory:',
    })
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture
def repository(connection):
    return MigrationRepository(connection)


@pytest.fixture
def migration_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture
def migrator(repository, connection, migration_path):
    return Migrator(repository, connection, [migration_path])


@pytest.fixture
def creator(migration_path):
    return MigrationCreator(migration_path)


class TestMigrationRepository:
    
    def test_create_repository(self, repository, connection):
        repository.create_repository()
        
        assert connection.schema().has_table('migrations')
        
        columns = connection.select('PRAGMA table_info(migrations)')
        column_names = [col['name'] for col in columns]
        
        assert 'id' in column_names
        assert 'migration' in column_names
        assert 'batch' in column_names
    
    def test_repository_exists(self, repository):
        assert not repository.repository_exists()
        
        repository.create_repository()
        
        assert repository.repository_exists()
    
    def test_get_ran_returns_empty_when_no_migrations(self, repository):
        repository.create_repository()
        
        ran = repository.get_ran()
        
        assert ran == []
    
    def test_log_migration(self, repository):
        repository.create_repository()
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        
        ran = repository.get_ran()
        
        assert ran == ['2024_01_01_000000_create_users_table']
    
    def test_get_ran_returns_migrations_in_order(self, repository):
        repository.create_repository()
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        repository.log('2024_01_02_000000_create_posts_table', 1)
        repository.log('2024_01_03_000000_create_comments_table', 2)
        
        ran = repository.get_ran()
        
        assert ran == [
            '2024_01_01_000000_create_users_table',
            '2024_01_02_000000_create_posts_table',
            '2024_01_03_000000_create_comments_table',
        ]
    
    def test_delete_migration(self, repository):
        repository.create_repository()
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        repository.log('2024_01_02_000000_create_posts_table', 1)
        
        repository.delete('2024_01_01_000000_create_users_table')
        
        ran = repository.get_ran()
        
        assert ran == ['2024_01_02_000000_create_posts_table']
    
    def test_get_next_batch_number(self, repository):
        repository.create_repository()
        
        assert repository.get_next_batch_number() == 1
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        
        assert repository.get_next_batch_number() == 2
        
        repository.log('2024_01_02_000000_create_posts_table', 2)
        
        assert repository.get_next_batch_number() == 3
    
    def test_get_last_batch_number(self, repository):
        repository.create_repository()
        
        assert repository.get_last_batch_number() == 0
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        
        assert repository.get_last_batch_number() == 1
        
        repository.log('2024_01_02_000000_create_posts_table', 2)
        repository.log('2024_01_03_000000_create_comments_table', 2)
        
        assert repository.get_last_batch_number() == 2
    
    def test_get_last_migrations(self, repository):
        repository.create_repository()
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        repository.log('2024_01_02_000000_create_posts_table', 2)
        repository.log('2024_01_03_000000_create_comments_table', 2)
        
        last = repository.get_last()
        
        assert len(last) == 2
        assert last[0]['migration'] == '2024_01_03_000000_create_comments_table'
        assert last[1]['migration'] == '2024_01_02_000000_create_posts_table'
    
    def test_get_migrations_batches(self, repository):
        repository.create_repository()
        
        repository.log('2024_01_01_000000_create_users_table', 1)
        repository.log('2024_01_02_000000_create_posts_table', 2)
        repository.log('2024_01_03_000000_create_comments_table', 2)
        
        batches = repository.get_migrations_batches()
        
        assert batches == {
            '2024_01_01_000000_create_users_table': 1,
            '2024_01_02_000000_create_posts_table': 2,
            '2024_01_03_000000_create_comments_table': 2,
        }


class TestMigrator:
    
    def test_run_creates_repository_if_not_exists(self, migrator, repository):
        assert not repository.repository_exists()
        
        migrator.run([])
        
        assert repository.repository_exists()
    
    def test_run_executes_pending_migrations(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        
        def define_table(table):
            table.increments('id')
            table.string('name')
        
        schema.create('users', define_table)
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run()
        
        assert connection.schema().has_table('users')
        
        ran = migrator._repository.get_ran()
        assert '2024_01_01_000000_create_users_table' in ran
    
    def test_run_skips_already_ran_migrations(self, migrator, migration_path, repository):
        repository.create_repository()
        repository.log('2024_01_01_000000_create_users_table', 1)
        
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        raise Exception('Should not be called')
    
    def down(self):
        pass
''')
        
        migrator.run()
        
        assert '2024_01_01_000000_create_users_table' in repository.get_ran()
    
    def test_run_with_step_option(self, migrator, migration_path):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        self._create_migration_file(migration_path, '2024_01_02_000000_create_posts_table', '''
from larapy.database.migrations.migration import Migration

class CreatePostsTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('posts', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('posts')
''')
        
        migrator.run(options={'step': True})
        
        ran = migrator._repository.get_ran()
        assert len(ran) == 1
        assert '2024_01_01_000000_create_users_table' in ran
    
    def test_run_with_pretend_option(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run(options={'pretend': True})
        
        assert not connection.schema().has_table('users')
        
        ran = migrator._repository.get_ran()
        assert len(ran) == 0
    
    def test_rollback_last_batch(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run()
        
        self._create_migration_file(migration_path, '2024_01_02_000000_create_posts_table', '''
from larapy.database.migrations.migration import Migration

class CreatePostsTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('posts', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('posts')
''')
        
        migrator.run()
        
        assert connection.schema().has_table('posts')
        
        migrator.rollback()
        
        assert not connection.schema().has_table('posts')
        assert connection.schema().has_table('users')
        
        ran = migrator._repository.get_ran()
        assert '2024_01_01_000000_create_users_table' in ran
        assert '2024_01_02_000000_create_posts_table' not in ran
    
    def test_rollback_with_step_option(self, migrator, migration_path):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        self._create_migration_file(migration_path, '2024_01_02_000000_create_posts_table', '''
from larapy.database.migrations.migration import Migration

class CreatePostsTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('posts', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('posts')
''')
        
        migrator.run()
        
        migrator.rollback(options={'step': True})
        
        ran = migrator._repository.get_ran()
        assert len(ran) == 1
        assert '2024_01_01_000000_create_users_table' in ran
    
    def test_rollback_with_pretend_option(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run()
        
        assert connection.schema().has_table('users')
        
        migrator.rollback(options={'pretend': True})
        
        assert connection.schema().has_table('users')
        
        ran = migrator._repository.get_ran()
        assert '2024_01_01_000000_create_users_table' in ran
    
    def test_reset_all_migrations(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        self._create_migration_file(migration_path, '2024_01_02_000000_create_posts_table', '''
from larapy.database.migrations.migration import Migration

class CreatePostsTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('posts', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('posts')
''')
        
        migrator.run()
        
        assert connection.schema().has_table('users')
        assert connection.schema().has_table('posts')
        
        migrator.reset()
        
        assert not connection.schema().has_table('users')
        assert not connection.schema().has_table('posts')
        
        ran = migrator._repository.get_ran()
        assert len(ran) == 0
    
    def test_refresh_resets_and_reruns_all(self, migrator, migration_path, connection):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run()
        
        assert connection.schema().has_table('users')
        
        migrator.refresh()
        
        assert connection.schema().has_table('users')
        
        ran = migrator._repository.get_ran()
        assert '2024_01_01_000000_create_users_table' in ran
    
    def test_get_migration_files(self, migrator, migration_path):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '')
        self._create_migration_file(migration_path, '2024_01_02_000000_create_posts_table', '')
        
        files = migrator.get_migration_files([migration_path])
        
        assert files == [
            '2024_01_01_000000_create_users_table',
            '2024_01_02_000000_create_posts_table',
        ]
    
    def test_get_notes(self, migrator, migration_path):
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda t: t.increments('id'))
    
    def down(self):
        self._connection.schema().drop_if_exists('users')
''')
        
        migrator.run()
        
        notes = migrator.get_notes()
        
        assert 'Migrating: 2024_01_01_000000_create_users_table' in notes
        assert 'Migrated: 2024_01_01_000000_create_users_table' in notes
    
    def test_repository_exists(self, migrator):
        assert not migrator.repository_exists()
        
        migrator.run()
        
        assert migrator.repository_exists()
    
    def test_has_ran_migrations(self, migrator, migration_path):
        assert not migrator.has_ran_migrations()
        
        self._create_migration_file(migration_path, '2024_01_01_000000_create_users_table', '''
from larapy.database.migrations.migration import Migration

class CreateUsersTableMigration(Migration):
    def up(self):
        pass
    
    def down(self):
        pass
''')
        
        migrator.run()
        
        assert migrator.has_ran_migrations()
    
    def _create_migration_file(self, path, name, content):
        file_path = os.path.join(path, f'{name}.py')
        with open(file_path, 'w') as f:
            f.write(content)


class TestMigrationCreator:
    
    def test_create_blank_migration(self, creator, migration_path):
        path = creator.create('create_users_table')
        
        assert os.path.exists(path)
        assert path.endswith('_create_users_table.py')
        
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'class Migration(Migration):' in content
        assert 'def up(self):' in content
        assert 'def down(self):' in content
    
    def test_create_table_migration(self, creator, migration_path):
        path = creator.create('create_users_table', table='users', create=True)
        
        assert os.path.exists(path)
        
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'class UsersMigration(Migration):' in content
        assert "schema.create('users'" in content
        assert "table.increments('id')" in content
        assert 'table.timestamps()' in content
        assert "drop_if_exists('users')" in content
    
    def test_create_update_migration(self, creator, migration_path):
        path = creator.create('add_email_to_users', table='users')
        
        assert os.path.exists(path)
        
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'class UsersMigration(Migration):' in content
        assert "schema.table('users'" in content
    
    def test_migration_name_includes_timestamp(self, creator):
        path1 = creator.create('create_users_table')
        path2 = creator.create('create_posts_table')
        
        assert path1 != path2
        assert '20' in os.path.basename(path1)
        assert '20' in os.path.basename(path2)
