"""
Facebook Comment Detector

Monitors Facebook posts for new comments and creates action files.

Usage:
    python scripts/facebook_comment_detector.py
    python scripts/facebook_comment_detector.py --interval 60
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class FacebookCommentDetector:
    """
    Monitor Facebook posts for new comments.
    
    Features:
    - Polls Facebook Graph API for new comments
    - Creates action files in Needs_Action folder
    - Tracks processed comments to avoid duplicates
    - Supports keyword-based alerts
    """
    
    def __init__(
        self,
        vault_path: str = 'AI_Employee_Vault',
        check_interval: int = 300,  # 5 minutes
        keywords: List[str] = None
    ):
        """
        Initialize Facebook Comment Detector.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks
            keywords: Keywords that trigger alerts
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.keywords = keywords or ['urgent', 'asap', 'help', 'question', 'price', 'cost', 'invoice']
        
        # Facebook credentials
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        
        if not self.access_token or not self.page_id:
            raise ValueError("Facebook credentials not set in .env")
        
        # Paths
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs = self.vault_path / 'Logs'
        self.cache_file = self.logs / 'facebook_comments_cache.json'
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Cache for processed comments
        self.processed_comments = self._load_cache()
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized FacebookCommentDetector')
        self.logger.info(f'Watching page: {self.page_id}')
        self.logger.info(f'Keywords: {self.keywords}')
    
    def _setup_logging(self):
        """Setup logging."""
        log_file = self.logs / f'facebook_comments_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('FacebookCommentDetector')
    
    def _load_cache(self) -> set:
        """Load processed comment IDs from cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except:
                pass
        return set()
    
    def _save_cache(self):
        """Save processed comment IDs to cache."""
        data = {
            'processed_ids': list(self.processed_comments),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def get_page_posts(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent posts from Facebook Page.
        
        Args:
            limit: Number of posts to retrieve
            
        Returns:
            List of posts with IDs
        """
        url = f"https://graph.facebook.com/v18.0/{self.page_id}/posts"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'id,message,created_time,permalink_url'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' in result:
                return result['data']
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to get posts: {e}')
            return None
    
    def get_post_comments(self, post_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get comments for a specific post.
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            List of comments
        """
        url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
        params = {
            'access_token': self.access_token,
            'fields': 'id,from,message,created_time,like_count,comment_count',
            'order': 'chronological'  # Oldest first
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' in result:
                return result['data']
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to get comments for {post_id}: {e}')
            return None
    
    def check_keywords(self, text: str) -> List[str]:
        """
        Check if text contains alert keywords.
        
        Args:
            text: Text to check
            
        Returns:
            List of matched keywords
        """
        if not text:
            return []
        
        text_lower = text.lower()
        matched = [kw for kw in self.keywords if kw.lower() in text_lower]
        
        return matched
    
    def create_comment_action_file(self, post: Dict, comment: Dict, matched_keywords: List[str]):
        """
        Create action file for new comment.
        
        Args:
            post: Post data
            comment: Comment data
            matched_keywords: Keywords found in comment
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        comment_id = comment.get('id', 'unknown')
        
        # Determine priority
        priority = 'high' if matched_keywords else 'normal'
        
        filename = f"FACEBOOK_COMMENT_{comment_id}_{timestamp}.md"
        filepath = self.needs_action / filename
        
        # Extract commenter info
        from_name = comment.get('from', {}).get('name', 'Unknown')
        from_id = comment.get('from', {}).get('id', 'unknown')
        
        markdown = f"""---
type: facebook_comment
priority: {priority}
post_id: {post.get('id', 'unknown')}
comment_id: {comment_id}
from_name: {from_name}
from_id: {from_id}
created: {comment.get('created_time', 'unknown')}
detected: {datetime.now().isoformat()}
keywords: {','.join(matched_keywords) if matched_keywords else 'none'}
status: pending
---

# Facebook Comment Alert

**Priority:** {'🔴 High' if priority == 'high' else '🟢 Normal'}  
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Post ID:** {post.get('id', 'unknown')}

---

## Comment Details

**From:** {from_name}  
**Time:** {comment.get('created_time', 'Unknown')}  
**Comment:** 

> {comment.get('message', '[No text]')}

---

## Context

**Original Post:**
{post.get('message', '[No message]')}

**Post Link:** {post.get('permalink_url', 'N/A')}

---

## Keywords Detected

{', '.join(matched_keywords) if matched_keywords else 'None'}

---

## Suggested Actions

- [ ] Review comment
- [ ] Draft response (if needed)
- [ ] Move to Approved to send response
- [ ] Move to Done after handling

---

## Response Template (if needed)

```
Hi {from_name},

Thank you for your comment! [Your response here]

Best regards,
[Your Name/Team]
```
"""
        
        filepath.write_text(markdown, encoding='utf-8')
        self.logger.info(f'Created comment action file: {filename}')
        
        # Log to JSONL
        self._log_comment(post, comment, matched_keywords)
    
    def _log_comment(self, post: Dict, comment: Dict, matched_keywords: List[str]):
        """Log comment detection to JSONL."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_id': f'fb_comment_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'action_type': 'facebook_comment_detected',
            'actor': 'facebook_comment_detector',
            'parameters': {
                'post_id': post.get('id'),
                'comment_id': comment.get('id'),
                'from_name': comment.get('from', {}).get('name'),
                'keywords': matched_keywords
            },
            'result': 'action_file_created',
            'priority': 'high' if matched_keywords else 'normal'
        }
        
        log_file = self.logs / 'facebook_comments.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def check_for_new_comments(self):
        """Main check for new comments."""
        self.logger.info('Checking for new Facebook comments...')
        
        # Get recent posts
        posts = self.get_page_posts(limit=10)
        
        if not posts:
            self.logger.warning('No posts found')
            return
        
        new_comments_count = 0
        
        for post in posts:
            post_id = post.get('id')
            
            if not post_id:
                continue
            
            # Get comments for this post
            comments = self.get_post_comments(post_id)
            
            if not comments:
                continue
            
            # Check each comment
            for comment in comments:
                comment_id = comment.get('id')
                
                # Skip if already processed
                if comment_id in self.processed_comments:
                    continue
                
                # This is a new comment!
                message = comment.get('message', '')
                matched_keywords = self.check_keywords(message)
                
                self.logger.info(f'New comment detected: {comment_id}')
                
                # Create action file
                self.create_comment_action_file(post, comment, matched_keywords)
                
                # Add to processed cache
                self.processed_comments.add(comment_id)
                new_comments_count += 1
        
        # Save cache
        self._save_cache()
        
        self.logger.info(f'Check complete: {new_comments_count} new comments found')
    
    def run(self):
        """Main watcher loop."""
        self.logger.info(f'Starting Facebook Comment Detector')
        self.logger.info(f'Check interval: {self.check_interval} seconds')
        
        try:
            while True:
                try:
                    self.check_for_new_comments()
                    
                    # Wait for next check
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f'Error in check: {e}', exc_info=True)
                    time.sleep(60)
        
        except KeyboardInterrupt:
            self.logger.info('Comment detector stopped by user')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook Comment Detector')
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        default='urgent,asap,help,question,price,cost,invoice',
        help='Comma-separated keywords to alert on'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Create detector
    detector = FacebookCommentDetector(
        check_interval=args.interval,
        keywords=args.keywords.split(',') if args.keywords else []
    )
    
    if args.once:
        # Test mode: run once
        print("Running single check...")
        detector.check_for_new_comments()
    else:
        # Normal mode: run continuously
        detector.run()


if __name__ == '__main__':
    main()
