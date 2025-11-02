import pytest
from datetime import datetime
from larapy.database.connection import Connection
from larapy.database.orm import Model, Collection


class User(Model):
    _table = 'users'
    _fillable = ['name', 'email', 'age']
    
    def posts(self):
        return self.has_many(Post)
    
    def phone(self):
        return self.has_one(Phone)
    
    def roles(self):
        return self.belongs_to_many(Role)


class Post(Model):
    _table = 'posts'
    _fillable = ['title', 'body', 'user_id']
    
    def user(self):
        return self.belongs_to(User)
    
    def comments(self):
        return self.has_many(Comment)
    
    def tags(self):
        return self.belongs_to_many(Tag)


class Comment(Model):
    _table = 'comments'
    _fillable = ['content', 'post_id']
    
    def post(self):
        return self.belongs_to(Post)


class Role(Model):
    _table = 'roles'
    _fillable = ['name']


class Phone(Model):
    _table = 'phones'
    _fillable = ['number', 'user_id']


class Tag(Model):
    _table = 'tags'
    _fillable = ['name']


@pytest.fixture
def connection():
    conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
    conn.connect()
    
    conn.statement('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, age INTEGER, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT, user_id INTEGER, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE comments (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, post_id INTEGER, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE phones (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, user_id INTEGER, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_at TEXT, updated_at TEXT)')
    conn.statement('CREATE TABLE role_user (user_id INTEGER, role_id INTEGER)')
    conn.statement('CREATE TABLE post_tag (post_id INTEGER, tag_id INTEGER)')
    
    return conn


def test_model_table_name_inference():
    user = User()
    assert user.get_table() == 'users'
    
    post = Post()
    assert post.get_table() == 'posts'


def test_model_create_and_save(connection):
    User._connection = connection
    
    user = User.create({'name': 'John Doe', 'email': 'john@example.com', 'age': 30})
    
    assert user._exists is True
    assert user._was_recently_created is True
    assert user.name == 'John Doe'
    assert user.email == 'john@example.com'
    assert user.age == 30
    assert user.get_key() is not None


def test_model_find(connection):
    User._connection = connection
    
    created_user = User.create({'name': 'Jane Doe', 'email': 'jane@example.com', 'age': 25})
    
    found_user = User.find(created_user.get_key())
    
    assert found_user is not None
    assert found_user.name == 'Jane Doe'
    assert found_user.email == 'jane@example.com'


def test_model_update(connection):
    User._connection = connection
    
    user = User.create({'name': 'Bob Smith', 'email': 'bob@example.com', 'age': 35})
    
    user.name = 'Robert Smith'
    user.email = 'robert@example.com'
    user.save()
    
    updated_user = User.find(user.get_key())
    
    assert updated_user.name == 'Robert Smith'
    assert updated_user.email == 'robert@example.com'


def test_model_delete(connection):
    User._connection = connection
    
    user = User.create({'name': 'Alice Johnson', 'email': 'alice@example.com', 'age': 28})
    user_id = user.get_key()
    
    user.delete()
    
    deleted_user = User.find(user_id)
    assert deleted_user is None


def test_model_where_query(connection):
    User._connection = connection
    
    User.create({'name': 'Charlie Brown', 'email': 'charlie@example.com', 'age': 40})
    User.create({'name': 'Diana Prince', 'email': 'diana@example.com', 'age': 30})
    User.create({'name': 'Eve Adams', 'email': 'eve@example.com', 'age': 30})
    
    users = User.where('age', 30).get()
    
    assert len(users) == 2
    assert all(user.age == 30 for user in users)


def test_model_all(connection):
    User._connection = connection
    
    User.create({'name': 'User 1', 'email': 'user1@example.com', 'age': 20})
    User.create({'name': 'User 2', 'email': 'user2@example.com', 'age': 25})
    User.create({'name': 'User 3', 'email': 'user3@example.com', 'age': 30})
    
    users = User.all()
    
    assert isinstance(users, Collection)
    assert len(users) == 3


def test_model_first(connection):
    User._connection = connection
    
    User.create({'name': 'First User', 'email': 'first@example.com', 'age': 20})
    User.create({'name': 'Second User', 'email': 'second@example.com', 'age': 25})
    
    first_user = User.where('age', 20).first()
    
    assert first_user is not None
    assert first_user.name == 'First User'


def test_model_count(connection):
    User._connection = connection
    
    User.create({'name': 'User 1', 'email': 'user1@example.com', 'age': 20})
    User.create({'name': 'User 2', 'email': 'user2@example.com', 'age': 25})
    User.create({'name': 'User 3', 'email': 'user3@example.com', 'age': 30})
    
    count = User.query().count()
    
    assert count == 3


