"""
Tests for Environment Variable Management
"""

import os
import tempfile
from pathlib import Path

import pytest

from larapy.config.environment import Environment, env


class TestEnvironmentLoading:
    """Test environment file loading."""

    def test_load_returns_false_when_file_doesnt_exist(self):
        """Test load returns False when .env file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Environment.load(tmpdir)
            assert result is False

    def test_load_returns_true_when_file_exists(self):
        """Test load returns True when .env file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('APP_NAME=Larapy\n')
            
            result = Environment.load(tmpdir)
            assert result is True

    def test_load_sets_environment_variables(self):
        """Test load sets environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('TEST_VAR=test_value\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('TEST_VAR') == 'test_value'
            
            del os.environ['TEST_VAR']

    def test_load_handles_multiple_variables(self):
        """Test loading multiple environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'VAR1=value1\n'
                'VAR2=value2\n'
                'VAR3=value3\n'
            )
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR1') == 'value1'
            assert os.environ.get('VAR2') == 'value2'
            assert os.environ.get('VAR3') == 'value3'
            
            for key in ['VAR1', 'VAR2', 'VAR3']:
                del os.environ[key]

    def test_load_skips_comments(self):
        """Test loading skips comment lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                '# This is a comment\n'
                'VAR1=value1\n'
                '# Another comment\n'
                'VAR2=value2\n'
            )
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR1') == 'value1'
            assert os.environ.get('VAR2') == 'value2'
            
            del os.environ['VAR1']
            del os.environ['VAR2']

    def test_load_skips_empty_lines(self):
        """Test loading skips empty lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'VAR1=value1\n'
                '\n'
                'VAR2=value2\n'
                '\n'
            )
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR1') == 'value1'
            assert os.environ.get('VAR2') == 'value2'
            
            del os.environ['VAR1']
            del os.environ['VAR2']

    def test_load_doesnt_override_existing_variables(self):
        """Test load doesn't override existing environment variables."""
        os.environ['EXISTING_VAR'] = 'original'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('EXISTING_VAR=new_value\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('EXISTING_VAR') == 'original'
            
            del os.environ['EXISTING_VAR']

    def test_load_custom_filename(self):
        """Test loading from custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env.testing'
            env_file.write_text('TEST_VAR=test\n')
            
            result = Environment.load(tmpdir, '.env.testing')
            assert result is True
            assert os.environ.get('TEST_VAR') == 'test'
            
            del os.environ['TEST_VAR']

    def test_file_path_returns_loaded_file_path(self):
        """Test file_path returns the path to loaded file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('VAR=value\n')
            
            Environment.load(tmpdir)
            assert Environment.file_path() == env_file
            
            del os.environ['VAR']


class TestEnvironmentValueParsing:
    """Test environment value parsing and type casting."""

    def test_parse_double_quoted_values(self):
        """Test parsing double-quoted values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('VAR="quoted value"\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR') == 'quoted value'
            
            del os.environ['VAR']

    def test_parse_single_quoted_values(self):
        """Test parsing single-quoted values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text("VAR='quoted value'\n")
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR') == 'quoted value'
            
            del os.environ['VAR']

    def test_parse_unquoted_values(self):
        """Test parsing unquoted values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('VAR=unquoted\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR') == 'unquoted'
            
            del os.environ['VAR']

    def test_parse_values_with_equals_sign(self):
        """Test parsing values containing equals signs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('VAR=value=with=equals\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR') == 'value=with=equals'
            
            del os.environ['VAR']

    def test_parse_empty_values(self):
        """Test parsing empty values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('VAR=\n')
            
            Environment.load(tmpdir)
            assert os.environ.get('VAR') == ''
            
            del os.environ['VAR']


class TestEnvironmentGet:
    """Test environment variable retrieval."""

    def test_get_existing_variable(self):
        """Test getting an existing environment variable."""
        os.environ['TEST_VAR'] = 'test_value'
        assert Environment.get('TEST_VAR') == 'test_value'
        del os.environ['TEST_VAR']

    def test_get_nonexistent_variable_returns_default(self):
        """Test getting nonexistent variable returns default."""
        assert Environment.get('NONEXISTENT', 'default') == 'default'

    def test_get_with_callable_default(self):
        """Test default value can be callable."""
        assert Environment.get('NONEXISTENT', lambda: 'computed') == 'computed'

    def test_get_casts_true(self):
        """Test 'true' is cast to boolean True."""
        os.environ['BOOL_VAR'] = 'true'
        assert Environment.get('BOOL_VAR') is True
        del os.environ['BOOL_VAR']

    def test_get_casts_false(self):
        """Test 'false' is cast to boolean False."""
        os.environ['BOOL_VAR'] = 'false'
        assert Environment.get('BOOL_VAR') is False
        del os.environ['BOOL_VAR']

    def test_get_casts_null(self):
        """Test 'null' is cast to None."""
        os.environ['NULL_VAR'] = 'null'
        assert Environment.get('NULL_VAR') is None
        del os.environ['NULL_VAR']

    def test_get_casts_none(self):
        """Test 'none' is cast to None."""
        os.environ['NULL_VAR'] = 'none'
        assert Environment.get('NULL_VAR') is None
        del os.environ['NULL_VAR']

    def test_get_casts_empty(self):
        """Test 'empty' is cast to empty string."""
        os.environ['EMPTY_VAR'] = 'empty'
        assert Environment.get('EMPTY_VAR') == ''
        del os.environ['EMPTY_VAR']

    def test_get_case_insensitive_casting(self):
        """Test type casting is case-insensitive."""
        os.environ['BOOL1'] = 'TRUE'
        os.environ['BOOL2'] = 'False'
        os.environ['NULL1'] = 'NULL'
        os.environ['NULL2'] = 'None'
        
        assert Environment.get('BOOL1') is True
        assert Environment.get('BOOL2') is False
        assert Environment.get('NULL1') is None
        assert Environment.get('NULL2') is None
        
        for key in ['BOOL1', 'BOOL2', 'NULL1', 'NULL2']:
            del os.environ[key]

    def test_get_returns_string_for_non_special_values(self):
        """Test non-special values are returned as strings."""
        os.environ['STR_VAR'] = 'regular_value'
        assert Environment.get('STR_VAR') == 'regular_value'
        del os.environ['STR_VAR']


class TestEnvironmentPut:
    """Test environment variable setting."""

    def test_put_sets_variable(self):
        """Test put sets environment variable."""
        Environment.put('NEW_VAR', 'new_value')
        assert os.environ.get('NEW_VAR') == 'new_value'
        del os.environ['NEW_VAR']

    def test_put_converts_to_string(self):
        """Test put converts values to strings."""
        Environment.put('INT_VAR', 123)
        assert os.environ.get('INT_VAR') == '123'
        del os.environ['INT_VAR']

    def test_put_overwrites_existing(self):
        """Test put overwrites existing variable."""
        os.environ['VAR'] = 'old'
        Environment.put('VAR', 'new')
        assert os.environ.get('VAR') == 'new'
        del os.environ['VAR']


class TestEnvironmentForget:
    """Test environment variable removal."""

    def test_forget_removes_variable(self):
        """Test forget removes environment variable."""
        os.environ['VAR'] = 'value'
        Environment.forget('VAR')
        assert 'VAR' not in os.environ

    def test_forget_handles_nonexistent_variable(self):
        """Test forget handles nonexistent variable gracefully."""
        Environment.forget('NONEXISTENT')

    def test_forget_multiple_times(self):
        """Test forget can be called multiple times."""
        os.environ['VAR'] = 'value'
        Environment.forget('VAR')
        Environment.forget('VAR')
        assert 'VAR' not in os.environ


class TestEnvironmentHas:
    """Test environment variable existence check."""

    def test_has_returns_true_for_existing(self):
        """Test has returns True for existing variable."""
        os.environ['VAR'] = 'value'
        assert Environment.has('VAR') is True
        del os.environ['VAR']

    def test_has_returns_false_for_nonexistent(self):
        """Test has returns False for nonexistent variable."""
        assert Environment.has('NONEXISTENT') is False

    def test_has_returns_true_for_empty_value(self):
        """Test has returns True even for empty value."""
        os.environ['EMPTY'] = ''
        assert Environment.has('EMPTY') is True
        del os.environ['EMPTY']


class TestEnvFunction:
    """Test env() helper function."""

    def test_env_function_gets_variable(self):
        """Test env() function gets environment variable."""
        os.environ['VAR'] = 'value'
        assert env('VAR') == 'value'
        del os.environ['VAR']

    def test_env_function_returns_default(self):
        """Test env() function returns default."""
        assert env('NONEXISTENT', 'default') == 'default'

    def test_env_function_casts_values(self):
        """Test env() function casts special values."""
        os.environ['BOOL'] = 'true'
        os.environ['NULL'] = 'null'
        
        assert env('BOOL') is True
        assert env('NULL') is None
        
        del os.environ['BOOL']
        del os.environ['NULL']


class TestEnvironmentComplexScenarios:
    """Test complex real-world scenarios."""

    def test_load_database_configuration(self):
        """Test loading database configuration from .env."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'DB_CONNECTION=mysql\n'
                'DB_HOST=localhost\n'
                'DB_PORT=3306\n'
                'DB_DATABASE=larapy\n'
                'DB_USERNAME=root\n'
                'DB_PASSWORD=secret\n'
            )
            
            Environment.load(tmpdir)
            
            assert env('DB_CONNECTION') == 'mysql'
            assert env('DB_HOST') == 'localhost'
            assert env('DB_PORT') == '3306'
            assert env('DB_DATABASE') == 'larapy'
            assert env('DB_USERNAME') == 'root'
            assert env('DB_PASSWORD') == 'secret'
            
            for key in ['DB_CONNECTION', 'DB_HOST', 'DB_PORT', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD']:
                del os.environ[key]

    def test_load_application_configuration(self):
        """Test loading application configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'APP_NAME=Larapy\n'
                'APP_ENV=production\n'
                'APP_DEBUG=false\n'
                'APP_URL=https://example.com\n'
            )
            
            Environment.load(tmpdir)
            
            assert env('APP_NAME') == 'Larapy'
            assert env('APP_ENV') == 'production'
            assert env('APP_DEBUG') is False
            assert env('APP_URL') == 'https://example.com'
            
            for key in ['APP_NAME', 'APP_ENV', 'APP_DEBUG', 'APP_URL']:
                del os.environ[key]

    def test_environment_with_mixed_formatting(self):
        """Test loading environment with various formatting styles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                '# Application Configuration\n'
                'APP_NAME="My Application"\n'
                "APP_ENV='production'\n"
                'APP_DEBUG=true\n'
                '\n'
                '# Database Configuration\n'
                'DB_HOST=localhost\n'
                'DB_PASSWORD=\n'
                'DB_ENABLED=null\n'
            )
            
            Environment.load(tmpdir)
            
            assert env('APP_NAME') == 'My Application'
            assert env('APP_ENV') == 'production'
            assert env('APP_DEBUG') is True
            assert env('DB_HOST') == 'localhost'
            assert env('DB_PASSWORD') == ''
            assert env('DB_ENABLED') is None
            
            for key in ['APP_NAME', 'APP_ENV', 'APP_DEBUG', 'DB_HOST', 'DB_PASSWORD', 'DB_ENABLED']:
                if key in os.environ:
                    del os.environ[key]

    def test_runtime_environment_modifications(self):
        """Test modifying environment at runtime."""
        os.environ['ORIGINAL'] = 'value'
        
        assert env('ORIGINAL') == 'value'
        
        Environment.put('RUNTIME', 'added')
        assert env('RUNTIME') == 'added'
        
        Environment.forget('ORIGINAL')
        assert env('ORIGINAL', 'missing') == 'missing'
        
        if 'RUNTIME' in os.environ:
            del os.environ['RUNTIME']

    def test_environment_precedence(self):
        """Test environment variable precedence."""
        os.environ['PRECEDENCE_TEST'] = 'system_value'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('PRECEDENCE_TEST=file_value\n')
            
            Environment.load(tmpdir)
            
            assert env('PRECEDENCE_TEST') == 'system_value'
            
            del os.environ['PRECEDENCE_TEST']
