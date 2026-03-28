#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily LinkedIn Scheduler

Automatically generates and schedules LinkedIn posts daily.
Runs as a background service and:
1. Generates AI posts from Business_Goals.md
2. Creates approval requests in database
3. Posts approved content automatically

Usage:
    python src/linkedin_scheduler.py
    python src/linkedin_scheduler.py --generate-only  # Just generate, don't post
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import requests
    from groq import Groq
except ImportError as e:
    print(f"Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "groq"])
    import requests
    from groq import Groq


class LinkedInScheduler:
    """
    Daily LinkedIn Scheduler.
    
    Automatically generates and posts LinkedIn content.
    """

    # Optimal posting times (24h format)
    POST_TIMES = ['09:00', '12:00', '17:00']  # Morning, Lunch, Evening
    
    # Post types for variety
    POST_TYPES = [
        'insight',      # Business insights
        'achievement',  # Celebrating wins
        'question',     # Engaging questions
        'tip',          # Helpful tips
        'motivation',   # Inspirational content
    ]

    def __init__(self):
        """Initialize LinkedIn Scheduler."""
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            print("⚠️  Supabase credentials not set")
            self.api_enabled = False
        else:
            self.api_url = self.supabase_url.rstrip('/').replace('/ref/v1', '')
            self.rest_url = f"{self.api_url}/rest/v1"
            self.admin_key = self.supabase_service_key or self.supabase_key
            self.headers = {
                'apikey': self.admin_key,
                'Authorization': f'Bearer {self.admin_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation',
                'X-Improve-Role': 'service_role'
            }
            self.api_enabled = True
            print(f"✅ Supabase connected: {self.supabase_url}")
        
        # Groq AI configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_model = os.getenv('GROQ_MODEL', 'llama-3.2-3b-instruct')
        
        if not self.groq_api_key:
            print("⚠️  GROQ_API_KEY not set - AI generation disabled")
            print("   Get FREE key from: https://console.groq.com/keys")
            self.ai_client = None
        else:
            self.ai_client = Groq(api_key=self.groq_api_key)
            print(f"✅ Groq AI enabled: {self.groq_model}")
            print(f"   🚀 Lightning fast inference")
        
        # LinkedIn credentials
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.linkedin_email or not self.linkedin_password:
            print("⚠️  LinkedIn credentials not set - posting disabled")
            print("   Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
            self.linkedin_enabled = False
        else:
            self.linkedin_enabled = True
            print(f"✅ LinkedIn credentials configured for: {self.linkedin_email}")
        
        # Vault path
        self.vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
        
        print("✅ LinkedIn Scheduler initialized")

    def supabase_query(self, table: str, method: str = 'GET', data: Optional[Dict] = None,
                       params: Optional[Dict] = None) -> Any:
        """Make a request to Supabase REST API."""
        if not self.api_enabled:
            return None
        
        url = f"{self.rest_url}/{table}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PATCH':
                # Build filter into URL
                if params:
                    filter_parts = []
                    for k, v in params.items():
                        filter_parts.append(f"{k}={v}")
                    url = f"{url}?{'&'.join(filter_parts)}"
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                print(f"   ❌ API Error {response.status_code}: {response.text[:200]}")
                return None
            
            if method in ['GET', 'POST', 'PATCH']:
                return response.json()
            return {'success': True}
            
        except Exception as e:
            print(f"   ❌ Supabase error: {e}")
            return None

    def get_all_users(self) -> List[Dict]:
        """Get all users with vaults."""
        if not self.api_enabled:
            return []
        
        # Query vaults with user_id from profiles
        result = self.supabase_query(
            'vaults', 
            params={'select': 'id,user_id'}
        )
        if not result:
            return []
        
        # Group by user_id
        users = {}
        for vault in result:
            user_id = vault.get('user_id')
            if user_id and user_id not in users:
                users[user_id] = {'id': user_id, 'vault_id': vault.get('id')}
        
        return list(users.values())

    def read_business_goals(self, user_id: str) -> str:
        """Read Business_Goals.md for user."""
        # For now, use shared vault
        goals_file = self.vault_path / 'Business_Goals.md'
        
        if not goals_file.exists():
            return ""
        
        content = goals_file.read_text(encoding='utf-8')
        return content

    def generate_post_with_ai(self, post_type: str, user_id: str) -> Optional[str]:
        """
        Generate a LinkedIn post using AI.
        
        Args:
            post_type: Type of post
            user_id: User ID
            
        Returns:
            Generated post or None
        """
        if not self.ai_client:
            return None
        
        business_goals = self.read_business_goals(user_id)
        
        if not business_goals:
            print(f"   ⚠️  No business goals for user {user_id}")
            return None
        
        prompts = {
            'insight': f"""Based on these business goals, create a LinkedIn post sharing a business insight or lesson learned.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (200-400 characters) that:
            - Shares a specific insight or lesson
            - Provides actionable value
            - Ends with a thought-provoking question
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'achievement': f"""Based on these business goals, create an inspiring LinkedIn post celebrating a recent milestone.
            
            Business Goals:
            {business_goals}
            
            Write a short, punchy LinkedIn post (150-300 characters) that:
            - Celebrates progress
            - Shows authenticity
            - Encourages engagement
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'question': f"""Based on these business goals, create an engaging LinkedIn post that asks the audience a question.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (150-250 characters) that:
            - Sets up context briefly
            - Asks an engaging question
            - Encourages comments and discussion
            - Includes 2-3 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'tip': f"""Based on these business goals, create a LinkedIn post sharing a helpful tip.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (200-350 characters) that:
            - Shares one specific, actionable tip
            - Explains why it matters
            - Uses clear formatting
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'motivation': f"""Based on these business goals, create an inspiring LinkedIn post.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (150-280 characters) that:
            - Shares an inspiring message
            - Relates to entrepreneurship or growth
            - Encourages action
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
        }
        
        prompt = prompts.get(post_type, prompts['insight'])
        
        try:
            print(f"   🤖 Generating {post_type} post...")
            
            response = self.ai_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": "You are a professional LinkedIn content creator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Clean up
            if '```' in post_content:
                post_content = post_content.split('```')[1].split('```')[0].strip()
            
            print(f"   ✅ Generated ({len(post_content)} chars)")
            return post_content
            
        except Exception as e:
            print(f"   ❌ AI error: {e}")
            return None

    def create_pending_post(self, user_id: str, vault_id: str, content: str, 
                           post_type: str, scheduled_for: datetime) -> Optional[Dict]:
        """Create a pending post in database."""
        if not self.api_enabled:
            return None
        
        post_data = {
            'user_id': user_id,
            'vault_id': vault_id,
            'content': content,
            'post_type': post_type,
            'status': 'pending_approval',
            'scheduled_for': scheduled_for.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'requires_approval': True,
            'ai_generated': True
        }
        
        result = self.supabase_query('linkedin_posts', method='POST', data=post_data)
        
        if result and len(result) > 0:
            print(f"   ✅ Created pending post for approval")
            return result[0]
        
        return None

    def generate_daily_posts(self) -> int:
        """
        Generate daily posts for all users.
        
        Returns:
            Number of posts generated
        """
        print("\n📝 Generating daily LinkedIn posts...")
        
        users = self.get_all_users()
        
        if not users:
            print("   ⚠️  No users found")
            return 0
        
        generated_count = 0
        
        for user in users:
            user_id = user['id']
            vault_id = user['vault_id']
            
            print(f"\n👤 User: {user_id[:8]}...")
            
            # Generate one post per type
            for post_type in self.POST_TYPES:
                content = self.generate_post_with_ai(post_type, user_id)
                
                if content:
                    # Schedule for different times
                    hour = len(generated_count % len(self.POST_TIMES))
                    scheduled_time = datetime.now().replace(
                        hour=int(self.POST_TIMES[hour].split(':')[0]),
                        minute=int(self.POST_TIMES[hour].split(':')[1]),
                        second=0,
                        microsecond=0
                    )
                    
                    # If time has passed, schedule for tomorrow
                    if scheduled_time < datetime.now():
                        scheduled_time += timedelta(days=1)
                    
                    self.create_pending_post(user_id, vault_id, content, post_type, scheduled_time)
                    generated_count += 1
        
        print(f"\n✅ Generated {generated_count} posts")
        return generated_count

    def post_to_linkedin(self, content: str) -> bool:
        """
        Post content to LinkedIn using browser automation.
        
        Args:
            content: Post content
            
        Returns:
            True if successful
        """
        if not self.linkedin_enabled:
            print("   ⚠️  LinkedIn not enabled")
            return False
        
        try:
            from linkedin_auto_post import LinkedInAutoPoster
            
            poster = LinkedInAutoPoster()
            
            # Login
            if not poster.login(self.linkedin_email, self.linkedin_password):
                print("   ❌ Login failed")
                return False
            
            # Post
            result = poster.post(content)
            poster.close()
            
            if result.get('success'):
                print("   ✅ Posted to LinkedIn")
                return True
            else:
                print(f"   ❌ Post failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def process_generation_requests(self):
        """Handle AI generation requests from frontend."""
        print("\n🤖 Checking for AI generation requests...")
        
        if not self.api_enabled:
            return
        
        # Get generation requests (draft posts with AI generation content)
        result = self.supabase_query(
            'linkedin_posts',
            params={
                'status': 'eq.draft',
                'select': 'id,user_id,vault_id,content'
            }
        )
        
        if not result or len(result) == 0:
            print("   ✓ No generation requests")
            return
        
        # Filter for posts that are being AI generated
        generation_requests = [
            r for r in result 
            if r.get('content') == 'Generating post with AI...' or not r.get('ai_generated', False)
        ]
        
        if not generation_requests:
            print("   ✓ No pending generation requests")
            return
        
        print(f"   ✓ Found {len(generation_requests)} generation request(s)")
        
        for request in generation_requests:
            request_id = request.get('id')
            user_id = request.get('user_id')
            vault_id = request.get('vault_id')
            
            print(f"\n📝 Processing generation request for user {user_id[:8]}...")
            
            # Generate AI post
            content = self.generate_post_with_ai('insight', user_id)
            
            if content:
                # Update the post with generated content
                update_result = self.supabase_query(
                    'linkedin_posts',
                    method='PATCH',
                    data={
                        'content': content,
                        'status': 'pending_approval',
                        'post_type': 'insight',
                        'ai_generated': True,
                        'generated_at': datetime.now().isoformat()
                    },
                    params={'id': f'eq.{request_id}'}
                )
                
                if update_result:
                    print(f"   ✅ Post generated successfully!")
                else:
                    print(f"   ❌ Failed to update post")
            else:
                # Mark as failed
                self.supabase_query(
                    'linkedin_posts',
                    method='PATCH',
                    data={
                        'status': 'failed',
                        'error_message': 'AI generation failed'
                    },
                    params={'id': f'eq.{request_id}'}
                )
                print(f"   ❌ AI generation failed")

    def process_approved_posts(self) -> int:
        """
        Process approved posts and post to LinkedIn.
        
        Returns:
            Number of posts processed
        """
        print("\n📤 Processing approved posts...")
        
        if not self.api_enabled:
            return 0
        
        # Get approved posts that haven't been posted
        result = self.supabase_query(
            'linkedin_posts',
            params={
                'status': 'eq.approved',
                'select': 'id,user_id,content,scheduled_for'
            }
        )
        
        if not result:
            print("   ✓ No approved posts to process")
            return 0
        
        posted_count = 0
        
        for post in result:
            post_id = post.get('id')
            content = post.get('content')
            scheduled_for = post.get('scheduled_for')
            
            # Check if it's time to post
            if scheduled_for:
                scheduled_time = datetime.fromisoformat(scheduled_for)
                if scheduled_time > datetime.now():
                    print(f"   ⏳ Skipping - scheduled for {scheduled_time}")
                    continue
            
            # Post to LinkedIn
            print(f"\n📧 Posting: {content[:50]}...")
            
            success = self.post_to_linkedin(content)
            
            if success:
                # Update status
                self.supabase_query(
                    'linkedin_posts',
                    method='PATCH',
                    data={
                        'status': 'posted',
                        'posted_at': datetime.now().isoformat()
                    },
                    params={'id': f'eq.{post_id}'}
                )
                posted_count += 1
            else:
                # Mark as failed
                self.supabase_query(
                    'linkedin_posts',
                    method='PATCH',
                    data={
                        'status': 'failed',
                        'error_message': 'Posting failed'
                    },
                    params={'id': f'eq.{post_id}'}
                )
        
        print(f"\n✅ Posted {posted_count}/{len(result)} posts")
        return posted_count

    def run(self):
        """Main scheduler loop."""
        print("\n" + "=" * 60)
        print("🚀 LinkedIn Daily Scheduler")
        print("=" * 60)
        print("This will:")
        print("  1. Generate daily posts from Business_Goals.md")
        print("  2. Create approval requests")
        print("  3. Post approved content automatically")
        print("  4. Handle AI generation requests from frontend")
        print("=" * 60)
        
        try:
            while True:
                now = datetime.now()
                
                # Handle AI generation requests from frontend
                self.process_generation_requests()
                
                # Generate posts at 8 AM daily
                if now.hour == 8 and now.minute < 5:
                    self.generate_daily_posts()
                
                # Process approved posts every 5 minutes
                self.process_approved_posts()
                
                # Wait 5 minutes
                print(f"\n⏰ [{now.strftime('%H:%M:%S')}] Waiting 5 minutes...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            print("\n\n👋 Scheduler stopped")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(60)
            self.run()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn Daily Scheduler")
    parser.add_argument("--generate-only", action="store_true", 
                       help="Just generate posts, don't run scheduler")
    parser.add_argument("--post-now", action="store_true",
                       help="Process approved posts immediately")
    
    args = parser.parse_args()
    
    scheduler = LinkedInScheduler()
    
    if args.generate_only:
        scheduler.generate_daily_posts()
    elif args.post_now:
        scheduler.process_approved_posts()
    else:
        scheduler.run()


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    main()
