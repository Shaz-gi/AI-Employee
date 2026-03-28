#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto-Poster - Actually posts to LinkedIn automatically

Uses Playwright to automate LinkedIn posting.
Requires LinkedIn session to be authenticated.

Usage:
    python src/linkedin_auto_post.py --content "Your post content here"
    python src/linkedin_auto_post.py --scheduled  # Run by scheduler
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright not installed")
    print("Run: pip install playwright && playwright install")
    sys.exit(1)


class LinkedInAutoPoster:
    """
    Actually posts to LinkedIn using browser automation.
    """
    
    def __init__(self, session_path: Optional[str] = None):
        """
        Initialize LinkedIn Auto-Poster.
        
        Args:
            session_path: Path to store browser session
        """
        self.src_path = Path(__file__).parent
        self.session_path = Path(session_path) if session_path else self.src_path.parent / 'linkedin_session'
        self.vault_path = self.src_path.parent / 'AI_Employee_Vault'
        
        # Ensure session directory exists
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.browser = None
        self.context = None
        self.page = None
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Log in to LinkedIn.
        
        Returns:
            True if successful
        """
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                print("🔗 Launching browser...")
                self.context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,  # Show browser for debugging
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                self.page = self.context.pages[0]
                
                # Navigate to LinkedIn
                print("🔗 Navigating to LinkedIn...")
                try:
                    # Try going to feed first (if already logged in)
                    self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
                    
                    # Check if already logged in
                    if 'feed' in self.page.url or 'mynetwork' in self.page.url:
                        print("✅ Already logged in (session restored)")
                        return True
                        
                except Exception as nav_error:
                    print(f"⚠️  Navigation issue: {nav_error}")
                    print("Trying login page...")
                    
                    # Try login page directly
                    try:
                        self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
                    except Exception as e2:
                        print(f"❌ Could not navigate to LinkedIn: {e2}")
                        print("Check your internet connection")
                        return False
                
                # Check if already logged in
                if 'feed' in self.page.url or 'mynetwork' in self.page.url:
                    print("✅ Already logged in (session restored)")
                    return True
                
                # Get credentials from environment or prompt
                if not email:
                    email = os.getenv('LINKEDIN_EMAIL')
                if not password:
                    password = os.getenv('LINKEDIN_PASSWORD')
                
                if not email or not password:
                    print("⚠️  LinkedIn credentials not set")
                    print("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
                    print("Or wait - you have 60 seconds to log in manually...")
                    
                    # Wait for manual login
                    try:
                        print("⏳ Waiting for manual login...")
                        self.page.wait_for_url('**/feed/**', timeout=60000)
                        print("✅ Manual login detected!")
                        return True
                    except PlaywrightTimeout:
                        print("❌ Login timeout")
                        return False
                
                # Fill login form
                print("🔗 Logging in...")
                
                try:
                    # Email field
                    email_field = self.page.wait_for_selector('#username', timeout=15000)
                    email_field.fill(email)
                    
                    # Password field
                    password_field = self.page.wait_for_selector('#password', timeout=10000)
                    password_field.fill(password)
                    
                    # Sign in button
                    sign_in = self.page.wait_for_selector('button[type="submit"]', timeout=10000)
                    sign_in.click()
                    
                    # Wait for navigation to feed
                    try:
                        self.page.wait_for_url('**/feed/**', timeout=60000)
                        print("✅ Login successful!")
                        return True
                    except PlaywrightTimeout:
                        # Check if we're on feed anyway
                        if 'feed' in self.page.url or 'mynetwork' in self.page.url:
                            print("✅ Login successful!")
                            return True
                        else:
                            print("❌ Login may have failed - checking...")
                            # Take screenshot for debugging
                            screenshot_path = self.session_path.parent / 'login_error.png'
                            self.page.screenshot(path=str(screenshot_path))
                            print(f"Screenshot saved to: {screenshot_path}")
                            print(f"Current URL: {self.page.url}")
                            return False
                            
                except PlaywrightTimeout as e:
                    print(f"❌ Login error: {e}")
                    # Take screenshot
                    screenshot_path = self.session_path.parent / 'login_timeout.png'
                    self.page.screenshot(path=str(screenshot_path))
                    print(f"Screenshot saved to: {screenshot_path}")
                    return False
                    
        except Exception as e:
            print(f"❌ Login exception: {e}")
            return False
    
    def post(self, content: str, image_path: Optional[str] = None) -> dict:
        """
        Post content to LinkedIn.
        
        Args:
            content: Post text
            image_path: Optional image to attach
            
        Returns:
            Result dictionary
        """
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                print("🔗 Launching browser...")
                self.context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                self.page = self.context.pages[0]
                
                # Navigate to feed
                print("📝 Navigating to LinkedIn feed...")
                try:
                    self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
                    self.page.wait_for_timeout(3000)
                    
                    # Check if logged in
                    if 'login' in self.page.url:
                        print("⚠️  Not logged in, attempting login...")
                        if not self._do_login(p):
                            return {'success': False, 'error': 'Login failed'}
                        self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
                        self.page.wait_for_timeout(3000)
                        
                except Exception as nav_error:
                    print(f"⚠️  Navigation error: {nav_error}")
                    return {'success': False, 'error': f'Navigation failed: {nav_error}'}
                
                # Now post
                return self._do_post(content, image_path)
                
        except Exception as e:
            print(f"❌ Post error: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            # Cleanup
            if self.context:
                print("🔗 Closing browser...")
                try:
                    self.context = None
                except:
                    pass
    
    def _do_login(self, p) -> bool:
        """Perform login within existing context."""
        try:
            email = os.getenv('LINKEDIN_EMAIL')
            password = os.getenv('LINKEDIN_PASSWORD')
            
            if not email or not password:
                print("⚠️  Credentials not set, waiting for manual login...")
                try:
                    self.page.wait_for_url('**/feed/**', timeout=60000)
                    return True
                except:
                    return False
            
            # Fill login form
            self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
            
            email_field = self.page.wait_for_selector('#username', timeout=15000)
            email_field.fill(email)
            
            password_field = self.page.wait_for_selector('#password', timeout=10000)
            password_field.fill(password)
            
            sign_in = self.page.wait_for_selector('button[type="submit"]', timeout=10000)
            sign_in.click()
            
            try:
                self.page.wait_for_url('**/feed/**', timeout=60000)
                return True
            except:
                return 'feed' in self.page.url
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def _do_post(self, content: str, image_path: Optional[str] = None) -> dict:
        """Perform the actual posting."""
        try:
            print("📝 Creating LinkedIn post...")
            
            # Find and click "Start a post"
            print("📝 Finding 'Start a post' button...")
            self.page.wait_for_selector('div.share-box-feed-entry', timeout=60000)
            self.page.wait_for_timeout(2000)
            
            start_post = None
            selectors = [
                'button[aria-label="Start a post"]',
                'div.share-box-feed-entry__trigger button',
                'button:has-text("Start a post")'
            ]
            
            for selector in selectors:
                start_post = self.page.query_selector(selector)
                if start_post:
                    print(f"✅ Found with: {selector}")
                    break
            
            if not start_post:
                screenshot_path = self.session_path.parent / 'no_start_post.png'
                self.page.screenshot(path=str(screenshot_path))
                return {'success': False, 'error': 'Could not find Start a post button'}
            
            start_post.click()
            print("✅ Post dialog opened")
            self.page.wait_for_timeout(3000)
            
            # Enter content
            print("📝 Entering content...")
            self.page.wait_for_selector('div.post-create-post-container', timeout=60000)
            self.page.wait_for_timeout(2000)
            
            text_field = None
            for selector in [
                'div[contenteditable="true"][aria-label="What do you want to talk about?"]',
                'div.post-create-post-container div[contenteditable="true"]'
            ]:
                text_field = self.page.query_selector(selector)
                if text_field:
                    break
            
            if not text_field:
                return {'success': False, 'error': 'Could not find text field'}
            
            text_field.click()
            self.page.wait_for_timeout(500)
            
            print(f"📝 Typing {len(content)} characters...")
            self.page.keyboard.type(content, delay=50)
            print("✅ Content entered")
            
            # Click Post
            print("📝 Posting...")
            self.page.wait_for_timeout(2000)
            
            post_button = self.page.query_selector('button[aria-label="Post"]')
            if not post_button:
                post_button = self.page.query_selector('button:has-text("Post")')
            
            if post_button:
                post_button.click()
                print("⏳ Waiting for post to submit...")
                self.page.wait_for_timeout(8000)
                print("✅ Post submitted!")
                
                result = {
                    'success': True,
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'timestamp': datetime.now().isoformat(),
                    'posted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self._save_post_record(content, result)
                return result
            else:
                return {'success': False, 'error': 'Could not find Post button'}
                
        except Exception as e:
            print(f"❌ Post error: {e}")
            try:
                screenshot_path = self.session_path.parent / 'post_error.png'
                self.page.screenshot(path=str(screenshot_path))
                print(f"Screenshot: {screenshot_path}")
            except:
                pass
            return {'success': False, 'error': str(e)}
    
    def _save_post_record(self, content: str, result: dict):
        """Save post record to vault."""
        try:
            posts_folder = self.vault_path / 'LinkedIn_Posts'
            posts_folder.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            post_file = posts_folder / f"POST_{timestamp}.md"
            
            post_content = f"""---
