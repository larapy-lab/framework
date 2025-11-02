"""
Tests for Views & Templating System

Tests template engine, compiler, directives, inheritance, and integration.
"""

import os
import pytest
import tempfile
from pathlib import Path

from larapy.views import View, Engine, Compiler
from larapy.http.response import ViewResponse


class TestCompilerBasics:
    """Test basic compiler functionality."""
    
    def test_compiler_instantiation(self):
        """Test compiler can be instantiated."""
        compiler = Compiler()
        assert isinstance(compiler, Compiler)
    
    def test_compile_simple_text(self):
        """Test compiling plain text."""
        compiler = Compiler()
        template = "Hello, World!"
        
        code = compiler.compile(template)
        assert 'def render' in code
        assert 'Hello, World!' in code
    
    def test_compile_variable_interpolation(self):
        """Test variable interpolation."""
        compiler = Compiler()
        template = "Hello, {{ name }}!"
        
        code = compiler.compile(template)
        assert '__context__' in code
        assert 'name' in code
    
    def test_compile_raw_output(self):
        """Test raw HTML output."""
        compiler = Compiler()
        template = "Content: {!! html !!}"
        
        code = compiler.compile(template)
        assert 'html' in code
    
    def test_compile_comments(self):
        """Test comment removal."""
        compiler = Compiler()
        template = "{{-- This is a comment --}}Visible"
        
        code = compiler.compile(template)
        assert 'This is a comment' not in code
        assert 'Visible' in code


class TestEngineBasics:
    """Test template engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.cache_dir = tempfile.mkdtemp()
        self.engine = Engine(
            view_paths=[self.test_dir],
            cache_path=self.cache_dir,
            cache_enabled=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
    
    def test_engine_instantiation(self):
        """Test engine can be instantiated."""
        assert isinstance(self.engine, Engine)
    
    def test_find_template(self):
        """Test finding template by name."""
        path = self.engine.find_template('simple')
        assert path is not None
        assert 'simple.blade.py' in path
    
    def test_find_template_not_found(self):
        """Test finding nonexistent template."""
        path = self.engine.find_template('nonexistent')
        assert path is None
    
    def test_render_simple_template(self):
        """Test rendering simple template."""
        result = self.engine.render('simple', {'name': 'John'})
        assert 'Hello, John!' in result
    
    def test_render_with_empty_context(self):
        """Test rendering with empty context."""
        result = self.engine.render('simple', {})
        assert 'Hello' in result


class TestVariableInterpolation:
    """Test variable interpolation and escaping."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.engine = Engine(view_paths=[self.test_dir], cache_enabled=False)
    
    def test_escaped_output(self):
        """Test escaped HTML output."""
        result = self.engine.render('escaping', {'html': '<script>alert("xss")</script>'})
        assert '&lt;script&gt;' in result
        assert '<script>' not in result or result.count('<script>') <= result.count('&lt;script&gt;')
    
    def test_raw_output(self):
        """Test raw HTML output."""
        result = self.engine.render('escaping', {'html': '<b>bold</b>'})
        assert '<b>bold</b>' in result


class TestConditionals:
    """Test conditional directives."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.engine = Engine(view_paths=[self.test_dir], cache_enabled=False)
    
    def test_if_true(self):
        """Test @if with true condition."""
        result = self.engine.render('conditional', {'show': True})
        assert 'Visible content' in result
        assert 'Hidden content' not in result
    
    def test_if_false(self):
        """Test @if with false condition."""
        result = self.engine.render('conditional', {'show': False})
        assert 'Visible content' not in result
        assert 'Hidden content' in result


class TestLoops:
    """Test loop directives."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.engine = Engine(view_paths=[self.test_dir], cache_enabled=False)
    
    def test_foreach_loop(self):
        """Test @foreach loop."""
        result = self.engine.render('loop', {'items': ['Apple', 'Banana', 'Cherry']})
        assert 'Apple' in result
        assert 'Banana' in result
        assert 'Cherry' in result
        assert result.count('<li>') == 3
    
    def test_foreach_empty(self):
        """Test @foreach with empty array."""
        result = self.engine.render('loop', {'items': []})
        assert '<li>' not in result


