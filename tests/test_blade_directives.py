"""
Tests for Blade Directives

Comprehensive tests for all Blade-like template directives including
authorization, conditionals, loops, and custom directives.
"""

import unittest
from larapy.views.compiler import Compiler


class TestAuthorizationDirectives(unittest.TestCase):
    """Test authorization directives (@auth, @guest, @can, @cannot)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_auth_directive_without_guard(self):
        """Test @auth directive without guard parameter."""
        template = """
@auth
    <p>User is authenticated</p>
@endauth
"""
        code = self.compiler.compile(template)
        
        assert "__auth__" in code
        assert "check" in code
        assert "if " in code
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context_authenticated = {
            '__auth__': {
                'check': lambda: True
            }
        }
        result = exec_globals['render'](context_authenticated)
        assert "User is authenticated" in result
        
        context_guest = {
            '__auth__': {
                'check': lambda: False
            }
        }
        result = exec_globals['render'](context_guest)
        assert "User is authenticated" not in result
    
    def test_auth_directive_with_guard(self):
        """Test @auth directive with specific guard."""
        template = """
@auth('admin')
    <p>Admin user authenticated</p>
@endauth
"""
        code = self.compiler.compile(template)
        
        assert "admin" in code
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context = {
            '__auth__': {
                'admin': {
                    'check': lambda: True
                }
            }
        }
        result = exec_globals['render'](context)
        assert "Admin user authenticated" in result
    
    def test_guest_directive(self):
        """Test @guest directive for unauthenticated users."""
        template = """
@guest
    <p>Please log in</p>
@endguest
"""
        code = self.compiler.compile(template)
        
        assert "guest" in code
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context_guest = {
            '__auth__': {
                'guest': lambda: True
            }
        }
        result = exec_globals['render'](context_guest)
        assert "Please log in" in result
        
        context_authenticated = {
            '__auth__': {
                'guest': lambda: False
            }
        }
        result = exec_globals['render'](context_authenticated)
        assert "Please log in" not in result
    
    def test_auth_and_guest_combined(self):
        """Test @auth and @guest directives in same template."""
        template = """
@auth
    <p>Welcome back, user!</p>
@endauth
@guest
    <p>Please register or log in</p>
@endguest
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context_authenticated = {
            '__auth__': {
                'check': lambda: True,
                'guest': lambda: False
            }
        }
        result = exec_globals['render'](context_authenticated)
        assert "Welcome back" in result
        assert "Please register" not in result
        
        context_guest = {
            '__auth__': {
                'check': lambda: False,
                'guest': lambda: True
            }
        }
        result = exec_globals['render'](context_guest)
        assert "Welcome back" not in result
        assert "Please register" in result


class TestConditionalDirectives(unittest.TestCase):
    """Test conditional directives (@if, @unless, @isset, @empty)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_if_directive(self):
        """Test @if directive with simple condition."""
        template = """
@if(user_count > 0)
    <p>There are {{ user_count }} users</p>
@endif
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context_with_users = {'user_count': 5}
        result = exec_globals['render'](context_with_users)
        assert "There are 5 users" in result
        
        context_no_users = {'user_count': 0}
        result = exec_globals['render'](context_no_users)
        assert "There are" not in result
    
    def test_if_elseif_else_directive(self):
        """Test @if, @elseif, @else directive chain."""
        template = """
@if(score >= 90)
    <p>Grade: A</p>
@elseif(score >= 80)
    <p>Grade: B</p>
@elseif(score >= 70)
    <p>Grade: C</p>
@else
    <p>Grade: F</p>
@endif
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        assert "Grade: A" in exec_globals['render']({'score': 95})
        assert "Grade: B" in exec_globals['render']({'score': 85})
        assert "Grade: C" in exec_globals['render']({'score': 75})
        assert "Grade: F" in exec_globals['render']({'score': 65})
    
    def test_unless_directive(self):
        """Test @unless directive (opposite of @if)."""
        template = """
@unless(user_logged_in)
    <p>Please log in to continue</p>
