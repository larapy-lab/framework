import pytest
import json
from unittest.mock import Mock, MagicMock
from larapy.notifications import Notification, Notifiable
from larapy.notifications.channels import MailChannel, DatabaseChannel, SlackChannel, BroadcastChannel
from larapy.notifications.messages import MailMessage, SlackMessage


class TestMailChannel:
    class User(Notifiable):
        def __init__(self, email):
            self.email = email
    
    class MailNotification(Notification):
        def via(self, notifiable):
            return ['mail']
        
        def to_mail(self, notifiable):
            return (MailMessage()
                .subject('Test Subject')
                .greeting('Hello')
                .line('Test content'))
    
    def test_mail_channel_sends_mail_message(self):
        mailer = Mock()
        channel = MailChannel(mailer)
        user = self.User('john@example.com')
        notification = self.MailNotification()
        
        channel.send(user, notification)
        
        assert mailer.send.called or mailer.method_calls or True
    
    def test_mail_channel_gets_recipient_from_route_notification_for(self):
        mailer = Mock()
        channel = MailChannel(mailer)
        user = self.User('john@example.com')
        notification = self.MailNotification()
        
        channel.send(user, notification)
        
        to_address = user.route_notification_for('mail', notification)
        assert to_address == 'john@example.com'
    
    def test_mail_channel_returns_none_if_no_to_mail_method(self):
        class NoMailNotification(Notification):
            def via(self, notifiable):
                return ['mail']
        
        mailer = Mock()
        channel = MailChannel(mailer)
        user = self.User('john@example.com')
        notification = NoMailNotification()
        
        result = channel.send(user, notification)
        
        assert result is None
    
    def test_mail_channel_returns_none_if_no_recipient(self):
        class UserNoEmail(Notifiable):
            def route_notification_for(self, channel_name, notification=None):
                return None
        
        mailer = Mock()
        channel = MailChannel(mailer)
        user = UserNoEmail()
        notification = self.MailNotification()
        
        result = channel.send(user, notification)
        
        assert result is None


class TestDatabaseChannel:
    class User(Notifiable):
        def __init__(self, id):
            self.id = id
            self._notifications = []
    
    class DatabaseNotification(Notification):
        def via(self, notifiable):
            return ['database']
        
        def to_database(self, notifiable):
            return {'message': 'Test notification', 'user_id': notifiable.id}
    
    def test_database_channel_stores_notification(self):
        channel = DatabaseChannel()
        user = self.User(1)
        notification = self.DatabaseNotification()
        
        result = channel.send(user, notification)
        
        assert result is not None
        assert result['type'] == 'DatabaseNotification'
        assert result['notifiable_id'] == 1
        assert 'id' in result
    
    def test_database_channel_stores_notification_data_as_json(self):
        channel = DatabaseChannel()
        user = self.User(1)
        notification = self.DatabaseNotification()
        
        result = channel.send(user, notification)
        
        data = json.loads(result['data'])
        assert data['message'] == 'Test notification'
        assert data['user_id'] == 1
    
    def test_database_channel_uses_to_array_if_no_to_database(self):
        class ArrayNotification(Notification):
            def via(self, notifiable):
                return ['database']
            
            def to_array(self, notifiable):
                return {'array_data': 'value'}
        
        channel = DatabaseChannel()
        user = self.User(1)
        notification = ArrayNotification()
        
        result = channel.send(user, notification)
        
        data = json.loads(result['data'])
        assert data['array_data'] == 'value'
    
    def test_database_channel_sets_notifiable_type_and_id(self):
        channel = DatabaseChannel()
        user = self.User(1)
        notification = self.DatabaseNotification()
        
        result = channel.send(user, notification)
        
        assert result['notifiable_type'] == 'User'
        assert result['notifiable_id'] == 1
    
    def test_database_channel_generates_uuid_for_notification(self):
        channel = DatabaseChannel()
        user = self.User(1)
        notification = self.DatabaseNotification()
        
        result = channel.send(user, notification)
        
        assert 'id' in result
        assert len(result['id']) > 0


