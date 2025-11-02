"""Tests for the database query builder and schema builder."""
import os
import pytest
from larapy.database.connection import Connection
from larapy.database.database_manager import DatabaseManager
from larapy.database.query.builder import QueryBuilder
from larapy.database.schema.schema import Schema, Blueprint


# Test configuration
TEST_DB_CONFIG = {
    'default': 'testing',
    'connections': {
        'testing': {
            'driver': 'sqlite',
            'database': ':memory:',
        }
    }
}


@pytest.fixture
def connection():
    """Create a test database connection."""
    conn = Connection(TEST_DB_CONFIG['connections']['testing'])
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture
def schema(connection):
    """Create a schema builder."""
    return connection.schema()


@pytest.fixture
def users_table(schema):
    """Create a users table for testing."""
    schema.create('users', lambda table: (
        table.increments('id'),
        table.string('name'),
        table.string('email').unique(),
        table.integer('age').nullable(),
        table.timestamps()
    ))
    yield
    schema.drop('users')


@pytest.fixture
def db_manager():
    """Create a database manager."""
    return DatabaseManager(TEST_DB_CONFIG)


class TestConnection:
    def test_creates_sqlite_connection(self, connection):
        assert connection._engine is not None
        assert connection._config['driver'] == 'sqlite'
    
    def test_executes_raw_select(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        results = connection.select('SELECT * FROM users WHERE name = ?', ['John Doe'])
        
        assert len(results) == 1
        assert results[0]['name'] == 'John Doe'
        assert results[0]['email'] == 'john@example.com'
    
    def test_executes_raw_insert(self, connection, schema, users_table):
        last_id = connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        assert last_id > 0
        
        results = connection.select('SELECT * FROM users WHERE id = ?', [last_id])
        assert len(results) == 1
        assert results[0]['name'] == 'Jane Doe'
    
    def test_executes_raw_update(self, connection, schema, users_table):
        last_id = connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        affected = connection.update('UPDATE users SET name = ? WHERE id = ?', ['Jane Doe', last_id])
        
        assert affected == 1
        
        results = connection.select('SELECT * FROM users WHERE id = ?', [last_id])
        assert results[0]['name'] == 'Jane Doe'
    
    def test_executes_raw_delete(self, connection, schema, users_table):
        last_id = connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        affected = connection.delete('DELETE FROM users WHERE id = ?', [last_id])
        
        assert affected == 1
        
        results = connection.select('SELECT * FROM users WHERE id = ?', [last_id])
        assert len(results) == 0
    
    def test_transaction_commits(self, connection, schema, users_table):
        def perform_insert():
            connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        connection.transaction(perform_insert)
        
        results = connection.select('SELECT * FROM users')
        assert len(results) == 1
    
    def test_transaction_rolls_back_on_exception(self, connection, schema, users_table):
        def perform_insert_with_error():
            connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
            raise Exception("Rollback!")
        
        with pytest.raises(Exception):
            connection.transaction(perform_insert_with_error)
        
        results = connection.select('SELECT * FROM users')
        assert len(results) == 0
    
    def test_gets_table_query_builder(self, connection, schema, users_table):
        builder = connection.table('users')
        
        assert isinstance(builder, QueryBuilder)
        assert builder._table == 'users'


class TestQueryBuilder:
    def test_selects_all_records(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        results = connection.table('users').get()
        
        assert len(results) == 2
    
    def test_selects_specific_columns(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        results = connection.table('users').select('name').get()
        
        assert len(results) == 1
        assert 'name' in results[0]
        assert 'email' not in results[0]
    
    def test_where_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        results = connection.table('users').where('name', '=', 'John Doe').get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'John Doe'
    
    def test_or_where_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        results = connection.table('users') \
            .where('name', '=', 'John Doe') \
            .or_where('name', '=', 'Jane Doe') \
            .get()
        
        assert len(results) == 2
    
    def test_where_in_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Bob Smith', 'bob@example.com'])
        
        results = connection.table('users').where_in('name', ['John Doe', 'Jane Doe']).get()
        
        assert len(results) == 2
    
    def test_where_not_in_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Bob Smith', 'bob@example.com'])
        
        results = connection.table('users').where_not_in('name', ['John Doe', 'Jane Doe']).get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'Bob Smith'
    
    def test_where_null_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', None])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        results = connection.table('users').where_null('age').get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'John Doe'
    
    def test_where_not_null_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', None])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        results = connection.table('users').where_not_null('age').get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'Jane Doe'
    
    def test_where_between_clause(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 25])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Bob Smith', 'bob@example.com', 35])
        
        results = connection.table('users').where_between('age', 26, 34).get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'Jane Doe'
    
    def test_nested_where_clauses(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 25])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Bob Smith', 'bob@example.com', 35])
        
        results = connection.table('users') \
            .where('age', '>', 20) \
            .where(lambda q: q.where('name', '=', 'John Doe').or_where('name', '=', 'Jane Doe')) \
            .get()
        
        assert len(results) == 2
    
    def test_order_by(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Bob Smith', 'bob@example.com'])
        
        results = connection.table('users').order_by('name', 'asc').get()
        
        assert results[0]['name'] == 'Bob Smith'
        assert results[1]['name'] == 'Jane Doe'
        assert results[2]['name'] == 'John Doe'
    
    def test_limit_and_offset(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Bob Smith', 'bob@example.com'])
        
        results = connection.table('users').order_by('name').limit(2).offset(1).get()
        
        assert len(results) == 2
        assert results[0]['name'] == 'Jane Doe'
    
    def test_distinct(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john2@example.com'])
        
        results = connection.table('users').select('name').distinct().get()
        
        assert len(results) == 1
    
    def test_first_method(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        result = connection.table('users').where('name', '=', 'John Doe').first()
        
        assert result is not None
        assert result['name'] == 'John Doe'
    
    def test_find_method(self, connection, schema, users_table):
        last_id = connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        result = connection.table('users').find(last_id)
        
        assert result is not None
        assert result['name'] == 'John Doe'
    
    def test_pluck_method(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        names = connection.table('users').pluck('name')
        
        assert len(names) == 2
        assert 'John Doe' in names
        assert 'Jane Doe' in names
    
    def test_value_method(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        name = connection.table('users').where('email', '=', 'john@example.com').value('name')
        
        assert name == 'John Doe'
    
    def test_count_aggregate(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['Jane Doe', 'jane@example.com'])
        
        count = connection.table('users').count()
        
        assert count == 2
    
    def test_sum_aggregate(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 25])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        total_age = connection.table('users').sum('age')
        
        assert total_age == 55
    
    def test_avg_aggregate(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 20])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        avg_age = connection.table('users').avg('age')
        
        assert avg_age == 25
    
    def test_min_aggregate(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 25])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        min_age = connection.table('users').min('age')
        
        assert min_age == 25
    
    def test_max_aggregate(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['John Doe', 'john@example.com', 25])
        connection.insert('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', ['Jane Doe', 'jane@example.com', 30])
        
        max_age = connection.table('users').max('age')
        
        assert max_age == 30
    
    def test_exists_method(self, connection, schema, users_table):
        connection.insert('INSERT INTO users (name, email) VALUES (?, ?)', ['John Doe', 'john@example.com'])
        
        exists = connection.table('users').where('name', '=', 'John Doe').exists()
        
        assert exists is True
        
        not_exists = connection.table('users').where('name', '=', 'Nobody').exists()
        
        assert not_exists is False
    
    def test_insert_single_record(self, connection, schema, users_table):
        connection.table('users').insert({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        results = connection.table('users').get()
        
        assert len(results) == 1
        assert results[0]['name'] == 'John Doe'
    
    def test_insert_multiple_records(self, connection, schema, users_table):
        connection.table('users').insert([
            {'name': 'John Doe', 'email': 'john@example.com'},
            {'name': 'Jane Doe', 'email': 'jane@example.com'}
        ])
        
        count = connection.table('users').count()
        
        assert count == 2
    
    def test_insert_get_id(self, connection, schema, users_table):
        last_id = connection.table('users').insert_get_id({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        assert last_id > 0
        
        result = connection.table('users').find(last_id)
        assert result['name'] == 'John Doe'
    
    def test_update_records(self, connection, schema, users_table):
        connection.table('users').insert({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        affected = connection.table('users') \
            .where('name', '=', 'John Doe') \
            .update({'email': 'newemail@example.com'})
        
        assert affected == 1
        
        result = connection.table('users').where('name', '=', 'John Doe').first()
        assert result['email'] == 'newemail@example.com'
    
    def test_increment_column(self, connection, schema, users_table):
        last_id = connection.table('users').insert_get_id({
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 25
        })
        
        connection.table('users').where('id', '=', last_id).increment('age', 5)
        
        result = connection.table('users').find(last_id)
        assert result['age'] == 30
    
    def test_decrement_column(self, connection, schema, users_table):
        last_id = connection.table('users').insert_get_id({
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        })
        
        connection.table('users').where('id', '=', last_id).decrement('age', 5)
        
        result = connection.table('users').find(last_id)
        assert result['age'] == 25
    
    def test_delete_records(self, connection, schema, users_table):
        connection.table('users').insert({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        
        affected = connection.table('users').where('name', '=', 'John Doe').delete()
        
        assert affected == 1
        
        count = connection.table('users').count()
        assert count == 0
    
    def test_truncate_table(self, connection, schema, users_table):
        connection.table('users').insert([
            {'name': 'John Doe', 'email': 'john@example.com'},
            {'name': 'Jane Doe', 'email': 'jane@example.com'}
        ])
        
        connection.table('users').truncate()
        
        count = connection.table('users').count()
        assert count == 0
    
    def test_join_tables(self, connection, schema):
        # Create posts table
        schema.create('posts', lambda table: (
            table.increments('id'),
            table.integer('user_id'),
            table.string('title')
        ))
        
        # Create users table
        schema.create('users', lambda table: (
            table.increments('id'),
            table.string('name')
        ))
        
        # Insert test data
        user_id = connection.table('users').insert_get_id({'name': 'John Doe'})
        connection.table('posts').insert({'user_id': user_id, 'title': 'First Post'})
        
        # Test join
        results = connection.table('posts') \
            .join('users', 'posts.user_id', '=', 'users.id') \
            .select('posts.title', 'users.name') \
            .get()
        
        assert len(results) == 1
        assert results[0]['title'] == 'First Post'
        assert results[0]['name'] == 'John Doe'
        
        # Cleanup
        schema.drop('posts')
        schema.drop('users')
    
    def test_to_sql_method(self, connection, schema, users_table):
        sql = connection.table('users') \
            .select('name', 'email') \
            .where('age', '>', 18) \
            .order_by('name') \
            .to_sql()
        
        assert 'SELECT' in sql
        assert 'FROM users' in sql
        assert 'WHERE' in sql
        assert 'ORDER BY' in sql


class TestSchema:
    def test_creates_table(self, schema):
        schema.create('test_table', lambda table: (
            table.increments('id'),
            table.string('name')
        ))
        
        assert schema.has_table('test_table')
        
        schema.drop('test_table')
    
    def test_creates_table_with_various_column_types(self, schema):
        schema.create('test_types', lambda table: (
            table.increments('id'),
            table.string('name', 100),
            table.text('description'),
            table.integer('count'),
            table.boolean('active'),
            table.float('price'),
            table.datetime('created_at')
        ))
        
        assert schema.has_table('test_types')
        assert schema.has_column('test_types', 'name')
        assert schema.has_column('test_types', 'description')
        assert schema.has_column('test_types', 'count')
        assert schema.has_column('test_types', 'active')
        assert schema.has_column('test_types', 'price')
        assert schema.has_column('test_types', 'created_at')
        
        schema.drop('test_types')
    
    def test_creates_nullable_columns(self, schema):
        schema.create('test_nullable', lambda table: (
            table.increments('id'),
            table.string('required_field'),
            table.string('optional_field').nullable()
        ))
        
        assert schema.has_table('test_nullable')
        
        schema.drop('test_nullable')
    
    def test_creates_columns_with_defaults(self, schema):
        schema.create('test_defaults', lambda table: (
            table.increments('id'),
            table.string('status').default('active'),
            table.integer('count').default(0)
        ))
        
        assert schema.has_table('test_defaults')
        
        schema.drop('test_defaults')
    
    def test_creates_unique_columns(self, schema):
        schema.create('test_unique', lambda table: (
            table.increments('id'),
            table.string('email').unique()
        ))
        
        assert schema.has_table('test_unique')
        
        schema.drop('test_unique')
    
    def test_creates_timestamps(self, schema):
        schema.create('test_timestamps', lambda table: (
            table.increments('id'),
            table.string('name'),
            table.timestamps()
        ))
        
        assert schema.has_column('test_timestamps', 'created_at')
        assert schema.has_column('test_timestamps', 'updated_at')
        
        schema.drop('test_timestamps')
    
    def test_drops_table(self, schema):
        schema.create('test_drop', lambda table: (
            table.increments('id'),
        ))
        
        schema.drop('test_drop')
        
        assert not schema.has_table('test_drop')
    
    def test_drops_table_if_exists(self, schema):
        schema.drop_if_exists('nonexistent_table')
        
        schema.create('test_drop_if_exists', lambda table: (
            table.increments('id'),
        ))
        
        schema.drop_if_exists('test_drop_if_exists')
        
        assert not schema.has_table('test_drop_if_exists')
    
    def test_has_table(self, schema):
        schema.create('test_has_table', lambda table: (
            table.increments('id'),
        ))
        
        assert schema.has_table('test_has_table')
        assert not schema.has_table('nonexistent_table')
        
        schema.drop('test_has_table')
    
    def test_has_column(self, schema):
        schema.create('test_has_column', lambda table: (
            table.increments('id'),
            table.string('name')
        ))
        
        assert schema.has_column('test_has_column', 'name')
        assert not schema.has_column('test_has_column', 'nonexistent_column')
        
        schema.drop('test_has_column')


class TestDatabaseManager:
    def test_creates_default_connection(self, db_manager):
        conn = db_manager.connection()
        
        assert conn is not None
        assert isinstance(conn, Connection)
    
    def test_caches_connections(self, db_manager):
        conn1 = db_manager.connection()
        conn2 = db_manager.connection()
        
        assert conn1 is conn2
    
    def test_gets_table_from_manager(self, db_manager):
        schema = db_manager.connection().schema()
        schema.create('test_manager', lambda table: (
            table.increments('id'),
            table.string('name')
        ))
        
        builder = db_manager.table('test_manager')
        
        assert isinstance(builder, QueryBuilder)
        
        schema.drop('test_manager')
    
    def test_disconnects_connection(self, db_manager):
        conn = db_manager.connection()
        db_manager.disconnect()
        
        new_conn = db_manager.connection()
        assert new_conn is not conn
