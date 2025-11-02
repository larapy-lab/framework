import pytest
from unittest.mock import Mock, patch, MagicMock
from larapy.mail.transports.smtp import SmtpTransport
from larapy.mail.message import Message


class TestSmtpTransportInitialization:
    
    def test_smtp_transport_initializes_with_defaults(self):
        transport = SmtpTransport({})
        
        assert transport.host == 'localhost'
        assert transport.port == 587
        assert transport.encryption == 'tls'
        assert transport.timeout == 30
        assert transport.username is None
        assert transport.password is None
    
    def test_smtp_transport_initializes_with_custom_config(self):
        config = {
            'host': 'smtp.example.com',
            'port': 465,
            'username': 'user@example.com',
            'password': 'secret',
            'encryption': 'ssl',
            'timeout': 60
        }
        
        transport = SmtpTransport(config)
        
        assert transport.host == 'smtp.example.com'
        assert transport.port == 465
        assert transport.username == 'user@example.com'
        assert transport.password == 'secret'
        assert transport.encryption == 'ssl'
        assert transport.timeout == 60
    
    def test_smtp_transport_handles_partial_config(self):
        config = {
            'host': 'mail.server.com',
            'port': 2525
        }
        
        transport = SmtpTransport(config)
        
        assert transport.host == 'mail.server.com'
        assert transport.port == 2525
        assert transport.encryption == 'tls'
        assert transport.username is None


