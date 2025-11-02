import pytest
from larapy.mail import Mailable, Address, Mailer, MailManager, Message, SmtpTransport
from larapy.views import Engine
from pathlib import Path


class TestMailable:
    
    def test_mailable_to_single_email(self):
        mailable = Mailable()
        mailable.to('test@example.com')
        
        assert len(mailable.get_to()) == 1
        assert mailable.get_to()[0].email == 'test@example.com'
        assert mailable.get_to()[0].name is None
    
    def test_mailable_to_with_name(self):
        mailable = Mailable()
        mailable.to('test@example.com', 'Test User')
        
        assert len(mailable.get_to()) == 1
        assert mailable.get_to()[0].email == 'test@example.com'
        assert mailable.get_to()[0].name == 'Test User'
    
    def test_mailable_to_multiple_emails(self):
        mailable = Mailable()
        mailable.to(['test1@example.com', 'test2@example.com'])
        
        assert len(mailable.get_to()) == 2
        assert mailable.get_to()[0].email == 'test1@example.com'
        assert mailable.get_to()[1].email == 'test2@example.com'
    
    def test_mailable_cc(self):
        mailable = Mailable()
        mailable.cc('cc@example.com')
        
        assert len(mailable.get_cc()) == 1
        assert mailable.get_cc()[0].email == 'cc@example.com'
    
    def test_mailable_bcc(self):
        mailable = Mailable()
        mailable.bcc('bcc@example.com')
        
        assert len(mailable.get_bcc()) == 1
        assert mailable.get_bcc()[0].email == 'bcc@example.com'
    
    def test_mailable_from(self):
        mailable = Mailable()
        mailable.from_address('from@example.com', 'From User')
        
        assert mailable.get_from().email == 'from@example.com'
        assert mailable.get_from().name == 'From User'
    
    def test_mailable_reply_to(self):
        mailable = Mailable()
        mailable.reply_to('reply@example.com')
        
        assert len(mailable.get_reply_to()) == 1
        assert mailable.get_reply_to()[0].email == 'reply@example.com'
    
    def test_mailable_subject(self):
        mailable = Mailable()
        mailable.subject('Test Subject')
        
        assert mailable.get_subject() == 'Test Subject'
    
    def test_mailable_view(self):
        mailable = Mailable()
        mailable.view('emails.test', {'name': 'John'})
        
        assert mailable.get_view() == 'emails.test'
        assert mailable.get_view_data() == {'name': 'John'}
    
    def test_mailable_text(self):
        mailable = Mailable()
        mailable.text('emails.test_text', {'name': 'John'})
        
        assert mailable.get_text_view() == 'emails.test_text'
        assert mailable.get_view_data() == {'name': 'John'}
    
    def test_mailable_html_content(self):
        mailable = Mailable()
        mailable.html('<h1>Test</h1>')
        
        assert mailable.get_html() == '<h1>Test</h1>'
    
    def test_mailable_text_content(self):
        mailable = Mailable()
        mailable.text_content('Plain text content')
        
        assert mailable.get_text() == 'Plain text content'
    
    def test_mailable_with_data(self):
        mailable = Mailable()
        mailable.with_data({'key': 'value'})
        
        assert mailable.get_view_data() == {'key': 'value'}
    
    def test_mailable_attach_file(self):
        mailable = Mailable()
        mailable.attach('/path/to/file.pdf', 'document.pdf', 'application/pdf')
        
        attachments = mailable.get_attachments()
        assert len(attachments) == 1
        assert attachments[0]['path'] == '/path/to/file.pdf'
        assert attachments[0]['name'] == 'document.pdf'
        assert attachments[0]['mime'] == 'application/pdf'
    
    def test_mailable_attach_data(self):
        mailable = Mailable()
        data = b'file content'
        mailable.attach_data(data, 'file.txt', 'text/plain')
        
        attachments = mailable.get_raw_attachments()
        assert len(attachments) == 1
        assert attachments[0]['data'] == data
        assert attachments[0]['name'] == 'file.txt'
        assert attachments[0]['mime'] == 'text/plain'
    
    def test_mailable_fluent_interface(self):
        mailable = (Mailable()
            .to('test@example.com')
            .from_address('from@example.com')
            .subject('Test')
            .html('<p>Test</p>'))
        
        assert mailable.get_to()[0].email == 'test@example.com'
        assert mailable.get_from().email == 'from@example.com'
        assert mailable.get_subject() == 'Test'
        assert mailable.get_html() == '<p>Test</p>'