@endunless
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        result = exec_globals['render']({'user_logged_in': False})
        assert "Please log in" in result
        
        result = exec_globals['render']({'user_logged_in': True})
        assert "Please log in" not in result
    
    def test_isset_directive(self):
        """Test @isset directive for checking variable existence."""
        template = """
@isset(user_name)
    <p>Hello, {{ user_name }}!</p>
@endisset
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context_with_name = {'user_name': 'John'}
        result = exec_globals['render'](context_with_name)
        assert "Hello, John!" in result
        
        context_without_name = {}
        result = exec_globals['render'](context_without_name)
        assert "Hello," not in result
    
    def test_empty_directive(self):
        """Test @empty directive for checking empty collections."""
        template = """
@empty(items)
    <p>No items found</p>
@endempty
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        result = exec_globals['render']({'items': []})
        assert "No items found" in result
        
        result = exec_globals['render']({'items': [1, 2, 3]})
        assert "No items found" not in result


class TestLoopDirectives(unittest.TestCase):
    """Test loop directives (@foreach, @for, @while)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_foreach_directive(self):
        """Test @foreach directive with list iteration."""
        template = """
@foreach(users as user)
    <p>User: {{ user }}</p>
@endforeach
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context = {'users': ['Alice', 'Bob', 'Charlie']}
        result = exec_globals['render'](context)
        
        assert "User: Alice" in result
        assert "User: Bob" in result
        assert "User: Charlie" in result
    
    def test_foreach_with_dict(self):
        """Test @foreach with dictionary iteration."""
        template = """
@foreach(user_data as key, value)
    <p>{{ key }}: {{ value }}</p>
@endforeach
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context = {
            'user_data': {
                'name': 'John',
                'age': 30,
                'city': 'New York'
            }
        }
        result = exec_globals['render'](context)
        
        assert "name: John" in result
        assert "age: 30" in result
        assert "city: New York" in result
    
    def test_for_directive(self):
        """Test @for directive with range."""
        template = """
@for(i in range(1, 4))
    <p>Item {{ i }}</p>
@endfor
"""
        code = self.compiler.compile(template)
        
        exec_globals = {'range': range}
        exec(code, exec_globals)
        
        result = exec_globals['render']({})
        
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
    
    def test_while_directive(self):
        """Test @while directive code generation."""
        template = """
@while(counter < 3)
    <p>Count: {{ counter }}</p>
@endwhile
"""
        code = self.compiler.compile(template)
        
        assert "while " in code
        assert "__context__.get('counter')" in code
        assert "< 3" in code
    
    def test_break_directive(self):
        """Test @break directive in loop."""
        template = """
@foreach(numbers as num)
    @if(num > 5)
        @break
    @endif
    <p>{{ num }}</p>
@endforeach
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context = {'numbers': [1, 2, 3, 6, 7, 8]}
        result = exec_globals['render'](context)
        
        assert "<p>1</p>" in result
        assert "<p>3</p>" in result
        assert "<p>6</p>" not in result
    
    def test_continue_directive(self):
        """Test @continue directive in loop."""
        template = """
@foreach(numbers as num)
    @if(num == 3)
        @continue
    @endif
    <p>{{ num }}</p>
@endforeach
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        context = {'numbers': [1, 2, 3, 4, 5]}
        result = exec_globals['render'](context)
        
        assert "<p>1</p>" in result
        assert "<p>2</p>" in result
        assert "<p>3</p>" not in result
        assert "<p>4</p>" in result


class TestTemplateInheritanceDirectives(unittest.TestCase):
    """Test template inheritance directives (@extends, @section, @yield)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_section_directive(self):
        """Test @section directive captures content."""
        template = """
@section('content')
    <h1>Page Content</h1>
    <p>This is the main content.</p>
@endsection
"""
        code = self.compiler.compile(template)
        
        assert 'content' in self.compiler.sections
        assert '<h1>Page Content</h1>' in self.compiler.sections['content']
    
    def test_yield_directive(self):
        """Test @yield directive for rendering sections."""
        template = """
<html>
    <body>
        @yield('content')
    </body>
</html>
"""
        code = self.compiler.compile(template)
        
        assert "content" in code
    
    def test_parent_directive(self):
        """Test @parent directive is captured in section."""
        template = """
@section('sidebar')
    @parent
    <p>Additional sidebar content</p>
@endsection
"""
        code = self.compiler.compile(template)
        
        assert 'sidebar' in self.compiler.sections
        assert '@parent' in self.compiler.sections['sidebar'] or 'Additional sidebar content' in self.compiler.sections['sidebar']


class TestIncludeDirectives(unittest.TestCase):
    """Test include directives (@include)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_include_directive(self):
        """Test @include directive for including partials."""
        template = """
