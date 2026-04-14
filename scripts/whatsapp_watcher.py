"""
WhatsApp Watcher Module

Monitors WhatsApp Web for new messages containing important keywords.
Uses Playwright for browser automation.

Usage:
    python whatsapp_watcher.py /path/to/vault --session /path/to/session

Requirements:
    pip install playwright
    playwright install
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing required package. Install with:")
    print("pip install playwright")
    print("playwright install")
    sys.exit(1)

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages containing important keywords.
    
    Creates action files in Needs_Action folder for Qwen Code to process.
    """
    
    DEFAULT_KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help', 'important']
    
    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 30,
        keywords: Optional[List[str]] = None
    ):
        """
        Initialize the WhatsApp watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
            keywords: List of keywords to monitor (default: DEFAULT_KEYWORDS)
        """
        super().__init__(vault_path, check_interval)
        
        self.session_path = Path(session_path)
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.processed_messages: Set[str] = set()
        
        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed messages from cache
        self._load_processed_cache()
    
    def _load_processed_cache(self):
        """Load cache of previously processed messages."""
        cache_file = self.vault_path / '.processed_whatsapp.cache'
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.processed_messages = set(f.read().strip().split('\n'))
                self.logger.info(f'Loaded {len(self.processed_messages)} processed message IDs')
            except Exception as e:
                self.logger.warning(f'Could not load processed cache: {e}')
                self.processed_messages = set()
    
    def _save_processed_cache(self):
        """Save cache of processed messages."""
        cache_file = self.vault_path / '.processed_whatsapp.cache'
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.processed_messages))
        except Exception as e:
            self.logger.warning(f'Could not save processed cache: {e}')
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check WhatsApp Web for new messages with important keywords.
        
        Returns:
            List of message dictionaries
        """
        messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to WhatsApp Web
                try:
                    page.goto('https://web.whatsapp.com', timeout=30000)
                    
                    # Wait for chat list to load
                    try:
                        page.wait_for_selector('[data-testid="chat-list"]', timeout=15000)
                    except PlaywrightTimeout:
                        self.logger.warning('WhatsApp Web not loaded - may need QR scan')
                        browser.close()
                        return []
                    
                    # Wait a bit for messages to load
                    page.wait_for_timeout(3000)
                    
                    # Find unread chats
                    unread_chats = page.query_selector_all('[aria-label*="unread"]')
                    
                    for chat in unread_chats:
                        try:
                            # Get chat name
                            chat_name_elem = chat.query_selector('[dir="auto"]')
                            chat_name = chat_name_elem.inner_text() if chat_name_elem else 'Unknown'
                            
                            # Get message preview
                            message_elem = chat.query_selector('[dir="auto"]:last-child')
                            message_text = message_elem.inner_text() if message_elem else ''
                            
                            # Check if message contains keywords
                            message_lower = message_text.lower()
                            matched_keywords = [kw for kw in self.keywords if kw in message_lower]
                            
                            if matched_keywords:
                                # Create unique message ID
                                msg_id = f"{chat_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                
                                if msg_id not in self.processed_messages:
                                    messages.append({
                                        'id': msg_id,
                                        'chat': chat_name,
                                        'text': message_text,
                                        'keywords': matched_keywords,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    self.processed_messages.add(msg_id)
                        except Exception as e:
                            self.logger.debug(f'Error processing chat: {e}')
                            continue
                    
                    browser.close()
                    
                    # Save updated cache
                    if messages:
                        self._save_processed_cache()
                        self.logger.info(f'Found {len(messages)} new message(s) with keywords')
                    
                except Exception as e:
                    self.logger.error(f'Error navigating WhatsApp Web: {e}')
                    browser.close()
                    return []
                    
        except Exception as e:
            self.logger.error(f'Error in WhatsApp watcher: {e}')
            return []
        
        return messages
    
    def create_action_file(self, message: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            message: Message dictionary
            
        Returns:
            Path to created file, or None if creation failed
        """
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_chat = self.sanitize_filename(message['chat'])
            filename = f"WHATSAPP_{timestamp}_{safe_chat}.md"
            filepath = self.needs_action / filename
            
            # Determine priority based on keywords
            priority = self._determine_priority(message['keywords'])
            
            # Create action file content
            content = f'''---
type: whatsapp_message
from: {message['chat']}
chat: {message['chat']}
received: {self.get_timestamp()}
priority: {priority}
status: pending
keywords: {', '.join(message['keywords'])}
message_id: {message['id']}
---

# 💬 WhatsApp Message: {message['chat']}

## Message Details

| Field | Value |
|-------|-------|
| **From** | {message['chat']} |
| **Received** | {message['timestamp']} |
| **Keywords** | {', '.join(message['keywords'])} |
| **Priority** | {priority} |

## Message Content

> {message['text']}

## Suggested Actions

{self._get_suggested_actions(message['keywords'], message['text'])}

## Notes

<!-- Add any additional context or instructions here -->

---
*Created by WhatsAppWatcher*
'''
            
            # Write action file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f'Created action file for WhatsApp message from: {message["chat"]}')
            return filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}')
            return None
    
    def _determine_priority(self, keywords: List[str]) -> str:
        """
        Determine message priority based on keywords.
        
        Args:
            keywords: List of matched keywords
            
        Returns:
            Priority level: 'critical', 'high', or 'normal'
        """
        critical_keywords = ['urgent', 'asap', 'emergency', 'help']
        high_keywords = ['invoice', 'payment', 'important']
        
        if any(kw in keywords for kw in critical_keywords):
            return 'critical'
        elif any(kw in keywords for kw in high_keywords):
            return 'high'
        return 'normal'
    
    def _get_suggested_actions(self, keywords: List[str], text: str) -> str:
        """
        Get suggested actions based on keywords and message content.
        
        Args:
            keywords: List of matched keywords
            text: Message text
            
        Returns:
            Markdown formatted list of suggested actions
        """
        actions = []
        
        if 'invoice' in keywords:
            return '''- [ ] Review invoice request
- [ ] Generate/send invoice
- [ ] Confirm payment details
- [ ] Reply to sender'''
        
        if 'payment' in keywords:
            return '''- [ ] Check payment status
- [ ] Process payment if due
- [ ] Confirm payment received
- [ ] Update accounting records'''
        
        if 'urgent' in keywords or 'asap' in keywords:
            return '''- [ ] Read message immediately
- [ ] Take urgent action required
- [ ] Reply to sender ASAP
- [ ] Escalate if necessary'''
        
        if 'help' in keywords:
            return '''- [ ] Understand the request
- [ ] Provide assistance
- [ ] Follow up if needed
- [ ] Document resolution'''
        
        # Default actions
        return '''- [ ] Read message
- [ ] Respond appropriately
- [ ] Take required action
- [ ] Archive after processing'''
    
    def setup_session(self):
        """
        Setup WhatsApp Web session by scanning QR code.
        
        This opens a visible browser window for QR code scanning.
        """
        print("Opening WhatsApp Web for QR code scan...")
        print("Please scan the QR code with your WhatsApp mobile app.")
        print("Press Ctrl+C when done.")
        
        try:
            with sync_playwright() as p:
                # Launch with visible window for QR scan
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://web.whatsapp.com')
                
                print("\nWhatsApp Web is open. Scan the QR code.")
                print("Keep the browser open until WhatsApp loads.")
                print("Press Ctrl+C to exit when done.\n")
                
                # Keep running until user interrupts
                try:
                    while True:
                        page.wait_for_timeout(1000)
                except KeyboardInterrupt:
                    print("\nSession setup complete!")
                    browser.close()
                    
        except Exception as e:
            print(f"Error during setup: {e}")