class TestComments:
    """Test comment handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.engine = Engine(view_paths=[self.test_dir], cache_enabled=False)
    
    def test_comments_removed(self):
        """Test comments are removed from output."""
        result = self.engine.render('comments', {})
        assert 'This is a comment' not in result
        assert 'should not appear' not in result
        assert 'Visible text' in result


class TestViewFacade:
    """Test View facade."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
    
    def test_view_make(self):
        """Test View.make()."""
        view = View.make('simple', {'name': 'Alice'})
        assert view is not None
        assert view.name == 'simple'
        assert view.data['name'] == 'Alice'
    
    def test_view_render(self):
        """Test rendering view."""
        view = View.make('simple', {'name': 'Bob'})
        result = view.render()
        assert 'Hello, Bob!' in result
    
    def test_view_string_conversion(self):
        """Test view string conversion."""
        view = View.make('simple', {'name': 'Charlie'})
        result = str(view)
        assert 'Hello, Charlie!' in result
    
    def test_view_with_data(self):
        """Test adding data to view."""
        view = View.make('simple')
        view.with_('name', 'Dave')
        result = view.render()
        assert 'Hello, Dave!' in result
    
    def test_view_with_dict(self):
        """Test adding dict data to view."""
        view = View.make('simple')
        view.with_({'name': 'Eve'})
        result = view.render()
        assert 'Hello, Eve!' in result


class TestViewSharedData:
    """Test shared view data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
        View._shared_data = {}
    
    def test_share_data_string(self):
        """Test sharing data with all views."""
        View.share('site_name', 'My Site')
        view = View.make('simple', {'name': 'Frank'})
        assert view.data['site_name'] == 'My Site'
    
    def test_share_data_dict(self):
        """Test sharing dict data."""
        View.share({'site_name': 'My Site', 'version': '1.0'})
        view = View.make('simple')
        assert view.data['site_name'] == 'My Site'
        assert view.data['version'] == '1.0'


class TestViewComposers:
    """Test view composers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
        View._composers = {}
    
    def test_composer_function(self):
        """Test composer with function."""
        def add_timestamp(view):
            view.with_('timestamp', '2025-10-24')
        
        View.composer('simple', add_timestamp)
        view = View.make('simple', {'name': 'Grace'})
        assert view.data['timestamp'] == '2025-10-24'
    
    def test_composer_wildcard(self):
        """Test composer with wildcard pattern."""
        def add_data(view):
            view.with_('composed', True)
        
        View.composer('*', add_data)
        view = View.make('simple')
        assert view.data['composed'] == True


class TestViewCreators:
    """Test view creators."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
        View._creators = {}
    
    def test_creator_function(self):
        """Test creator with function."""
        def init_data(view):
            view.with_('created', True)
        
        View.creator('simple', init_data)
        view = View.make('simple')
        assert view.data['created'] == True


class TestViewResponse:
    """Test view HTTP response."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
    
    def test_view_response_creation(self):
        """Test creating view response."""
        response = ViewResponse('simple', {'name': 'Henry'})
        assert response.status() == 200
        assert 'Hello, Henry!' in response.content()
    
    def test_view_response_status(self):
        """Test view response with custom status."""
        response = ViewResponse('simple', {'name': 'Iris'}, status=201)
        assert response.status() == 201
    
    def test_view_response_headers(self):
        """Test view response headers."""
        response = ViewResponse('simple', {'name': 'Jack'})
        headers = response.getHeaders()
        assert 'Content-Type' in headers
        assert 'text/html' in headers['Content-Type']
    
    def test_view_response_get_data(self):
        """Test getting view data."""
        response = ViewResponse('simple', {'name': 'Kate'})
        data = response.getData()
        assert data['name'] == 'Kate'


