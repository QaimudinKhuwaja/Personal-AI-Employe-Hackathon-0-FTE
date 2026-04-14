"""
Facebook Auto-Poster Scheduler

Checks for scheduled posts and publishes them automatically.

Usage:
    python scripts/facebook_scheduler.py
    python scripts/facebook_scheduler.py --check-interval 300
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from facebook_graph_poster import FacebookGraphPoster

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class FacebookScheduler:
    """
    Schedule and auto-post to Facebook.
    
    Features:
    - Checks Approved folder for scheduled posts
    - Posts at scheduled time
    - Supports immediate posting
    - Logs all activity
    """
    
    def __init__(self, vault_path: str = 'AI_Employee_Vault'):
        """
        Initialize Facebook Scheduler.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        
        # Ensure directories exist
        for folder in [self.needs_action, self.approved, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized FacebookScheduler')
    
    def _setup_logging(self):
        """Setup logging."""
        log_file = self.logs / f'facebook_scheduler_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('FacebookScheduler')
    
    def check_and_post_scheduled_posts(self):
        """Check for scheduled posts and publish if time is right."""
        
        self.logger.info('Checking for scheduled posts...')
        
        now = datetime.now()
        posts_processed = 0
        
        # Check Approved folder for posts ready to publish
        for file in self.approved.glob('*.md'):
            if file.name.startswith('.'):
                continue
            
            content = file.read_text(encoding='utf-8')
            
            # Check if it's a Facebook post request
            if 'type: facebook_post' not in content.lower():
                continue
            
            self.logger.info(f'Checking post: {file.name}')
            
            # Parse frontmatter
            scheduled_time = None
            post_content = None
            hashtags = None
            link = None
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Extract scheduled time
                if 'scheduled_time:' in line.lower():
                    try:
                        scheduled_str = line.split(':', 1)[1].strip()
                        scheduled_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
                        # Make timezone-naive for comparison
                        if scheduled_time.tzinfo:
                            scheduled_time = scheduled_time.replace(tzinfo=None)
                    except Exception as e:
                        self.logger.warning(f'Could not parse scheduled time: {e}')
                
                # Extract content
                if '**content:**' in line.lower() or '"content":' in line.lower():
                    post_content = self._extract_field_value(line, 'content')
                
                # Extract hashtags
                if '**hashtags:**' in line.lower() or '"hashtags":' in line.lower():
                    hashtags_str = self._extract_field_value(line, 'hashtags')
                    hashtags = [h.strip() for h in hashtags_str.split(',')] if hashtags_str else None
                
                # Extract link
                if '**link:**' in line.lower() or '"link":' in line.lower():
                    link = self._extract_field_value(line, 'link')
            
            # Determine if we should post
            should_post = False
            
            if scheduled_time:
                if now >= scheduled_time:
                    self.logger.info(f'Time to post (scheduled: {scheduled_time})')
                    should_post = True
                else:
                    self.logger.info(f'Waiting until {scheduled_time}')
                    continue
            else:
                # No scheduled time - post immediately
                self.logger.info('No scheduled time - posting immediately')
                should_post = True
            
            # Post to Facebook
            if should_post:
                if self._post_to_facebook(file, post_content, hashtags, link):
                    posts_processed += 1
        
        self.logger.info(f'Check complete: {posts_processed} posts processed')
    
    def _extract_field_value(self, line: str, field_name: str) -> Optional[str]:
        """Extract field value from markdown line."""
        # Try different formats
        formats = [
            f'**{field_name}:**',
            f'**{field_name}:**',
            f'"{field_name}":',
            f'{field_name}:',
        ]
        
        for fmt in formats:
            if fmt.lower() in line.lower():
                value = line.split(fmt, 1)[1].strip()
                # Remove quotes if present
                value = value.strip('"\'')
                return value
        
        return None
    
    def _post_to_facebook(self, file: Path, content: str, hashtags: List[str], link: str) -> bool:
        """
        Post to Facebook.
        
        Args:
            file: Post file path
            content: Post content
            hashtags: List of hashtags
            link: Optional link
            
        Returns:
            True if successful
        """
        self.logger.info(f'Posting to Facebook: {file.name}')
        
        try:
            # Create poster
            poster = FacebookGraphPoster()
            
            # If no content extracted, use filename
            if not content:
                content = f"Post: {file.stem}"
            
            # Post
            result = poster.post_to_facebook(
                message=content,
                link=link,
                hashtags=hashtags
            )
            
            if result:
                self.logger.info(f'✅ Posted successfully: {result.get("id")}')
                
                # Log to JSONL
                self._log_post(file, result, content, hashtags)
                
                # Move to Done
                dest = self.done / file.name
                file.rename(dest)
                self.logger.info(f'Moved to Done: {dest.name}')
                
                return True
            else:
                self.logger.error('❌ Failed to post')
                return False
        
        except Exception as e:
            self.logger.error(f'Error posting: {e}', exc_info=True)
            return False
    
    def _log_post(self, file: Path, result: Dict, content: str, hashtags: List[str]):
        """Log post to JSONL."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_id': f'fb_sched_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'action_type': 'facebook_scheduled_post',
            'actor': 'facebook_scheduler',
            'parameters': {
                'file': file.name,
                'content': content[:100] + '...' if len(content) > 100 else content,
                'hashtags': hashtags,
                'result': result
            },
            'approval_status': 'approved',
            'approved_by': 'human',
            'result': 'success',
            'post_id': result.get('id')
        }
        
        log_file = self.logs / 'facebook_posts.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def run(self, check_interval: int = 300):
        """
        Run scheduler continuously.
        
        Args:
            check_interval: Seconds between checks
        """
        self.logger.info(f'Starting Facebook Scheduler')
        self.logger.info(f'Check interval: {check_interval} seconds')
        
        try:
            while True:
                try:
                    self.check_and_post_scheduled_posts()
                    time.sleep(check_interval)
                except Exception as e:
                    self.logger.error(f'Error in loop: {e}', exc_info=True)
                    time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info('Scheduler stopped by user')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook Auto-Poster Scheduler')
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Create scheduler
    scheduler = FacebookScheduler()
    
    if args.once:
        # Test mode: run once
        print("Checking for scheduled posts...")
        scheduler.check_and_post_scheduled_posts()
    else:
        # Normal mode: run continuously
        scheduler.run(check_interval=args.interval)


if __name__ == '__main__':
    main()
