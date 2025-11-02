import pytest
from larapy.notifications import Notifiable, Notification
from larapy.notifications.messages import MailMessage


class TestNotifiable:
    class User(Notifiable):
        def __init__(self, id, name, email):
            self.id = id
            self.name = name
            self.email = email
            self._notifications = []
    
    class SimpleNotification(Notification):
        def via(self, notifiable):
            return ['database']
        
        def to_database(self, notifiable):
            return {'message': 'Test notification'}
    
    class MailNotification(Notification):
        def via(self, notifiable):
            return ['mail']
        
        def to_mail(self, notifiable):
            return MailMessage().subject('Test').line('Test content')
    
    def test_notifiable_has_route_notification_for_mail(self):
        user = self.User(1, 'John', 'john@example.com')
        
        route = user.route_notification_for('mail')
        
        assert route == 'john@example.com'
    
    def test_notifiable_route_notification_for_database_returns_self(self):
        user = self.User(1, 'John', 'john@example.com')
        
        route = user.route_notification_for('database')
        
        assert route == user
    
    def test_notifiable_route_notification_for_broadcast(self):
        user = self.User(1, 'John', 'john@example.com')
        
        route = user.route_notification_for('broadcast')
        
        assert route == 'User.1'
    
    def test_notifiable_can_define_custom_route_method(self):
        class CustomUser(Notifiable):
            def __init__(self):
                self.phone = '+1234567890'
            
            def route_notification_for_sms(self, notification=None):
                return self.phone
        
        user = CustomUser()
        route = user.route_notification_for('sms')
        
        assert route == '+1234567890'
    
    def test_notifiable_returns_none_for_unknown_channel(self):
        user = self.User(1, 'John', 'john@example.com')
        
        route = user.route_notification_for('unknown_channel')
        
        assert route is None
    
    def test_notifiable_uses_mail_attribute_if_email_not_available(self):
        class UserWithMail(Notifiable):
            def __init__(self):
                self.mail = 'user@example.com'
        
        user = UserWithMail()
        route = user.route_notification_for('mail')
        
        assert route == 'user@example.com'
    
    def test_notifiable_custom_route_receives_notification(self):
        notification_received = []
        
        class CustomUser(Notifiable):
            def route_notification_for_custom(self, notification=None):
                notification_received.append(notification)
                return 'custom_route'
        
        user = CustomUser()
        notification = self.SimpleNotification()
        
        route = user.route_notification_for('custom', notification)
        
        assert route == 'custom_route'
        assert notification_received[0] == notification
    
    def test_notifiable_route_prefers_custom_method_over_default(self):
        class UserWithCustomMail(Notifiable):
            def __init__(self):
                self.email = 'default@example.com'
            
            def route_notification_for_mail(self, notification=None):
                return 'custom@example.com'
        
        user = UserWithCustomMail()
        route = user.route_notification_for('mail')
        
        assert route == 'custom@example.com'
