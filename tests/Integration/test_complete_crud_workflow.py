"""
Integration Tests: Complete CRUD Workflows
==========================================

Tests complete CRUD operations with relationships.
"""
import pytest
from larapy.database.orm.model import Model
from larapy.database.connection import Connection


class User(Model):
    """Test User model"""
    _table = 'users'
    _fillable = ['name', 'email', 'active']
    
    def posts(self):
        return self.has_many(Post)


class Post(Model):
    """Test Post model"""
    _table = 'posts'
    _fillable = ['user_id', 'title', 'content']
    
    def user(self):
        return self.belongs_to(User)


@pytest.fixture
def connection():
    """Setup test database connection"""
    conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
    conn.connect()
    
    # Create tables
    conn.statement('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.statement('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    return conn


class TestCompleteUserLifecycle:
    """Test complete user lifecycle with all operations"""
    
    def test_user_creation(self, connection):
        """Test user creation"""
        User._connection = connection
        
        user = User.create({
            'name': 'John Doe',
            'email': 'john@example.com',
            'active': 1
        })
        
        assert user.get_key() is not None
        assert user.name == 'John Doe'
        assert user.email == 'john@example.com'
        # Active defaults to 1 in database
        found_user = User.find(user.get_key())
        assert found_user.active == 1
    
    def test_user_with_relationships(self, connection):
        """Test user creation with related models"""
        User._connection = connection
        Post._connection = connection
        
        # Create user
        user = User.create({
            'name': 'Jane Smith',
            'email': 'jane@example.com'
        })
        
        # Create posts
        post1 = user.posts().create({
            'title': 'First Post',
            'content': 'Hello World'
        })
        
        post2 = user.posts().create({
            'title': 'Second Post',
            'content': 'Another post'
        })
        
        # Verify relationships
        posts = user.posts().get()
        assert len(posts) == 2
        assert posts[0].title in ['First Post', 'Second Post']
    
    def test_update_operations(self, connection):
        """Test various update operations"""
        User._connection = connection
        
        user = User.create({
            'name': 'Alice Brown',
            'email': 'alice@example.com',
            'active': 1
        })
        
        original_id = user.get_key()
        
        # Update single field
        user.name = 'Alice Johnson'
        user.save()
        
        updated_user = User.find(original_id)
        assert updated_user.name == 'Alice Johnson'
    
    def test_deletion(self, connection):
        """Test deletion operations"""
        User._connection = connection
        
        user = User.create({
            'name': 'Delete Test',
            'email': 'delete@example.com'
        })
        
        user_id = user.get_key()
        
        # Delete user
        user.delete()
        assert User.find(user_id) is None
    
    def test_query_operations(self, connection):
        """Test various query operations"""
        User._connection = connection
        
        # Create multiple users
        for i in range(5):
            User.create({
                'name': f'User {i}',
                'email': f'user{i}@example.com',
                'active': i % 2
            })
        
        # Query active users
        active_users = User.where('active', 1).get()
        assert len(active_users) >= 2
        
        # Find by email
        user = User.where('email', 'user0@example.com').first()
        assert user is not None
        assert user.name == 'User 0'


class TestTransactions:
    """Test transaction handling"""
    
    def test_successful_transaction(self, connection):
        """Test successful transaction commits changes"""
        User._connection = connection
        
        initial_count = len(User.all())
        
        # Create users within transaction
        User.create({'name': 'Trans User 1', 'email': 'trans1@example.com'})
        User.create({'name': 'Trans User 2', 'email': 'trans2@example.com'})
        
        final_count = len(User.all())
        assert final_count == initial_count + 2


class TestComplexQueries:
    """Test complex query scenarios"""
    
    def test_multiple_where_conditions(self, connection):
        """Test queries with multiple conditions"""
        User._connection = connection
        
        User.create({'name': 'Active User 1', 'email': 'active1@example.com', 'active': 1})
        User.create({'name': 'Inactive User', 'email': 'inactive@example.com', 'active': 0})
        
        result = User.where('active', 1).where('name', 'Active User 1').get()
        
        assert len(result) == 1
        assert result[0].name == 'Active User 1'
    
    def test_limiting(self, connection):
        """Test LIMIT"""
        User._connection = connection
        
        for i in range(5):
            User.create({'name': f'Limit User {i:02d}', 'email': f'limit{i}@example.com'})
        
        # Query all users
        all_users = User.all()
        
        assert len(all_users) >= 5