def main():
    """Main entry point for the WhatsApp watcher."""
    parser = argparse.ArgumentParser(
        description='WhatsApp Watcher for AI Employee'
    )
    parser.add_argument(
        'vault_path',
        type=str,
        help='Path to the Obsidian vault root directory'
    )
    parser.add_argument(
        '--session',
        type=str,
        required=True,
        help='Path to store WhatsApp session data'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        default=','.join(WhatsAppWatcher.DEFAULT_KEYWORDS),
        help=f'Comma-separated keywords to monitor (default: {",".join(WhatsAppWatcher.DEFAULT_KEYWORDS)})'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    parser.add_argument(
        '--setup-session',
        action='store_true',
        help='Setup WhatsApp session (QR scan) and exit'
    )
    
    args = parser.parse_args()
    
    # Validate vault path
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)
    
    # Setup session mode
    if args.setup_session:
        session_path = Path(args.session)
        watcher = WhatsAppWatcher(str(vault), str(session_path))
        watcher.setup_session()
        return
    
    # Parse keywords
    keywords = [kw.strip() for kw in args.keywords.split(',')]
    
    # Create and run watcher
    session_path = Path(args.session)
    watcher = WhatsAppWatcher(
        str(vault),
        str(session_path),
        check_interval=args.interval,
        keywords=keywords
    )
    
    if args.once:
        # Test mode: run once and exit
        print("Running in test mode (once)...")
        items = watcher.check_for_updates()
        print(f"Found {len(items)} new message(s)")
        for item in items:
            filepath = watcher.create_action_file(item)
            if filepath:
                print(f"  Created: {filepath.name}")
    else:
        # Normal mode: run continuously
        watcher.run()


if __name__ == '__main__':
    main()
