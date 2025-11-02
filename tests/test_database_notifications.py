import pytest
from datetime import datetime
from larapy.notifications import HasDatabaseNotifications, Notifiable, Notification


class TestDatabaseNotifications:
    class User(Notifiable, HasDatabaseNotifications):
        def __init__(self, id):
            self.id = id
            self._notifications = []
    
    def test_has_database_notifications_returns_collection(self):
        user = self.User(1)
        
        notifications = user.notifications()
        
        assert hasattr(notifications, 'all')
        assert hasattr(notifications, 'count')
    
    def test_notifications_collection_starts_empty(self):
        user = self.User(1)
        
        notifications = user.notifications()
        
        assert notifications.count() == 0
    
    def test_can_create_notification_in_collection(self):
        user = self.User(1)
        
        user.notifications().create({
            'id': '123',
            'type': 'TestNotification',
            'data': '{"message": "test"}',
            'read_at': None
        })
        
        assert user.notifications().count() == 1
    
    def test_unread_notifications_filters_by_read_at(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': None},
            {'id': '2', 'read_at': datetime.now()},
            {'id': '3', 'read_at': None}
        ]
        
        unread = user.unread_notifications()
        
        assert unread.count() == 2
    
    def test_read_notifications_filters_by_read_at(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': None},
            {'id': '2', 'read_at': datetime.now()},
            {'id': '3', 'read_at': datetime.now()}
        ]
        
        read = user.read_notifications()
        
        assert read.count() == 2
    
    def test_mark_as_read_sets_read_at(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': None},
            {'id': '2', 'read_at': None}
        ]
        
        user.mark_as_read()
        
        assert all(n['read_at'] is not None for n in user._notifications)
    
    def test_mark_as_read_with_specific_ids(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': None},
            {'id': '2', 'read_at': None},
            {'id': '3', 'read_at': None}
        ]
        
        user.mark_as_read(['1', '3'])
        
        assert user._notifications[0]['read_at'] is not None
        assert user._notifications[1]['read_at'] is None
        assert user._notifications[2]['read_at'] is not None
    
    def test_mark_as_unread_clears_read_at(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': datetime.now()},
            {'id': '2', 'read_at': datetime.now()}
        ]
        
        user.mark_as_unread()
        
        assert all(n['read_at'] is None for n in user._notifications)
    
    def test_notification_collection_first_returns_first_item(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'message': 'first'},
            {'id': '2', 'message': 'second'}
        ]
        
        first = user.notifications().first()
        
        assert first['id'] == '1'
    
    def test_notification_collection_find_returns_by_id(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'message': 'first'},
            {'id': '2', 'message': 'second'}
        ]
        
        found = user.notifications().find('2')
        
        assert found['message'] == 'second'
    
    def test_notification_collection_where_filters(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'type': 'Welcome'},
            {'id': '2', 'type': 'Alert'},
            {'id': '3', 'type': 'Welcome'}
        ]
        
        welcome = user.notifications().where('type', 'Welcome')
        
        assert welcome.count() == 2
    
    def test_notification_collection_pluck_extracts_values(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'type': 'Welcome'},
            {'id': '2', 'type': 'Alert'}
        ]
        
        types = user.notifications().pluck('type')
        
        assert types == ['Welcome', 'Alert']
    
    def test_notification_collection_mark_as_read(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1', 'read_at': None},
            {'id': '2', 'read_at': None}
        ]
        
        user.notifications().mark_as_read()
        
        assert all(n['read_at'] is not None for n in user._notifications)
    
    def test_notification_collection_delete_clears_all(self):
        user = self.User(1)
        user._notifications = [
            {'id': '1'},
            {'id': '2'}
        ]
        
        user.notifications().delete()
        
        assert len(user._notifications) == 0
