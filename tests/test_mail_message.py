import pytest
from larapy.notifications.messages import MailMessage


class TestMailMessage:
    def test_mail_message_can_set_subject(self):
        message = MailMessage()
        
        message.subject('Test Subject')
        
        assert message.subject_text == 'Test Subject'
    
    def test_mail_message_can_set_greeting(self):
        message = MailMessage()
        
        message.greeting('Hello User')
        
        assert message.greeting_text == 'Hello User'
    
    def test_mail_message_can_add_lines(self):
        message = MailMessage()
        
        message.line('First line').line('Second line')
        
        assert len(message.intro_lines) == 2
        assert message.intro_lines[0] == 'First line'
        assert message.intro_lines[1] == 'Second line'
    
    def test_mail_message_can_add_multiple_lines_at_once(self):
        message = MailMessage()
        
        message.lines(['First line', 'Second line', 'Third line'])
        
        assert len(message.intro_lines) == 3
    
    def test_mail_message_can_set_action(self):
        message = MailMessage()
        
        message.action('Click Here', 'https://example.com')
        
        assert message.action_text == 'Click Here'
        assert message.action_url == 'https://example.com'
    
    def test_mail_message_action_with_color(self):
        message = MailMessage()
        
        message.action('Click Here', 'https://example.com', 'blue')
        
        assert message.action_color == 'blue'
    
    def test_mail_message_can_set_level_to_success(self):
        message = MailMessage()
        
        message.success()
        
        assert message.level == 'success'
    
    def test_mail_message_can_set_level_to_error(self):
        message = MailMessage()
        
        message.error()
        
        assert message.level == 'error'
    
    def test_mail_message_can_set_level_to_warning(self):
        message = MailMessage()
        
        message.warning()
        
        assert message.level == 'warning'
    
    def test_mail_message_default_level_is_info(self):
        message = MailMessage()
        
        assert message.level == 'info'
    
    def test_mail_message_can_set_salutation(self):
        message = MailMessage()
        
        message.salutation('Best regards')
        
        assert message.salutation_text == 'Best regards'
    
    def test_mail_message_fluent_api(self):
        message = (MailMessage()
            .subject('Welcome!')
            .greeting('Hello User')
            .line('Thank you for signing up.')
            .action('Get Started', 'https://example.com/dashboard')
            .line('If you have any questions, contact us.')
            .success())
        
        assert message.subject_text == 'Welcome!'
        assert message.greeting_text == 'Hello User'
        assert len(message.intro_lines) == 2
        assert message.action_text == 'Get Started'
        assert message.level == 'success'
    
    def test_mail_message_can_set_view(self):
        message = MailMessage()
        
        message.view('emails.welcome', {'name': 'John'})
        
        assert message.view_template == 'emails.welcome'
        assert message.view_data == {'name': 'John'}
    
    def test_mail_message_can_set_markdown(self):
        message = MailMessage()
        
        message.markdown('emails.welcome', {'name': 'John'})
        
        assert message.markdown_template == 'emails.welcome'
        assert message.view_data == {'name': 'John'}
    
    def test_mail_message_to_dict_includes_all_properties(self):
        message = (MailMessage()
            .subject('Test')
            .greeting('Hello')
            .line('Content')
            .action('Click', 'https://example.com')
            .success())
        
        data = message.to_dict()
        
        assert data['subject'] == 'Test'
        assert data['greeting'] == 'Hello'
        assert 'Content' in data['intro_lines']
        assert data['action_text'] == 'Click'
        assert data['action_url'] == 'https://example.com'
        assert data['level'] == 'success'
    
    def test_mail_message_can_set_from_address(self):
        message = MailMessage()
        
        message.from_email('noreply@example.com', 'Example')
        
        assert message.from_address == ('noreply@example.com', 'Example')
    
    def test_mail_message_can_set_reply_to(self):
        message = MailMessage()
        
        message.replyTo('support@example.com')
        
        assert message.reply_to_address == 'support@example.com'
    
    def test_mail_message_can_add_cc_recipients(self):
        message = MailMessage()
        
        message.cc('user1@example.com').cc('user2@example.com', 'User Two')
        
        assert len(message.cc_addresses) == 2
        assert message.cc_addresses[0] == 'user1@example.com'
        assert message.cc_addresses[1] == ('user2@example.com', 'User Two')
    
    def test_mail_message_can_add_bcc_recipients(self):
        message = MailMessage()
        
        message.bcc('hidden@example.com')
        
        assert len(message.bcc_addresses) == 1
        assert message.bcc_addresses[0] == 'hidden@example.com'
    
    def test_mail_message_can_attach_files(self):
        message = MailMessage()
        
        message.attach('/path/to/file.pdf', {'mime': 'application/pdf'})
        
        assert len(message.attachments) == 1
        assert message.attachments[0]['file'] == '/path/to/file.pdf'
        assert message.attachments[0]['options']['mime'] == 'application/pdf'
    
    def test_mail_message_can_attach_raw_data(self):
        message = MailMessage()
        
        message.attach_data(b'file content', 'document.txt')
        
        assert len(message.raw_attachments) == 1
        assert message.raw_attachments[0]['data'] == b'file content'
        assert message.raw_attachments[0]['name'] == 'document.txt'
    
    def test_mail_message_can_set_priority(self):
        message = MailMessage()
        
        message.priority_level(1)
        
        assert message.priority == 1
    
    def test_mail_message_with_content_is_alias_for_line(self):
        message = MailMessage()
        
        message.with_content('Test content')
        
        assert 'Test content' in message.intro_lines
