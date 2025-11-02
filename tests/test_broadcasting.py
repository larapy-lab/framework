import pytest
from unittest.mock import Mock, MagicMock
from larapy.broadcasting import BroadcastManager, Broadcaster
from larapy.broadcasting.broadcasters import LogBroadcaster, NullBroadcaster


class TestBroadcastManager:
    def test_creates_default_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        driver = manager.driver()
        
        assert isinstance(driver, NullBroadcaster)
    
    def test_creates_log_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        driver = manager.driver('log')
        
        assert isinstance(driver, LogBroadcaster)
    
    def test_caches_driver_instances(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        driver1 = manager.driver('log')
        driver2 = manager.driver('log')
        
        assert driver1 is driver2
    
    def test_extends_with_custom_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        custom_driver = Mock(spec=Broadcaster)
        
        manager = BroadcastManager(container)
        manager.extend('custom', lambda c: custom_driver)
        
        driver = manager.driver('custom')
        assert driver is custom_driver
    
    def test_extend_clears_cached_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        driver1 = manager.driver('log')
        
        new_driver = Mock(spec=Broadcaster)
        manager.extend('log', lambda c: new_driver)
        
        driver2 = manager.driver('log')
        assert driver2 is not driver1
        assert driver2 is new_driver
    
    def test_invalid_driver_throws_exception(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        
        with pytest.raises(ValueError, match="driver 'invalid' is not supported"):
            manager.driver('invalid')
    
    def test_get_default_driver_from_config(self):
        config = Mock()
        config.get = Mock(return_value='log')
        
        container = Mock()
        container.bound = Mock(side_effect=lambda key: key == 'config')
        container.make = Mock(return_value=config)
        
        manager = BroadcastManager(container)
        default = manager.get_default_driver()
        
        assert default == 'log'
    
    def test_get_default_driver_without_config(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        default = manager.get_default_driver()
        
        assert default == 'null'
    
    def test_broadcast_delegates_to_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        driver = Mock(spec=Broadcaster)
        driver.broadcast = Mock()
        
        manager = BroadcastManager(container)
        manager.extend('test', lambda c: driver)
        manager.get_default_driver = Mock(return_value='test')
        
        manager.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        driver.broadcast.assert_called_once_with(['channel1'], 'TestEvent', {'data': 'value'})
    
    def test_callable_interface(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        driver = Mock(spec=Broadcaster)
        driver.broadcast = Mock()
        
        manager = BroadcastManager(container)
        manager.extend('test', lambda c: driver)
        manager.get_default_driver = Mock(return_value='test')
        
        manager(['channel1'], 'TestEvent', {'data': 'value'})
        
        driver.broadcast.assert_called_once_with(['channel1'], 'TestEvent', {'data': 'value'})
    
    def test_creates_null_driver(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        driver = manager.create_null_driver()
        
        assert isinstance(driver, NullBroadcaster)
    
    def test_creates_redis_driver_when_redis_available(self):
        redis_client = Mock()
        redis_manager = Mock()
        redis_manager.connection = Mock(return_value=redis_client)
        
        config = Mock()
        config.get = Mock(return_value='default')
        
        container = Mock()
        container.make = Mock(side_effect=lambda key: redis_manager if key == 'redis' else config)
        container.bound = Mock(return_value=True)
        
        manager = BroadcastManager(container)
        driver = manager.create_redis_driver()
        
        from larapy.broadcasting.broadcasters import RedisBroadcaster
        assert isinstance(driver, RedisBroadcaster)
        assert driver.redis is redis_client
    
    def test_multiple_drivers_can_coexist(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        
        log_driver = manager.driver('log')
        null_driver = manager.driver('null')
        
        assert isinstance(log_driver, LogBroadcaster)
        assert isinstance(null_driver, NullBroadcaster)
        assert log_driver is not null_driver
    
    def test_driver_factory_method_pattern(self):
        container = Mock()
        container.bound = Mock(return_value=False)
        
        manager = BroadcastManager(container)
        
        assert hasattr(manager, 'create_log_driver')
        assert hasattr(manager, 'create_null_driver')
        assert hasattr(manager, 'create_redis_driver')
        assert hasattr(manager, 'create_pusher_driver')
    
    def test_pusher_driver_requires_pusher_library(self):
        config = Mock()
        config.get = Mock(return_value={})
        
        container = Mock()
        container.make = Mock(return_value=config)
        container.bound = Mock(return_value=True)
        
        manager = BroadcastManager(container)
        
        with pytest.raises(ImportError, match="pusher library is required"):
            manager.create_pusher_driver()
