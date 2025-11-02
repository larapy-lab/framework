import pytest
from larapy.database.orm.model import Model
from larapy.database.orm.collection import Collection
from larapy.database.connection import Connection
from datetime import datetime


class User(Model):
    _table = 'users'
    _fillable = ['name', 'email']
    _timestamps = False
    
    def profile(self):
        return self.has_one(Profile)
    
    def posts(self):
        return self.has_many(Post)
    
    def roles(self):
        return self.belongs_to_many(Role, 'role_user')


class Profile(Model):
    _table = 'profiles'
    _fillable = ['user_id', 'bio', 'avatar']
    _timestamps = False
    
    def user(self):
        return self.belongs_to(User)


class Post(Model):
    _table = 'posts'
    _fillable = ['user_id', 'title', 'content']
    _timestamps = False
    
    def author(self):
        return self.belongs_to(User, 'user_id')
    
    def comments(self):
        return self.has_many(Comment)


class Comment(Model):
    _table = 'comments'
    _fillable = ['post_id', 'user_id', 'content']
    _timestamps = False
    
    def post(self):
        return self.belongs_to(Post)
    
    def user(self):
        return self.belongs_to(User)


class Role(Model):
    _table = 'roles'
    _fillable = ['name']
    _timestamps = False
    
    def users(self):
        return self.belongs_to_many(User, 'role_user')


@pytest.fixture
def db_connection():
    config = {
        'driver': 'sqlite',
        'database': ':memory:'
    }
    connection = Connection(config)
    connection.connect()
    
    connection.statement('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            email VARCHAR(255)
        )
    ''')
    
    connection.statement('''
        CREATE TABLE profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bio TEXT,
            avatar VARCHAR(255)
        )
    ''')
    
    connection.statement('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title VARCHAR(255),
            content TEXT
        )
    ''')
    
    connection.statement('''
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            content TEXT
        )
    ''')
    
    connection.statement('''
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255)
        )
    ''')
    
    connection.statement('''
        CREATE TABLE role_user (
            role_id INTEGER,
            user_id INTEGER,
            expires_at VARCHAR(255)
        )
    ''')
    
    yield connection


