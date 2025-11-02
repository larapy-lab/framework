import pytest
from unittest.mock import Mock
from larapy.broadcasting import ShouldBroadcast, BroadcastEvent


class OrderShipped(ShouldBroadcast):
    def __init__(self, order_id, customer_name):
        self.order_id = order_id
        self.customer_name = customer_name
    
    def broadcast_on(self):
        return [f'orders.{self.order_id}']


class ConditionalEvent(ShouldBroadcast):
    def __init__(self, should_send):
        self.should_send = should_send
    
    def broadcast_on(self):
        return ['test.channel']
    
    def broadcast_when(self):
        return self.should_send


class CustomEvent(ShouldBroadcast):
    def __init__(self):
        self.data = 'value'
        self._internal = 'hidden'
    
    def broadcast_on(self):
        return ['custom.channel']
    
    def broadcast_as(self):
        return 'CustomEventName'
    
    def broadcast_with(self):
        return {'custom': 'data', 'value': 123}


class TestShouldBroadcast:
    def test_broadcast_on_returns_channels(self):
        event = OrderShipped(123, 'John Doe')
        channels = event.broadcast_on()
        
        assert channels == ['orders.123']
    
    def test_broadcast_as_returns_class_name(self):
        event = OrderShipped(123, 'John Doe')
        name = event.broadcast_as()
        
        assert name == 'OrderShipped'
    
    def test_broadcast_as_can_be_overridden(self):
        event = CustomEvent()
        name = event.broadcast_as()
        
        assert name == 'CustomEventName'
    
    def test_broadcast_with_returns_public_attributes(self):
        event = OrderShipped(123, 'John Doe')
        data = event.broadcast_with()
        
        assert data == {
            'order_id': 123,
            'customer_name': 'John Doe'
        }
    
    def test_broadcast_with_excludes_private_attributes(self):
        event = CustomEvent()
        data = event.broadcast_with()
        
        assert '_internal' not in data
    
    def test_broadcast_with_can_be_overridden(self):
        event = CustomEvent()
        data = event.broadcast_with()
        
        assert data == {'custom': 'data', 'value': 123}
    
    def test_broadcast_when_returns_true_by_default(self):
        event = OrderShipped(123, 'John Doe')
        
        assert event.broadcast_when() is True


class TestBroadcastEvent:
    def test_dispatch_broadcasts_event(self):
        event = OrderShipped(123, 'John Doe')
        broadcaster = Mock()
        broadcaster.broadcast = Mock()
        
        wrapper = BroadcastEvent(event)
        wrapper.dispatch(broadcaster)
        
        broadcaster.broadcast.assert_called_once_with(
            ['orders.123'],
            'OrderShipped',
            {'order_id': 123, 'customer_name': 'John Doe'}
        )
    
    def test_dispatch_respects_broadcast_when(self):
        event = ConditionalEvent(should_send=False)
        broadcaster = Mock()
        broadcaster.broadcast = Mock()
        
        wrapper = BroadcastEvent(event)
        result = wrapper.dispatch(broadcaster)
        
        broadcaster.broadcast.assert_not_called()
        assert result is False
    
    def test_dispatch_with_custom_event_name(self):
        event = CustomEvent()
        broadcaster = Mock()
        broadcaster.broadcast = Mock()
        
        wrapper = BroadcastEvent(event)
        wrapper.dispatch(broadcaster)
        
        call_args = broadcaster.broadcast.call_args[0]
        assert call_args[1] == 'CustomEventName'
