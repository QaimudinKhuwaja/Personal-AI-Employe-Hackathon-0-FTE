"""
Gmail Watcher Module

Monitors Gmail for new unread/important emails and creates action files
for Qwen Code to process.

Usage:
    python gmail_watcher.py /path/to/vault --credentials /path/to/credentials.json

Requirements:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Missing required packages. Install with:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

from base_watcher import BaseWatcher


# Gmail API scopes (read + send for full email functionality)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new unread/important emails.
    
    Creates action files in Needs_Action folder for Qwen Code to process.
    """
    
    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        check_interval: int = 120,
        query: str = 'is:unread is:important'
    ):
        """
        Initialize the Gmail watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            credentials_path: Path to Gmail OAuth credentials.json
            check_interval: Seconds between checks (default: 120)
            query: Gmail query string (default: 'is:unread is:important')
        """
        super().__init__(vault_path, check_interval)
        
        self.credentials_path = Path(credentials_path)
        self.token_path = self.vault_path / '.gmail_token.json'
        self.query = query
        self.processed_ids: Set[str] = set()
        self.service = None
        
        # Load previously processed email IDs from cache
        self._load_processed_cache()
        
        # Initialize Gmail service
        self._initialize_service()
    
    def _load_processed_cache(self):
        """Load cache of previously processed email IDs."""
        cache_file = self.vault_path / '.processed_gmail.cache'
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.processed_ids = set(f.read().strip().split('\n'))
                self.logger.info(f'Loaded {len(self.processed_ids)} processed email IDs')
            except Exception as e:
                self.logger.warning(f'Could not load processed cache: {e}')
                self.processed_ids = set()
    
    def _save_processed_cache(self):
        """Save cache of processed email IDs."""
        cache_file = self.vault_path / '.processed_gmail.cache'
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.processed_ids))
        except Exception as e:
            self.logger.warning(f'Could not save processed cache: {e}')
    
    def _initialize_service(self):
        """Initialize Gmail API service with OAuth credentials."""
        try:
            creds = None
            
            # Load token from file if exists
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    self.token_path, SCOPES
                )
            
            # Refresh or obtain new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    self.logger.info('Starting OAuth authentication flow...')
                    self.logger.info('Opening browser for Gmail authentication...')
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=8080, open_browser=True)
                    self.logger.info('Authentication successful!')
                
                # Save credentials for next run
                with open(self.token_path, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                self.logger.info(f'Token saved to: {self.token_path}')
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail service initialized successfully')
            
        except Exception as e:
            self.logger.error(f'Failed to initialize Gmail service: {e}')
            raise
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new unread/important emails.
        
        Returns:
            List of email message dictionaries
        """
        if not self.service:
            self.logger.error('Gmail service not initialized')
            return []
        
        try:
            # Fetch messages matching query
            results = self.service.users().messages().list(
                userId='me',
                q=self.query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            
            # Filter out already processed emails
            new_messages = []
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)
                    self.processed_ids.add(msg['id'])
            
            # Save updated cache
            if new_messages:
                self._save_processed_cache()
                self.logger.info(f'Found {len(new_messages)} new email(s)')
            
            return new_messages
            
        except HttpError as error:
            self.logger.error(f'Gmail API error: {error}')
            return []
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
            return []
    
    def create_action_file(self, message: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            message: Gmail message dictionary
            
        Returns:
            Path to created file, or None if creation failed
        """
        try:
            # Fetch full message details
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = msg.get('payload', {}).get('headers', [])
            email_data = {h['name']: h['value'] for h in headers}
            
            # Get email snippet
            snippet = msg.get('snippet', 'No content preview available')
            
            # Determine priority based on sender/subject
            priority = self._determine_priority(email_data)
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = self._sanitize_subject(email_data.get('Subject', 'No Subject'))
            filename = f"EMAIL_{timestamp}_{safe_subject}.md"
            filepath = self.needs_action / filename
            
            # Create action file content
            content = f'''---
type: email
from: {email_data.get('From', 'Unknown')}
to: {email_data.get('To', 'Unknown')}
subject: {email_data.get('Subject', 'No Subject')}
received: {self.get_timestamp()}
priority: {priority}
status: pending
email_id: {message['id']}
---

# 📧 Email: {email_data.get('Subject', 'No Subject')}

## Sender Information

| Field | Value |
|-------|-------|
| **From** | {email_data.get('From', 'Unknown')} |
| **To** | {email_data.get('To', 'Unknown')} |
| **Received** | {email_data.get('Date', 'Unknown')} |

## Email Preview

{snippet}

## Suggested Actions

{self._get_suggested_actions(priority, email_data)}

## Notes

<!-- Add any additional context or instructions here -->

---
*Created by GmailWatcher*
'''
            
            # Write action file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f'Created action file for email: {email_data.get("Subject", "No Subject")}')
            return filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}')
            return None
    
    def _determine_priority(self, email_data: Dict[str, str]) -> str:
        """
        Determine email priority based on sender and subject.
        
        Args:
            email_data: Dictionary of email headers
            
        Returns:
            Priority level: 'critical', 'high', 'normal', or 'low'
        """
        subject = email_data.get('Subject', '').lower()
        sender = email_data.get('From', '').lower()
        
        # Critical keywords
        critical_keywords = ['urgent', 'asap', 'emergency', 'deadline', 'immediate']
        if any(kw in subject for kw in critical_keywords):
            return 'critical'
        
        # High priority keywords
        high_keywords = ['invoice', 'payment', 'important', 'priority', 'review']
        if any(kw in subject for kw in high_keywords):
            return 'high'
        
        return 'normal'
    
    def _get_suggested_actions(self, priority: str, email_data: Dict[str, str]) -> str:
        """
        Get suggested actions based on email priority and content.
        """
        subject = email_data.get('Subject', '').lower()
        
        if 'invoice' in subject or 'payment' in subject:
            return '''- [ ] Review invoice details
- [ ] Verify amount and due date
- [ ] Process payment or forward to accounting
- [ ] Send confirmation reply'''
        
        if 'meeting' in subject or 'schedule' in subject:
            return '''- [ ] Check calendar availability
- [ ] Respond with available time slots
- [ ] Create calendar event if confirmed
- [ ] Send meeting link/details'''
        
        if priority == 'critical':
            return '''- [ ] Read email immediately
- [ ] Take urgent action required
- [ ] Reply to sender ASAP
- [ ] Escalate if necessary'''
        elif priority == 'high':
            return '''- [ ] Read and prioritize
- [ ] Respond within 4 hours
- [ ] Take required action
- [ ] Update Dashboard'''
        else:
            return '''- [ ] Read when available
- [ ] Respond within 24 hours
- [ ] Archive after processing'''
    
    def _sanitize_subject(self, subject: str) -> str:
        """Sanitize email subject for use in filename."""
        invalid_chars = '<>:"/\\|？*.'
        for char in invalid_chars:
            subject = subject.replace(char, '_')
        return subject.strip()[:50]


