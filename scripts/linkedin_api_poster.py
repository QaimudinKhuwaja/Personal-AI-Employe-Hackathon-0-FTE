"""
LinkedIn API Poster - Official API Integration

Uses LinkedIn's official Posts API to create posts programmatically.
This is more reliable than browser automation and avoids anti-bot detection.

Requirements:
    - LinkedIn Developer App: https://www.linkedin.com/developers/
    - OAuth 2.0 Access Token with w_member_social permission
    - Person URN (your LinkedIn profile ID)

Setup:
    1. Create LinkedIn Developer App at https://www.linkedin.com/developers/
    2. Enable "Share on LinkedIn" product
    3. Generate access token with w_member_social scope
    4. Get your Person URN from API response
    5. Store credentials in .env file
"""

import os
import sys
import argparse
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import requests
except ImportError:
    print("Installing required package: requests")
    os.system("pip install requests")
    import requests

try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing required package: python-dotenv")
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv


class LinkedInAPIPoster:
    """Post to LinkedIn using the official Posts API."""
    
    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize LinkedIn API Poster.
        
        Args:
            vault_path: Path to Obsidian vault (for loading credentials)
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.logs_path = self.vault_path / 'Logs'
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables from .env file
        self._load_credentials()
        
        # Setup logging
        self._setup_logging()
        
        # API configuration
        self.base_url = "https://api.linkedin.com/rest/posts"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": "202506",  # Latest stable version
            "Content-Type": "application/json"
        }
        
        self.logger.info(f"LinkedIn API Poster initialized for: {self.person_urn}")

    def _load_credentials(self):
        """Load LinkedIn credentials from environment or .env file."""
        # Try to load from .env file in project root
        env_paths = [
            Path.cwd() / '.env',
            self.vault_path / '.env',
            Path.home() / '.linkedin_api.env'
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break
        else:
            # Try to load from current environment
            load_dotenv()
        
        # Get credentials
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.person_urn = os.getenv('LINKEDIN_PERSON_URN')
        
        if not self.access_token:
            raise ValueError(
                "LINKEDIN_ACCESS_TOKEN not found. "
                "Please set it in .env file or environment variable.\n"
                "See LINKEDIN_SETUP_GUIDE.md for instructions."
            )
        
        if not self.person_urn:
            raise ValueError(
                "LINKEDIN_PERSON_URN not found. "
                "Please set it in .env file or environment variable.\n"
                "See LINKEDIN_SETUP_GUIDE.md for instructions."
            )

    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.logs_path / f'linkedin_api_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LinkedInAPIPoster')

    def get_person_urn(self) -> str:
        """
        Get the authenticated user's Person URN.

        Returns:
            Person URN string (e.g., "urn:li:person:ABC123")
        """
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # NEW LinkedIn API returns 'sub' field instead of 'id'
            # Try both 'sub' and 'id' for compatibility
            person_id = data.get('sub') or data.get('id')
            
            if not person_id:
                self.logger.error(f"API response missing 'sub' and 'id' fields. Response: {data}")
                raise ValueError("Could not extract Person URN from API response")
            
            # Convert to proper URN format
            if person_id.startswith('urn:li:person:'):
                person_urn = person_id
            else:
                person_urn = f"urn:li:person:{person_id}"
            
            self.logger.info(f"Extracted Person URN: {person_urn}")
            return person_urn

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get Person URN: {e}")
            raise

    def post(
        self,
        content: str,
        hashtags: Optional[List[str]] = None,
        visibility: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """
        Create a post on LinkedIn.
        
        Args:
            content: The text content of the post
            hashtags: Optional list of hashtags (without # symbol)
            visibility: Post visibility - "PUBLIC", "CONNECTIONS", or "ANYONE"
        
        Returns:
            Dictionary with post details and status
        
        Example:
            >>> poster = LinkedInAPIPoster()
            >>> result = poster.post(
            ...     content="Excited to share our new product!",
            ...     hashtags=["AI", "Automation"],
            ...     visibility="PUBLIC"
            ... )
            >>> print(result['post_id'])
            urn:li:share:123456789
        """
        # Format content with hashtags
        if hashtags:
            hashtag_string = " ".join([f"#{tag.lstrip('#')}" for tag in hashtags])
            content = f"{content}\n\n{hashtag_string}"
        
        self.logger.info(f"Creating post ({len(content)} chars)")
        self.logger.info(f"Content preview: {content[:100]}...")
        
        # Build request payload
        payload = {
            "author": self.person_urn,
            "commentary": content,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
        
        # Log the full payload (for debugging)
        self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Send POST request to LinkedIn API
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Check response
            result = {
                'success': False,
                'post_id': None,
                'status_code': response.status_code,
                'response': None,
                'error': None
            }
            
            if response.status_code == 201:
                # Success! Extract post ID from header
                post_id = response.headers.get('x-restli-id')
                result['success'] = True
                result['post_id'] = post_id
                result['response'] = response.json() if response.text else {}
                
                self.logger.info(f"[OK] Post created successfully!")
                self.logger.info(f"Post ID: {post_id}")
                
                # Log to posts file
                self._log_post(content, hashtags, post_id, success=True)
                
            else:
                # Error occurred
                error_data = response.json() if response.text else {}
                result['error'] = error_data
                result['response'] = error_data
                
                self.logger.error(f"[FAIL] Failed to create post")
                self.logger.error(f"Status code: {response.status_code}")
                self.logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                
                # Log failed attempt
                self._log_post(content, hashtags, None, success=False, error=str(error_data))
            
            return result
            
        except requests.exceptions.Timeout:
            self.logger.error("Request timed out")
            return {
                'success': False,
                'post_id': None,
                'error': 'Request timed out',
                'status_code': None
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return {
                'success': False,
                'post_id': None,
                'error': str(e),
                'status_code': None
            }

    def _log_post(
        self,
        content: str,
        hashtags: Optional[List[str]],
        post_id: Optional[str],
        success: bool,
        error: Optional[str] = None
    ):
        """Log post to JSONL file for audit trail."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': content[:500],  # Truncate long content
            'hashtags': hashtags or [],
            'post_id': post_id,
            'success': success,
            'error': error
        }
        
        log_file = self.logs_path / 'linkedin_posts.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        self.logger.info(f"Post logged to: {log_file}")

    def test_connection(self) -> bool:
        """
        Test the LinkedIn API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        self.logger.info("Testing LinkedIn API connection...")
        
        try:
            # Try to get user info
            person_urn = self.get_person_urn()
            self.logger.info(f"[OK] Connection successful! Person URN: {person_urn}")
            return True
            
        except Exception as e:
            self.logger.error(f"[FAIL] Connection failed: {e}")
            return False


def main():
    """Main entry point for LinkedIn API Poster."""
    parser = argparse.ArgumentParser(
        description='LinkedIn API Poster - Post to LinkedIn using official API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple text post
  python linkedin_api_poster.py --content "Hello LinkedIn!"
  
  # Post with hashtags
  python linkedin_api_poster.py --content "New product launch" --hashtags "AI,Automation,Tech"
  
  # Test connection
  python linkedin_api_poster.py --test
  
  # Get your Person URN
  python linkedin_api_poster.py --get-urn
        """
    )
    
    parser.add_argument('--content', type=str, help='Post content text')
    parser.add_argument('--hashtags', type=str, help='Comma-separated hashtags (without #)')
    parser.add_argument('--visibility', type=str, default='PUBLIC',
                       choices=['PUBLIC', 'CONNECTIONS', 'ANYONE'],
                       help='Post visibility (default: PUBLIC)')
    parser.add_argument('--vault', type=str, default='.',
                       help='Path to Obsidian vault (default: current directory)')
    parser.add_argument('--test', action='store_true',
                       help='Test API connection and exit')
    parser.add_argument('--get-urn', action='store_true',
                       help='Get your Person URN and exit')
    parser.add_argument('--setup', action='store_true',
                       help='Show setup instructions')
    
    args = parser.parse_args()
    
    # Show setup instructions
    if args.setup:
        print("""
=================================================================
          LinkedIn API Setup Instructions
=================================================================

1. Create LinkedIn Developer App:
   - Go to: https://www.linkedin.com/developers/
   - Click "Create app"
   - Fill in app details

2. Enable Share on LinkedIn:
   - In your app dashboard, go to "Products"
   - Enable "Share on LinkedIn"

3. Generate Access Token:
   - Go to "Auth" tab
   - Click "Generate access token"
   - Select scopes: w_member_social, r_basicprofile
   - Copy the token

4. Get Your Person URN:
   - Run: python linkedin_api_poster.py --get-urn
   - Or use the token in the API call

5. Create .env file:
   LINKEDIN_ACCESS_TOKEN=your_token_here
   LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID

6. Test connection:
   python linkedin_api_poster.py --test

For more details, see LINKEDIN_API_SETUP_GUIDE.md
        """)
        return 0
    
    try:
        poster = LinkedInAPIPoster(vault_path=args.vault)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nRun with --setup for setup instructions")
        return 1
    
    # Test connection
    if args.test:
        success = poster.test_connection()
        return 0 if success else 1
    
    # Get Person URN
    if args.get_urn:
        try:
            person_urn = poster.get_person_urn()
            print(f"Your Person URN: {person_urn}")
            print(f"\nAdd to .env file:")
            print(f"LINKEDIN_PERSON_URN={person_urn}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    # Create post
    if args.content:
        hashtags = None
        if args.hashtags:
            hashtags = [t.strip() for t in args.hashtags.split(',')]
        
        result = poster.post(
            content=args.content,
            hashtags=hashtags,
            visibility=args.visibility
        )
        
        if result['success']:
            print(f"\n[OK] Post published successfully!")
            print(f"Post ID: {result['post_id']}")
            return 0
        else:
            print(f"\n[FAIL] Failed to publish post")
            print(f"Error: {result['error']}")
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
