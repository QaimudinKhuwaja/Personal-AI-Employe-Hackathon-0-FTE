"""
Facebook Graph API Poster

Posts to Facebook Pages and Instagram Business accounts via Graph API.
Supports text posts, image posts, and cross-posting to Instagram.

Usage:
    python scripts/facebook_graph_poster.py --content "Hello Facebook!" --page-id $PAGE_ID
    python scripts/facebook_graph_poster.py --content "Instagram post" --instagram --media-path image.jpg
    python scripts/facebook_graph_poster.py --test-connection

Requirements:
    - Facebook App with Graph API access
    - Page Access Token (long-lived)
    - Instagram Business Account (for Instagram posting)
"""

import os
import sys
import json
import logging
import argparse
import base64
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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


class FacebookGraphPoster:
    """
    Facebook Graph API Poster.
    
    Implements Facebook Graph API for posting to Pages and Instagram.
    API Version: v18.0 (latest stable)
    """
    
    GRAPH_API_VERSION = 'v18.0'
    GRAPH_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'
    
    def __init__(
        self,
        page_access_token: Optional[str] = None,
        page_id: Optional[str] = None,
        instagram_account_id: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Initialize Facebook Graph API poster.
        
        Args:
            page_access_token: Facebook Page Access Token
            page_id: Facebook Page ID
            instagram_account_id: Instagram Business Account ID
            dry_run: If True, log actions without executing
        """
        self.page_access_token = page_access_token or os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.page_id = page_id or os.getenv('FACEBOOK_PAGE_ID')
        self.instagram_account_id = instagram_account_id or os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        self.dry_run = dry_run
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized FacebookGraphPoster')
        self.logger.info(f'Page ID: {self.page_id or "Not set"}')
        self.logger.info(f'Instagram Account: {self.instagram_account_id or "Not set"}')
    
    def _setup_logging(self):
        """Setup logging."""
        log_dir = Path('Logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'facebook_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('FacebookGraphPoster')
    
    def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make request to Facebook Graph API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body data
            files: Files to upload
            
        Returns:
            Response data or None
        """
        url = f"{self.GRAPH_URL}/{endpoint}"
        
        # Add access token to params
        if params is None:
            params = {}
        params['access_token'] = self.page_access_token
        
        if self.dry_run:
            self.logger.info(f'[DRY RUN] Would make {method} request to {url}')
            self.logger.info(f'[DRY RUN] Params: {params}')
            self.logger.info(f'[DRY RUN] Data: {data}')
            return {'id': 'DRY_RUN_ID', 'success': True}
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, params=params, data=data, files=files, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, timeout=30)
            else:
                self.logger.error(f'Unsupported HTTP method: {method}')
                return None
            
            response.raise_for_status()
            result = response.json()
            
            # Check for Facebook API errors
            if 'error' in result:
                error = result['error']
                self.logger.error(f'Facebook API Error: {error.get("message", "Unknown error")}')
                return None
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Request failed: {e}')
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f'JSON decode error: {e}')
            return None
    
    def test_connection(self) -> bool:
        """
        Test Facebook Graph API connection.

        Returns:
            True if connection successful
        """
        print("Testing Facebook Graph API connection...")

        if not self.page_access_token:
            print("[ERROR] Page access token not set")
            return False

        # Test token validity by getting page info
        result = self._make_request(self.page_id, params={'fields': 'name,username,category'})

        if result:
            print("[OK] Connected to Facebook Page")
            print(f"   Name: {result.get('name', 'Unknown')}")
            print(f"   Username: @{result.get('username', 'N/A')}")
            print(f"   Category: {result.get('category', 'N/A')}")

            # Test Instagram connection if available
            if self.instagram_account_id:
                ig_result = self._make_request(
                    self.instagram_account_id,
                    params={'fields': 'username,name'}
                )
                if ig_result:
                    print("[OK] Connected to Instagram Business")
                    print(f"   Username: @{result.get('username', 'N/A')}")
                else:
                    print("[WARN] Instagram connection failed")

            return True
        else:
            print("[ERROR] Failed to connect to Facebook Page")
            print("   Check your access token and page ID")
            return False
    
    def post_to_facebook(
        self,
        message: str,
        link: Optional[str] = None,
        photo_url: Optional[str] = None,
        photo_path: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Post to Facebook Page.
        
        Args:
            message: Post message text
            link: URL to share (optional)
            photo_url: URL of photo to post (optional)
            photo_path: Local path of photo to post (optional)
            scheduled_time: ISO 8601 datetime for scheduled posting (optional)
            hashtags: List of hashtags (optional)
            
        Returns:
            Post data including ID
        """
        self.logger.info(f'Posting to Facebook Page: {message[:50]}...')
        
        # Prepare post data
        post_data = {
            'message': message,
        }
        
        # Add link if provided
        if link:
            post_data['link'] = link
        
        # Add photo URL if provided
        if photo_url:
            post_data['attached_media'] = json.dumps([{'media_url': photo_url}])
        
        # Add scheduled time if provided
        if scheduled_time:
            post_data['scheduled_publish_time'] = scheduled_time
        
        # Add hashtags to message if provided
        if hashtags:
            hashtag_text = ' '.join([f'#{tag}' for tag in hashtags])
            post_data['message'] = f"{message}\n\n{hashtag_text}"
        
        # Upload photo file if provided
        files = None
        if photo_path:
            if not os.path.exists(photo_path):
                self.logger.error(f'Photo not found: {photo_path}')
                return None
            
            with open(photo_path, 'rb') as f:
                photo_data = f.read()
            
            files = {
                'source': ('photo.jpg', photo_data, 'image/jpeg')
            }
            # Remove message when uploading photo (use caption instead)
            if 'message' in post_data:
                post_data['caption'] = post_data.pop('message')
        
        # Make API request
        endpoint = f"{self.page_id}/photos" if photo_path or photo_url else f"{self.page_id}/feed"
        
        result = self._make_request(
            endpoint,
            method='POST',
            data=post_data,
            files=files
        )
        
        if result and result.get('id'):
            post_id = result['id']
            self.logger.info(f'✅ Facebook post created: {post_id}')
            
            # Log to file
            self._log_post({
                'post_id': post_id,
                'platform': 'facebook',
                'message': message,
                'link': link,
                'scheduled_time': scheduled_time,
                'result': 'success'
            })
            
            return {
                'id': post_id,
                'platform': 'facebook',
                'message': message,
                'permalink': f'https://www.facebook.com/{self.page_id}/posts/{post_id.split("_")[1] if "_" in post_id else post_id}'
            }
        else:
            self.logger.error('Failed to create Facebook post')
            return None
    
    def post_to_instagram(
        self,
        caption: str,
        media_path: str,
        media_type: str = 'IMAGE',
        share_to_feed: bool = True,
        hashtags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Post to Instagram Business Account.
        
        Instagram posting requires a 2-step process:
        1. Create a media container
        2. Publish the container
        
        Args:
            caption: Post caption
            media_path: Path to image/video file
            media_type: 'IMAGE' or 'VIDEO'
            share_to_feed: Share to Facebook feed as well
            hashtags: List of hashtags
            
        Returns:
            Post data including ID
        """
        if not self.instagram_account_id:
            self.logger.error('Instagram Business Account ID not set')
            return None
        
        self.logger.info(f'Posting to Instagram: {caption[:50]}...')
        
        # Add hashtags to caption
        if hashtags:
            hashtag_text = ' '.join([f'#{tag}' for tag in hashtags])
            caption = f"{caption}\n\n{hashtag_text}"
        
        # Step 1: Upload media to Instagram
        self.logger.info('Step 1: Creating media container...')
        
        # Upload photo
        with open(media_path, 'rb') as f:
            photo_data = f.read()
        
        # First, upload photo to Facebook (Instagram uses Facebook's hosting)
        upload_result = self._make_request(
            f"{self.page_id}/photos",
            method='POST',
            data={'published': 'false'},  # Don't publish to Facebook yet
            files={'source': ('photo.jpg', photo_data, 'image/jpeg')}
        )
        
        if not upload_result:
            self.logger.error('Failed to upload media')
            return None
        
        facebook_photo_id = upload_result.get('id')
        
        # Step 2: Create Instagram media container
        container_data = {
            'image_url': f'https://graph.facebook.com/{facebook_photo_id}/picture',
            'caption': caption,
            'share_to_feed': share_to_feed,
        }
        
        if media_type == 'VIDEO':
            container_data['media_type'] = 'VIDEO'
            # For video, you'd need to provide video_url instead
        
        container_result = self._make_request(
            f"{self.instagram_account_id}/media",
            method='POST',
            data=container_data
        )
        
        if not container_result or 'id' not in container_result:
            self.logger.error('Failed to create Instagram media container')
            return None
        
        container_id = container_result['id']
        self.logger.info(f'Media container created: {container_id}')
        
        # Step 3: Publish the media
        self.logger.info('Step 2: Publishing media...')
        
        publish_result = self._make_request(
            f"{self.instagram_account_id}/media_publish",
            method='POST',
            data={'creation_id': container_id}
        )
        
        if publish_result and 'id' in publish_result:
            instagram_media_id = publish_result['id']
            self.logger.info(f'✅ Instagram post published: {instagram_media_id}')
            
            # Log to file
            self._log_post({
                'post_id': instagram_media_id,
                'platform': 'instagram',
                'caption': caption,
                'media_type': media_type,
                'result': 'success'
            })
            
            return {
                'id': instagram_media_id,
                'platform': 'instagram',
                'caption': caption,
                'permalink': f'https://www.instagram.com/p/{instagram_media_id}'
            }
        else:
            self.logger.error('Failed to publish Instagram post')
            return None
    
    def _log_post(self, post_data: Dict[str, Any]):
        """Log post to JSONL file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_id': f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'action_type': f"{post_data['platform']}_post",
            'actor': 'facebook_graph_poster',
            'parameters': {
                'message': post_data.get('message', post_data.get('caption', '')),
                'platform': post_data['platform']
            },
            'approval_status': 'approved',
            'approved_by': 'system',
            'result': post_data.get('result', 'success'),
            'post_id': post_data.get('post_id')
        }
        
        log_file = Path('Logs') / 'facebook_posts.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_page_posts(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent posts from Facebook Page.
        
        Args:
            limit: Number of posts to retrieve
            
        Returns:
            List of posts
        """
        result = self._make_request(
            f"{self.page_id}/posts",
            params={'limit': limit, 'fields': 'message,created_time,permalink_url,likes.summary(true),comments.summary(true)'}
        )
        
        if result and 'data' in result:
            return result['data']
        
        return None
    
    def get_instagram_media(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent media from Instagram Business Account.
        
        Args:
            limit: Number of media items to retrieve
            
        Returns:
            List of media items
        """
        if not self.instagram_account_id:
            return None
        
        result = self._make_request(
            f"{self.instagram_account_id}/media",
            params={'limit': limit, 'fields': 'caption,media_type,media_url,permalink,timestamp'}
        )
        
        if result and 'data' in result:
            return result['data']
        
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook Graph API Poster')
    parser.add_argument('--content', type=str, help='Post content/message')
    parser.add_argument('--page-id', type=str, help='Facebook Page ID')
    parser.add_argument('--link', type=str, help='URL to share')
    parser.add_argument('--photo-url', type=str, help='Photo URL to post')
    parser.add_argument('--photo-path', type=str, help='Local photo path to upload')
    parser.add_argument('--instagram', action='store_true', help='Post to Instagram')
    parser.add_argument('--media-path', type=str, help='Media path for Instagram')
    parser.add_argument('--hashtags', type=str, help='Comma-separated hashtags')
    parser.add_argument('--scheduled-time', type=str, help='Scheduled publish time (ISO 8601)')
    parser.add_argument('--test-connection', action='store_true', help='Test Facebook connection')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual post)')
    
    args = parser.parse_args()
    
    # Create poster
    poster = FacebookGraphPoster(
        page_id=args.page_id,
        dry_run=args.dry_run
    )
    
    # Test connection
    if args.test_connection:
        success = poster.test_connection()
        sys.exit(0 if success else 1)
    
    # Post to Instagram
    elif args.instagram:
        if not args.content or not args.media_path:
            print("Error: --content and --media-path are required for Instagram")
            sys.exit(1)
        
        hashtags = args.hashtags.split(',') if args.hashtags else None

        result = poster.post_to_instagram(
            caption=args.content,
            media_path=args.media_path,
            hashtags=hashtags
        )

        if result:
            print("[OK] Instagram post published!")
            print(f"   Post ID: {result['id']}")
            print(f"   Permalink: {result.get('permalink', 'N/A')}")
        else:
            print("[ERROR] Failed to post to Instagram")
            sys.exit(1)

    # Post to Facebook
    elif args.content:
        hashtags = args.hashtags.split(',') if args.hashtags else None

        result = poster.post_to_facebook(
            message=args.content,
            link=args.link,
            photo_url=args.photo_url,
            photo_path=args.photo_path,
            scheduled_time=args.scheduled_time,
            hashtags=hashtags
        )

        if result:
            print("[OK] Facebook post published!")
            print(f"   Post ID: {result['id']}")
            print(f"   Permalink: {result.get('permalink', 'N/A')}")
        else:
            print("[ERROR] Failed to post to Facebook")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