class TestMessage:
    
    def test_message_set_from(self):
        message = Message()
        message.set_from('from@example.com', 'From User')
        
        msg = message.get_message()
        assert 'From User' in msg['From']
        assert 'from@example.com' in msg['From']
    
    def test_message_set_to(self):
        message = Message()
        message.set_to(['to@example.com'])
        
        msg = message.get_message()
        assert msg['To'] == 'to@example.com'
    
    def test_message_set_cc(self):
        message = Message()
        message.set_cc(['cc@example.com'])
        
        msg = message.get_message()
        assert msg['Cc'] == 'cc@example.com'
    
    def test_message_set_subject(self):
        message = Message()
        message.set_subject('Test Subject')
        
        msg = message.get_message()
        assert msg['Subject'] == 'Test Subject'
    
    def test_message_set_html_body(self):
        message = Message()
        message.set_html_body('<h1>Test</h1>')
        
        msg_str = message.as_string()
        assert 'text/html' in msg_str
    
    def test_message_set_text_body(self):
        message = Message()
        message.set_text_body('Plain text')
        
        msg_str = message.as_string()
        assert 'text/plain' in msg_str
    
    def test_message_html_and_text(self):
        message = Message()
        message.set_text_body('Plain text')
        message.set_html_body('<h1>HTML</h1>')
        
        msg_str = message.as_string()
        assert 'text/plain' in msg_str
        assert 'text/html' in msg_str


class TestMailer:
    
    def test_mailer_initialization(self):
        transport = SmtpTransport({
            'host': 'localhost',
            'port': 587,
            'username': 'test',
            'password': 'password'
        })
        from_address = Address('from@example.com', 'From User')
        
        mailer = Mailer(transport, from_address)
        
        assert mailer.transport == transport
        assert mailer.from_address == from_address
    
    def test_mailer_sets_from_if_not_provided(self):
        transport = SmtpTransport({'host': 'localhost', 'port': 587})
        from_address = Address('default@example.com')
        mailer = Mailer(transport, from_address)
        
        mailable = Mailable().to('to@example.com').subject('Test')
        
        assert mailable.get_from() is None


class TestMailManager:
    
    def test_mail_manager_initialization(self):
        config = {
            'default': 'smtp',
            'mailers': {
                'smtp': {
                    'transport': 'smtp',
                    'host': 'localhost',
                    'port': 587
                }
            },
            'from': {
                'address': 'from@example.com',
                'name': 'From User'
            }
        }
        
        manager = MailManager(config)
        
        assert manager.config == config
        assert manager.get_default_driver() == 'smtp'
    
    def test_mail_manager_get_config(self):
        config = {
            'mailers': {
                'smtp': {
                    'host': 'localhost',
                    'port': 587
                }
            }
        }
        
        manager = MailManager(config)
        smtp_config = manager.get_config('smtp')
        
        assert smtp_config['host'] == 'localhost'
        assert smtp_config['port'] == 587
    
    def test_mail_manager_get_config_missing_raises_error(self):
        config = {'mailers': {}}
        manager = MailManager(config)
        
        with pytest.raises(ValueError, match="not found"):
            manager.get_config('missing')
    
    def test_mail_manager_mailer_returns_same_instance(self):
        config = {
            'default': 'smtp',
            'mailers': {
                'smtp': {
                    'transport': 'smtp',
                    'host': 'localhost',
                    'port': 587
                }
            }
        }
        
        manager = MailManager(config)
        mailer1 = manager.mailer('smtp')
        mailer2 = manager.mailer('smtp')
        
        assert mailer1 is mailer2
    
    def test_mail_manager_purge(self):
        config = {
            'default': 'smtp',
            'mailers': {
                'smtp': {
                    'transport': 'smtp',
                    'host': 'localhost',
                    'port': 587
                }
            }
        }
        
        manager = MailManager(config)
        mailer1 = manager.mailer('smtp')
        manager.purge('smtp')
        mailer2 = manager.mailer('smtp')
        
        assert mailer1 is not mailer2


class TestSmtpTransport:
    
    def test_smtp_transport_initialization(self):
        config = {
            'host': 'smtp.example.com',
            'port': 587,
            'username': 'user',
            'password': 'pass',
            'encryption': 'tls',
            'timeout': 30
        }
        
        transport = SmtpTransport(config)
        
        assert transport.host == 'smtp.example.com'
        assert transport.port == 587
        assert transport.username == 'user'
        assert transport.password == 'pass'
        assert transport.encryption == 'tls'
        assert transport.timeout == 30
    
    def test_smtp_transport_defaults(self):
        transport = SmtpTransport({})
        
        assert transport.host == 'localhost'
        assert transport.port == 587
        assert transport.encryption == 'tls'
        assert transport.timeout == 30


class TestAddress:
    
    def test_address_with_name(self):
        addr = Address('test@example.com', 'Test User')
        
        assert addr.email == 'test@example.com'
        assert addr.name == 'Test User'
        assert str(addr) == '"Test User" <test@example.com>'
    
    def test_address_without_name(self):
        addr = Address('test@example.com')
        
        assert addr.email == 'test@example.com'
        assert addr.name is None
        assert str(addr) == 'test@example.com'
