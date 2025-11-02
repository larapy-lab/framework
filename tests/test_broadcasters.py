import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from larapy.broadcasting.broadcasters import (
    PusherBroadcaster,
    RedisBroadcaster,
    LogBroadcaster,
    NullBroadcaster
)


class TestPusherBroadcaster:
    def test_broadcasts_to_channels(self):
        pusher_client = Mock()
        pusher_client.trigger = Mock()
        
        broadcaster = PusherBroadcaster(pusher_client, {})
        broadcaster.broadcast(['channel1', 'channel2'], 'TestEvent', {'data': 'value'})
        
        pusher_client.trigger.assert_called_once_with(
            channels=['channel1', 'channel2'],
            event_name='TestEvent',
            data={'data': 'value'},
            socket_id=None
        )
    
    def test_formats_channels_correctly(self):
        pusher_client = Mock()
        pusher_client.trigger = Mock()
        
        broadcaster = PusherBroadcaster(pusher_client, {})
        formatted = broadcaster.format_channels(['channel1', 'channel2'])
        
        assert formatted == ['channel1', 'channel2']
    
    def test_handles_socket_id_in_payload(self):
        pusher_client = Mock()
        pusher_client.trigger = Mock()
        
        broadcaster = PusherBroadcaster(pusher_client, {})
        broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value', 'socket_id': 'socket123'})
        
        pusher_client.trigger.assert_called_once()
        call_args = pusher_client.trigger.call_args
        
        assert call_args[1]['socket_id'] == 'socket123'
        assert 'socket_id' not in call_args[1]['data']
    
    def test_auth_for_private_channel(self):
        pusher_client = Mock()
        pusher_client.authenticate = Mock(return_value={'auth': 'signature'})
        
        broadcaster = PusherBroadcaster(pusher_client, {})
        result = broadcaster.auth('private-channel', 'socket123')
        
        pusher_client.authenticate.assert_called_once_with(
            channel='private-channel',
            socket_id='socket123'
        )
        assert result == {'auth': 'signature'}
    
    def test_auth_for_presence_channel(self):
        pusher_client = Mock()
        pusher_client.authenticate = Mock(return_value={'auth': 'signature', 'channel_data': '{}'})
        
        broadcaster = PusherBroadcaster(pusher_client, {})
        custom_data = {'user_id': 1, 'user_info': {'name': 'John'}}
        result = broadcaster.auth('presence-channel', 'socket123', custom_data)
        
        pusher_client.authenticate.assert_called_once_with(
            channel='presence-channel',
            socket_id='socket123',
            custom_data=custom_data
        )


class TestRedisBroadcaster:
    def test_broadcasts_to_channels(self):
        redis_client = Mock()
        redis_client.publish = Mock()
        
        broadcaster = RedisBroadcaster(redis_client, 'default')
        result = broadcaster.broadcast(['channel1', 'channel2'], 'TestEvent', {'data': 'value'})
        
        assert result is True
        assert redis_client.publish.call_count == 2
    
    def test_publishes_json_message(self):
        redis_client = Mock()
        redis_client.publish = Mock()
        
        broadcaster = RedisBroadcaster(redis_client, 'default')
        broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        redis_client.publish.assert_called_once()
        call_args = redis_client.publish.call_args[0]
        
        assert call_args[0] == 'channel1'
        message = json.loads(call_args[1])
        assert message['event'] == 'TestEvent'
        assert message['data'] == {'data': 'value'}
    
    def test_formats_channels(self):
        redis_client = Mock()
        
        broadcaster = RedisBroadcaster(redis_client, 'default')
        formatted = broadcaster.format_channels(['channel1', 'channel2'])
        
        assert formatted == ['channel1', 'channel2']


class TestLogBroadcaster:
    def test_logs_broadcast_events(self, capsys):
        broadcaster = LogBroadcaster(logger=None)
        broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        captured = capsys.readouterr()
        assert '[BROADCAST]' in captured.out
        assert 'TestEvent' in captured.out
        assert 'channel1' in captured.out
    
    def test_uses_logger_when_provided(self):
        logger = Mock()
        logger.info = Mock()
        
        broadcaster = LogBroadcaster(logger=logger)
        broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        assert 'TestEvent' in call_args
        assert 'channel1' in call_args
    
    def test_returns_true(self):
        broadcaster = LogBroadcaster(logger=None)
        result = broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        assert result is True


class TestNullBroadcaster:
    def test_does_nothing(self):
        broadcaster = NullBroadcaster()
        result = broadcaster.broadcast(['channel1'], 'TestEvent', {'data': 'value'})
        
        assert result is None
