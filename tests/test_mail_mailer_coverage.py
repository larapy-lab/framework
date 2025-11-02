import pytest
import tempfile
from pathlib import Path
from larapy.mail.mailer import Mailer
from larapy.mail.mailable import Mailable, Address
from larapy.mail.message import Message
from larapy.mail.transports.transport import Transport


class MockTransport(Transport):
    def __init__(self):
        self.sent_messages = []
        self.sent_recipients = []
        self.should_fail = False
    
    def send(self, message: Message, recipients):
        if self.should_fail:
            raise RuntimeError("Transport failure")
        
        self.sent_messages.append(message)
        self.sent_recipients.append(recipients)
        return True


class MockViewEngine:
    def __init__(self, templates=None):
        self.templates = templates or {}
        self.rendered_views = []
    
    def render(self, view, data):
        self.rendered_views.append({'view': view, 'data': data})
        return self.templates.get(view, f"Rendered: {view}")


class TestMailerBasicFunctionality:
    
    def test_mailer_sends_basic_email(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Test Email')
        mailable.html('<p>Hello World</p>')
        
        result = mailer.send(mailable)
        
        assert result is True
        assert len(transport.sent_messages) == 1
        assert 'user@example.com' in transport.sent_recipients[0]
    
    def test_mailer_applies_default_from_address(self):
        transport = MockTransport()
        default_from = Address('noreply@example.com', 'No Reply')
        mailer = Mailer(transport, from_address=default_from)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        message = transport.sent_messages[0]
        assert 'noreply@example.com' in message.as_string()
    
    def test_mailer_respects_mailable_from_over_default(self):
        transport = MockTransport()
        default_from = Address('noreply@example.com', 'No Reply')
        mailer = Mailer(transport, from_address=default_from)
        
        mailable = Mailable()
        mailable.from_address(Address('custom@example.com', 'Custom Sender'))
        mailable.to('recipient@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        message = transport.sent_messages[0]
        message_str = message.as_string()
        assert 'custom@example.com' in message_str
        assert 'noreply@example.com' not in message_str
    
    def test_mailer_raises_error_without_recipients(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        with pytest.raises(ValueError, match="No recipients specified"):
            mailer.send(mailable)
    
    def test_mailer_sends_to_multiple_recipients(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('user1@example.com')
        mailable.to('user2@example.com')
        mailable.cc('cc@example.com')
        mailable.bcc('bcc@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        recipients = transport.sent_recipients[0]
        assert 'user1@example.com' in recipients
        assert 'user2@example.com' in recipients
        assert 'cc@example.com' in recipients
        assert 'bcc@example.com' in recipients
    
    def test_mailer_deduplicates_recipients(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.cc('user@example.com')
        mailable.bcc('user@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        recipients = transport.sent_recipients[0]
        assert recipients.count('user@example.com') == 1


class TestMailerViewRendering:
    
    def test_mailer_renders_html_view(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.welcome': '<h1>Welcome {{ name }}</h1>'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Welcome')
        mailable.view('emails.welcome', {'name': 'John'})
        
        mailer.send(mailable)
        
        assert len(view_engine.rendered_views) == 1
        assert view_engine.rendered_views[0]['view'] == 'emails.welcome'
        assert view_engine.rendered_views[0]['data']['name'] == 'John'
    
    def test_mailer_renders_text_view(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.welcome_text': 'Welcome {{ name }}'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Welcome')
        mailable.text('emails.welcome_text', {'name': 'John'})
        
        mailer.send(mailable)
        
        assert len(view_engine.rendered_views) == 1
        assert view_engine.rendered_views[0]['view'] == 'emails.welcome_text'
    
    def test_mailer_renders_both_html_and_text_views(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.welcome': '<h1>Welcome {{ name }}</h1>',
            'emails.welcome_text': 'Welcome {{ name }}'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Welcome')
        mailable.view('emails.welcome', {'name': 'John'})
        mailable.text('emails.welcome_text', {'name': 'John'})
        
        mailer.send(mailable)
        
        assert len(view_engine.rendered_views) == 2
    
    def test_mailer_skips_view_rendering_when_html_provided(self):
        transport = MockTransport()
        view_engine = MockViewEngine()
        mailer = Mailer(transport, view_engine=view_engine)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Test')
        mailable.html('<p>Direct HTML</p>')
        mailable.view('emails.test', {})
        
        mailer.send(mailable)
        
        assert len(view_engine.rendered_views) == 0
    
    def test_mailer_skips_text_view_rendering_when_text_provided(self):
        transport = MockTransport()
        view_engine = MockViewEngine()
        mailer = Mailer(transport, view_engine=view_engine)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Test')
        mailable.text_content('Direct text')
        mailable.text('emails.test', {})
        
        mailer.send(mailable)
        
        assert len(view_engine.rendered_views) == 0
    
    def test_mailer_without_view_engine_skips_rendering(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('user@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        mailable.view('emails.test', {})
        
        result = mailer.send(mailable)
        assert result is True


class TestMailerMessageBuilding:
    
    def test_mailer_builds_complete_message(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.from_address(Address('sender@example.com', 'Sender'))
        mailable.to('recipient@example.com')
        mailable.cc('cc@example.com')
        mailable.bcc('bcc@example.com')
        mailable.reply_to('reply@example.com')
        mailable.subject('Complete Email')
        mailable.html('<p>HTML Content</p>')
        mailable.text_content('Text Content')
        
        mailer.send(mailable)
        
        message = transport.sent_messages[0]
        message_str = message.as_string()
        
        assert 'sender@example.com' in message_str
        assert 'recipient@example.com' in message_str
        assert 'cc@example.com' in message_str
        assert 'reply@example.com' in message_str
        assert 'Complete Email' in message_str
    
    def test_mailer_builds_message_without_optional_fields(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.subject('Minimal Email')
        mailable.html('<p>Content</p>')
        
        result = mailer.send(mailable)
        assert result is True
    
    def test_mailer_handles_multiple_to_addresses(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('user1@example.com')
        mailable.to('user2@example.com')
        mailable.to('user3@example.com')
        mailable.subject('Multi-recipient')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        recipients = transport.sent_recipients[0]
        assert len(recipients) == 3
        assert 'user1@example.com' in recipients
        assert 'user2@example.com' in recipients
        assert 'user3@example.com' in recipients
    
    def test_mailer_handles_multiple_cc_addresses(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.cc('cc1@example.com')
        mailable.cc('cc2@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        recipients = transport.sent_recipients[0]
        assert 'cc1@example.com' in recipients
        assert 'cc2@example.com' in recipients
    
    def test_mailer_handles_multiple_bcc_addresses(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.bcc('bcc1@example.com')
        mailable.bcc('bcc2@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        recipients = transport.sent_recipients[0]
        assert 'bcc1@example.com' in recipients
        assert 'bcc2@example.com' in recipients
    
    def test_mailer_handles_multiple_reply_to_addresses(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.reply_to('reply1@example.com')
        mailable.reply_to('reply2@example.com')
        mailable.subject('Test')
        mailable.html('<p>Content</p>')
        
        mailer.send(mailable)
        
        message = transport.sent_messages[0]
        message_str = message.as_string()
        assert 'reply1@example.com' in message_str
        assert 'reply2@example.com' in message_str


class TestMailerAttachments:
    
    def test_mailer_sends_email_with_file_attachment(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test attachment content')
            temp_path = f.name
        
        try:
            mailable = Mailable()
            mailable.to('recipient@example.com')
            mailable.subject('With Attachment')
            mailable.html('<p>See attachment</p>')
            mailable.attach(temp_path)
            
            mailer.send(mailable)
            
            message = transport.sent_messages[0]
            message_str = message.as_string()
            assert 'Content-Disposition: attachment' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_mailer_sends_email_with_raw_data_attachment(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        mailable = Mailable()
        mailable.to('recipient@example.com')
        mailable.subject('With Data Attachment')
        mailable.html('<p>See attachment</p>')
        mailable.attach_data(b'Binary data', 'data.bin', 'application/octet-stream')
        
        mailer.send(mailable)
        
        message = transport.sent_messages[0]
        message_str = message.as_string()
        assert 'Content-Disposition: attachment' in message_str
        assert 'data.bin' in message_str
    
    def test_mailer_sends_email_with_multiple_attachments(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        temp_files = []
        try:
            for i in range(3):
                f = tempfile.NamedTemporaryFile(mode='w', suffix=f'.txt', delete=False)
                f.write(f'Content {i}')
                f.close()
                temp_files.append(f.name)
            
            mailable = Mailable()
            mailable.to('recipient@example.com')
            mailable.subject('Multiple Attachments')
            mailable.html('<p>See attachments</p>')
            
            for temp_file in temp_files:
                mailable.attach(temp_file)
            
            mailer.send(mailable)
            
            message = transport.sent_messages[0]
            assert message is not None
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_mailer_sends_email_with_mixed_attachments(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('File content')
            temp_path = f.name
        
        try:
            mailable = Mailable()
            mailable.to('recipient@example.com')
            mailable.subject('Mixed Attachments')
            mailable.html('<p>See attachments</p>')
            mailable.attach(temp_path)
            mailable.attach_data(b'Data content', 'data.bin')
            
            mailer.send(mailable)
            
            message = transport.sent_messages[0]
            message_str = message.as_string()
            assert message_str.count('Content-Disposition: attachment') == 2
        finally:
            Path(temp_path).unlink()


class TestMailerRealWorldScenarios:
    
    def test_welcome_email_with_verification_link(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.welcome': '<h1>Welcome {{ user_name }}</h1><p><a href="{{ verification_url }}">Verify Email</a></p>',
            'emails.welcome_text': 'Welcome {{ user_name }}\n\nVerify: {{ verification_url }}'
        })
        mailer = Mailer(
            transport,
            from_address=Address('noreply@myapp.com', 'MyApp'),
            view_engine=view_engine
        )
        
        user_data = {
            'user_name': 'Alice Johnson',
            'user_email': 'alice@example.com',
            'verification_url': 'https://myapp.com/verify/abc123'
        }
        
        mailable = Mailable()
        mailable.to(user_data['user_email'])
        mailable.subject('Welcome to MyApp - Verify Your Email')
        mailable.view('emails.welcome', user_data)
        mailable.text('emails.welcome_text', user_data)
        
        result = mailer.send(mailable)
        
        assert result is True
        assert len(transport.sent_messages) == 1
        assert user_data['user_email'] in transport.sent_recipients[0]
        assert len(view_engine.rendered_views) == 2
    
    def test_password_reset_email(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.password_reset': '<h1>Password Reset</h1><p>Token: {{ token }}</p>'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        reset_data = {
            'user_email': 'user@example.com',
            'token': 'reset_token_xyz789',
            'expiry_minutes': 60
        }
        
        mailable = Mailable()
        mailable.to(reset_data['user_email'])
        mailable.subject('Reset Your Password')
        mailable.view('emails.password_reset', reset_data)
        mailable.reply_to('support@myapp.com')
        
        result = mailer.send(mailable)
        
        assert result is True
        assert 'support@myapp.com' in transport.sent_messages[0].as_string()
    
    def test_order_confirmation_email_with_invoice(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.order_confirmation': '<h1>Order {{ order_id }}</h1><p>Total: ${{ total }}</p>'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write('Invoice PDF content')
            invoice_path = f.name
        
        try:
            order_data = {
                'order_id': 'ORD-12345',
                'customer_email': 'customer@example.com',
                'customer_name': 'Bob Smith',
                'total': '149.99',
                'items': [
                    {'name': 'Product A', 'price': '99.99'},
                    {'name': 'Product B', 'price': '50.00'}
                ]
            }
            
            mailable = Mailable()
            mailable.to(order_data['customer_email'])
            mailable.cc('orders@mystore.com')
            mailable.subject(f"Order Confirmation - {order_data['order_id']}")
            mailable.view('emails.order_confirmation', order_data)
            mailable.attach(invoice_path, 'invoice.pdf')
            
            result = mailer.send(mailable)
            
            assert result is True
            assert 'orders@mystore.com' in transport.sent_recipients[0]
        finally:
            Path(invoice_path).unlink()
    
    def test_newsletter_to_multiple_subscribers(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.newsletter': '<h1>{{ title }}</h1><p>{{ content }}</p>'
        })
        mailer = Mailer(
            transport,
            from_address=Address('newsletter@myapp.com', 'MyApp Newsletter'),
            view_engine=view_engine
        )
        
        subscribers = [
            'subscriber1@example.com',
            'subscriber2@example.com',
            'subscriber3@example.com'
        ]
        
        newsletter_data = {
            'title': 'Monthly Update - November 2025',
            'content': 'Check out our latest features and updates!'
        }
        
        mailable = Mailable()
        for subscriber in subscribers:
            mailable.bcc(subscriber)
        
        mailable.to('newsletter@myapp.com')
        mailable.subject(newsletter_data['title'])
        mailable.view('emails.newsletter', newsletter_data)
        
        result = mailer.send(mailable)
        
        assert result is True
        recipients = transport.sent_recipients[0]
        for subscriber in subscribers:
            assert subscriber in recipients
    
    def test_support_ticket_notification(self):
        transport = MockTransport()
        mailer = Mailer(transport)
        
        ticket_data = {
            'ticket_id': 'TICKET-567',
            'customer_email': 'customer@example.com',
            'customer_name': 'Jane Doe',
            'subject': 'Login issues',
            'message': 'I cannot log into my account',
            'priority': 'High'
        }
        
        customer_email = Mailable()
        customer_email.to(ticket_data['customer_email'])
        customer_email.subject(f"Support Ticket Created - {ticket_data['ticket_id']}")
        customer_email.html(f"<p>Your ticket {ticket_data['ticket_id']} has been created.</p>")
        customer_email.reply_to('support@myapp.com')
        
        mailer.send(customer_email)
        
        support_email = Mailable()
        support_email.to('support@myapp.com')
        support_email.subject(f"[{ticket_data['priority']}] New Ticket - {ticket_data['ticket_id']}")
        support_email.html(f"<p><strong>From:</strong> {ticket_data['customer_name']}</p><p><strong>Subject:</strong> {ticket_data['subject']}</p>")
        support_email.reply_to(ticket_data['customer_email'])
        
        mailer.send(support_email)
        
        assert len(transport.sent_messages) == 2
    
    def test_team_collaboration_email_with_mentions(self):
        transport = MockTransport()
        view_engine = MockViewEngine({
            'emails.task_assigned': '<h1>Task Assigned</h1><p>{{ assigner }} assigned you to {{ task_title }}</p>'
        })
        mailer = Mailer(transport, view_engine=view_engine)
        
        task_data = {
            'task_id': 'TASK-789',
            'task_title': 'Update documentation',
            'assignee_email': 'developer@myapp.com',
            'assigner': 'Manager',
            'watchers': ['watcher1@myapp.com', 'watcher2@myapp.com'],
            'due_date': '2025-11-10'
        }
        
        mailable = Mailable()
        mailable.to(task_data['assignee_email'])
        for watcher in task_data['watchers']:
            mailable.cc(watcher)
        
        mailable.subject(f"Task Assigned: {task_data['task_title']}")
        mailable.view('emails.task_assigned', task_data)
        
        result = mailer.send(mailable)
        
        assert result is True
        recipients = transport.sent_recipients[0]
        assert task_data['assignee_email'] in recipients
        for watcher in task_data['watchers']:
            assert watcher in recipients
