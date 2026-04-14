"""
Email Sender Module (Email MCP)

Sends emails via Gmail API or SMTP.
Supports attachments, CC/BCC, and rate limiting.

Usage:
    python email_sender.py --to recipient@example.com --subject "Test" --body "Hello"
"""

import os
import sys
import argparse
import logging
import smtplib
import time
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EmailSender')


class EmailSender:
    """Send emails via Gmail API or SMTP."""
    
    def __init__(
        self,
        use_gmail_api: bool = True,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Initialize email sender.
        
        Args:
            use_gmail_api: Use Gmail API instead of SMTP
            credentials_path: Path to Gmail credentials.json
            token_path: Path to Gmail token.json
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            dry_run: Log emails without sending
        """
        self.use_gmail_api = use_gmail_api
        self.dry_run = dry_run
        self.gmail_service = None
        self.smtp_config = {
            'host': smtp_host,
            'port': smtp_port,
            'username': smtp_username,
            'password': smtp_password
        }
        
        # Rate limiting
        self.sent_count = 0
        self.last_sent_time = 0
        self.min_interval = 60  # Minimum seconds between emails
        
        # Initialize Gmail API if configured
        if use_gmail_api and credentials_path and GMAIL_AVAILABLE:
            self._initialize_gmail(credentials_path, token_path)
    
    def _initialize_gmail(self, credentials_path: str, token_path: str):
        """Initialize Gmail API service."""
        try:
            creds = None
            scopes = ['https://www.googleapis.com/auth/gmail.send']
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, scopes)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    print("Please authenticate Gmail...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, scopes
                    )
                    creds = flow.run_local_server(port=8080)
                
                with open(token_path, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info('Gmail API initialized successfully')
            
        except Exception as e:
            logger.error(f'Failed to initialize Gmail API: {e}')
            self.use_gmail_api = False
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        if current_time - self.last_sent_time < self.min_interval:
            wait_time = self.min_interval - (current_time - self.last_sent_time)
            logger.info(f'Rate limiting: waiting {wait_time:.1f} seconds...')
            time.sleep(wait_time)
        self.last_sent_time = time.time()
        self.sent_count += 1
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            attachments: List of file paths to attach
            html: Whether body is HTML
            
        Returns:
            True if sent successfully
        """
        if self.dry_run:
            logger.info(f'[DRY RUN] Would send email to {to}')
            logger.info(f'[DRY RUN] Subject: {subject}')
            return True
        
        # Rate limiting
        self._check_rate_limit()
        
        try:
            if self.use_gmail_api and self.gmail_service:
                return self._send_via_gmail_api(to, subject, body, cc, bcc, attachments, html)
            else:
                return self._send_via_smtp(to, subject, body, cc, bcc, attachments, html)
                
        except Exception as e:
            logger.error(f'Failed to send email: {e}')
            return False
    
    def _send_via_gmail_api(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str],
        bcc: Optional[str],
        attachments: Optional[List[str]],
        html: bool
    ) -> bool:
        """Send email via Gmail API."""
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            if cc:
                message['cc'] = cc
            # BCC not added to headers, handled separately in sending

            # Add body
            content_type = 'html' if html else 'plain'
            message.attach(MIMEText(body, content_type))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(open(filepath, 'rb').read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(filepath)}"'
                        )
                        message.attach(part)

            # Create RFC 2822 message and encode to base64url
            raw_message = message.as_string()
            
            # Gmail API requires base64url encoding
            import base64
            raw_message_base64 = base64.urlsafe_b64encode(raw_message.encode('utf-8')).decode('utf-8')

            # Send via Gmail API
            gmail_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message_base64}
            ).execute()

            logger.info(f'Email sent successfully via Gmail API. Message ID: {gmail_message.get("id")}')
            return True

        except Exception as e:
            logger.error(f'Gmail API send failed: {e}')
            raise
    
    def _send_via_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str],
        bcc: Optional[str],
        attachments: Optional[List[str]],
        html: bool
    ) -> bool:
        """Send email via SMTP."""
        if not self.smtp_config.get('host'):
            raise ValueError("SMTP not configured. Use Gmail API or configure SMTP settings.")
        
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.smtp_config['username']
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            
            # Add body
            content_type = 'html' if html else 'plain'
            message.attach(MIMEText(body, content_type))
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(open(filepath, 'rb').read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(filepath)}"'
                        )
                        message.attach(part)
            
            # Build recipient list
            recipients = [to]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))
            
            # Send via SMTP
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.sendmail(self.smtp_config['username'], recipients, message.as_string())
            server.quit()
            
            logger.info(f'Email sent successfully via SMTP to {recipients}')
            return True
            
        except Exception as e:
            logger.error(f'SMTP send failed: {e}')
            raise


