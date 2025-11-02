import pytest
from unittest.mock import Mock, MagicMock
from larapy.broadcasting import ChannelAuthenticator, ChannelRouter


class TestChannelAuthenticator:
    def test_public_channel_needs_no_auth(self):
        gate = Mock()
        request = Mock()
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate('public-channel')
        
        assert result == {'auth': None}
    
    def test_private_channel_requires_user(self):
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=False)
        
        request = Mock()
        request.user = None
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_private('private-channel')
        
        assert 'error' in result
        assert result['error'] == 'Unauthorized'
        assert result['status'] == 403
    
    def test_private_channel_authorization_success(self):
        user = Mock()
        user.id = 1
        
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=False)
        
        request = Mock()
        request.user = user
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_private('private-user.1', 'socket123')
        
        assert 'auth' in result
        assert result['auth'] is not None
        assert result['channel_data'] is None
    
    def test_private_channel_authorization_failure(self):
        user = Mock()
        user.id = 1
        
        router = ChannelRouter()
        router.channel('private-user.{id}', lambda u, id: u.id == int(id))
        
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=True)
        gate.container.make = Mock(return_value=router)
        
        request = Mock()
        request.user = user
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_private('private-user.2', 'socket123')
        
        assert 'error' in result
        assert result['error'] == 'Forbidden'
    
    def test_presence_channel_requires_user(self):
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=False)
        
        request = Mock()
        request.user = None
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_presence('presence-room.1')
        
        assert 'error' in result
        assert result['error'] == 'Unauthorized'
    
    def test_presence_channel_returns_user_info(self):
        user = Mock()
        user.id = 1
        user.name = 'John Doe'
        
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=False)
        
        request = Mock()
        request.user = user
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_presence('presence-room.1', 'socket123')
        
        assert 'auth' in result
        assert 'channel_data' in result
        assert result['channel_data'] is not None
        
        import json
        channel_data = json.loads(result['channel_data'])
        assert channel_data['id'] == 1
        assert channel_data['name'] == 'John Doe'
    
    def test_presence_channel_custom_user_info(self):
        user = Mock()
        user.id = 1
        user.name = 'John Doe'
        user.avatar = 'https://example.com/avatar.jpg'
        
        router = ChannelRouter()
        router.presence('room.{room_id}', lambda u, room_id: {
            'id': u.id,
            'name': u.name,
            'avatar': u.avatar,
            'room': room_id
        })
        
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'broadcasting.connections.pusher.key': 'test-key',
            'broadcasting.connections.pusher.secret': 'test-secret'
        }.get(key, default))
        
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=True)
        gate.container.make = Mock(side_effect=lambda key: router if key == 'broadcast.channel' else config)
        
        request = Mock()
        request.user = user
        
        authenticator = ChannelAuthenticator(gate, request)
        result = authenticator.authenticate_presence('presence-room.1', 'socket123')
        
        import json
        channel_data = json.loads(result['channel_data'])
        assert channel_data['id'] == 1
        assert channel_data['avatar'] == 'https://example.com/avatar.jpg'
        assert channel_data['room'] == '1'
    
    def test_get_user_from_request(self):
        user = Mock()
        request = Mock()
        request.user = user
        
        gate = Mock()
        authenticator = ChannelAuthenticator(gate, request)
        
        assert authenticator.get_user() is user
    
    def test_generates_auth_signature(self):
        gate = Mock()
        gate.container = Mock()
        gate.container.bound = Mock(return_value=False)
        
        request = Mock()
        
        authenticator = ChannelAuthenticator(gate, request)
        signature = authenticator.generate_auth_signature('private-channel', 'socket123')
        
        assert ':' in signature
        parts = signature.split(':')
        assert len(parts) == 2
        assert parts[0] == 'default-key'
