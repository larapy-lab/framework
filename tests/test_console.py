import pytest
import os
import tempfile
import shutil
from datetime import datetime
from larapy.console.command import Command
from larapy.console.kernel import Kernel
from larapy.console.commands import (
    MigrateCommand,
    MigrateRollbackCommand,
    MigrateResetCommand,
    MigrateRefreshCommand,
    MigrateFreshCommand,
    MigrateStatusCommand,
    DbSeedCommand,
    MakeMigrationCommand,
    MakeSeederCommand,
    MakeFactoryCommand,
)
from larapy.database.connection import Connection
from larapy.database.migrations.migration_repository import MigrationRepository


class TestCommand:
    
    def test_simple_command(self):
        class SimpleCommand(Command):
            signature = 'test'
            description = 'A test command'
            
            def handle(self):
                self.line('Hello World')
                return 0
        
        command = SimpleCommand()
        assert command.get_name() == 'test'
        assert command.description == 'A test command'
        assert command.handle() == 0
        assert 'Hello World' in command.get_output()
    
    def test_command_with_arguments(self):
        class CommandWithArgs(Command):
            signature = 'greet {name}'
            description = 'Greet someone'
            
            def handle(self):
                name = self.argument('name')
                self.line(f'Hello {name}')
                return 0
        
        command = CommandWithArgs()
        command.set_arguments(['John'])
        
        assert command.handle() == 0
        assert 'Hello John' in command.get_output()
    
    def test_command_with_optional_arguments(self):
        class CommandWithOptionalArgs(Command):
            signature = 'greet {name?}'
            description = 'Greet someone'
            
            def handle(self):
                name = self.argument('name', 'Guest')
                self.line(f'Hello {name}')
                return 0
        
        command = CommandWithOptionalArgs()
        command.set_arguments([])
        
        assert command.handle() == 0
        assert 'Hello Guest' in command.get_output()
    
    def test_command_with_options(self):
        class CommandWithOptions(Command):
            signature = 'greet {name} {--formal}'
            description = 'Greet someone'
            
            def handle(self):
                name = self.argument('name')
                formal = self.option('formal', False)
                
                if formal:
                    self.line(f'Good day, {name}')
                else:
                    self.line(f'Hello {name}')
                return 0
        
        command = CommandWithOptions()
        command.set_arguments(['John'])
        command.set_options({'formal': True})
        
        assert command.handle() == 0
        assert 'Good day, John' in command.get_output()
    
    def test_command_output_methods(self):
        class OutputCommand(Command):
            signature = 'output'
            
            def handle(self):
                self.info('Info message')
                self.comment('Comment message')
                self.question('Question message')
                self.error('Error message')
                self.warn('Warning message')
                return 0
        
        command = OutputCommand()
        command.handle()
        
        output = command.get_output()
        assert any('[INFO]' in line for line in output)
        assert any('[COMMENT]' in line for line in output)
        assert any('[QUESTION]' in line for line in output)
        assert any('[ERROR]' in line for line in output)
        assert any('[WARNING]' in line for line in output)
    
    def test_command_table_output(self):
        class TableCommand(Command):
            signature = 'table'
            
            def handle(self):
                self.table(
                    ['Name', 'Age'],
                    [
                        ['John', '30'],
                        ['Jane', '25'],
                    ]
                )
                return 0
        
        command = TableCommand()
        command.handle()
        
        output = command.get_output()
        assert any('Name' in line for line in output)
        assert any('John' in line for line in output)


class TestKernel:
    
    def test_register_command(self):
        class TestCommand(Command):
            signature = 'test'
            description = 'Test command'
            
            def handle(self):
                return 0
        
        kernel = Kernel()
        kernel.register(TestCommand)
        
        assert kernel.has('test')
        assert 'test' in kernel.all()
    
    def test_register_many_commands(self):
        class Command1(Command):
            signature = 'cmd1'
            
            def handle(self):
                return 0
        
        class Command2(Command):
            signature = 'cmd2'
            
            def handle(self):
                return 0
        
        kernel = Kernel()
        kernel.register_many([Command1, Command2])
        
        assert kernel.has('cmd1')
        assert kernel.has('cmd2')
    
    def test_call_command(self):
        class EchoCommand(Command):
            signature = 'echo {message}'
            
            def handle(self):
                self.line(self.argument('message'))
                return 0
        
        kernel = Kernel()
        kernel.register(EchoCommand)
        
        result = kernel.call('echo', ['Hello'])
        assert result == 0
    
    def test_call_nonexistent_command(self):
        kernel = Kernel()
        result = kernel.call('nonexistent')
        assert result == 1
    
    def test_run_with_arguments(self):
        class AddCommand(Command):
            signature = 'add {a} {b}'
            
            def handle(self):
                a = int(self.argument('a'))
                b = int(self.argument('b'))
                self.line(str(a + b))
                return 0
        
        kernel = Kernel()
        kernel.register(AddCommand)
        
        result = kernel.run(['add', '5', '3'])
        assert result == 0
    
    def test_run_with_options(self):
        class GreetCommand(Command):
            signature = 'greet {name} {--uppercase}'
            
            def handle(self):
                name = self.argument('name')
                if self.option('uppercase'):
                    self.line(name.upper())
                else:
                    self.line(name)
                return 0
        
        kernel = Kernel()
        kernel.register(GreetCommand)
        
        result = kernel.run(['greet', 'john', '--uppercase'])
        assert result == 0


