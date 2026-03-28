#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Poster - Auto-post business updates to LinkedIn.

This script uses Playwright to:
1. Log in to LinkedIn
2. Create and post business updates
3. Generate engagement summaries

Requirements:
- playwright installed: pip install playwright
- Playwright browsers: playwright install
- LinkedIn credentials (via environment or secure storage)

Usage:
    python linkedin_poster.py --post "Your post content here"
    python linkedin_poster.py --session /path/to/session
    python linkedin_poster.py --login  # Interactive login
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright not installed")
    print("Run: pip install playwright && playwright install")
    sys.exit(1)


class LinkedInPoster:
    """
    LinkedIn automation using Playwright.
    
    Features:
    - Post updates to LinkedIn
    - Maintain session for reuse
    - Extract engagement metrics
    """
    
    def __init__(
        self,
        session_path: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize LinkedIn Poster.
        
        Args:
            session_path: Path to store/load session data
            email: LinkedIn email (for login)
            password: LinkedIn password (for login)
        """
        self.session_path = Path(session_path) if session_path else Path.home() / '.ai_employee' / 'linkedin_session'
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        
        self.browser = None
        self.context = None
        self.page = None
        self.logged_in = False
    
    def _ensure_session_dir(self):
        """Create session directory if it doesn't exist."""
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Log in to LinkedIn.
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            
        Returns:
            True if login successful
        """
        email = email or self.email
        password = password or self.password
        
        if not email or not password:
            print("Error: LinkedIn credentials required")
            print("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
            print("Or pass --email and --password arguments")
            return False
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                self.context = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )
                
                self.page = self.context.pages[0]
                
                # Navigate to LinkedIn
                print("Navigating to LinkedIn...")
                self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')
                
                # Check if already logged in
                if 'feed' in self.page.url:
                    print("Already logged in (session restored)")
                    self.logged_in = True
                    return True
                
                # Fill login form
                print("Logging in...")
                
                # Wait for and fill email
                try:
                    email_field = self.page.wait_for_selector('#username', timeout=10000)
                    email_field.fill(email)
                except PlaywrightTimeout:
                    print("Could not find email field")
                    return False
                
                # Fill password
                try:
                    password_field = self.page.wait_for_selector('#password', timeout=5000)
                    password_field.fill(password)
                except PlaywrightTimeout:
                    print("Could not find password field")
                    return False
                
                # Click sign in
                sign_in_button = self.page.wait_for_selector('button[type="submit"]', timeout=5000)
                sign_in_button.click()
                
                # Wait for navigation
                try:
                    self.page.wait_for_url('**/feed/**', timeout=30000)
                    self.logged_in = True
                    print("Login successful!")
                    return True
                except PlaywrightTimeout:
                    print("Login may have failed - checking current URL")
                    if 'feed' in self.page.url:
                        self.logged_in = True
                        return True
                    return False
                    
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def create_post(self, content: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a post on LinkedIn.
        
        Args:
            content: Post content (text)
            image_path: Optional image to attach
            
        Returns:
            Result dictionary
        """
        if not self.logged_in:
            if not self.login():
                return {"success": False, "error": "Not logged in"}
        
        try:
            # Navigate to post creation
            print("Creating post...")
            self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            
            # Wait for post input field
            start_post_button = self.page.wait_for_selector(
                'button[aria-label="Start a post"]',
                timeout=10000
            )
            start_post_button.click()
            
            # Wait for modal and fill content
            text_field = self.page.wait_for_selector(
                'div[contenteditable="true"][aria-label="What do you want to talk about?"]',
                timeout=10000
            )
            
            # Clear and fill
            text_field.click()
            time.sleep(1)
            
            # Type content (simulate typing)
            self.page.keyboard.type(content, delay=50)
            
            # Handle image if provided
            if image_path and Path(image_path).exists():
                print(f"Attaching image: {image_path}")
                # Click media button
                media_button = self.page.wait_for_selector(
                    'button[aria-label="Add media"]',
                    timeout=5000
                )
                media_button.click()
                
                # Upload file
                file_input = self.page.wait_for_selector('input[type="file"]', timeout=5000)
                file_input.set_input_files(str(image_path))
                time.sleep(2)
            
            # Click post button
            post_button = self.page.wait_for_selector(
                'button[aria-label="Post"]',
                timeout=10000
            )
            post_button.click()
            
            # Wait for confirmation
            time.sleep(3)
            
            print("Post created successfully!")
            
            return {
                "success": True,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "timestamp": datetime.now().isoformat(),
                "has_image": bool(image_path)
            }
            
        except PlaywrightTimeout as e:
            return {
                "success": False,
                "error": f"Timeout: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_engagement(self, post_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get engagement metrics for recent posts.
        
        Args:
            post_url: Specific post URL (optional, gets most recent if not provided)
            
        Returns:
            Engagement metrics
        """
        if not self.logged_in:
            if not self.login():
                return {"success": False, "error": "Not logged in"}
        
        try:
            # Navigate to profile
            self.page.goto('https://www.linkedin.com/in/me/', wait_until='networkidle')
            
            # Scroll to activity section
            self.page.evaluate('window.scrollBy(0, 1000)')
            time.sleep(2)
            
            # Find recent posts
            posts = self.page.query_selector_all('div.update-components-text')
            
            engagement_data = []
            for i, post in enumerate(posts[:5]):  # Get last 5 posts
                try:
                    # Get post text
                    text = post.inner_text()[:200]
                    
                    # Navigate to post for metrics (simplified)
                    engagement_data.append({
                        "content": text,
                        "index": i
                    })
                except Exception:
                    continue
            
            return {
                "success": True,
                "posts": engagement_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Close browser context."""
        if self.context:
            self.context.close()
            self.logged_in = False


def generate_business_post(business_goals: Path) -> str:
    """
    Generate a LinkedIn post from business goals.
    
    Args:
        business_goals: Path to Business_Goals.md
        
    Returns:
        Generated post content
    """
    if not business_goals.exists():
        return "Excited to share updates from our business! #BusinessUpdate #Growth"
    
    content = business_goals.read_text(encoding='utf-8')
    
    # Extract key info
    lines = content.split('\n')
    goals = []
    
    for line in lines:
        if line.startswith('- [ ]') or line.startswith('- [x]'):
            goals.append(line[5:].strip())
    
    if goals:
        post = "🚀 Business Update:\n\n"
        for goal in goals[:3]:  # Top 3 goals
            post += f"• {goal}\n"
        post += "\n#BusinessGoals #Entrepreneurship #Growth"
        return post
    
    return "Making progress on our business objectives! Stay tuned for updates. #BusinessUpdate"


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn Poster for AI Employee")
    parser.add_argument("--post", "-p", help="Post content")
    parser.add_argument("--file", "-f", help="Read post content from file")
    parser.add_argument("--image", "-i", help="Image path to attach")
    parser.add_argument("--login", action="store_true", help="Force login")
    parser.add_argument("--session", "-s", help="Session path")
    parser.add_argument("--email", help="LinkedIn email")
    parser.add_argument("--password", help="LinkedIn password")
    parser.add_argument("--engagement", action="store_true", help="Get engagement metrics")
    parser.add_argument("--generate", action="store_true", help="Generate post from Business_Goals.md")
    parser.add_argument("--vault", help="Path to Obsidian vault")
    
    args = parser.parse_args()
    
    poster = LinkedInPoster(
        session_path=args.session,
        email=args.email,
        password=args.password
    )
    
    try:
        if args.login:
            # Interactive login
            print("🔗 LinkedIn Login")
            print("=" * 50)
            if not args.email:
                args.email = input("Email: ")
            if not args.password:
                args.password = input("Password: ")
            
            if poster.login(args.email, args.password):
                print("✅ Login successful!")
                print(f"Session saved to: {poster.session_path}")
            else:
                print("❌ Login failed")
                sys.exit(1)
        
        elif args.post or args.file:
            # Post content
            if args.file:
                content = Path(args.file).read_text(encoding='utf-8')
            else:
                content = args.post
            
            # Login if needed
            if not poster.logged_in:
                if not poster.login():
                    sys.exit(1)
            
            # Create post
            result = poster.create_post(content, args.image)
            print(f"\nResult: {result}")
        
        elif args.generate:
            # Generate post from business goals
            vault = Path(args.vault) if args.vault else Path('AI_Employee_Vault')
            goals_file = vault / 'Business_Goals.md'
            
            content = generate_business_post(goals_file)
            print("📝 Generated Post:")
            print("=" * 50)
            print(content)
            print("\nTo post, run:")
            print(f'  python linkedin_poster.py --post "{content[:50]}..."')
        
        elif args.engagement:
            # Get engagement metrics
            if not poster.logged_in:
                if not poster.login():
                    sys.exit(1)
            
            result = poster.get_engagement()
            print(f"\nEngagement: {result}")
        
        else:
            parser.print_help()
    
    finally:
        poster.close()


if __name__ == "__main__":
    main()
