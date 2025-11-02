import pytest
import tempfile
from pathlib import Path
from larapy.mail.message import Message


class TestMessageBasicFunctionality:
    
    def test_message_sets_from_address_with_name(self):
        message = Message()
        message.set_from('sender@example.com', 'John Doe')
        
        message_str = message.as_string()
        assert '"John Doe" <sender@example.com>' in message_str
    
    def test_message_sets_from_address_without_name(self):
        message = Message()
        message.set_from('sender@example.com')
        
        message_str = message.as_string()
        assert 'sender@example.com' in message_str
    
    def test_message_sets_single_to_recipient(self):
        message = Message()
        message.set_to(['recipient@example.com'])
        
        message_str = message.as_string()
        assert 'To: recipient@example.com' in message_str
    
    def test_message_sets_multiple_to_recipients(self):
        message = Message()
        message.set_to(['user1@example.com', 'user2@example.com', 'user3@example.com'])
        
        message_str = message.as_string()
        assert 'user1@example.com' in message_str
        assert 'user2@example.com' in message_str
        assert 'user3@example.com' in message_str
    
    def test_message_sets_cc_recipients(self):
        message = Message()
        message.set_cc(['cc1@example.com', 'cc2@example.com'])
        
        message_str = message.as_string()
        assert 'Cc:' in message_str
        assert 'cc1@example.com' in message_str
        assert 'cc2@example.com' in message_str
    
    def test_message_sets_empty_cc_recipients(self):
        message = Message()
        message.set_cc([])
        
        message_str = message.as_string()
        assert 'Cc:' not in message_str
    
    def test_message_sets_bcc_recipients(self):
        message = Message()
        result = message.set_bcc(['bcc@example.com'])
        
        assert result == message
    
    def test_message_sets_reply_to_addresses(self):
        message = Message()
        message.set_reply_to(['reply1@example.com', 'reply2@example.com'])
        
        message_str = message.as_string()
        assert 'Reply-To:' in message_str
        assert 'reply1@example.com' in message_str
    
    def test_message_sets_empty_reply_to(self):
        message = Message()
        message.set_reply_to([])
        
        message_str = message.as_string()
        assert 'Reply-To:' not in message_str
    
    def test_message_sets_subject(self):
        message = Message()
        message.set_subject('Test Email Subject')
        
        message_str = message.as_string()
        assert 'Subject: Test Email Subject' in message_str
    
    def test_message_subject_with_special_characters(self):
        message = Message()
        message.set_subject('Important: Update Required!')
        
        message_str = message.as_string()
        assert 'Important: Update Required!' in message_str


class TestMessageContentTypes:
    
    def test_message_sets_html_body(self):
        message = Message()
        message.set_html_body('<h1>Hello World</h1><p>This is HTML</p>')
        
        message_str = message.as_string()
        assert 'Content-Type: text/html' in message_str
        assert 'base64' in message_str or '<h1>Hello World</h1>' in message_str
    
    def test_message_sets_text_body(self):
        message = Message()
        message.set_text_body('Hello World\nThis is plain text')
        
        message_str = message.as_string()
        assert 'Content-Type: text/plain' in message_str
        assert 'base64' in message_str or 'Hello World' in message_str
    
    def test_message_sets_both_html_and_text_bodies(self):
        message = Message()
        message.set_html_body('<h1>HTML Version</h1>')
        message.set_text_body('Text Version')
        
        message_str = message.as_string()
        assert 'Content-Type: text/html' in message_str
        assert 'Content-Type: text/plain' in message_str
        assert 'base64' in message_str
    
    def test_message_html_body_with_utf8_characters(self):
        message = Message()
        message.set_html_body('<p>Héllo Wörld 你好 مرحبا</p>')
        
        message_str = message.as_string()
        assert 'charset="utf-8"' in message_str
    
    def test_message_text_body_with_utf8_characters(self):
        message = Message()
        message.set_text_body('Héllo Wörld 你好 مرحبا')
        
        message_str = message.as_string()
        assert 'charset="utf-8"' in message_str


