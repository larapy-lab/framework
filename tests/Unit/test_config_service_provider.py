"""
Tests for Config Service Provider
"""

import tempfile
from pathlib import Path

import pytest

from larapy.foundation.application import Application
from larapy.config.config_service_provider import ConfigServiceProvider
from larapy.config.repository import Repository


class TestConfigServiceProviderRegistration:
    """Test configuration service provider registration."""

    def test_registers_config_in_container(self):
        """Test provider registers config in the container."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            
            provider.register()
            
            assert app.bound('config')

    def test_config_is_singleton(self):
        """Test config is registered as a singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            
            provider.register()
            
            config1 = app.make('config')
            config2 = app.make('config')
            
            assert config1 is config2

    def test_config_is_repository_instance(self):
        """Test config is a Repository instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            
            provider.register()
            
            config = app.make('config')
            assert isinstance(config, Repository)


class TestConfigFileLoading:
    """Test loading configuration files."""

    def test_loads_config_file_with_config_variable(self):
        """Test loading config file with 'config' variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'app.py'
            config_file.write_text(
                "config = {\n"
                "    'name': 'Larapy',\n"
                "    'env': 'production'\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('app.name') == 'Larapy'
            assert config.get('app.env') == 'production'

    def test_loads_config_file_with_module_attributes(self):
        """Test loading config file with module-level attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'database.py'
            config_file.write_text(
                "default = 'mysql'\n"
                "connections = {\n"
                "    'mysql': {'host': 'localhost'}\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('database.default') == 'mysql'
            assert config.get('database.connections.mysql.host') == 'localhost'

    def test_loads_multiple_config_files(self):
        """Test loading multiple configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'app.py').write_text("config = {'name': 'Larapy'}")
            (config_dir / 'database.py').write_text("config = {'default': 'mysql'}")
            (config_dir / 'cache.py').write_text("config = {'driver': 'redis'}")
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('app.name') == 'Larapy'
            assert config.get('database.default') == 'mysql'
            assert config.get('cache.driver') == 'redis'

    def test_skips_files_starting_with_underscore(self):
        """Test skips configuration files starting with underscore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'app.py').write_text("config = {'name': 'Larapy'}")
            (config_dir / '_private.py').write_text("config = {'secret': 'value'}")
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('app.name') == 'Larapy'
            assert config.has('_private') is False

    def test_handles_missing_config_directory(self):
        """Test handles missing config directory gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            
            provider.register()
            
            config = app.make('config')
            assert isinstance(config, Repository)
            assert config.all() == {}

    def test_handles_invalid_config_file(self):
        """Test handles invalid configuration file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'valid.py').write_text("config = {'key': 'value'}")
            (config_dir / 'invalid.py').write_text("invalid python syntax {{{")
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('valid.key') == 'value'
            assert config.has('invalid') is False

    def test_skips_callable_module_attributes(self):
        """Test skips callable attributes when loading module attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'app.py'
            config_file.write_text(
                "name = 'Larapy'\n"
                "def get_env():\n"
                "    return 'production'\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            assert config.get('app.name') == 'Larapy'
            assert config.has('app.get_env') is False


class TestConfigComplexScenarios:
    """Test complex configuration scenarios."""

    def test_nested_configuration_structure(self):
        """Test loading nested configuration structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'database.py'
            config_file.write_text(
                "config = {\n"
                "    'default': 'mysql',\n"
                "    'connections': {\n"
                "        'mysql': {\n"
                "            'driver': 'mysql',\n"
                "            'host': 'localhost',\n"
                "            'port': 3306,\n"
                "            'database': 'larapy',\n"
                "            'username': 'root',\n"
                "            'password': 'secret'\n"
                "        },\n"
                "        'sqlite': {\n"
                "            'driver': 'sqlite',\n"
                "            'database': ':memory:'\n"
                "        }\n"
                "    }\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            
            assert config.string('database.default') == 'mysql'
            assert config.string('database.connections.mysql.driver') == 'mysql'
            assert config.integer('database.connections.mysql.port') == 3306
            assert config.string('database.connections.sqlite.database') == ':memory:'

    def test_array_configuration_values(self):
        """Test loading array configuration values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'app.py'
            config_file.write_text(
                "config = {\n"
                "    'providers': [\n"
                "        'DatabaseServiceProvider',\n"
                "        'CacheServiceProvider',\n"
                "        'QueueServiceProvider'\n"
                "    ]\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            providers = config.array('app.providers')
            
            assert len(providers) == 3
            assert 'DatabaseServiceProvider' in providers

    def test_mixed_type_configuration(self):
        """Test loading configuration with mixed types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            config_file = config_dir / 'app.py'
            config_file.write_text(
                "config = {\n"
                "    'name': 'Larapy',\n"
                "    'debug': True,\n"
                "    'timeout': 30,\n"
                "    'rate': 1.5,\n"
                "    'providers': ['ServiceProvider'],\n"
                "    'settings': {'key': 'value'}\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            
            assert config.string('app.name') == 'Larapy'
            assert config.boolean('app.debug') is True
            assert config.integer('app.timeout') == 30
            assert config.float('app.rate') == 1.5
            assert config.array('app.providers') == ['ServiceProvider']
            assert isinstance(config.get('app.settings'), dict)

    def test_multiple_files_alphabetical_order(self):
        """Test config files are loaded in alphabetical order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'z_last.py').write_text("config = {'order': 3}")
            (config_dir / 'a_first.py').write_text("config = {'order': 1}")
            (config_dir / 'm_middle.py').write_text("config = {'order': 2}")
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            provider.register()
            
            config = app.make('config')
            
            assert config.get('a_first.order') == 1
            assert config.get('m_middle.order') == 2
            assert config.get('z_last.order') == 3

    def test_application_integration(self):
        """Test full application integration with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'app.py').write_text(
                "config = {\n"
                "    'name': 'Larapy Framework',\n"
                "    'env': 'production',\n"
                "    'debug': False,\n"
                "    'url': 'https://larapy.dev'\n"
                "}\n"
            )
            
            (config_dir / 'cache.py').write_text(
                "config = {\n"
                "    'default': 'redis',\n"
                "    'stores': {\n"
                "        'redis': {'driver': 'redis'},\n"
                "        'file': {'driver': 'file'}\n"
                "    }\n"
                "}\n"
            )
            
            app = Application(tmpdir)
            app.register(ConfigServiceProvider)
            
            config = app.make('config')
            
            assert config.string('app.name') == 'Larapy Framework'
            assert config.boolean('app.debug') is False
            assert config.string('cache.default') == 'redis'
            assert config.has('cache.stores.redis') is True
            assert config.has('cache.stores.file') is True

    def test_config_access_after_provider_boot(self):
        """Test configuration remains accessible after provider lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / 'config'
            config_dir.mkdir()
            
            (config_dir / 'app.py').write_text("config = {'name': 'Larapy'}")
            
            app = Application(tmpdir)
            provider = ConfigServiceProvider(app)
            
            provider.register()
            provider.boot()
            
            config = app.make('config')
            assert config.get('app.name') == 'Larapy'
            
            config.set('app.debug', True)
            
            config_again = app.make('config')
            assert config_again.get('app.debug') is True