class TestHasOneRelationship:
    
    def test_has_one_basic(self, db_connection):
        User._connection = db_connection
        Profile._connection = db_connection
        
        user = User({'name': 'John Doe', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        profile = Profile({'user_id': user.id, 'bio': 'Developer', 'avatar': 'avatar.jpg'}, db_connection)
        profile.save()
        
        user_with_profile = User.find(user.id)
        
        relation = user_with_profile.profile()
        loaded_profile = relation.get_results()
        
        assert loaded_profile is not None
        assert loaded_profile.bio == 'Developer'
        assert loaded_profile.user_id == user.id
    
    def test_has_one_returns_none_when_not_found(self, db_connection):
        user = User({'name': 'Jane Doe', 'email': 'jane@example.com'}, db_connection)
        user.save()
        
        user_without_profile = User.find(user.id)
        user_without_profile._connection = db_connection
        
        loaded_profile = user_without_profile.profile().get_results()
        
        assert loaded_profile is None
    
    def test_has_one_create(self, db_connection):
        user = User({'name': 'Alice', 'email': 'alice@example.com'}, db_connection)
        user.save()
        
        user._connection = db_connection
        profile = user.profile().create({'bio': 'Designer', 'avatar': 'alice.jpg'})
        
        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.bio == 'Designer'
    
    def test_has_one_save(self, db_connection):
        user = User({'name': 'Bob', 'email': 'bob@example.com'}, db_connection)
        user.save()
        
        user._connection = db_connection
        profile = Profile({'bio': 'Manager', 'avatar': 'bob.jpg'}, db_connection)
        user.profile().save(profile)
        
        assert profile.id is not None
        assert profile.user_id == user.id


class TestHasManyRelationship:
    
    def test_has_many_basic(self, db_connection):
        user = User({'name': 'John Doe', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        Post({'user_id': user.id, 'title': 'First Post', 'content': 'Content 1'}, db_connection).save()
        Post({'user_id': user.id, 'title': 'Second Post', 'content': 'Content 2'}, db_connection).save()
        
        user_with_posts = User.find(user.id)
        user_with_posts._connection = db_connection
        
        posts = user_with_posts.posts().get_results()
        
        assert isinstance(posts, Collection)
        assert posts.count() == 2
        assert posts.first().title == 'First Post'
    
    def test_has_many_returns_empty_collection(self, db_connection):
        user = User({'name': 'Jane Doe', 'email': 'jane@example.com'}, db_connection)
        user.save()
        
        user_without_posts = User.find(user.id)
        user_without_posts._connection = db_connection
        
        posts = user_without_posts.posts().get_results()
        
        assert isinstance(posts, Collection)
        assert posts.is_empty()
    
    def test_has_many_create(self, db_connection):
        user = User({'name': 'Alice', 'email': 'alice@example.com'}, db_connection)
        user.save()
        
        user._connection = db_connection
        post = user.posts().create({'title': 'New Post', 'content': 'New Content'})
        
        assert post.id is not None
        assert post.user_id == user.id
        assert post.title == 'New Post'
    
    def test_has_many_create_many(self, db_connection):
        user = User({'name': 'Bob', 'email': 'bob@example.com'}, db_connection)
        user.save()
        
        user._connection = db_connection
        posts = user.posts().create_many([
            {'title': 'Post 1', 'content': 'Content 1'},
            {'title': 'Post 2', 'content': 'Content 2'}
        ])
        
        assert posts.count() == 2
        assert all(post.user_id == user.id for post in posts.all())
    
    def test_has_many_where_constraint(self, db_connection):
        user = User({'name': 'Charlie', 'email': 'charlie@example.com'}, db_connection)
        user.save()
        
        Post({'user_id': user.id, 'title': 'Published', 'content': 'Content'}, db_connection).save()
        Post({'user_id': user.id, 'title': 'Draft', 'content': 'Content'}, db_connection).save()
        
        user_with_posts = User.find(user.id)
        user_with_posts._connection = db_connection
        
        published_posts = user_with_posts.posts().where('title', 'Published').get()
        
        assert published_posts.count() == 1
        assert published_posts.first().title == 'Published'


class TestBelongsToRelationship:
    
    def test_belongs_to_basic(self, db_connection):
        user = User({'name': 'John Doe', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        post = Post({'user_id': user.id, 'title': 'My Post', 'content': 'Content'}, db_connection)
        post.save()
        
        post_with_author = Post({}, db_connection)
        post_with_author = post_with_author.instance_query().find(post.id)
        
        author = post_with_author.author().get_results()
        
        assert author is not None
        assert author.id == user.id
        assert author.name == 'John Doe'
    
    def test_belongs_to_returns_none_when_not_found(self, db_connection):
        post = Post({'user_id': 999, 'title': 'Orphan Post', 'content': 'Content'}, db_connection)
        post.save()
        
        post_without_author = Post({}, db_connection)
        post_without_author = post_without_author.instance_query().find(post.id)
        
        author = post_without_author.author().get_results()
        
        assert author is None
    
    def test_belongs_to_associate(self, db_connection):
        user = User({'name': 'Alice', 'email': 'alice@example.com'}, db_connection)
        user.save()
        
        post = Post({'title': 'New Post', 'content': 'Content'}, db_connection)
        post.save()
        
        post._connection = db_connection
        post.author().associate(user)
        post.save()
        
        assert post.user_id == user.id
    
    def test_belongs_to_dissociate(self, db_connection):
        user = User({'name': 'Bob', 'email': 'bob@example.com'}, db_connection)
        user.save()
        
        post = Post({'user_id': user.id, 'title': 'Post', 'content': 'Content'}, db_connection)
        post.save()
        
        post._connection = db_connection
        post.author().dissociate()
        post.save()
        
        assert post.user_id is None


class TestBelongsToManyRelationship:
    
    def test_belongs_to_many_basic(self, db_connection):
        user = User({'name': 'John Doe', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        admin_role = Role({'name': 'admin'}, db_connection)
        admin_role.save()
        
        editor_role = Role({'name': 'editor'}, db_connection)
        editor_role.save()
        
        db_connection.table('role_user').insert({'role_id': admin_role.id, 'user_id': user.id})
        db_connection.table('role_user').insert({'role_id': editor_role.id, 'user_id': user.id})
        
        user_with_roles = User({}, db_connection)
        user_with_roles = user_with_roles.instance_query().find(user.id)
        
        roles = user_with_roles.roles().get_results()
        
        assert isinstance(roles, Collection)
        assert roles.count() == 2
    
    def test_belongs_to_many_attach(self, db_connection):
        user = User({'name': 'Alice', 'email': 'alice@example.com'}, db_connection)
        user.save()
        
        role = Role({'name': 'moderator'}, db_connection)
        role.save()
        
        user._connection = db_connection
        user.roles().attach(role.id)
        
        roles = user.roles().get_results()
        assert roles.count() == 1
        assert roles.first().id == role.id
    
    def test_belongs_to_many_detach(self, db_connection):
        user = User({'name': 'Bob', 'email': 'bob@example.com'}, db_connection)
        user.save()
        
        role = Role({'name': 'user'}, db_connection)
        role.save()
        
        db_connection.table('role_user').insert({'role_id': role.id, 'user_id': user.id})
        
        user._connection = db_connection
        user.roles().detach(role.id)
        
        roles = user.roles().get_results()
        assert roles.is_empty()
    
    def test_belongs_to_many_sync(self, db_connection):
        user = User({'name': 'Charlie', 'email': 'charlie@example.com'}, db_connection)
        user.save()
        
        role1 = Role({'name': 'admin'}, db_connection)
        role1.save()
        role2 = Role({'name': 'editor'}, db_connection)
        role2.save()
        role3 = Role({'name': 'viewer'}, db_connection)
        role3.save()
        
        user._connection = db_connection
        user.roles().attach([role1.id, role2.id])
        
        changes = user.roles().sync([role2.id, role3.id])
        
        assert role3.id in changes['attached']
        assert role1.id in changes['detached']
        
        roles = user.roles().get_results()
        assert roles.count() == 2
    
    def test_belongs_to_many_toggle(self, db_connection):
        user = User({'name': 'David', 'email': 'david@example.com'}, db_connection)
        user.save()
        
        role = Role({'name': 'guest'}, db_connection)
        role.save()
        
        user._connection = db_connection
        
        changes1 = user.roles().toggle(role.id)
        assert role.id in changes1['attached']
        
        changes2 = user.roles().toggle(role.id)
        assert role.id in changes2['detached']
    
    def test_belongs_to_many_update_existing_pivot(self, db_connection):
        user = User({'name': 'Eve', 'email': 'eve@example.com'}, db_connection)
        user.save()
        
        role = Role({'name': 'premium'}, db_connection)
        role.save()
        
        # Attach with initial attributes
        user._connection = db_connection
        user.roles().attach(role.id, {'expires_at': '2025-01-01'})
        
        # Verify initial pivot data
        roles = user.roles().with_pivot('expires_at').get_results()
        assert roles.first().pivot.expires_at == '2025-01-01'
        
        # Update the pivot
        user.roles().update_existing_pivot(role.id, {'expires_at': '2025-12-31'})
        
        # Verify updated pivot data
        roles = user.roles().with_pivot('expires_at').get_results()
        assert roles.first().pivot.expires_at == '2025-12-31'


class TestEagerLoading:
    
    def test_eager_load_has_one(self, db_connection):
        user1 = User({'name': 'User 1', 'email': 'user1@example.com'}, db_connection)
        user1.save()
        user2 = User({'name': 'User 2', 'email': 'user2@example.com'}, db_connection)
        user2.save()
        
        Profile({'user_id': user1.id, 'bio': 'Bio 1'}, db_connection).save()
        Profile({'user_id': user2.id, 'bio': 'Bio 2'}, db_connection).save()
        
        users = User({}, db_connection).instance_query().with_('profile').get()
        
        assert users.count() == 2
        assert users.first().relation_loaded('profile')
        assert users.first().profile.bio == 'Bio 1'
    
    def test_eager_load_has_many(self, db_connection):
        user1 = User({'name': 'User 1', 'email': 'user1@example.com'}, db_connection)
        user1.save()
        user2 = User({'name': 'User 2', 'email': 'user2@example.com'}, db_connection)
        user2.save()
        
        Post({'user_id': user1.id, 'title': 'Post 1', 'content': 'Content'}, db_connection).save()
        Post({'user_id': user1.id, 'title': 'Post 2', 'content': 'Content'}, db_connection).save()
        Post({'user_id': user2.id, 'title': 'Post 3', 'content': 'Content'}, db_connection).save()
        
        users = User({}, db_connection).instance_query().with_('posts').get()
        
        assert users.count() == 2
        assert users.first().posts.count() == 2
        assert users.last().posts.count() == 1
    
    def test_eager_load_belongs_to(self, db_connection):
        user = User({'name': 'John', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        Post({'user_id': user.id, 'title': 'Post 1', 'content': 'Content'}, db_connection).save()
        Post({'user_id': user.id, 'title': 'Post 2', 'content': 'Content'}, db_connection).save()
        
        posts = Post({}, db_connection).instance_query().with_('author').get()
        
        assert posts.count() == 2
        assert posts.first().relation_loaded('author')
        assert posts.first().author.name == 'John'
    
    def test_eager_load_nested_relationships(self, db_connection):
        user = User({'name': 'John', 'email': 'john@example.com'}, db_connection)
        user.save()
        
        post = Post({'user_id': user.id, 'title': 'Post', 'content': 'Content'}, db_connection)
        post.save()
        
        Comment({'post_id': post.id, 'user_id': user.id, 'content': 'Comment 1'}, db_connection).save()
        Comment({'post_id': post.id, 'user_id': user.id, 'content': 'Comment 2'}, db_connection).save()
        
        users = User({}, db_connection).instance_query().with_('posts.comments').get()
        
        assert users.count() == 1
        assert users.first().posts.count() == 1
        assert users.first().posts.first().comments.count() == 2
    
    def test_lazy_eager_loading(self, db_connection):
        user = User({'name': 'Alice', 'email': 'alice@example.com'}, db_connection)
        user.save()
        
        Post({'user_id': user.id, 'title': 'Post 1', 'content': 'Content'}, db_connection).save()
        
        loaded_user = User({}, db_connection).instance_query().find(user.id)
        
        assert not loaded_user.relation_loaded('posts')
        
        loaded_user.load('posts')
        
        assert loaded_user.relation_loaded('posts')
        assert loaded_user.posts.count() == 1
    
    def test_load_missing(self, db_connection):
        user = User({'name': 'Bob', 'email': 'bob@example.com'}, db_connection)
        user.save()
        
        Profile({'user_id': user.id, 'bio': 'Bio'}, db_connection).save()
        Post({'user_id': user.id, 'title': 'Post', 'content': 'Content'}, db_connection).save()
        
        loaded_user = User({}, db_connection).instance_query().find(user.id)
        loaded_user.load('profile')
        
        assert loaded_user.relation_loaded('profile')
        assert not loaded_user.relation_loaded('posts')
        
        loaded_user.load_missing('profile', 'posts')
        
        assert loaded_user.relation_loaded('profile')
        assert loaded_user.relation_loaded('posts')
        assert loaded_user.posts.count() == 1


class TestComplexScenarios:
    
    def test_blog_system_with_nested_relationships(self, db_connection):
        author = User({'name': 'John Doe', 'email': 'john@example.com'}, db_connection)
        author.save()
        
        commenter = User({'name': 'Jane Doe', 'email': 'jane@example.com'}, db_connection)
        commenter.save()
        
        post = Post({'user_id': author.id, 'title': 'Laravel Tips', 'content': 'Great tips'}, db_connection)
        post.save()
        
        Comment({'post_id': post.id, 'user_id': commenter.id, 'content': 'Nice post!'}, db_connection).save()
        Comment({'post_id': post.id, 'user_id': author.id, 'content': 'Thanks!'}, db_connection).save()
        
        users_with_posts = User({}, db_connection).instance_query().with_('posts.comments').get()
        
        author_with_posts = users_with_posts.where('id', author.id).first()
        assert author_with_posts.posts.count() == 1
        assert author_with_posts.posts.first().comments.count() == 2
        
        first_comment = author_with_posts.posts.first().comments.first()
        first_comment.load('user')
        assert first_comment.user.name == 'Jane Doe'
    
    def test_role_based_access_with_pivot(self, db_connection):
        user = User({'name': 'Admin User', 'email': 'admin@example.com'}, db_connection)
        user.save()
        
        admin_role = Role({'name': 'admin'}, db_connection)
        admin_role.save()
        editor_role = Role({'name': 'editor'}, db_connection)
        editor_role.save()
        
        user.roles().attach([admin_role.id, editor_role.id])
        
        loaded_user = User({}, db_connection).instance_query().find(user.id)
        roles = loaded_user.roles().get_results()
        
        assert roles.count() == 2
        role_names = [role.name for role in roles.all()]
        assert 'admin' in role_names
        assert 'editor' in role_names
