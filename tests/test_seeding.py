import pytest
import os
import tempfile
import shutil
from faker import Faker
from larapy.database.connection import Connection
from larapy.database.seeding.seeder import Seeder
from larapy.database.seeding.factory import Factory
from larapy.database.seeding.seeder_runner import SeederRunner
from larapy.database.seeding.database_seeder import DatabaseSeeder


@pytest.fixture
def connection():
    conn = Connection({
        'driver': 'sqlite',
        'database': ':memory:',
    })
    conn.connect()
    
    conn.schema().create('users', lambda table: (
        table.increments('id'),
        table.string('name'),
        table.string('email'),
    ))
    
    conn.schema().create('posts', lambda table: (
        table.increments('id'),
        table.integer('user_id'),
        table.string('title'),
        table.text('content'),
    ))
    
    yield conn
    conn.disconnect()


@pytest.fixture
def seeder_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture
def faker():
    return Faker()


class TestSeeder:
    
    def test_seeder_receives_connection(self, connection):
        class TestSeeder(Seeder):
            def run(self):
                pass
        
        seeder = TestSeeder(connection)
        
        assert seeder._connection == connection
    
    def test_seeder_can_insert_data(self, connection):
        class UserSeeder(Seeder):
            def run(self):
                self._connection.table('users').insert({
                    'name': 'John Doe',
                    'email': 'john@example.com',
                })
        
        seeder = UserSeeder(connection)
        seeder.run()
        
        users = connection.table('users').get()
        
        assert len(users) == 1
        assert users[0]['name'] == 'John Doe'
        assert users[0]['email'] == 'john@example.com'
    
    def test_seeder_can_insert_multiple_records(self, connection):
        class UserSeeder(Seeder):
            def run(self):
                for i in range(5):
                    self._connection.table('users').insert({
                        'name': f'User {i}',
                        'email': f'user{i}@example.com',
                    })
        
        seeder = UserSeeder(connection)
        seeder.run()
        
        users = connection.table('users').get()
        
        assert len(users) == 5
    
    def test_seeder_can_use_query_builder(self, connection):
        class UserSeeder(Seeder):
            def run(self):
                self._connection.table('users').insert({
                    'name': 'Admin',
                    'email': 'admin@example.com',
                })
        
        seeder = UserSeeder(connection)
        seeder.run()
        
        admin = connection.table('users').where('email', 'admin@example.com').first()
        
        assert admin is not None
        assert admin['name'] == 'Admin'
    
    def test_database_seeder_is_abstract(self, connection):
        seeder = DatabaseSeeder(connection)
        
        assert hasattr(seeder, 'run')
    
    def test_seeder_with_relationships(self, connection):
        class UserPostSeeder(Seeder):
            def run(self):
                user_id = self._connection.table('users').insert_get_id({
                    'name': 'Author',
                    'email': 'author@example.com',
                })
                
                self._connection.table('posts').insert({
                    'user_id': user_id,
                    'title': 'First Post',
                    'content': 'Content here',
                })
        
        seeder = UserPostSeeder(connection)
        seeder.run()
        
        posts = connection.table('posts').get()
        
        assert len(posts) == 1
        assert posts[0]['title'] == 'First Post'
    
    def test_seeder_can_truncate_tables(self, connection):
        connection.table('users').insert({'name': 'Old User', 'email': 'old@example.com'})
        
        class UserSeeder(Seeder):
            def run(self):
                self._connection.table('users').truncate()
                self._connection.table('users').insert({
                    'name': 'New User',
                    'email': 'new@example.com',
                })
        
        seeder = UserSeeder(connection)
        seeder.run()
        
        users = connection.table('users').get()
        
        assert len(users) == 1
        assert users[0]['name'] == 'New User'
    
    def test_seeder_can_call_other_operations(self, connection):
        class ComplexSeeder(Seeder):
            def run(self):
                self._connection.table('users').insert({
                    'name': 'User 1',
                    'email': 'user1@example.com',
                })
                
                count = self._connection.table('users').count()
                
                if count > 0:
                    self._connection.table('users').insert({
                        'name': 'User 2',
                        'email': 'user2@example.com',
                    })
        
        seeder = ComplexSeeder(connection)
        seeder.run()
        
        assert connection.table('users').count() == 2