class TestMigrationCommands:
    
    @pytest.fixture
    def connection(self):
        conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
        conn.connect()
        yield conn
        conn.disconnect()
    
    @pytest.fixture
    def config(self, tmp_path):
        migration_path = tmp_path / 'migrations'
        migration_path.mkdir()
        
        migration_file = migration_path / '2024_01_01_000001_create_users_table.py'
        migration_file.write_text('''class CreateUsersTable:
    
    def __init__(self, connection):
        self._connection = connection
    
    def up(self):
        schema = self._connection.schema()
        schema.create('users', lambda table: (
            table.increments('id'),
            table.string('name'),
            table.string('email')
        ))
    
    def down(self):
        schema = self._connection.schema()
        schema.drop('users')
''')
        
        return {
            'migrations': {
                'path': str(migration_path),
                'paths': [str(migration_path)],
                'table': 'migrations'
            }
        }
    
    def test_migrate_command(self, connection, config):
        command = MigrateCommand(connection, config)
        command.set_arguments([])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert connection.schema().has_table('users')
        assert connection.schema().has_table('migrations')
    
    def test_migrate_status_command(self, connection, config):
        migrate_cmd = MigrateCommand(connection, config)
        migrate_cmd.set_arguments([])
        migrate_cmd.set_options({})
        migrate_cmd.handle()
        
        status_cmd = MigrateStatusCommand(connection, config)
        status_cmd.set_arguments([])
        status_cmd.set_options({})
        
        result = status_cmd.handle()
        
        assert result == 0
        output = status_cmd.get_output()
        assert any('create_users_table' in line for line in output)
    
    def test_migrate_rollback_command(self, connection, config):
        migrate_cmd = MigrateCommand(connection, config)
        migrate_cmd.set_arguments([])
        migrate_cmd.set_options({})
        migrate_cmd.handle()
        
        rollback_cmd = MigrateRollbackCommand(connection, config)
        rollback_cmd.set_arguments([])
        rollback_cmd.set_options({})
        
        result = rollback_cmd.handle()
        
        assert result == 0
        assert not connection.schema().has_table('users')
    
    def test_migrate_reset_command(self, connection, config):
        migrate_cmd = MigrateCommand(connection, config)
        migrate_cmd.set_arguments([])
        migrate_cmd.set_options({})
        migrate_cmd.handle()
        
        reset_cmd = MigrateResetCommand(connection, config)
        reset_cmd.set_arguments([])
        reset_cmd.set_options({})
        
        result = reset_cmd.handle()
        
        assert result == 0
        assert not connection.schema().has_table('users')
    
    def test_migrate_refresh_command(self, connection, config):
        migrate_cmd = MigrateCommand(connection, config)
        migrate_cmd.set_arguments([])
        migrate_cmd.set_options({})
        migrate_cmd.handle()
        
        connection.table('users').insert({'name': 'John', 'email': 'john@example.com'})
        
        refresh_cmd = MigrateRefreshCommand(connection, config)
        refresh_cmd.set_arguments([])
        refresh_cmd.set_options({})
        
        result = refresh_cmd.handle()
        
        assert result == 0
        assert connection.schema().has_table('users')
        assert connection.table('users').count() == 0
    
    def test_migrate_fresh_command(self, connection, config):
        migrate_cmd = MigrateCommand(connection, config)
        migrate_cmd.set_arguments([])
        migrate_cmd.set_options({})
        migrate_cmd.handle()
        
        connection.table('users').insert({'name': 'John', 'email': 'john@example.com'})
        
        fresh_cmd = MigrateFreshCommand(connection, config)
        fresh_cmd.set_arguments([])
        fresh_cmd.set_options({})
        
        result = fresh_cmd.handle()
        
        assert result == 0
        assert connection.schema().has_table('users')
        assert connection.table('users').count() == 0


