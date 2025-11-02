import pytest
from unittest.mock import Mock
from larapy.broadcasting import ChannelRouter, BroadcastChannelRoute


class TestBroadcastChannelRoute:
    def test_matches_exact_pattern(self):
        route = BroadcastChannelRoute('channel.test', lambda u: True)
        
        assert route.matches('channel.test') is True
        assert route.matches('channel.other') is False
    
    def test_matches_wildcard_pattern(self):
        route = BroadcastChannelRoute('channel.*', lambda u: True)
        
        assert route.matches('channel.test') is True
        assert route.matches('channel.other') is True
        assert route.matches('other.test') is False
    
    def test_matches_parameter_pattern(self):
        route = BroadcastChannelRoute('user.{id}', lambda u, id: True)
        
        assert route.matches('user.123') is True
        assert route.matches('user.456') is True
        assert route.matches('post.123') is False
    
    def test_extracts_parameters(self):
        route = BroadcastChannelRoute('user.{id}.posts.{post_id}', lambda u, id, post_id: True)
        params = route.extract_parameters('user.123.posts.456')
        
        assert params == {'id': '123', 'post_id': '456'}
    
    def test_authorize_with_parameters(self):
        callback = Mock(return_value=True)
        route = BroadcastChannelRoute('user.{id}', callback)
        
        user = Mock()
        result = route.authorize(user, 'user.123')
        
        callback.assert_called_once_with(user, id='123')
        assert result is True


class TestChannelRouter:
    def test_registers_channel(self):
        router = ChannelRouter()
        
        router.channel('test.channel', lambda u: True)
        
        assert len(router.routes) == 1
        assert router.routes[0].pattern == 'test.channel'
    
    def test_registers_private_channel(self):
        router = ChannelRouter()
        
        router.private('user.{id}', lambda u, id: True)
        
        assert len(router.routes) == 1
        assert router.routes[0].pattern == 'private-user.{id}'
    
    def test_registers_presence_channel(self):
        router = ChannelRouter()
        
        router.presence('room.{id}', lambda u, id: True)
        
        assert len(router.routes) == 1
        assert router.routes[0].pattern == 'presence-room.{id}'
    
    def test_authorize_calls_matching_route(self):
        router = ChannelRouter()
        
        callback = Mock(return_value=True)
        router.channel('user.{id}', callback)
        
        user = Mock()
        user.id = 123
        result = router.authorize(user, 'user.123')
        
        callback.assert_called_once_with(user, id='123')
        assert result is True
    
    def test_authorize_returns_true_if_no_route_found(self):
        router = ChannelRouter()
        
        user = Mock()
        result = router.authorize(user, 'unknown.channel')
        
        assert result is True
    
    def test_find_route_returns_matching_route(self):
        router = ChannelRouter()
        
        router.channel('test.channel', lambda u: True)
        router.channel('other.channel', lambda u: True)
        
        route = router.find_route('test.channel')
        
        assert route is not None
        assert route.pattern == 'test.channel'
    
    def test_find_route_returns_none_if_not_found(self):
        router = ChannelRouter()
        
        router.channel('test.channel', lambda u: True)
        
        route = router.find_route('unknown.channel')
        
        assert route is None
    
    def test_multiple_routes_first_match_wins(self):
        router = ChannelRouter()
        
        callback1 = Mock(return_value=True)
        callback2 = Mock(return_value=False)
        
        router.channel('user.*', callback1)
        router.channel('user.123', callback2)
        
        user = Mock()
        result = router.authorize(user, 'user.123')
        
        callback1.assert_called_once()
        callback2.assert_not_called()
        assert result is True
