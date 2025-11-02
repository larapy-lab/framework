import pytest
from unittest.mock import Mock
from larapy.notifications import Notification, Notifiable
from larapy.notifications.events import NotificationSending, NotificationSent, NotificationFailed
from larapy.notifications.notification_sender import NotificationSender
from larapy.notifications.channel_manager import ChannelManager


class TestNotificationEvents:
    class User(Notifiable):
        def __init__(self, id):
            self.id = id
            self._notifications = []
    
    class TestNotification(Notification):
        def via(self, notifiable):
            return ['database']
        
        def to_database(self, notifiable):
            return {'message': 'test'}
    
    def test_notification_sending_event_has_correct_properties(self):
        user = self.User(1)
        notification = self.TestNotification()
        
        event = NotificationSending(user, notification, 'database')
        
        assert event.notifiable == user
        assert event.notification == notification
        assert event.channel == 'database'
    
    def test_notification_sent_event_has_correct_properties(self):
        user = self.User(1)
        notification = self.TestNotification()
        response = {'status': 'sent'}
        
        event = NotificationSent(user, notification, 'database', response)
        
        assert event.notifiable == user
        assert event.notification == notification
        assert event.channel == 'database'
        assert event.response == response
    
    def test_notification_failed_event_has_correct_properties(self):
        user = self.User(1)
        notification = self.TestNotification()
        exception = Exception('Test error')
        
        event = NotificationFailed(user, notification, 'database', exception)
        
        assert event.notifiable == user
        assert event.notification == notification
        assert event.channel == 'database'
        assert event.exception == exception
    
    def test_notification_sender_dispatches_sending_event(self):
        events = Mock()
        container = Mock()
        manager = Mock()
        manager.driver = Mock(return_value=Mock(send=Mock(return_value=None)))
        
        sender = NotificationSender(manager, events)
        user = self.User(1)
        notification = self.TestNotification()
        
        sender.send_to_notifiable(user, notification)
        
        assert events.dispatch.called
        first_call = events.dispatch.call_args_list[0][0][0]
        assert isinstance(first_call, NotificationSending)
    
    def test_notification_sender_dispatches_sent_event(self):
        events = Mock()
        manager = Mock()
        manager.driver = Mock(return_value=Mock(send=Mock(return_value={'status': 'ok'})))
        
        sender = NotificationSender(manager, events)
        user = self.User(1)
        notification = self.TestNotification()
        
        sender.send_to_notifiable(user, notification)
        
        sent_events = [call for call in events.dispatch.call_args_list 
                      if isinstance(call[0][0], NotificationSent)]
        assert len(sent_events) > 0
    
    def test_notification_sender_dispatches_failed_event_on_exception(self):
        events = Mock()
        manager = Mock()
        manager.driver = Mock(return_value=Mock(
            send=Mock(side_effect=Exception('Send failed'))
        ))
        
        sender = NotificationSender(manager, events)
        user = self.User(1)
        notification = self.TestNotification()
        
        with pytest.raises(Exception):
            sender.send_to_notifiable(user, notification)
        
        failed_events = [call for call in events.dispatch.call_args_list 
                        if isinstance(call[0][0], NotificationFailed)]
        assert len(failed_events) > 0