<div class="header">
    @include('partials.navbar')
</div>
"""
        code = self.compiler.compile(template)
        
        assert "navbar" in code or "include" in code


class TestComplexDirectiveScenarios(unittest.TestCase):
    """Test complex scenarios with multiple directives."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compiler = Compiler()
    
    def test_nested_conditionals(self):
        """Test nested @if directives."""
        template = """
@if(user)
    @if(user.is_admin)
        <p>Admin Panel</p>
    @else
        <p>User Dashboard</p>
    @endif
@endif
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        class User:
            def __init__(self, is_admin):
                self.is_admin = is_admin
        
        context_admin = {'user': User(is_admin=True)}
        result = exec_globals['render'](context_admin)
        assert "Admin Panel" in result
        
        context_user = {'user': User(is_admin=False)}
        result = exec_globals['render'](context_user)
        assert "User Dashboard" in result
    
    def test_loop_with_conditionals(self):
        """Test @foreach with @if inside."""
        template = """
@foreach(users as user)
    @if(user.active)
        <p>Active: {{ user.name }}</p>
    @else
        <p>Inactive: {{ user.name }}</p>
    @endif
@endforeach
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        class User:
            def __init__(self, name, active):
                self.name = name
                self.active = active
        
        context = {
            'users': [
                User('Alice', True),
                User('Bob', False),
                User('Charlie', True)
            ]
        }
        result = exec_globals['render'](context)
        
        assert "Active: Alice" in result
        assert "Inactive: Bob" in result
        assert "Active: Charlie" in result
    
    def test_auth_with_foreach(self):
        """Test @auth directive containing @foreach."""
        template = """
@auth
    <h2>Your Items:</h2>
    @foreach(items as item)
        <li>{{ item.name }}</li>
    @endforeach
@endauth
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        class Item:
            def __init__(self, name):
                self.name = name
        
        context_authenticated = {
            '__auth__': {
                'check': lambda: True
            },
            'items': [
                Item('Book'),
                Item('Pen'),
                Item('Notebook')
            ]
        }
        result = exec_globals['render'](context_authenticated)
        
        assert "Your Items:" in result
        assert "<li>Book</li>" in result
        assert "<li>Pen</li>" in result
    
    def test_real_world_user_profile_template(self):
        """Test realistic user profile template with multiple directives."""
        template = """
<div class="profile">
    @auth
        <h1>Welcome, {{ user.name }}!</h1>
        
        @if(user.is_premium)
            <span class="badge">Premium Member</span>
        @endif
        
        <h2>Your Posts:</h2>
        @empty(posts)
            <p>No posts yet. Create your first post!</p>
        @endempty
        
        @foreach(posts as post)
            <article>
                <h3>{{ post.title }}</h3>
                <p>{{ post.excerpt }}</p>
                @if(post.published)
                    <span class="status">Published</span>
                @else
                    <span class="status draft">Draft</span>
                @endif
            </article>
        @endforeach
    @endauth
    
    @guest
        <h1>Welcome, Guest!</h1>
        <p>Please log in to see your profile.</p>
    @endguest
</div>
"""
        code = self.compiler.compile(template)
        
        exec_globals = {}
        exec(code, exec_globals)
        
        class User:
            def __init__(self, name, is_premium):
                self.name = name
                self.is_premium = is_premium
        
        class Post:
            def __init__(self, title, excerpt, published):
                self.title = title
                self.excerpt = excerpt
                self.published = published
        
        context_authenticated = {
            '__auth__': {
                'check': lambda: True,
                'guest': lambda: False
            },
            'user': User('John Doe', True),
            'posts': [
                Post('My First Post', 'This is my first post...', True),
                Post('Draft Article', 'Work in progress...', False)
            ]
        }
        result = exec_globals['render'](context_authenticated)
        
        assert "Welcome, John Doe!" in result
        assert "Premium Member" in result
        assert "My First Post" in result
        assert "Published" in result
        assert "Draft" in result
        assert "Please log in" not in result
        
        context_guest = {
            '__auth__': {
                'check': lambda: False,
                'guest': lambda: True
            }
        }
        result = exec_globals['render'](context_guest)
        
        assert "Welcome, Guest!" in result
        assert "Please log in" in result
        assert "John Doe" not in result


if __name__ == '__main__':
    unittest.main()