def main():
    """Main entry point for the Gmail watcher."""
    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('vault_path', type=str, help='Path to the Obsidian vault')
    parser.add_argument('--credentials', type=str, default='credentials.json',
                        help='Path to Gmail credentials.json (default: credentials.json)')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    parser.add_argument('--query', type=str, default='is:unread is:important', help='Gmail query')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--auth-only', action='store_true', help='Only authenticate and exit')
    
    args = parser.parse_args()
    
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)
    
    creds_path = Path(args.credentials)
    if not creds_path.exists():
        print(f"Error: Credentials file not found: {args.credentials}")
        sys.exit(1)
    
    # Auth-only mode
    if args.auth_only:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=8080, open_browser=True)
        token_path = vault / '.gmail_token.json'
        with open(token_path, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
        print(f"Authentication successful! Token saved to: {token_path}")
        return
    
    # Create and run watcher
    watcher = GmailWatcher(str(vault), str(creds_path), args.interval, args.query)
    
    if args.once:
        print("Running in test mode (once)...")
        items = watcher.check_for_updates()
        print(f"Found {len(items)} new email(s)")
        for item in items:
            filepath = watcher.create_action_file(item)
            if filepath:
                print(f"  Created: {filepath.name}")
    else:
        watcher.run()


if __name__ == '__main__':
    main()