def parse_action_file(filepath: Path) -> Dict[str, Any]:
    """Parse email action file."""
    content = filepath.read_text(encoding='utf-8')
    
    data = {
        'to': '',
        'subject': '',
        'body': '',
        'cc': None,
        'bcc': None,
        'attachments': []
    }
    
    # Simple parsing (improve with proper frontmatter parser)
    lines = content.split('\n')
    in_frontmatter = False
    in_body = False
    
    for line in lines:
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                in_frontmatter = False
                in_body = True
                continue
        
        if in_frontmatter:
            if line.startswith('to:'):
                data['to'] = line.split(':', 1)[1].strip()
            elif line.startswith('subject:'):
                data['subject'] = line.split(':', 1)[1].strip()
            elif line.startswith('cc:'):
                data['cc'] = line.split(':', 1)[1].strip()
            elif line.startswith('bcc:'):
                data['bcc'] = line.split(':', 1)[1].strip()
            elif line.startswith('- /') and 'Attachments' in content:
                data['attachments'].append(line[2:].strip())
        elif in_body and not line.startswith('#') and not line.startswith('<!--'):
            data['body'] += line + '\n'
    
    return data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Email Sender (Email MCP)')
    parser.add_argument('--to', type=str, help='Recipient email address')
    parser.add_argument('--subject', type=str, help='Email subject')
    parser.add_argument('--body', type=str, help='Email body')
    parser.add_argument('--cc', type=str, help='CC recipients')
    parser.add_argument('--bcc', type=str, help='BCC recipients')
    parser.add_argument('--attachment', action='append', help='Attachment file path')
    parser.add_argument('--html', action='store_true', help='Body is HTML')
    parser.add_argument('--action-file', type=Path, help='Email action file to process')
    parser.add_argument('--dry-run', action='store_true', help='Log without sending')
    parser.add_argument('--smtp', action='store_true', help='Use SMTP instead of Gmail API')
    parser.add_argument('--credentials', type=str, help='Gmail credentials.json path')
    parser.add_argument('--token', type=str, help='Gmail token.json path')
    
    args = parser.parse_args()
    
    # Parse action file if provided
    if args.action_file:
        data = parse_action_file(args.action_file)
        args.to = args.to or data['to']
        args.subject = args.subject or data['subject']
        args.body = args.body or data['body']
        args.cc = args.cc or data['cc']
        args.bcc = args.bcc or data['bcc']
        args.attachment = args.attachment or data['attachments']
    
    # Validate required args
    if not args.to or not args.subject:
        print("Error: --to and --subject are required")
        sys.exit(1)
    
    # Determine credentials paths
    credentials_path = args.credentials or os.getenv('GMAIL_CREDENTIALS_PATH')
    token_path = args.token or str(Path.home() / '.gmail_token.json')
    
    # Create sender
    sender = EmailSender(
        use_gmail_api=not args.smtp,
        credentials_path=credentials_path,
        token_path=token_path,
        smtp_host=os.getenv('SMTP_HOST'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        smtp_username=os.getenv('SMTP_USERNAME'),
        smtp_password=os.getenv('SMTP_PASSWORD'),
        dry_run=args.dry_run
    )
    
    # Send email
    success = sender.send_email(
        to=args.to,
        subject=args.subject,
        body=args.body or '',
        cc=args.cc,
        bcc=args.bcc,
        attachments=args.attachment,
        html=args.html
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
            