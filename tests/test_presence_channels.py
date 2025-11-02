import pytest
from larapy.broadcasting import PresenceChannel


class TestPresenceChannel:
    def test_subscribes_member(self):
        channel = PresenceChannel('presence-room.1')
        
        user_info = {'id': 1, 'name': 'John Doe'}
        result = channel.subscribe('socket123', user_info)
        
        assert result['id'] == 1
        assert result['name'] == 'John Doe'
        assert 'joined_at' in result
    
    def test_unsubscribes_member(self):
        channel = PresenceChannel('presence-room.1')
        
        channel.subscribe('socket123', {'id': 1, 'name': 'John'})
        result = channel.unsubscribe('socket123')
        
        assert result is True
        assert not channel.has_member('socket123')
    
    def test_unsubscribe_nonexistent_member_returns_false(self):
        channel = PresenceChannel('presence-room.1')
        
        result = channel.unsubscribe('socket999')
        
        assert result is False
    
    def test_get_members_returns_all_members(self):
        channel = PresenceChannel('presence-room.1')
        
        channel.subscribe('socket1', {'id': 1, 'name': 'John'})
        channel.subscribe('socket2', {'id': 2, 'name': 'Jane'})
        
        members = channel.get_members()
        
        assert len(members) == 2
        assert any(m['name'] == 'John' for m in members)
        assert any(m['name'] == 'Jane' for m in members)
    
    def test_has_member_checks_subscription(self):
        channel = PresenceChannel('presence-room.1')
        
        channel.subscribe('socket123', {'id': 1, 'name': 'John'})
        
        assert channel.has_member('socket123') is True
        assert channel.has_member('socket999') is False
    
    def test_get_member_returns_member_info(self):
        channel = PresenceChannel('presence-room.1')
        
        user_info = {'id': 1, 'name': 'John'}
        channel.subscribe('socket123', user_info)
        
        member = channel.get_member('socket123')
        
        assert member is not None
        assert member['id'] == 1
        assert member['name'] == 'John'
    
    def test_count_returns_member_count(self):
        channel = PresenceChannel('presence-room.1')
        
        assert channel.count() == 0
        
        channel.subscribe('socket1', {'id': 1, 'name': 'John'})
        assert channel.count() == 1
        
        channel.subscribe('socket2', {'id': 2, 'name': 'Jane'})
        assert channel.count() == 2
    
    def test_clear_removes_all_members(self):
        channel = PresenceChannel('presence-room.1')
        
        channel.subscribe('socket1', {'id': 1, 'name': 'John'})
        channel.subscribe('socket2', {'id': 2, 'name': 'Jane'})
        
        channel.clear()
        
        assert channel.count() == 0
        assert len(channel.get_members()) == 0