class TestMessageAttachments:
    
    def test_message_attaches_text_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test file content')
            temp_path = f.name
        
        try:
            message = Message()
            message.attach_file(temp_path)
            
            message_str = message.as_string()
            assert 'Content-Disposition: attachment' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_message_attaches_file_with_custom_name(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Content')
            temp_path = f.name
        
        try:
            message = Message()
            message.attach_file(temp_path, name='custom_name.txt')
            
            message_str = message.as_string()
            assert 'custom_name.txt' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_message_attaches_file_with_custom_mime_type(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write('Data')
            temp_path = f.name
        
        try:
            message = Message()
            message.attach_file(temp_path, mime='application/custom')
            
            message_str = message.as_string()
            assert 'Content-Type: application/custom' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_message_raises_error_for_nonexistent_file(self):
        message = Message()
        
        with pytest.raises(FileNotFoundError, match="Attachment file not found"):
            message.attach_file('/nonexistent/file.txt')
    
    def test_message_attaches_pdf_file(self):
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 fake pdf content')
            temp_path = f.name
        
        try:
            message = Message()
            message.attach_file(temp_path)
            
            message_str = message.as_string()
            assert 'Content-Type: application/pdf' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_message_attaches_image_file(self):
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(b'\x89PNG fake image data')
            temp_path = f.name
        
        try:
            message = Message()
            message.attach_file(temp_path)
            
            message_str = message.as_string()
            assert 'Content-Type: image/png' in message_str
        finally:
            Path(temp_path).unlink()
    
    def test_message_attaches_multiple_files(self):
        temp_files = []
        try:
            for i in range(3):
                f = tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False)
                f.write(f'Content {i}')
                f.close()
                temp_files.append(f.name)
            
            message = Message()
            for temp_file in temp_files:
                message.attach_file(temp_file)
            
            message_str = message.as_string()
            assert message_str.count('Content-Disposition: attachment') == 3
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_message_attaches_data_with_name(self):
        message = Message()
        message.attach_data(b'Binary data content', 'data.bin')
        
        message_str = message.as_string()
        assert 'Content-Disposition: attachment' in message_str
        assert 'data.bin' in message_str
    
    def test_message_attaches_data_with_mime_type(self):
        message = Message()
        message.attach_data(b'JSON data', 'data.json', 'application/json')
        
        message_str = message.as_string()
        assert 'Content-Type: application/json' in message_str
        assert 'data.json' in message_str
    
    def test_message_attaches_data_without_mime_type(self):
        message = Message()
        message.attach_data(b'Unknown data', 'unknown.dat')
        
        message_str = message.as_string()
        assert 'Content-Type: application/octet-stream' in message_str
    
    def test_message_attaches_multiple_data_attachments(self):
        message = Message()
        message.attach_data(b'Data 1', 'file1.bin')
        message.attach_data(b'Data 2', 'file2.bin')
        message.attach_data(b'Data 3', 'file3.bin')
        
        message_str = message.as_string()
        assert message_str.count('Content-Disposition: attachment') == 3


class TestMessageFluentInterface:
    
    def test_message_fluent_chaining(self):
        message = (Message()
            .set_from('sender@example.com', 'Sender')
            .set_to(['recipient@example.com'])
            .set_cc(['cc@example.com'])
            .set_bcc(['bcc@example.com'])
            .set_reply_to(['reply@example.com'])
            .set_subject('Test Subject')
            .set_html_body('<p>HTML</p>')
            .set_text_body('Text'))
        
        message_str = message.as_string()
        assert 'sender@example.com' in message_str
        assert 'recipient@example.com' in message_str
        assert 'Test Subject' in message_str
    
    def test_message_fluent_with_attachments(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Attachment')
            temp_path = f.name
        
        try:
            message = (Message()
                .set_from('sender@example.com')
                .set_to(['recipient@example.com'])
                .set_subject('With Attachment')
                .set_html_body('<p>See attached</p>')
                .attach_file(temp_path))
            
            message_str = message.as_string()
            assert 'Content-Disposition: attachment' in message_str
        finally:
            Path(temp_path).unlink()


class TestMessageCompleteEmails:
    
    def test_message_builds_complete_marketing_email(self):
        message = Message()
        message.set_from('marketing@company.com', 'Company Marketing')
        message.set_to([
            'customer1@example.com',
            'customer2@example.com',
            'customer3@example.com'
        ])
        message.set_subject('Special Offer - 50% Off!')
        message.set_html_body('''
            <html>
                <body>
                    <h1>Limited Time Offer</h1>
                    <p>Get 50% off all products this week!</p>
                    <a href="https://company.com/sale">Shop Now</a>
                </body>
            </html>
        ''')
        message.set_text_body('Limited Time Offer\n\nGet 50% off!\n\nVisit: https://company.com/sale')
        
        message_str = message.as_string()
        assert 'marketing@company.com' in message_str
        assert 'Special Offer' in message_str
        assert 'base64' in message_str or '50% off' in message_str
    
    def test_message_builds_transactional_email_with_receipt(self):
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'PDF receipt content')
            receipt_path = f.name
        
        try:
            message = Message()
            message.set_from('orders@store.com', 'Online Store')
            message.set_to(['customer@example.com'])
            message.set_cc(['accounting@store.com'])
            message.set_subject('Order Confirmation #12345')
            message.set_html_body('<h1>Thank you for your order!</h1><p>Order #12345</p>')
            message.attach_file(receipt_path, 'receipt.pdf')
            
            message_str = message.as_string()
            assert 'Order Confirmation' in message_str
            assert 'receipt.pdf' in message_str
        finally:
            Path(receipt_path).unlink()
    
    def test_message_builds_support_ticket_email(self):
        message = Message()
        message.set_from('support@helpdesk.com', 'Support Team')
        message.set_to(['customer@example.com'])
        message.set_reply_to(['support@helpdesk.com'])
        message.set_subject('[Ticket #567] Your Issue Has Been Resolved')
        message.set_html_body('''
            <p>Hello Customer,</p>
            <p>Your support ticket #567 has been resolved.</p>
            <p>If you need further assistance, reply to this email.</p>
        ''')
        message.set_text_body('Your ticket #567 has been resolved.')
        
        message_str = message.as_string()
        assert 'Ticket #567' in message_str
        assert 'Reply-To: support@helpdesk.com' in message_str
    
    def test_message_builds_newsletter_with_images(self):
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(b'PNG image data')
            image_path = f.name
        
        try:
            message = Message()
            message.set_from('newsletter@magazine.com', 'Magazine')
            message.set_to(['subscriber@example.com'])
            message.set_subject('Weekly Newsletter - November 2025')
            message.set_html_body('<h1>This Week in Tech</h1><p>Latest news and updates...</p>')
            message.attach_file(image_path, 'header.png')
            
            message_str = message.as_string()
            assert 'Weekly Newsletter' in message_str
            assert 'header.png' in message_str
        finally:
            Path(image_path).unlink()
    
    def test_message_builds_invoice_email_with_multiple_attachments(self):
        temp_files = []
        try:
            invoice_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
            invoice_file.write(b'Invoice PDF')
            invoice_file.close()
            temp_files.append(invoice_file.name)
            
            terms_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            terms_file.write('Terms and conditions')
            terms_file.close()
            temp_files.append(terms_file.name)
            
            message = Message()
            message.set_from('billing@company.com', 'Billing Department')
            message.set_to(['client@example.com'])
            message.set_cc(['accounting@company.com'])
            message.set_subject('Invoice #INV-2025-001')
            message.set_html_body('<h1>Invoice Attached</h1><p>Payment due: 30 days</p>')
            message.attach_file(temp_files[0], 'invoice.pdf')
            message.attach_file(temp_files[1], 'terms.txt')
            
            message_str = message.as_string()
            assert 'Invoice #INV-2025-001' in message_str
            assert message_str.count('Content-Disposition: attachment') == 2
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_message_builds_event_invitation_with_calendar(self):
        calendar_data = b'''BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Team Meeting
DTSTART:20251110T140000Z
DTEND:20251110T150000Z
END:VEVENT
END:VCALENDAR'''
        
        message = Message()
        message.set_from('calendar@company.com', 'Company Calendar')
        message.set_to(['employee@company.com'])
        message.set_subject('Invitation: Team Meeting - Nov 10, 2025')
        message.set_html_body('<p>You are invited to Team Meeting</p><p>Nov 10, 2025 at 2:00 PM</p>')
        message.attach_data(calendar_data, 'meeting.ics', 'text/calendar')
        
        message_str = message.as_string()
        assert 'Team Meeting' in message_str
        assert 'meeting.ics' in message_str
        assert 'text/calendar' in message_str
    
    def test_message_builds_report_email_with_csv_attachment(self):
        csv_data = b'Name,Email,Status\nJohn,john@example.com,Active\nJane,jane@example.com,Active'
        
        message = Message()
        message.set_from('reports@analytics.com', 'Analytics System')
        message.set_to(['manager@company.com'])
        message.set_subject('Weekly User Report - Week 44, 2025')
        message.set_html_body('<p>Please find attached the weekly user report.</p>')
        message.attach_data(csv_data, 'users_report.csv', 'text/csv')
        
        message_str = message.as_string()
        assert 'Weekly User Report' in message_str
        assert 'users_report.csv' in message_str
        assert 'text/csv' in message_str
