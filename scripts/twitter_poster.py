"""
Twitter/X Poster

Posts to Twitter/X via API v2 and generates weekly Twitter summaries.
Integrates with the AI Employee system for automated social media posting.

Usage:
    python scripts/twitter_poster.py --content "Hello Twitter!" --hashtags "AI,Automation"
    python scripts/twitter_poster.py --test-connection
    python scripts/twitter_poster.py --generate-summary --days 7
    python scripts/twitter_poster.py --action-file path/to/action.md
    python scripts/twitter_poster.py --list-tweets --days 7
    python scripts/twitter_poster.py --dry-run --content "Test tweet"

Configuration:
    Set in .env file:
    TWITTER_BEARER_TOKEN=your_bearer_token
    TWITTER_API_KEY=your_api_key
    TWITTER_API_SECRET=your_api_secret
    TWITTER_ACCESS_TOKEN=your_access_token
    TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

API Setup:
    1. Go to https://developer.twitter.com/en/portal/dashboard
    2. Create a Project and App
    3. Get API Key, API Secret, Bearer Token
    4. Generate Access Token and Secret
    5. Add to .env file
"""

import os
import sys
import json
import logging
import argparse
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class TwitterPoster:
    """
    Twitter/X posting and summary generation.

    Uses Twitter API v2 for posting and reading.
    Falls back to API v1.1 if needed.
    """

    def __init__(
        self,
        vault_path: str = 'AI_Employee_Vault',
        dry_run: bool = False
    ):
        """
        Initialize Twitter poster.

        Args:
            vault_path: Path to Obsidian vault
            dry_run: If True, simulate without posting
        """
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.logs_path = self.vault_path / 'Logs'
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Also check project-level Logs/
        self.project_logs_path = Path(__file__).parent.parent / 'Logs'
        self.project_logs_path.mkdir(parents=True, exist_ok=True)

        # Credentials
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.api_key = os.getenv('TWITTER_API_KEY', '')
        self.api_secret = os.getenv('TWITTER_API_SECRET', '')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN', '')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')

        # Setup logging
        self._setup_logging()

        self.logger.info(f'Initialized TwitterPoster')
        self.logger.info(f'Bearer token configured: {bool(self.bearer_token)}')
        self.logger.info(f'API key configured: {bool(self.api_key)}')
        self.logger.info(f'Dry run: {self.dry_run}')

    def _setup_logging(self):
        """Setup logging."""
        log_file = self.project_logs_path / f'twitter_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('TwitterPoster')

    def _log_tweet(self, content: str, tweet_id: str = None, success: bool = True, error: str = None):
        """Log tweet to JSONL file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': content,
            'tweet_id': tweet_id,
            'success': success,
            'error': error
        }

        # Write to project-level Logs/
        jsonl_file = self.project_logs_path / 'twitter_posts.jsonl'
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        # Also write to vault Logs/
        vault_jsonl = self.logs_path / 'twitter_posts.jsonl'
        with open(vault_jsonl, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def post_tweet(
        self,
        content: str,
        hashtags: List[str] = None,
        reply_to: str = None,
        dry_run: bool = None
    ) -> Dict[str, Any]:
        """
        Post a tweet via Twitter API v2.

        Args:
            content: Tweet text (max 280 chars)
            hashtags: List of hashtags (without #)
            reply_to: Tweet ID to reply to (optional)
            dry_run: Override dry_run setting

        Returns:
            Dict with tweet details or error
        """
        dry_run = dry_run if dry_run is not None else self.dry_run

        # Format content with hashtags
        if hashtags:
            hashtag_str = ' '.join([f'#{h}' for h in hashtags])
            content = f"{content}\n\n{hashtag_str}"

        # Truncate to 280 chars
        if len(content) > 280:
            content = content[:277] + '...'

        if dry_run:
            self.logger.info(f'[DRY RUN] Would tweet: {content[:100]}...')
            result = {
                'success': True,
                'content': content,
                'tweet_id': 'dry-run-id',
                'dry_run': True
            }
            self._log_tweet(content, tweet_id='dry-run-id', success=True)
            return result

        # Try API v2 first
        result = self._post_via_api_v2(content, reply_to)

        if result['success']:
            self.logger.info(f'Tweet posted successfully: {result.get("tweet_id")}')
        else:
            self.logger.error(f'Failed to post tweet: {result.get("error")}')

        self._log_tweet(
            content,
            tweet_id=result.get('tweet_id'),
            success=result['success'],
            error=result.get('error')
        )

        return result

    def _post_via_api_v2(self, content: str, reply_to: str = None) -> Dict[str, Any]:
        """Post tweet via Twitter API v2."""
        import urllib.request
        import urllib.error

        if not self.bearer_token:
            return {'success': False, 'error': 'No bearer token configured'}

        url = 'https://api.twitter.com/2/tweets'

        payload = {'text': content}
        if reply_to:
            payload['reply'] = {'in_reply_to_tweet_id': reply_to}

        data = json.dumps(payload).encode('utf-8')

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }

        try:
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                tweet_id = result.get('data', {}).get('id')
                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'text': content
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {
                'success': False,
                'error': f'HTTP {e.code}: {error_body}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test Twitter API connection."""
        import urllib.request
        import urllib.error

        if not self.bearer_token:
            return {'success': False, 'error': 'No bearer token configured'}

        # Get authenticated user info
        url = 'https://api.twitter.com/2/users/me'
        headers = {'Authorization': f'Bearer {self.bearer_token}'}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                user = result.get('data', {})
                return {
                    'success': True,
                    'username': user.get('username'),
                    'name': user.get('name'),
                    'id': user.get('id')
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate weekly Twitter activity summary.

        Reads from twitter_posts.jsonl log file and generates
        a summary report.

        Args:
            days: Number of days to summarize

        Returns:
            Summary dictionary
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Read tweets from log files
        tweets = []

        for log_file in [self.project_logs_path / 'twitter_posts.jsonl',
                         self.logs_path / 'twitter_posts.jsonl']:
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                tweet = json.loads(line)
                                ts = tweet.get('timestamp', '')
                                if ts:
                                    tweet_date = datetime.fromisoformat(ts)
                                    if tweet_date >= cutoff:
                                        tweets.append(tweet)
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    self.logger.warning(f'Could not read {log_file}: {e}')

        # Generate summary
        total_tweets = len(tweets)
        successful = sum(1 for t in tweets if t.get('success'))
        failed = sum(1 for t in tweets if not t.get('success'))

        # Get unique dates
        dates = set()
        for t in tweets:
            ts = t.get('timestamp', '')
            if ts:
                dates.add(ts[:10])

        summary = {
            'period_days': days,
            'total_tweets': total_tweets,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / max(1, total_tweets)) * 100,
            'active_days': len(dates),
            'tweets_per_day': total_tweets / max(1, days),
            'recent_tweets': tweets[-5:] if tweets else []
        }

        self.logger.info(f'Generated Twitter summary: {total_tweets} tweets in {days} days')

        return summary

    def format_summary_report(self, days: int = 7) -> str:
        """
        Format Twitter summary as Markdown report.

        Args:
            days: Number of days to summarize

        Returns:
            Markdown formatted report
        """
        summary = self.generate_summary(days)

        report = f"""# 🐦 Twitter/X Weekly Summary

**Period:** Last {days} days
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| **Total Tweets** | {summary['total_tweets']} |
| **Successful** | {summary['successful']} ✅ |
| **Failed** | {summary['failed']} {'⚠️' if summary['failed'] > 0 else ''} |
| **Success Rate** | {summary['success_rate']:.1f}% |
| **Active Days** | {summary['active_days']} |
| **Tweets/Day** | {summary['tweets_per_day']:.1f} |

---

## 📈 Activity Level

"""

        if summary['tweets_per_day'] >= 2:
            report += "✅ **High activity** - Consistent posting schedule\n"
        elif summary['tweets_per_day'] >= 1:
            report += "🟡 **Moderate activity** - Consider increasing frequency\n"
        else:
            report += "⚠️ **Low activity** - Recommend 1-2 tweets per day\n"

        report += "\n---\n\n"

        # Recent tweets
        recent = summary.get('recent_tweets', [])
        if recent:
            report += "## 📝 Recent Tweets\n\n"
            report += "| Date | Content | Status |\n"
            report += "|------|---------|----------|\n"
            for tweet in recent[-5:]:
                ts = tweet.get('timestamp', 'N/A')[:10]
                content = tweet.get('content', '')[:60]
                status = '✅' if tweet.get('success') else '❌'
                report += f"| {ts} | {content} | {status} |\n"

        report += "\n---\n\n"

        # Recommendations
        report += "## 💡 Recommendations\n\n"

        if summary['success_rate'] < 80:
            report += "- 🔴 **Improve success rate** - Review failed tweets for errors\n"
        if summary['tweets_per_day'] < 1:
            report += "- 🟡 **Increase posting frequency** - Target 1-2 tweets per day\n"
        if summary['failed'] > 0:
            report += f"- ⚠️ **Review {summary['failed']} failed tweets** - Check API credentials\n"
        if summary['success_rate'] >= 90 and summary['tweets_per_day'] >= 1:
            report += "- ✅ **Great performance** - Maintain current posting schedule\n"

        return report

    def list_tweets(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        List recent tweets from logs.

        Args:
            days: Number of days to look back

        Returns:
            List of tweet dictionaries
        """
        cutoff = datetime.now() - timedelta(days=days)
        tweets = []

        for log_file in [self.project_logs_path / 'twitter_posts.jsonl',
                         self.logs_path / 'twitter_posts.jsonl']:
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                tweet = json.loads(line)
                                ts = tweet.get('timestamp', '')
                                if ts:
                                    tweet_date = datetime.fromisoformat(ts)
                                    if tweet_date >= cutoff:
                                        tweets.append(tweet)
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    self.logger.warning(f'Could not read {log_file}: {e}')

        tweets.sort(key=lambda t: t.get('timestamp', ''))
        return tweets


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Twitter/X Poster')
    parser.add_argument('--vault', type=str, default='AI_Employee_Vault', help='Vault path')
    parser.add_argument('--content', type=str, help='Tweet content')
    parser.add_argument('--hashtags', type=str, help='Hashtags (comma-separated)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without posting')
    parser.add_argument('--test-connection', action='store_true', help='Test API connection')
    parser.add_argument('--generate-summary', action='store_true', help='Generate weekly summary')
    parser.add_argument('--days', type=int, default=7, help='Days for summary (default: 7)')
    parser.add_argument('--list-tweets', action='store_true', help='List recent tweets')
    parser.add_argument('--action-file', type=str, help='Process action file')

    args = parser.parse_args()

    # Create poster
    poster = TwitterPoster(
        vault_path=args.vault,
        dry_run=args.dry_run
    )

    if args.test_connection:
        result = poster.test_connection()
        if result['success']:
            print(f"✅ Connected as @{result['username']} ({result['name']})")
        else:
            print(f"❌ Connection failed: {result['error']}")
        return

    if args.generate_summary:
        report = poster.format_summary_report(args.days)
        print(report)

        # Save to vault
        summary_file = poster.logs_path / f'twitter_summary_{datetime.now().strftime("%Y-%m-%d")}.md'
        summary_file.write_text(report, encoding='utf-8')
        print(f"\n📄 Summary saved to: {summary_file}")
        return

    if args.list_tweets:
        tweets = poster.list_tweets(args.days)
        print(f"\n📝 Recent Tweets (last {args.days} days):")
        print("=" * 60)
        for tweet in tweets:
            ts = tweet.get('timestamp', 'N/A')[:16]
            content = tweet.get('content', '')[:70]
            status = '✅' if tweet.get('success') else '❌'
            print(f"{status} [{ts}] {content}")
        print(f"\nTotal: {len(tweets)} tweets")
        return

    if args.action_file:
        action_file = Path(args.action_file)
        if action_file.exists():
            content = action_file.read_text(encoding='utf-8')
            # Simple parsing: look for content field
            for line in content.split('\n'):
                if line.startswith('content:') or line.startswith('tweet:'):
                    tweet_content = line.split(':', 1)[1].strip()
                    result = poster.post_tweet(tweet_content)
                    print(f"Tweet result: {result}")
                    break
        return

    if args.content:
        hashtags = args.hashtags.split(',') if args.hashtags else []
        result = poster.post_tweet(args.content, hashtags)
        if result['success']:
            print(f"✅ Tweet posted: {result.get('tweet_id')}")
        else:
            print(f"❌ Failed: {result.get('error')}")
        return

    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()
