import pytest
from larapy.database.orm import Model
from larapy.database.orm.collection import Collection


class Country(Model):
    _table = 'countries'
    _fillable = ['name']
    _timestamps = False
    
    def users(self):
        return self.has_many(User)
    
    def posts(self):
        return self.has_many_through(Post, User, 'country_id', 'user_id', 'id', 'id')


class User(Model):
    _table = 'users'
    _fillable = ['name', 'country_id']
    _timestamps = False
    
    def country(self):
        return self.belongs_to(Country, 'country_id')
    
    def posts(self):
        return self.has_many(Post, 'user_id')


class Post(Model):
    _table = 'posts'
    _fillable = ['title', 'content', 'user_id', 'published']
    _casts = {'published': 'bool'}
    _timestamps = False
    
    def user(self):
        return self.belongs_to(User, 'user_id')


@pytest.fixture
def connection():
    from larapy.database import Connection
    
    conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
    conn.connect()
    
    conn.statement('''
        CREATE TABLE countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL
        )
    ''')
    
    conn.statement('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            country_id INTEGER,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    ''')
    
    conn.statement('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            user_id INTEGER,
            published INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    Country._connection = conn
    User._connection = conn
    Post._connection = conn
    
    yield conn
    
    conn.disconnect()


def test_has_many_through_basic_retrieval(connection):
    country = Country.create({'name': 'USA'})
    
    user1 = User.create({'name': 'John', 'country_id': country.get_key()})
    user2 = User.create({'name': 'Jane', 'country_id': country.get_key()})
    
    post1 = Post.create({'title': 'Post 1', 'content': 'Content 1', 'user_id': user1.get_key()})
    post2 = Post.create({'title': 'Post 2', 'content': 'Content 2', 'user_id': user1.get_key()})
    post3 = Post.create({'title': 'Post 3', 'content': 'Content 3', 'user_id': user2.get_key()})
    
    posts = country.posts().get_results()
    
    assert isinstance(posts, Collection)
    assert posts.count() == 3
    assert all(isinstance(post, Post) for post in posts)
    assert {post.title for post in posts} == {'Post 1', 'Post 2', 'Post 3'}


def test_has_many_through_with_no_results(connection):
    country = Country.create({'name': 'Canada'})
    
    posts = country.posts().get_results()
    
    assert isinstance(posts, Collection)
    assert posts.count() == 0


def test_has_many_through_with_users_but_no_posts(connection):
    country = Country.create({'name': 'UK'})
    
    User.create({'name': 'Bob', 'country_id': country.get_key()})
    User.create({'name': 'Alice', 'country_id': country.get_key()})
    
    posts = country.posts().get_results()
    
    assert isinstance(posts, Collection)
    assert posts.count() == 0


def test_has_many_through_with_constraints_on_final_model(connection):
    country = Country.create({'name': 'Germany'})
    
    user = User.create({'name': 'Hans', 'country_id': country.get_key()})
    
    Post.create({'title': 'Published Post', 'content': 'Content', 'user_id': user.get_key(), 'published': True})
    Post.create({'title': 'Draft Post', 'content': 'Content', 'user_id': user.get_key(), 'published': False})
    
    published_posts = country.posts().where('published', True).get_results()
    
    assert published_posts.count() == 1
    assert published_posts[0].title == 'Published Post'


def test_has_many_through_with_ordering(connection):
    country = Country.create({'name': 'France'})
    
    user = User.create({'name': 'Pierre', 'country_id': country.get_key()})
    
    Post.create({'title': 'C Post', 'content': 'Content', 'user_id': user.get_key()})
    Post.create({'title': 'A Post', 'content': 'Content', 'user_id': user.get_key()})
    Post.create({'title': 'B Post', 'content': 'Content', 'user_id': user.get_key()})
    
    posts = country.posts().order_by('title', 'asc').get_results()
    
    assert posts.count() == 3
    assert [post.title for post in posts] == ['A Post', 'B Post', 'C Post']


def test_has_many_through_with_limit(connection):
    country = Country.create({'name': 'Spain'})
    
    user = User.create({'name': 'Carlos', 'country_id': country.get_key()})
    
    for i in range(5):
        Post.create({'title': f'Post {i+1}', 'content': 'Content', 'user_id': user.get_key()})
    
    posts = country.posts().limit(3).get_results()
    
    assert posts.count() == 3


def test_has_many_through_multiple_countries(connection):
    usa = Country.create({'name': 'USA'})
    canada = Country.create({'name': 'Canada'})
    
    usa_user = User.create({'name': 'John', 'country_id': usa.get_key()})
    canada_user = User.create({'name': 'Bob', 'country_id': canada.get_key()})
    
    Post.create({'title': 'USA Post 1', 'content': 'Content', 'user_id': usa_user.get_key()})
    Post.create({'title': 'USA Post 2', 'content': 'Content', 'user_id': usa_user.get_key()})
    Post.create({'title': 'Canada Post', 'content': 'Content', 'user_id': canada_user.get_key()})
    
    usa_posts = usa.posts().get_results()
    canada_posts = canada.posts().get_results()
    
    assert usa_posts.count() == 2
    assert canada_posts.count() == 1
    assert all('USA' in post.title for post in usa_posts)
    assert 'Canada' in canada_posts[0].title


def test_has_many_through_with_multiple_users_per_country(connection):
    country = Country.create({'name': 'Japan'})
    
    user1 = User.create({'name': 'Yuki', 'country_id': country.get_key()})
    user2 = User.create({'name': 'Hiro', 'country_id': country.get_key()})
    user3 = User.create({'name': 'Akira', 'country_id': country.get_key()})
    
    Post.create({'title': 'Yuki Post 1', 'content': 'Content', 'user_id': user1.get_key()})
    Post.create({'title': 'Yuki Post 2', 'content': 'Content', 'user_id': user1.get_key()})
    Post.create({'title': 'Hiro Post', 'content': 'Content', 'user_id': user2.get_key()})
    Post.create({'title': 'Akira Post', 'content': 'Content', 'user_id': user3.get_key()})
    
    posts = country.posts().get_results()
    
    assert posts.count() == 4


def test_has_many_through_query_count_efficiency(connection):
    country = Country.create({'name': 'Italy'})
    
    for i in range(10):
        user = User.create({'name': f'User {i+1}', 'country_id': country.get_key()})
        for j in range(5):
            Post.create({'title': f'Post {j+1} by User {i+1}', 'content': 'Content', 'user_id': user.get_key()})
    
    posts = country.posts().get_results()
    
    assert posts.count() == 50
    assert all(isinstance(post, Post) for post in posts)


def test_has_many_through_attributes_accessible(connection):
    country = Country.create({'name': 'Brazil'})
    
    user = User.create({'name': 'Maria', 'country_id': country.get_key()})
    
    Post.create({'title': 'Test Post', 'content': 'Test Content', 'user_id': user.get_key()})
    
    posts = country.posts().get_results()
    
    assert posts.count() == 1
    post = posts[0]
    assert post.title == 'Test Post'
    assert post.content == 'Test Content'
    assert post.user_id == user.get_key()


def test_has_many_through_with_where_in_constraint(connection):
    country = Country.create({'name': 'Australia'})
    
    user = User.create({'name': 'Jack', 'country_id': country.get_key()})
    
    post1 = Post.create({'title': 'Post 1', 'content': 'Content', 'user_id': user.get_key()})
    post2 = Post.create({'title': 'Post 2', 'content': 'Content', 'user_id': user.get_key()})
    post3 = Post.create({'title': 'Post 3', 'content': 'Content', 'user_id': user.get_key()})
    
    posts = country.posts().where_in('id', [post1.get_key(), post3.get_key()]).get_results()
    
    assert posts.count() == 2
    post_ids = {post.get_key() for post in posts}
    assert post_ids == {post1.get_key(), post3.get_key()}


def test_has_many_through_first_method(connection):
    country = Country.create({'name': 'Mexico'})
    
    user = User.create({'name': 'Juan', 'country_id': country.get_key()})
    
    Post.create({'title': 'First Post', 'content': 'Content', 'user_id': user.get_key()})
    Post.create({'title': 'Second Post', 'content': 'Content', 'user_id': user.get_key()})
    
    first_post = country.posts().order_by('title', 'asc').get_results().first()
    
    assert first_post is not None
    assert first_post.title == 'First Post'


def test_has_many_through_custom_keys(connection):
    connection.statement('''
        CREATE TABLE departments (
            dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name VARCHAR(100) NOT NULL
        )
    ''')
    
    connection.statement('''
        CREATE TABLE employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name VARCHAR(100) NOT NULL,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(dept_id)
        )
    ''')
    
    connection.statement('''
        CREATE TABLE tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_title VARCHAR(200) NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(emp_id)
        )
    ''')
    
    class Department(Model):
        _table = 'departments'
        _primary_key = 'dept_id'
        _fillable = ['dept_name']
        _timestamps = False
        
        def tasks(self):
            return self.has_many_through(
                Task,
                Employee,
                'department_id',
                'employee_id',
                'dept_id',
                'emp_id'
            )
    
    class Employee(Model):
        _table = 'employees'
        _primary_key = 'emp_id'
        _fillable = ['emp_name', 'department_id']
        _timestamps = False
    
    class Task(Model):
        _table = 'tasks'
        _primary_key = 'task_id'
        _fillable = ['task_title', 'employee_id']
        _timestamps = False
    
    Department._connection = connection
    Employee._connection = connection
    Task._connection = connection
    
    dept = Department.create({'dept_name': 'Engineering'})
    emp = Employee.create({'emp_name': 'Alice', 'department_id': dept.get_key()})
    task = Task.create({'task_title': 'Build Feature', 'employee_id': emp.get_key()})
    
    tasks = dept.tasks().get_results()
    
    assert tasks.count() == 1
    assert tasks[0].task_title == 'Build Feature'
