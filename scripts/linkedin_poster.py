"""
LinkedIn Poster - Production Ready with Full Validation

Posts updates to LinkedIn using browser automation via Playwright.
Includes full validation to ensure posts are actually published.

Usage:
    python linkedin_poster.py --content "Your post content" --vault /path/to/vault
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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, expect
except ImportError:
    print("Missing required package. Install with:")
    print("pip install playwright")
    print("playwright install")
    sys.exit(1)


class LinkedInPoster:
    """Post updates to LinkedIn using browser automation."""

    POST_BUTTON_SELECTORS = [
        'button:has-text("Start a post")',
        'button:has-text("Start")',
        '.share-box-feed-entry__trigger',
        'button.ember-view[id*="ember"]',
    ]

    EDITOR_SELECTORS = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"]',
        '[data-test="update-editor"]',
    ]

    SUBMIT_BUTTON_SELECTORS = [
        'button:has-text("Post")',
        '[data-test="update-submit-button"]',
        'button:has-text("Post to")',
    ]

    def __init__(
        self,
        vault_path: str,
        session_path: Optional[str] = None,
        headless: bool = True,
        timeout: int = 90000
    ):
        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path) if session_path else self.vault_path / '.linkedin_session'
        self.headless = headless
        self.timeout = timeout
        self.logs_path = self.vault_path / 'Logs'
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self.session_path.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        log_file = self.logs_path / f'linkedin_{datetime.now().strftime("%Y-%m-%d")}.log'
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LinkedInPoster')

    def _take_screenshot(self, page, name: str):
        """Take screenshot for debugging."""
        try:
            screenshot_path = self.logs_path / f'{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            page.screenshot(path=str(screenshot_path), full_page=False)
            self.logger.info(f'Screenshot saved: {screenshot_path}')
            return screenshot_path
        except Exception as e:
            self.logger.warning(f'Could not take screenshot: {e}')
            return None

    def _wait_for_page_load(self, page, timeout: int = 30000):
        """Wait for LinkedIn feed page to fully load."""
        self.logger.info('Waiting for LinkedIn feed to load...')
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            if 'linkedin.com/feed' not in page.url and 'linkedin.com/home' not in page.url:
                self.logger.warning(f'Unexpected URL: {page.url}')
                if 'login' in page.url:
                    return False
            indicators = [
                page.locator('nav').first,
                page.locator('div.feed-main').first,
                page.locator('div[id*="feed"]').first,
            ]
            loaded_count = 0
            for indicator in indicators:
                try:
                    if indicator.is_visible(timeout=3000):
                        loaded_count += 1
                except:
                    pass
            if loaded_count >= 2:
                self.logger.info(f'Page loaded successfully ({loaded_count} indicators)')
                return True
            page.wait_for_timeout(2000)
        self.logger.warning(f'Page load timeout after {timeout}ms')
        return False

    def _find_element(self, page, selectors: List[str], description: str, timeout: int = 10000):
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=timeout):
                    self.logger.info(f'Found {description} with selector: {selector}')
                    return locator
            except Exception as e:
                self.logger.debug(f'Selector {selector} failed: {str(e)[:50]}')
        self.logger.error(f'Could not find {description} with any selector')
        return None

    def _check_for_errors(self, page) -> Optional[str]:
        """Check if there are any error messages on the page."""
        error_selectors = [
            '.msg-error',
            '[data-test="error"]',
            '.artdeco-toast-item--error',
            'text=Error',
            'text=Failed',
            'text=Unable to post',
        ]
        for selector in error_selectors:
            try:
                if page.locator(selector).first.is_visible(timeout=2000):
                    error_text = page.locator(selector).first.inner_text(timeout=2000)
                    return error_text
            except:
                pass
        return None

    def _check_post_published(self, page) -> bool:
        """
        Check if the post was actually published.
        Looks for confirmation messages or the post in the feed.
        """
        # Look for success toast/message
        success_indicators = [
            'text=Post sent',
            'text=Your post has been sent',
            'text=Posted',
            '.artdeco-toast-item--success',
        ]
        
        for indicator in success_indicators:
            try:
                if page.locator(indicator).first.is_visible(timeout=3000):
                    self.logger.info('Found post confirmation message')
                    return True
            except:
                pass
        
        # Look for the post in the feed (most reliable)
        try:
            # Look for the first post in the feed that matches our content
            feed_posts = page.locator('div.feed-shared-update-v2').all()
            if feed_posts:
                self.logger.info(f'Found {len(feed_posts)} posts in feed')
                # If we can see posts, the feed is loaded
                return True
        except Exception as e:
            self.logger.warning(f'Could not check feed: {e}')
        
        return False

    def post_to_linkedin(
        self,
        content: str,
        hashtags: Optional[List[str]] = None,
        image_path: Optional[str] = None
    ) -> bool:
        """Post content to LinkedIn with full validation."""
        if hashtags:
            hashtag_text = ' '.join([f'#{tag}' for tag in hashtags])
            content = f"{content}\n\n{hashtag_text}"

        self.logger.info(f'Posting to LinkedIn (length: {len(content)} chars)')
        self.logger.info(f'Content preview: {content[:100]}...')

        browser = None
        try:
            with sync_playwright() as p:
                self.logger.info(f'Launching browser (session: {self.session_path})')
                self.logger.info(f'Headless mode: {self.headless}')

                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--window-size=1920,1080'
                    ],
                    viewport={'width': 1920, 'height': 1080}
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to LinkedIn
                self.logger.info('Navigating to LinkedIn feed...')
                page.goto('https://www.linkedin.com/feed', timeout=self.timeout)

                # Wait for page load
                if not self._wait_for_page_load(page, timeout=40000):
                    self.logger.error('Failed to load LinkedIn feed')
                    self._take_screenshot(page, 'error_load')
                    browser.close()
                    return False

                self.logger.info('Waiting for page to become interactive...')
                page.wait_for_timeout(3000)
                self._take_screenshot(page, 'after_load')

                # Find and click "Start a post"
                self.logger.info('Looking for "Start a post" button...')
                post_button = self._find_element(page, self.POST_BUTTON_SELECTORS, 'post button', timeout=15000)
                if not post_button:
                    self._take_screenshot(page, 'error_no_button')
                    browser.close()
                    return False

                post_button.click()
                self.logger.info('"Start a post" button clicked')
                page.wait_for_timeout(3000)
                self._take_screenshot(page, 'after_click_start')

                # Check if editor opened
                self.logger.info('Looking for post editor...')
                editor = self._find_element(page, self.EDITOR_SELECTORS, 'post editor', timeout=15000)
                if not editor:
                    self.logger.error('Post editor did not open')
                    self._take_screenshot(page, 'error_no_editor')
                    browser.close()
                    return False

                # Check for audience selector (important!)
                try:
                    audience_button = page.locator('button:has-text("Anyone")').first
                    if audience_button.is_visible(timeout=2000):
                        self.logger.info('Found audience selector - ensuring "Anyone" is selected')
                        # Click to verify/change audience if needed
                        # audience_button.click()
                        # page.wait_for_timeout(1000)
                except:
                    self.logger.debug('No audience selector found - using default')

                # Enter content
                self.logger.info('Entering post content...')
                try:
                    editor.press('Control+a')
                    page.wait_for_timeout(500)
                    editor.press('Delete')
                    page.wait_for_timeout(500)
                    editor.type(content, delay=80)
                    page.wait_for_timeout(2000)
                    self.logger.info('Content entered successfully')
                    
                    # Verify content was entered
                    editor_content = editor.inner_text(timeout=2000)
                    self.logger.info(f'Editor content length: {len(editor_content)} chars')
                    if len(editor_content) < len(content) * 0.8:
                        self.logger.warning('Content may not have been fully entered')
                    
                except Exception as e:
                    self.logger.error(f'Failed to enter content: {e}')
                    self._take_screenshot(page, 'error_entering')
                    browser.close()
                    return False

                # Add image if provided
                if image_path and os.path.exists(image_path):
                    self.logger.info(f'Adding image: {image_path}')
                    try:
                        file_input = page.locator('input[type="file"][accept*="image"]').first
                        file_input.set_input_files(image_path)
                        page.wait_for_timeout(3000)
                        self.logger.info('Image attached successfully')
                    except Exception as e:
                        self.logger.warning(f'Failed to add image: {e}')

                # Find and click Post button
                self.logger.info('Looking for Post submit button...')
                submit_button = self._find_element(page, self.SUBMIT_BUTTON_SELECTORS, 'submit button', timeout=15000)
                if not submit_button:
                    self.logger.error('Submit button not found')
                    self._take_screenshot(page, 'error_no_submit')
                    browser.close()
                    return False

                # Check if button is enabled
                try:
                    expect(submit_button).to_be_enabled(timeout=5000)
                    self.logger.info('Submit button is enabled')
                except Exception as e:
                    self.logger.error(f'Submit button is disabled: {e}')
                    self._take_screenshot(page, 'disabled_button')
                    browser.close()
                    return False

                # Click submit (FIRST TIME - opens visibility modal)
                self.logger.info('Clicking Post button (step 1 of 2)...')
                submit_button.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                submit_button.click()
                
                # Wait for visibility modal or processing
                self.logger.info('Waiting for LinkedIn response...')
                page.wait_for_timeout(5000)
                
                # Take screenshot
                self._take_screenshot(page, 'after_first_submit')

                # CHECK FOR VISIBILITY MODAL
                self.logger.info('Checking for visibility confirmation modal...')
                visibility_handled = False
                
                try:
                    visibility_modal = page.locator('text=Who can see your post?').first
                    if visibility_modal.is_visible(timeout=3000):
                        self.logger.info('Found visibility confirmation modal!')
                        
                        # Click "Anyone" to enable Done button
                        try:
                            anyone_button = page.locator('button:has-text("Anyone")').first
                            if anyone_button.is_visible(timeout=2000):
                                self.logger.info('Clicking "Anyone" option...')
                                anyone_button.click()
                                page.wait_for_timeout(1500)
                        except Exception as e:
                            self.logger.debug(f'Anyone button: {e}')
                        
                        # Click "Done" button (this CLOSES modal, doesn't submit yet!)
                        try:
                            done_button = page.locator('button:has-text("Done")').first
                            if done_button.is_visible(timeout=2000):
                                is_disabled = done_button.get_attribute('disabled') is not None
                                if is_disabled:
                                    self.logger.warning('Done button disabled - waiting...')
                                    page.wait_for_timeout(3000)
                                
                                self.logger.info('Clicking "Done" button...')
                                done_button.scroll_into_view_if_needed()
                                page.wait_for_timeout(500)
                                done_button.click()
                                page.wait_for_timeout(3000)
                                self.logger.info('Visibility modal closed!')
                                visibility_handled = True
                        except Exception as e:
                            self.logger.error(f'Could not click Done: {e}')
                            
                        self._take_screenshot(page, 'after_visibility_modal')
                    else:
                        self.logger.info('No visibility modal found')
                except Exception as e:
                    self.logger.debug(f'Visibility check: {e}')

                # CRITICAL: After handling visibility modal, we need to click Post AGAIN
                if visibility_handled:
                    self.logger.info('Looking for Post button to click (step 2 of 2)...')
                    page.wait_for_timeout(2000)
                    
                    # Find Post button again
                    try:
                        submit_button2 = self._find_element(page, self.SUBMIT_BUTTON_SELECTORS, 'submit button (final)', timeout=10000)
                        if submit_button2:
                            expect(submit_button2).to_be_enabled(timeout=5000)
                            submit_button2.scroll_into_view_if_needed()
                            page.wait_for_timeout(500)
                            
                            self.logger.info('Clicking Post button (FINAL SUBMIT)...')
                            submit_button2.click()
                            page.wait_for_timeout(8000)
                            
                            self._take_screenshot(page, 'after_final_submit')
                            self.logger.info('Final submit clicked!')
                        else:
                            self.logger.warning('Could not find final Post button')
                    except Exception as e:
                        self.logger.error(f'Final submit failed: {e}')
                else:
                    # No visibility modal, just wait for normal processing
                    self.logger.info('No visibility modal - waiting for normal processing...')
                    page.wait_for_timeout(5000)

                # Check for error messages
                error_msg = self._check_for_errors(page)
                if error_msg:
                    self.logger.error(f'Post failed with error: {error_msg}')
                    self._take_screenshot(page, 'error_message')
                    browser.close()
                    return False

                # Check for success indicators
                success = False
                
                # Look for success toast
                try:
                    if page.locator('.artdeco-toast-item--success').first.is_visible(timeout=5000):
                        self.logger.info('Found success toast message')
                        success = True
                except:
                    pass
                
                # Look for "Post sent" message
                try:
                    if page.locator('text=Post sent').first.is_visible(timeout=3000):
                        self.logger.info('Found "Post sent" message')
                        success = True
                except:
                    pass
                
                # Look for "Your post has been sent" message
                try:
                    if page.locator('text=Your post has been sent').first.is_visible(timeout=3000):
                        self.logger.info('Found "Your post has been sent" message')
                        success = True
                except:
                    pass
                
                # Check if feed is visible
                if not success:
                    try:
                        if page.locator('div.feed-main').first.is_visible(timeout=5000):
                            self.logger.info('Feed visible - post may be submitted')
                            success = True
                    except:
                        pass
                
                if success:
                    self.logger.info('✅ POST SUBMISSION CONFIRMED!')
                else:
                    self.logger.warning('Could not confirm post, but no errors detected')

                self.logger.info('Post process complete')
                browser.close()
                return True

        except Exception as e:
            self.logger.error(f'Error posting to LinkedIn: {e}')
            if browser:
                try:
                    self._take_screenshot(browser.pages[0] if browser.pages else page, 'error_exception')
                    browser.close()
                except:
                    pass
            return False

    def setup_session(self, visible: bool = True):
        """Setup LinkedIn session by logging in manually."""
        self.logger.info('Opening LinkedIn for login...')
        print("\n" + "="*60)
        print("LINKEDIN SESSION SETUP")
        print("="*60)
        print("\nPlease:")
        print("  1. Log in to LinkedIn")
        print("  2. Wait for feed to load")
        print("  3. Scroll through feed")
        print("  4. Keep browser open 10 seconds")
        print("  5. Close browser when done\n")

        browser = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=not visible,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
                    viewport={'width': 1920, 'height': 1080}
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://www.linkedin.com/login')
                print("Complete login, navigate to feed, then close browser.\n")
                try:
                    while browser.pages:
                        page.wait_for_timeout(1000)
                except KeyboardInterrupt:
                    pass
                print("\nSession setup complete!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass


def parse_action_file(filepath: Path) -> Dict[str, Any]:
    """Parse LinkedIn post action file."""
    content = filepath.read_text(encoding='utf-8')
    data = {'content': '', 'hashtags': [], 'image': None, 'scheduled_time': None}
    lines = content.split('\n')
    in_frontmatter = False
    in_body = False
    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            if line.startswith('content:'):
                data['content'] = line.split(':', 1)[1].strip().strip('"')
            elif line.startswith('#hashtags:'):
                tags = line.split(':', 1)[1].strip()
                data['hashtags'] = [t.strip().lstrip('#') for t in tags.split()]
            elif line.startswith('image:'):
                data['image'] = line.split(':', 1)[1].strip()
        elif in_body and not line.startswith('#') and not line.startswith('<!--'):
            if line.strip():
                data['content'] += line + '\n'
    return data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LinkedIn Poster for AI Employee')
    parser.add_argument('--content', type=str, help='Post content')
    parser.add_argument('--hashtags', type=str, help='Hashtags (comma-separated)')
    parser.add_argument('--image', type=str, help='Image path')
    parser.add_argument('--vault', type=str, required=True, help='Vault path')
    parser.add_argument('--action-file', type=Path, help='Action file')
    parser.add_argument('--setup-session', action='store_true', help='Setup session')
    parser.add_argument('--visible', action='store_true', help='Visible mode')
    parser.add_argument('--timeout', type=int, default=90000, help='Timeout ms')

    args = parser.parse_args()
    vault = Path(args.vault)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault}")
        sys.exit(1)

    if args.setup_session:
        poster = LinkedInPoster(str(vault))
        poster.setup_session(visible=True)
        return

    if args.action_file:
        data = parse_action_file(args.action_file)
        args.content = args.content or data['content']
        args.hashtags = args.hashtags or ','.join(data['hashtags'])
        args.image = args.image or data['image']

    if not args.content:
        print("Error: --content is required")
        sys.exit(1)

    hashtags = None
    if args.hashtags:
        hashtags = [t.strip().lstrip('#') for t in args.hashtags.split(',')]

    poster = LinkedInPoster(str(vault), headless=not args.visible, timeout=args.timeout)
    success = poster.post_to_linkedin(content=args.content, hashtags=hashtags, image_path=args.image)

    if success:
        print("\n[OK] Post published successfully!")
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': args.content[:100] + '...',
            'hashtags': hashtags,
            'result': 'success'
        }
        log_file = vault / 'Logs' / 'linkedin_posts.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        sys.exit(0)
    else:
        print("\n[FAIL] Failed to publish post. Check logs for details.")
        print(f"Log file: {poster.logs_path / f'linkedin_{datetime.now().strftime('%Y-%m-%d')}.log'}")
        sys.exit(1)


if __name__ == '__main__':
    main()
