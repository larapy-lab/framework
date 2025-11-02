import pytest
from larapy.notifications import Notification
from larapy.notifications.messages import MailMessage


class TestNotification:
    class UserWelcomeNotification(Notification):
        def __init__(self, user):
            super().__init__()
            self.user = user
        
        def via(self, notifiable):
            return ['mail', 'database']
        
        def to_mail(self, notifiable):
            return (MailMessage()
                .subject('Welcome!')
                .greeting(f'Hello {self.user.name}!')
                .line('Welcome to our platform.')
                .action('Get Started', 'https://example.com/dashboard'))
        
        def to_database(self, notifiable):
            return {
                'user_id': self.user.id,
                'message': f'Welcome {self.user.name}!'
            }
        
        def to_array(self, notifiable):
            return {
                'user_id': self.user.id,
                'user_name': self.user.name
            }
    
    class User:
        def __init__(self, id, name, email):
            self.id = id
            self.name = name
            self.email = email
    
    def test_notification_returns_channels_via_method(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        channels = notification.via(user)
        
        assert channels == ['mail', 'database']
    
    def test_notification_builds_mail_message(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        mail = notification.to_mail(user)
        
        assert isinstance(mail, MailMessage)
        assert mail.subject_text == 'Welcome!'
        assert 'Hello John!' == mail.greeting_text
        assert 'Welcome to our platform.' in mail.intro_lines
        assert mail.action_text == 'Get Started'
        assert mail.action_url == 'https://example.com/dashboard'
    
    def test_notification_to_database_returns_dict(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        data = notification.to_database(user)
        
        assert isinstance(data, dict)
        assert data['user_id'] == 1
        assert data['message'] == 'Welcome John!'
    
    def test_notification_to_array_returns_dict(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        data = notification.to_array(user)
        
        assert isinstance(data, dict)
        assert data['user_id'] == 1
        assert data['user_name'] == 'John'
    
    def test_notification_to_broadcast_uses_to_array(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        data = notification.to_broadcast(user)
        
        assert data == notification.to_array(user)
    
    def test_notification_should_send_returns_true_by_default(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        should_send = notification.should_send(user, 'mail')
        
        assert should_send is True
    
    def test_notification_can_set_locale(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        notification.locale = 'es'
        
        assert notification.locale == 'es'
    
    def test_notification_can_set_queue_settings(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        notification.connection = 'redis'
        notification.queue = 'notifications'
        notification.delay = 60
        
        assert notification.connection == 'redis'
        assert notification.queue == 'notifications'
        assert notification.delay == 60
    
    def test_notification_with_single_channel(self):
        class MailOnlyNotification(Notification):
            def via(self, notifiable):
                return ['mail']
        
        user = self.User(1, 'John', 'john@example.com')
        notification = MailOnlyNotification()
        
        channels = notification.via(user)
        
        assert channels == ['mail']
    
    def test_notification_with_conditional_channels(self):
        class ConditionalNotification(Notification):
            def via(self, notifiable):
                channels = ['database']
                if hasattr(notifiable, 'email') and notifiable.email:
                    channels.append('mail')
                return channels
        
        user = self.User(1, 'John', 'john@example.com')
        notification = ConditionalNotification()
        
        channels = notification.via(user)
        
        assert 'database' in channels
        assert 'mail' in channels
    
    def test_notification_via_connections_returns_empty_dict(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        connections = notification.via_connections()
        
        assert connections == {}
    
    def test_notification_via_queues_returns_empty_dict(self):
        user = self.User(1, 'John', 'john@example.com')
        notification = self.UserWelcomeNotification(user)
        
        queues = notification.via_queues()
        
        assert queues == {}
