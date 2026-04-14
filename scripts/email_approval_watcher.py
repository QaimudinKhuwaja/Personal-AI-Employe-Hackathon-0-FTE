"""
Email Approval Watcher

Monitors the Approved/ folder for email approval files and sends them via Gmail API.
This is the missing piece that actually sends approved emails.

Usage:
    python email_approval_watcher.py /path/to/vault --credentials /path/to/credentials.json

Or with custom options:
    python email_approval_watcher.py /path/to/vault --credentials credentials.json --interval 30
"""

import os
import sys
import argparse
import logging
import time
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Missing required packages. Install with:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Gmail API scopes for sending (request both read and send)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


class EmailApprovalWatcher:
    """
    Watches Approved/ folder for email approval files and sends them.
    """

    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        check_interval: int = 30
    ):
        """
        Initialize the email approval watcher.

        Args:
            vault_path: Path to the Obsidian vault root directory
            credentials_path: Path to Gmail OAuth credentials.json
            check_interval: Seconds between checks (default: 30)
        """
        self.vault_path = Path(vault_path)
        self.credentials_path = Path(credentials_path)
        self.check_interval = check_interval

        # Define folders
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.rejected = self.vault_path / 'Rejected'
        self.logs = self.vault_path / 'Logs'

        # Ensure directories exist
        for folder in [self.approved, self.done, self.rejected, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Gmail service
        self.gmail_service = None
        self._initialize_gmail()

        self.logger.info(f'Initialized Email Approval Watcher')
        self.logger.info(f'Vault: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')

    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.logs / f'email_sender_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('EmailApprovalWatcher')

    def _initialize_gmail(self):
        """Initialize Gmail API service for sending emails."""
        try:
            creds = None
            token_path = self.vault_path / '.gmail_token.json'

            # Load token from file if exists
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # Refresh or obtain new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    self.logger.info('Starting OAuth authentication flow...')
                    self.logger.info('Opening browser for Gmail authentication...')
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=8080, open_browser=True)
                    self.logger.info('Authentication successful!')

                # Save credentials for next run
                with open(token_path, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())

            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail send service initialized successfully')

        except Exception as e:
            self.logger.error(f'Failed to initialize Gmail service: {e}')
            raise

    def get_approved_emails(self) -> List[Path]:
        """
        Get all approved email files waiting to be sent.

        Returns:
            List of Path objects for approved email files
        """
        if not self.approved.exists():
            return []

        approved_files = []
        for filepath in self.approved.iterdir():
            if filepath.is_file() and filepath.suffix == '.md':
                # Skip hidden files
                if not filepath.name.startswith('.'):
                    # Check if it's an email approval file
                    content = filepath.read_text(encoding='utf-8')
                    if 'type: email_response' in content or 'type: approval_request' in content:
                        approved_files.append(filepath)

        return sorted(approved_files, key=lambda p: p.stat().st_mtime)

    def send_approved_emails(self, files: List[Path]) -> tuple:
        """
        Send all approved emails.

        Args:
            files: List of approved email file paths

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not files:
            self.logger.info('No approved emails to send')
            return (0, 0)

        self.logger.info(f'Sending {len(files)} approved email(s)')

        successful = 0
        failed = 0

        for filepath in files:
            try:
                result = self._send_single_email(filepath)
                if result:
                    successful += 1
                    # Move to Done folder
                    self._move_to_done(filepath)
                else:
                    failed += 1
            except Exception as e:
                self.logger.error(f'Failed to send {filepath.name}: {e}')
                failed += 1

        return (successful, failed)

    def _send_single_email(self, filepath: Path) -> bool:
        """
        Send a single approved email.

        Args:
            filepath: Path to the approved email file

        Returns:
            True if sent successfully
        """
        self.logger.info(f'Sending: {filepath.name}')

        try:
            # Parse the email file
            email_data = self._parse_email_file(filepath)

            if not email_data.get('to'):
                self.logger.error(f'No recipient found in {filepath.name}')
                return False

            if not email_data.get('subject'):
                self.logger.error(f'No subject found in {filepath.name}')
                return False

            # Create email message
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            message = MIMEMultipart()
            message['to'] = email_data['to']
            message['subject'] = email_data['subject']
            if email_data.get('cc'):
                message['cc'] = email_data['cc']

            # Add body
            message.attach(MIMEText(email_data['body'], 'plain'))

            # Create RFC 2822 message
            raw_message = message.as_string()

            # Encode for Gmail API
            raw_bytes = raw_message.encode('utf-8')
            raw_base64 = base64.urlsafe_b64encode(raw_bytes).decode('utf-8')

            # Send via Gmail API
            gmail_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_base64}
            ).execute()

            message_id = gmail_message.get('id')
            self.logger.info(f'✅ Email sent successfully! Message ID: {message_id}')

            # Log the sent email
            self._log_sent_email(filepath, email_data, message_id)

            return True

        except Exception as e:
            self.logger.error(f'Error sending email: {e}', exc_info=True)
            return False

    def _parse_email_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Parse email approval file to extract email details.

        Args:
            filepath: Path to the email file

        Returns:
            Dictionary with email details
        """
        content = filepath.read_text(encoding='utf-8')

        email_data = {
            'to': '',
            'subject': '',
            'cc': '',
            'body': '',
            'original_email_id': ''
        }

        # Parse frontmatter
        lines = content.split('\n')
        in_frontmatter = False
        in_body = False
        body_lines = []

        for line in lines:
            # Check for frontmatter markers
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    in_frontmatter = False
                    in_body = True
                    continue

            if in_frontmatter:
                # Parse frontmatter fields
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    # Handle both 'to' and 'recipient' fields
                    if key == 'to' or key == 'recipient':
                        email_data['to'] = value
                    elif key == 'subject':
                        email_data['subject'] = value
                    elif key == 'cc':
                        email_data['cc'] = value
                    elif key == 'original_email_id':
                        email_data['original_email_id'] = value

            elif in_body:
                # Skip markdown headers and comments
                if not line.startswith('#') and not line.startswith('<!--') and not line.startswith('```'):
                    # Skip table rows
                    if not line.startswith('|'):
                        body_lines.append(line)

        # Clean up body
        email_data['body'] = '\n'.join(body_lines).strip()

        # If body is empty, look for response content in code blocks
        if not email_data['body']:
            import re
            code_block_match = re.search(r'```\n(.*?)```', content, re.DOTALL)
            if code_block_match:
                email_data['body'] = code_block_match.group(1).strip()

        self.logger.info(f'Parsed email: To={email_data["to"]}, Subject={email_data["subject"]}')
        return email_data

    def _log_sent_email(self, filepath: Path, email_data: Dict[str, Any], message_id: str):
        """Log the sent email to the Logs folder."""
        log_file = self.logs / f'sent_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{email_data["original_email_id"]}.md'

        log_content = f'''---
timestamp: {datetime.now().isoformat()}
action_type: email_sent
original_email_id: {email_data.get('original_email_id', 'N/A')}
to: {email_data['to']}
subject: {email_data['subject']}
gmail_message_id: {message_id}
status: success
---

# Email Sent Successfully

## Details

| Field | Value |
|-------|-------|
| **To** | {email_data['to']} |
| **Subject** | {email_data['subject']} |
| **Sent At** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **Gmail Message ID** | {message_id} |
| **Source File** | {filepath.name} |

## Response Content

```
{email_data['body']}
```

---
*Logged by EmailApprovalWatcher*
'''

        log_file.write_text(log_content, encoding='utf-8')
        self.logger.info(f'Log written to: {log_file.name}')

    def _move_to_done(self, filepath: Path):
        """Move processed file to Done folder."""
        try:
            dest = self.done / filepath.name
            filepath.rename(dest)
            self.logger.info(f'Moved to Done: {filepath.name}')
        except Exception as e:
            self.logger.error(f'Failed to move file to Done: {e}')

    def run(self):
        """Main run loop for the email approval watcher."""
        self.logger.info('Starting Email Approval Watcher')
        self.logger.info(f'Check interval: {self.check_interval}s')

        try:
            while True:
                try:
                    # Get approved emails
                    approved = self.get_approved_emails()

                    if approved:
                        # Send them
                        success, failed = self.send_approved_emails(approved)
                        self.logger.info(f'Sent: {success} successful, {failed} failed')
                    else:
                        self.logger.debug('No approved emails waiting')

                    # Wait for next check
                    time.sleep(self.check_interval)

                except Exception as e:
                    self.logger.error(f'Error in processing loop: {e}', exc_info=True)
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Email Approval Watcher stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise


def main():
    """Main entry point for the email approval watcher."""
    parser = argparse.ArgumentParser(
        description='Email Approval Watcher - Sends approved emails'
    )
    parser.add_argument(
        'vault_path',
        type=str,
        help='Path to the Obsidian vault root directory'
    )
    parser.add_argument(
        '--credentials',
        type=str,
        default='credentials.json',
        help='Path to Gmail credentials.json (default: credentials.json)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )

    args = parser.parse_args()

    # Validate paths
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)

    creds_path = Path(args.credentials)
    if not creds_path.exists():
        print(f"Error: Credentials file not found: {args.credentials}")
        sys.exit(1)

    # Create watcher
    watcher = EmailApprovalWatcher(str(vault), str(creds_path), args.interval)

    if args.once:
        # Test mode: run once and exit
        print("Running in test mode (once)...")
        approved = watcher.get_approved_emails()
        print(f"Found {len(approved)} approved email(s)")
        if approved:
            success, failed = watcher.send_approved_emails(approved)
            print(f"Sent: {success} successful, {failed} failed")
    else:
        # Normal mode: run continuously
        watcher.run()


if __name__ == '__main__':
    main()