class TestSmtpTransportSending:
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_with_tls(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.example.com',
            'port': 587,
            'encryption': 'tls',
            'username': 'user@example.com',
            'password': 'password'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        result = transport.send(message, ['recipient@example.com'])
        
        assert result is True
        mock_smtp_class.assert_called_once_with('smtp.example.com', 587, timeout=30)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('user@example.com', 'password')
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP_SSL')
    def test_smtp_transport_sends_with_ssl(self, mock_smtp_ssl_class):
        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.example.com',
            'port': 465,
            'encryption': 'ssl',
            'username': 'user@example.com',
            'password': 'password'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        result = transport.send(message, ['recipient@example.com'])
        
        assert result is True
        mock_smtp_ssl_class.assert_called_once_with('smtp.example.com', 465, timeout=30)
        mock_smtp.starttls.assert_not_called()
        mock_smtp.login.assert_called_once_with('user@example.com', 'password')
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_without_authentication(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'localhost',
            'port': 25,
            'encryption': None
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        result = transport.send(message, ['recipient@example.com'])
        
        assert result is True
        mock_smtp.login.assert_not_called()
        mock_smtp.starttls.assert_not_called()
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_to_multiple_recipients(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        transport = SmtpTransport({'host': 'smtp.example.com'})
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['user1@example.com', 'user2@example.com'])
        message.set_cc(['cc@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        recipients = ['user1@example.com', 'user2@example.com', 'cc@example.com']
        result = transport.send(message, recipients)
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_uses_custom_timeout(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.example.com',
            'port': 587,
            'timeout': 120
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        transport.send(message, ['recipient@example.com'])
        
        mock_smtp_class.assert_called_once_with('smtp.example.com', 587, timeout=120)


class TestSmtpTransportErrorHandling:
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_raises_error_on_connection_failure(self, mock_smtp_class):
        mock_smtp_class.side_effect = Exception('Connection refused')
        
        transport = SmtpTransport({'host': 'smtp.example.com'})
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        with pytest.raises(RuntimeError, match='Failed to send email'):
            transport.send(message, ['recipient@example.com'])
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_raises_error_on_authentication_failure(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = Exception('Authentication failed')
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.example.com',
            'username': 'user@example.com',
            'password': 'wrong_password'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        with pytest.raises(RuntimeError, match='Failed to send email'):
            transport.send(message, ['recipient@example.com'])
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_raises_error_on_send_failure(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp.send_message.side_effect = Exception('Sending failed')
        mock_smtp_class.return_value = mock_smtp
        
        transport = SmtpTransport({'host': 'smtp.example.com'})
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        with pytest.raises(RuntimeError, match='Failed to send email'):
            transport.send(message, ['recipient@example.com'])
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_raises_error_on_starttls_failure(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp.starttls.side_effect = Exception('TLS negotiation failed')
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.example.com',
            'encryption': 'tls'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('sender@example.com')
        message.set_to(['recipient@example.com'])
        message.set_subject('Test')
        message.set_html_body('<p>Test</p>')
        
        with pytest.raises(RuntimeError, match='Failed to send email'):
            transport.send(message, ['recipient@example.com'])


class TestSmtpTransportRealWorldScenarios:
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_welcome_email(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'encryption': 'tls',
            'username': 'noreply@myapp.com',
            'password': 'app_password'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('noreply@myapp.com', 'MyApp')
        message.set_to(['newuser@example.com'])
        message.set_subject('Welcome to MyApp!')
        message.set_html_body('<h1>Welcome!</h1><p>Thanks for signing up.</p>')
        message.set_text_body('Welcome! Thanks for signing up.')
        
        result = transport.send(message, ['newuser@example.com'])
        
        assert result is True
        mock_smtp.login.assert_called_once_with('noreply@myapp.com', 'app_password')
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP_SSL')
    def test_smtp_transport_sends_order_confirmation(self, mock_smtp_ssl_class):
        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.sendgrid.net',
            'port': 465,
            'encryption': 'ssl',
            'username': 'apikey',
            'password': 'SG.xyz123'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('orders@store.com', 'Online Store')
        message.set_to(['customer@example.com'])
        message.set_cc(['accounting@store.com'])
        message.set_subject('Order Confirmation #12345')
        message.set_html_body('<h1>Order Confirmed</h1><p>Thank you for your order!</p>')
        
        recipients = ['customer@example.com', 'accounting@store.com']
        result = transport.send(message, recipients)
        
        assert result is True
        mock_smtp.login.assert_called_once_with('apikey', 'SG.xyz123')
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_password_reset(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.mailgun.org',
            'port': 587,
            'encryption': 'tls',
            'username': 'postmaster@mg.myapp.com',
            'password': 'mailgun_password'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('security@myapp.com', 'MyApp Security')
        message.set_to(['user@example.com'])
        message.set_reply_to(['support@myapp.com'])
        message.set_subject('Password Reset Request')
        message.set_html_body('<p>Click here to reset: https://myapp.com/reset/token123</p>')
        
        result = transport.send(message, ['user@example.com'])
        
        assert result is True
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_newsletter_to_many(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'smtp.aws.amazon.com',
            'port': 587,
            'encryption': 'tls',
            'username': 'AKIAIOSFODNN7EXAMPLE',
            'password': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('newsletter@magazine.com', 'Tech Magazine')
        message.set_to(['newsletter@magazine.com'])
        message.set_subject('Weekly Newsletter - November 2025')
        message.set_html_body('<h1>This Week in Tech</h1>')
        
        subscribers = [
            'subscriber1@example.com',
            'subscriber2@example.com',
            'subscriber3@example.com',
            'subscriber4@example.com',
            'subscriber5@example.com'
        ]
        
        result = transport.send(message, subscribers)
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_sends_support_ticket(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        transport = SmtpTransport({
            'host': 'smtp.office365.com',
            'port': 587,
            'encryption': 'tls',
            'username': 'support@company.com',
            'password': 'office365_password'
        })
        
        message = Message()
        message.set_from('support@company.com', 'Support Team')
        message.set_to(['customer@example.com'])
        message.set_reply_to(['support@company.com'])
        message.set_subject('[Ticket #789] Issue Resolved')
        message.set_html_body('<p>Your issue has been resolved.</p>')
        message.set_text_body('Your issue has been resolved.')
        
        result = transport.send(message, ['customer@example.com'])
        
        assert result is True
    
    @patch('larapy.mail.transports.smtp.smtplib.SMTP')
    def test_smtp_transport_local_development_server(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        config = {
            'host': 'localhost',
            'port': 1025,
            'encryption': None
        }
        
        transport = SmtpTransport(config)
        
        message = Message()
        message.set_from('test@localhost')
        message.set_to(['dev@localhost'])
        message.set_subject('Test Email')
        message.set_html_body('<p>Testing</p>')
        
        result = transport.send(message, ['dev@localhost'])
        
        assert result is True
        mock_smtp.login.assert_not_called()
        mock_smtp.starttls.assert_not_called()