class TestSeedCommand:
    
    @pytest.fixture
    def connection(self):
        conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
        conn.connect()
        
        schema = conn.schema()
        schema.create('users', lambda table: (
            table.increments('id'),
            table.string('name'),
            table.string('email')
        ))
        
        yield conn
        conn.disconnect()
    
    @pytest.fixture
    def config(self, tmp_path):
        seeder_path = tmp_path / 'seeders'
        seeder_path.mkdir()
        
        seeder_file = seeder_path / 'UserSeeder.py'
        seeder_file.write_text('''from larapy.database.seeding.seeder import Seeder

class UserSeeder(Seeder):
    
    def run(self):
        self._connection.table('users').insert({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
''')
        
        database_seeder_file = seeder_path / 'DatabaseSeeder.py'
        database_seeder_file.write_text('''from larapy.database.seeding.database_seeder import DatabaseSeeder as BaseSeeder

class DatabaseSeeder(BaseSeeder):
    
    def run(self):
        self._connection.table('users').insert({
            'name': 'Admin',
            'email': 'admin@example.com'
        })
''')
        
        return {
            'seeders': {
                'path': str(seeder_path),
                'paths': [str(seeder_path)]
            }
        }
    
    def test_db_seed_default(self, connection, config):
        command = DbSeedCommand(connection, config)
        command.set_arguments([])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        assert connection.table('users').count() == 1
        assert connection.table('users').where('email', '=', 'admin@example.com').exists()
    
    def test_db_seed_with_class(self, connection, config):
        command = DbSeedCommand(connection, config)
        command.set_arguments([])
        command.set_options({'class': 'UserSeeder'})
        
        result = command.handle()
        
        assert result == 0
        assert connection.table('users').count() == 1
        assert connection.table('users').where('email', '=', 'john@example.com').exists()


class TestMakeCommands:
    
    @pytest.fixture
    def config(self, tmp_path):
        migration_path = tmp_path / 'migrations'
        seeder_path = tmp_path / 'seeders'
        factory_path = tmp_path / 'factories'
        
        return {
            'migrations': {
                'path': str(migration_path),
                'paths': [str(migration_path)]
            },
            'seeders': {
                'path': str(seeder_path),
                'paths': [str(seeder_path)]
            },
            'factories': {
                'path': str(factory_path),
                'paths': [str(factory_path)]
            }
        }
    
    def test_make_migration_command(self, config):
        command = MakeMigrationCommand(config)
        command.set_arguments(['create_posts_table'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        
        migration_path = config['migrations']['path']
        files = os.listdir(migration_path)
        
        assert len(files) == 1
        assert 'create_posts_table' in files[0]
        assert files[0].endswith('.py')
    
    def test_make_migration_with_create_option(self, config):
        command = MakeMigrationCommand(config)
        command.set_arguments(['create_posts_table'])
        command.set_options({'create': 'posts'})
        
        result = command.handle()
        
        assert result == 0
        
        migration_path = config['migrations']['path']
        files = os.listdir(migration_path)
        migration_file = os.path.join(migration_path, files[0])
        
        with open(migration_file, 'r') as f:
            content = f.read()
        
        assert 'posts' in content
        assert 'schema.create' in content
    
    def test_make_migration_with_table_option(self, config):
        command = MakeMigrationCommand(config)
        command.set_arguments(['add_column_to_posts'])
        command.set_options({'table': 'posts'})
        
        result = command.handle()
        
        assert result == 0
        
        migration_path = config['migrations']['path']
        files = os.listdir(migration_path)
        migration_file = os.path.join(migration_path, files[0])
        
        with open(migration_file, 'r') as f:
            content = f.read()
        
        assert 'posts' in content
        assert 'schema.table' in content
    
    def test_make_seeder_command(self, config):
        command = MakeSeederCommand(config)
        command.set_arguments(['UserSeeder'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        
        seeder_path = config['seeders']['path']
        seeder_file = os.path.join(seeder_path, 'UserSeeder.py')
        
        assert os.path.exists(seeder_file)
        
        with open(seeder_file, 'r') as f:
            content = f.read()
        
        assert 'class UserSeeder' in content
        assert 'from larapy.database.seeding.seeder import Seeder' in content
    
    def test_make_seeder_appends_suffix(self, config):
        command = MakeSeederCommand(config)
        command.set_arguments(['User'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        
        seeder_path = config['seeders']['path']
        seeder_file = os.path.join(seeder_path, 'UserSeeder.py')
        
        assert os.path.exists(seeder_file)
    
    def test_make_factory_command(self, config):
        command = MakeFactoryCommand(config)
        command.set_arguments(['UserFactory'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        
        factory_path = config['factories']['path']
        factory_file = os.path.join(factory_path, 'UserFactory.py')
        
        assert os.path.exists(factory_file)
        
        with open(factory_file, 'r') as f:
            content = f.read()
        
        assert 'class UserFactory' in content
        assert 'from larapy.database.seeding.factory import Factory' in content
    
    def test_make_factory_appends_suffix(self, config):
        command = MakeFactoryCommand(config)
        command.set_arguments(['Post'])
        command.set_options({})
        
        result = command.handle()
        
        assert result == 0
        
        factory_path = config['factories']['path']
        factory_file = os.path.join(factory_path, 'PostFactory.py')
        
        assert os.path.exists(factory_file)