class TestCaching:
    """Test template caching."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.cache_dir = tempfile.mkdtemp()
        self.engine = Engine(
            view_paths=[self.test_dir],
            cache_path=self.cache_dir,
            cache_enabled=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
    
    def test_cache_creation(self):
        """Test cache files are created."""
        self.engine.render('simple', {'name': 'Leo'})
        cache_files = os.listdir(self.cache_dir)
        assert len(cache_files) > 0
    
    def test_cache_reuse(self):
        """Test cached templates are reused."""
        self.engine.render('simple', {'name': 'Maya'})
        cache_files_before = len(os.listdir(self.cache_dir))
        
        self.engine.render('simple', {'name': 'Nina'})
        cache_files_after = len(os.listdir(self.cache_dir))
        
        assert cache_files_before == cache_files_after
    
    def test_clear_cache(self):
        """Test clearing cache."""
        self.engine.render('simple', {'name': 'Oscar'})
        assert len(os.listdir(self.cache_dir)) > 0
        
        self.engine.clear_cache()
        assert len(os.listdir(self.cache_dir)) == 0


class TestComplexScenarios:
    """Test complex templating scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        View.configure(view_paths=self.test_dir, cache_enabled=False)
    
    def test_nested_data_access(self):
        """Test accessing nested data."""
        compiler = Compiler()
        template = "User: {{ user.name }}, Email: {{ user.email }}"
        code = compiler.compile(template)
        
        namespace = {'html': __import__('html')}
        exec(code, namespace)
        render_func = namespace['render']
        
        result = render_func({
            'user': {
                'name': 'Paul',
                'email': 'paul@example.com'
            }
        })
        assert 'Paul' in result
        assert 'paul@example.com' in result
    
    def test_multiple_conditionals(self):
        """Test multiple conditional blocks."""
        compiler = Compiler()
        template = """
@if(admin)
    <p>Admin</p>
@elseif(moderator)
    <p>Moderator</p>
@else
    <p>User</p>
@endif
"""
        code = compiler.compile(template)
        namespace = {'html': __import__('html')}
        exec(code, namespace)
        render_func = namespace['render']
        
        result_admin = render_func({'admin': True, 'moderator': False})
        assert 'Admin' in result_admin
        
        result_mod = render_func({'admin': False, 'moderator': True})
        assert 'Moderator' in result_mod
        
        result_user = render_func({'admin': False, 'moderator': False})
        assert 'User' in result_user
    
    def test_nested_loops(self):
        """Test nested loop structures."""
        compiler = Compiler()
        template = """
@foreach(categories as category)
    <h2>{{ category.name }}</h2>
    <ul>
    @foreach(category.items as item)
        <li>{{ item }}</li>
    @endforeach
    </ul>
@endforeach
"""
        code = compiler.compile(template)
        namespace = {'html': __import__('html')}
        exec(code, namespace)
        render_func = namespace['render']
        
        result = render_func({
            'categories': [
                {'name': 'Fruits', 'items': ['Apple', 'Banana']},
                {'name': 'Vegetables', 'items': ['Carrot', 'Broccoli']}
            ]
        })
        assert 'Fruits' in result
        assert 'Apple' in result
        assert 'Vegetables' in result
        assert 'Carrot' in result


class TestErrorHandling:
    """Test error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = os.path.join(os.path.dirname(__file__), 'views')
        self.engine = Engine(view_paths=[self.test_dir], cache_enabled=False)
    
    def test_template_not_found(self):
        """Test error when template not found."""
        with pytest.raises(FileNotFoundError):
            self.engine.render('does_not_exist', {})
    
    def test_render_error(self):
        """Test error during render."""
        compiler = Compiler()
        template = "{{ undefined_var.nonexistent }}"
        code = compiler.compile(template)
        
        namespace = {'html': __import__('html')}
        exec(code, namespace)
        render_func = namespace['render']
        
        result = render_func({})
        assert result is not None