def test_model_fillable_mass_assignment(connection):
    User._connection = connection
    
    user = User()
    user.fill({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    
    assert user.name == 'Test User'
    assert user.email == 'test@example.com'
    assert user.age == 25


def test_model_is_dirty(connection):
    User._connection = connection
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    
    assert user.is_dirty() is False
    
    user.name = 'Modified User'
    
    assert user.is_dirty() is True
    assert user.is_dirty(['name']) is True
    assert user.is_dirty(['email']) is False


def test_model_get_changes(connection):
    User._connection = connection
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    
    user.name = 'Modified User'
    user.age = 30
    
    changes = user.get_changes()
    
    assert 'name' in changes
    assert 'age' in changes
    assert changes['name'] == 'Modified User'
    assert changes['age'] == 30


def test_model_fresh(connection):
    User._connection = connection
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    user.name = 'Modified User'
    
    fresh_user = user.fresh()
    
    assert fresh_user.name == 'Test User'
    assert user.name == 'Modified User'


def test_model_refresh(connection):
    User._connection = connection
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    user.name = 'Modified User'
    
    user.refresh()
    
    assert user.name == 'Test User'


def test_collection_methods(connection):
    User._connection = connection
    
    User.create({'name': 'User 1', 'email': 'user1@example.com', 'age': 20})
    User.create({'name': 'User 2', 'email': 'user2@example.com', 'age': 25})
    User.create({'name': 'User 3', 'email': 'user3@example.com', 'age': 30})
    
    users = User.all()
    
    assert users.count() == 3
    assert users.first().name == 'User 1'
    assert users.last().name == 'User 3'
    
    names = users.pluck('name')
    assert names == ['User 1', 'User 2', 'User 3']
    
    young_users = users.filter(lambda user: user.age < 30)
    assert young_users.count() == 2


def test_belongs_to_relationship(connection):
    User._connection = connection
    Post._connection = connection
    
    user = User.create({'name': 'Author', 'email': 'author@example.com', 'age': 30})
    post = Post.create({'title': 'Test Post', 'body': 'Content', 'user_id': user.get_key()})
    
    post_user = post.user().get_results()
    
    assert post_user is not None
    assert post_user.get_key() == user.get_key()
    assert post_user.name == 'Author'


def test_model_timestamps(connection):
    User._connection = connection
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    
    assert user.get_attribute('created_at') is not None
    assert user.get_attribute('updated_at') is not None


def test_model_attribute_casting(connection):
    User._connection = connection
    User._casts = {'age': 'int'}
    
    user = User.create({'name': 'Test User', 'email': 'test@example.com', 'age': '30'})
    
    assert isinstance(user.age, int)
    assert user.age == 30


def test_model_paginate(connection):
    User._connection = connection
    
    for i in range(25):
        User.create({'name': f'User {i+1}', 'email': f'user{i+1}@example.com', 'age': 20 + i})
    
    paginated = User.query().paginate(per_page=10, page=1)
    
    assert paginated['total'] == 25
    assert paginated['per_page'] == 10
    assert paginated['current_page'] == 1
    assert paginated['last_page'] == 3
    assert len(paginated['data']) == 10


def test_model_exists_and_doesnt_exist(connection):
    User._connection = connection
    
    User.create({'name': 'Test User', 'email': 'test@example.com', 'age': 25})
    
    assert User.where('name', 'Test User').exists() is True
    assert User.where('name', 'Nonexistent User').doesnt_exist() is True


def test_has_one_relationship(connection):
    User._connection = connection
    Phone._connection = connection
    
    user = User.create({'name': 'John Doe', 'email': 'john@example.com', 'age': 30})
    phone = Phone.create({'number': '555-1234', 'user_id': user.get_key()})
    
    user_phone = user.phone().get_results()
    
    assert user_phone is not None
    assert user_phone.number == '555-1234'
    assert user_phone.user_id == user.get_key()


def test_has_many_relationship(connection):
    User._connection = connection
    Post._connection = connection
    
    user = User.create({'name': 'Author', 'email': 'author@example.com', 'age': 30})
    post1 = Post.create({'title': 'Post 1', 'body': 'Content 1', 'user_id': user.get_key()})
    post2 = Post.create({'title': 'Post 2', 'body': 'Content 2', 'user_id': user.get_key()})
    
    user_posts = user.posts().get_results()
    
    assert user_posts.count() == 2
    assert all(post.user_id == user.get_key() for post in user_posts)


def test_belongs_to_many_relationship(connection):
    User._connection = connection
    Role._connection = connection
    
    user = User.create({'name': 'John Doe', 'email': 'john@example.com', 'age': 30})
    role1 = Role.create({'name': 'Admin'})
    role2 = Role.create({'name': 'Editor'})
    
    connection.table('role_user').insert({'user_id': user.get_key(), 'role_id': role1.get_key()})
    connection.table('role_user').insert({'user_id': user.get_key(), 'role_id': role2.get_key()})
    
    user_roles = user.roles().get_results()
    
    assert user_roles.count() == 2
    role_names = [role.name for role in user_roles]
    assert 'Admin' in role_names
    assert 'Editor' in role_names


def test_nested_relationships(connection):
    User._connection = connection
    Post._connection = connection
    Comment._connection = connection
    
    user = User.create({'name': 'Author', 'email': 'author@example.com', 'age': 30})
    post = Post.create({'title': 'Test Post', 'body': 'Content', 'user_id': user.get_key()})
    comment1 = Comment.create({'content': 'Great post!', 'post_id': post.get_key()})
    comment2 = Comment.create({'content': 'Thanks for sharing', 'post_id': post.get_key()})
    
    post_comments = post.comments().get_results()
    
    assert post_comments.count() == 2
    assert all(comment.post_id == post.get_key() for comment in post_comments)