class TestFactory:
    
    def test_factory_definition_is_abstract(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        
        assert hasattr(factory, 'definition')
    
    def test_factory_make_returns_single_instance(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                }
        
        factory = UserFactory(connection, faker)
        user = factory.make()
        
        assert isinstance(user, dict)
        assert user['name'] == 'John Doe'
        assert user['email'] == 'john@example.com'
    
    def test_factory_make_with_count_returns_list(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        users = factory.count(3).make()
        
        assert isinstance(users, list)
        assert len(users) == 3
    
    def test_factory_make_with_overrides(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        user = factory.make({'name': 'Custom Name'})
        
        assert user['name'] == 'Custom Name'
        assert 'email' in user
    
    def test_factory_create_inserts_into_database(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': 'Test User',
                    'email': 'test@example.com',
                }
        
        factory = UserFactory(connection, faker)
        user = factory.create()
        
        db_users = connection.table('users').get()
        
        assert len(db_users) == 1
        assert db_users[0]['name'] == 'Test User'
    
    def test_factory_create_multiple_inserts_all(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        users = factory.count(5).create()
        
        db_users = connection.table('users').get()
        
        assert len(db_users) == 5
        assert len(users) == 5
    
    def test_factory_uses_faker_for_random_data(self, connection):
        faker = Faker()
        Faker.seed(12345)
        
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        user1 = factory.make()
        
        Faker.seed(54321)
        user2 = factory.make()
        
        assert user1['name'] != user2['name']
        assert user1['email'] != user2['email']
    
    def test_factory_state_modifies_attributes(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        user = factory.state(lambda attrs: {'name': 'Admin User'}).make()
        
        assert user['name'] == 'Admin User'
    
    def test_factory_state_can_be_chained(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        user = factory.state(lambda attrs: {'name': 'Admin'}).state(lambda attrs: {'email': 'admin@test.com'}).make()
        
        assert user['name'] == 'Admin'
        assert user['email'] == 'admin@test.com'
    
    def test_factory_raw_returns_attributes_without_creating(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': 'Raw User',
                    'email': 'raw@example.com',
                }
        
        factory = UserFactory(connection, faker)
        attributes = factory.raw()
        
        assert attributes['name'] == 'Raw User'
        assert attributes['email'] == 'raw@example.com'
        
        db_users = connection.table('users').get()
        assert len(db_users) == 0
    
    def test_factory_infers_table_name_from_class(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': 'Test',
                    'email': 'test@example.com',
                }
        
        factory = UserFactory(connection, faker)
        
        assert factory._get_table_name() == 'users'
    
    def test_factory_table_name_with_multiple_words(self, connection, faker):
        class BlogPostFactory(Factory):
            def definition(self):
                return {}
        
        factory = BlogPostFactory(connection, faker)
        
        assert factory._get_table_name() == 'blog_posts'
    
    def test_factory_with_relationships(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        class PostFactory(Factory):
            def definition(self):
                user_factory = UserFactory(self._connection, self._faker)
                user = user_factory.create()
                
                return {
                    'user_id': user['id'] if 'id' in user else 1,
                    'title': self._faker.sentence(),
                    'content': self._faker.text(),
                }
        
        user_factory = UserFactory(connection, faker)
        user_factory.create()
        
        post_factory = PostFactory(connection, faker)
        post = post_factory.create()
        
        assert 'user_id' in post
        assert 'title' in post
    
    def test_factory_count_does_not_mutate_original(self, connection, faker):
        class UserFactory(Factory):
            def definition(self):
                return {
                    'name': self._faker.name(),
                    'email': self._faker.email(),
                }
        
        factory = UserFactory(connection, faker)
        
        factory.count(5).create()
        
        single_user = factory.create()
        
        assert isinstance(single_user, dict)
        
        db_users = connection.table('users').get()
        assert len(db_users) == 6


class TestSeederRunner:
    
    def test_runner_can_call_seeder_class(self, connection, seeder_path):
        class TestSeeder(Seeder):
            def run(self):
                self._connection.table('users').insert({
                    'name': 'Runner Test',
                    'email': 'runner@example.com',
                })
        
        runner = SeederRunner(connection, [seeder_path])
        runner.call(TestSeeder)
        
        users = connection.table('users').get()
        
        assert len(users) == 1
    
    def test_runner_can_call_seeder_by_name(self, connection, seeder_path):
        seeder_file = os.path.join(seeder_path, 'UserSeeder.py')
        
        with open(seeder_file, 'w') as f:
            f.write('''
from larapy.database.seeding.seeder import Seeder

class UserSeeder(Seeder):
    def run(self):
        self._connection.table('users').insert({
            'name': 'File Seeder',
            'email': 'file@example.com',
        })
''')
        
        runner = SeederRunner(connection, [seeder_path])
        runner.call('UserSeeder')
        
        users = connection.table('users').get()
        
        assert len(users) == 1
        assert users[0]['name'] == 'File Seeder'
    
    def test_runner_tracks_called_seeders(self, connection, seeder_path):
        class FirstSeeder(Seeder):
            def run(self):
                pass
        
        class SecondSeeder(Seeder):
            def run(self):
                pass
        
        runner = SeederRunner(connection, [seeder_path])
        runner.call(FirstSeeder, silent=True)
        runner.call(SecondSeeder, silent=True)
        
        called = runner.get_called_seeders()
        
        assert 'FirstSeeder' in called
        assert 'SecondSeeder' in called
        assert len(called) == 2
    
    def test_runner_can_run_multiple_seeders(self, connection, seeder_path):
        class UserSeeder(Seeder):
            def run(self):
                self._connection.table('users').insert({
                    'name': 'User 1',
                    'email': 'user1@example.com',
                })
        
        class PostSeeder(Seeder):
            def run(self):
                self._connection.table('posts').insert({
                    'user_id': 1,
                    'title': 'Post 1',
                    'content': 'Content 1',
                })
        
        runner = SeederRunner(connection, [seeder_path])
        runner.run([UserSeeder, PostSeeder])
        
        assert connection.table('users').count() == 1
        assert connection.table('posts').count() == 1
    
    def test_runner_silent_mode_suppresses_output(self, connection, seeder_path, capsys):
        class QuietSeeder(Seeder):
            def run(self):
                pass
        
        runner = SeederRunner(connection, [seeder_path])
        runner.call(QuietSeeder, silent=True)
        
        captured = capsys.readouterr()
        
        assert captured.out == ''
    
    def test_runner_non_silent_mode_shows_output(self, connection, seeder_path, capsys):
        class VerboseSeeder(Seeder):
            def run(self):
                pass
        
        runner = SeederRunner(connection, [seeder_path])
        runner.call(VerboseSeeder, silent=False)
        
        captured = capsys.readouterr()
        
        assert 'Seeding: VerboseSeeder' in captured.out
        assert 'Seeded: VerboseSeeder' in captured.out
    
    def test_runner_raises_exception_for_missing_seeder(self, connection, seeder_path):
        runner = SeederRunner(connection, [seeder_path])
        
        with pytest.raises(Exception, match='Seeder not found'):
            runner.call('NonExistentSeeder')