posted: {result['posted_at']}
status: posted
---

# LinkedIn Post

{content}

---
*Posted automatically by AI Employee Auto-Poster*
"""
            post_file.write_text(post_content, encoding='utf-8')
            
        except Exception as e:
            print(f"⚠️  Could not save post record: {e}")
    
    def close(self):
        """Close browser (only if still open)."""
        try:
            if self.context:
                print("🔗 Closing browser...")
                # Context is usually closed automatically by sync_playwright
                # Only close if we're outside the context manager
                self.context = None
        except Exception as e:
            # Ignore errors during cleanup
            pass


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn Auto-Poster")
    parser.add_argument("--content", "-c", help="Post content")
    parser.add_argument("--file", "-f", help="Read content from file")
    parser.add_argument("--image", "-i", help="Image path to attach")
    parser.add_argument("--login", action="store_true", help="Force login")
    parser.add_argument("--scheduled", action="store_true", help="Run in scheduled mode")
    parser.add_argument("--email", help="LinkedIn email")
    parser.add_argument("--password", help="LinkedIn password")
    
    args = parser.parse_args()
    
    print("🤖 LinkedIn Auto-Poster")
    print("=" * 50)
    
    poster = LinkedInAutoPoster()
    
    try:
        # Get content - from env var, file, or argument
        content = None
        
        # Check environment variable first (for batch file)
        env_content = os.getenv('LINKEDIN_POST_CONTENT')
        if env_content:
            content = env_content
            print(f"📝 Using content from environment ({len(content)} chars)")
        elif args.file:
            content = Path(args.file).read_text(encoding='utf-8')
            print(f"📝 Reading from file: {args.file}")
        elif args.content:
            content = args.content
            print(f"📝 Using provided content ({len(content)} chars)")
        
        if not content and not args.login:
            print("❌ No content provided")
            print("Use --content or --file to specify post content")
            print("Or use --login to just log in")
            return
        
        # Login if needed or requested
        if args.login or not poster.session_path.exists():
            print("\n🔗 Login required")
            if not poster.login(args.email, args.password):
                print("❌ Login failed")
                return
        
        # If just login, we're done
        if args.login:
            print("\n✅ Login complete! Session saved.")
            print("Next time you can post without logging in again.")
            return
        
        # Post content
        print(f"\n📝 Posting content ({len(content)} characters)...")
        result = poster.post(content, args.image)
        
        if result.get('success'):
            print("\n" + "=" * 50)
            print("✅ POST SUCCESSFUL!")
            print("=" * 50)
            print(f"Posted at: {result.get('posted_at')}")
            print(f"Content: {result.get('content')}")
        else:
            print("\n" + "=" * 50)
            print("❌ POST FAILED")
            print("=" * 50)
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    finally:
        poster.close()


if __name__ == "__main__":
    main()