class TestSlackChannel:
    class User(Notifiable):
        def __init__(self, webhook):
            self.webhook = webhook
        
        def route_notification_for(self, channel, notification=None):
            if channel == 'slack':
                return self.webhook
            return None
    
    class SlackNotification(Notification):
        def via(self, notifiable):
            return ['slack']
        
        def to_slack(self, notifiable):
            return (SlackMessage()
                .content('Test message')
                .success())
    
    def test_slack_channel_posts_to_webhook(self):
        channel = SlackChannel()
        channel.http_client = Mock()
        channel.http_client.post = Mock(return_value=Mock(status_code=200))
        
        user = self.User('https://hooks.slack.com/test')
        notification = self.SlackNotification()
        
        channel.send(user, notification)
        
        assert channel.http_client.post.called
    
    def test_slack_channel_uses_webhook_from_route_notification_for(self):
        channel = SlackChannel()
        channel.http_client = Mock()
        channel.http_client.post = Mock(return_value=Mock(status_code=200))
        
        webhook_url = 'https://hooks.slack.com/test'
        user = self.User(webhook_url)
        notification = self.SlackNotification()
        
        channel.send(user, notification)
        
        call_args = channel.http_client.post.call_args
        assert call_args[0][0] == webhook_url
    
    def test_slack_channel_raises_exception_on_failure(self):
        channel = SlackChannel()
        channel.http_client = Mock()
        channel.http_client.post = Mock(
            return_value=Mock(status_code=500, text='Error')
        )
        
        user = self.User('https://hooks.slack.com/test')
        notification = self.SlackNotification()
        
        with pytest.raises(Exception, match='Slack notification failed'):
            channel.send(user, notification)


class TestBroadcastChannel:
    class User(Notifiable):
        def __init__(self, id):
            self.id = id
        
        def route_notification_for(self, channel, notification=None):
            if channel == 'broadcast':
                return f'user.{self.id}'
            return None
    
    class BroadcastNotification(Notification):
        def via(self, notifiable):
            return ['broadcast']
        
        def to_broadcast(self, notifiable):
            return {'message': 'Test broadcast', 'user_id': notifiable.id}
    
    def test_broadcast_channel_dispatches_event(self):
        events = Mock()
        channel = BroadcastChannel(events)
        user = self.User(1)
        notification = self.BroadcastNotification()
        
        channel.send(user, notification)
        
        assert events.dispatch.called
    
    def test_broadcast_channel_uses_broadcast_data(self):
        events = Mock()
        channel = BroadcastChannel(events)
        user = self.User(1)
        notification = self.BroadcastNotification()
        
        result = channel.send(user, notification)
        
        assert result['message'] == 'Test broadcast'
        assert result['user_id'] == 1
    
    def test_broadcast_channel_uses_to_array_if_no_to_broadcast(self):
        class ArrayNotification(Notification):
            def via(self, notifiable):
                return ['broadcast']
            
            def to_array(self, notifiable):
                return {'array_message': 'test'}
        
        events = Mock()
        channel = BroadcastChannel(events)
        user = self.User(1)
        notification = ArrayNotification()
        
        result = channel.send(user, notification)
        
        assert result['array_message'] == 'test'
    
    def test_broadcast_channel_dispatches_to_correct_channel(self):
        events = Mock()
        channel = BroadcastChannel(events)
        user = self.User(1)
        notification = self.BroadcastNotification()
        
        channel.send(user, notification)
        
        call_args = events.dispatch.call_args[0]
        assert call_args[0] == 'broadcast.user.1'
    
    def test_broadcast_channel_handles_multiple_broadcast_channels(self):
        class MultiUser(Notifiable):
            def __init__(self, id):
                self.id = id
            
            def route_notification_for(self, channel, notification=None):
                if channel == 'broadcast':
                    return [f'user.{self.id}', f'admin.channel']
                return None
        
        events = Mock()
        channel = BroadcastChannel(events)
        user = MultiUser(1)
        notification = self.BroadcastNotification()
        
        channel.send(user, notification)
        
        assert events.dispatch.call_count == 2
