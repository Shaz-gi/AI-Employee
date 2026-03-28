#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI LinkedIn Post Generator

Generates LinkedIn posts from Business_Goals.md using AI.
Creates approval requests in the database.

Usage:
    python src/ai_linkedin_generator.py
    python src/ai_linkedin_generator.py --vault-path /path/to/vault
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except ImportError:
    print("Error: groq not installed")
    print("Run: pip install groq")
    sys.exit(1)


class AILinkedinGenerator:
    """
    AI LinkedIn Post Generator.
    
    Generates engaging LinkedIn posts from business goals and updates.
    """

    # Post templates for variety
    POST_TYPES = [
        'achievement',      # Celebrating milestones
        'insight',          # Sharing learnings
        'question',         # Engaging questions
        'tip',              # Helpful tips
        'update',           # Business updates
        'motivation',       # Inspirational content
    ]

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize AI LinkedIn Generator.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.src_path = Path(__file__).parent
        self.vault_path = Path(vault_path) if vault_path else self.src_path.parent / 'AI_Employee_Vault'
        
        # Groq AI configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_model = os.getenv('GROQ_MODEL', 'llama-3.2-3b-instruct')  # Fixed: removed meta-llama/ prefix
        
        if not self.groq_api_key:
            print("⚠️  GROQ_API_KEY not set - AI generation disabled")
            print("   Get FREE key from: https://console.groq.com/keys")
            self.client = None
            self.ai_client = None  # Add alias for compatibility
        else:
            self.client = Groq(api_key=self.groq_api_key)
            self.ai_client = self.client  # Add alias for compatibility
            print(f"✅ Groq AI initialized ({self.groq_model})")
            print(f"   🚀 Lightning fast inference")
        
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if self.supabase_url and self.supabase_key:
            try:
                import requests
                self.api_url = self.supabase_url.rstrip('/').replace('/ref/v1', '')
                self.rest_url = f"{self.api_url}/rest/v1"
                self.headers = {
                    'apikey': self.supabase_service_key or self.supabase_key,
                    'Authorization': f'Bearer {self.supabase_service_key or self.supabase_key}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                }
                print(f"✅ Supabase connected")
            except:
                print("⚠️  Supabase not configured - will save to vault only")
        else:
            print("⚠️  Supabase credentials not set - will save to vault only")
    
    def read_business_goals(self) -> str:
        """Read Business_Goals.md content."""
        goals_file = self.vault_path / 'Business_Goals.md'
        
        if not goals_file.exists():
            print(f"❌ Business_Goals.md not found at {goals_file}")
            return ""
        
        content = goals_file.read_text(encoding='utf-8')
        print(f"📄 Read Business_Goals.md ({len(content)} chars)")
        return content
    
    def generate_post_with_ai(self, post_type: str = 'insight') -> Optional[str]:
        """
        Generate a LinkedIn post using AI.
        
        Args:
            post_type: Type of post to generate
            
        Returns:
            Generated post content or None
        """
        if not self.client:
            return None
        
        business_goals = self.read_business_goals()
        
        if not business_goals:
            print("❌ No business goals content to generate from")
            return None
        
        # Different prompts for different post types
        prompts = {
            'achievement': f"""Based on these business goals, create an inspiring LinkedIn post celebrating a recent milestone or progress. 
            Make it personal, engaging, and include relevant hashtags.
            
            Business Goals:
            {business_goals}
            
            Write a short, punchy LinkedIn post (150-300 characters) that:
            - Celebrates progress
            - Shows authenticity
            - Encourages engagement
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'insight': f"""Based on these business goals, create a LinkedIn post sharing a business insight or lesson learned.
            Make it valuable for other entrepreneurs and professionals.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (200-400 characters) that:
            - Shares a specific insight or lesson
            - Provides actionable value
            - Ends with a thought-provoking question
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'question': f"""Based on these business goals, create an engaging LinkedIn post that asks the audience a thought-provoking question.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (150-250 characters) that:
            - Sets up context briefly
            - Asks an engaging question
            - Encourages comments and discussion
            - Includes 2-3 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'tip': f"""Based on these business goals, create a LinkedIn post sharing a helpful tip or best practice.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (200-350 characters) that:
            - Shares one specific, actionable tip
            - Explains why it matters
            - Uses clear formatting (bullets or numbers if helpful)
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'update': f"""Based on these business goals, create a LinkedIn post sharing a business update.
            
            Business Goals:
            {business_goals}
            
            Write a LinkedIn post (150-300 characters) that:
            - Shares what's new or happening
            - Shows progress or momentum
            - Invites engagement
            - Includes 3-5 relevant hashtags
            
            Format just the post text, no explanations.""",
            
            'motivation': f"""Based on these business goals, create an inspiring LinkedIn post with motivational content.
            
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
            print(f"🤖 Generating {post_type} post with Groq...")
            
            response = self.client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": "You are a professional LinkedIn content creator. Write engaging, authentic posts that drive meaningful engagement."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Clean up the response
            if '```' in post_content:
                post_content = post_content.split('```')[1].split('```')[0].strip()
            
            print(f"✅ Generated post ({len(post_content)} chars)")
            return post_content
            
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return None
    
    def save_to_database(self, user_id: str, vault_id: str, content: str, post_type: str) -> Optional[Dict]:
        """
        Save generated post to database for approval.
        
        Args:
            user_id: User ID
            vault_id: Vault ID
            content: Post content
            post_type: Type of post
            
        Returns:
            Inserted record or None
        """
        if not hasattr(self, 'headers'):
            print("❌ Supabase not configured")
            return None
        
        try:
            import requests
            
            post_data = {
                'user_id': user_id,
                'vault_id': vault_id,
                'content': content,
                'post_type': post_type,
                'status': 'pending_approval',
                'generated_at': datetime.now().isoformat(),
                'requires_approval': True
            }
            
            response = requests.post(
                f"{self.rest_url}/linkedin_posts",
                headers=self.headers,
                json=post_data
            )
            
            if response.status_code >= 400:
                print(f"❌ Database error {response.status_code}: {response.text[:200]}")
                return None
            
            result = response.json()
            print(f"✅ Saved to database for approval")
            return result
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    def get_user_vault(self, user_id: str) -> Optional[Dict]:
        """Get user's vault."""
        if not hasattr(self, 'headers'):
            return None
        
        try:
            import requests
            
            response = requests.get(
                f"{self.rest_url}/vaults",
                headers=self.headers,
                params={'user_id': f'eq.{user_id}', 'limit': 1}
            )
            
            if response.status_code >= 400:
                return None
            
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting vault: {e}")
            return None
    
    def generate_and_save(self, user_id: str, post_type: Optional[str] = None) -> Optional[Dict]:
        """
        Generate a post and save to database for approval.
        
        Args:
            user_id: User ID
            post_type: Optional specific post type
            
        Returns:
            Generated post record or None
        """
        # Get user's vault
        vault = self.get_user_vault(user_id)
        if not vault:
            print(f"❌ No vault found for user {user_id}")
            return None
        
        vault_id = vault['id']
        
        # Choose random post type if not specified
        if not post_type:
            import random
            post_type = random.choice(self.POST_TYPES)
        
        # Generate post
        content = self.generate_post_with_ai(post_type)
        if not content:
            return None
        
        # Save to database
        result = self.save_to_database(user_id, vault_id, content, post_type)
        
        return result
    
    def generate_multiple_posts(self, user_id: str, count: int = 5) -> List[Dict]:
        """
        Generate multiple posts for scheduling.
        
        Args:
            user_id: User ID
            count: Number of posts to generate
            
        Returns:
            List of generated post records
        """
        results = []
        
        print(f"\n📝 Generating {count} LinkedIn posts...")
        
        for i in range(count):
            post_type = self.POST_TYPES[i % len(self.POST_TYPES)]
            print(f"\n[{i+1}/{count}] Generating {post_type} post...")
            
            result = self.generate_and_save(user_id, post_type)
            if result:
                results.append(result)
        
        print(f"\n✅ Generated {len(results)}/{count} posts")
        return results
    
    def save_to_vault_only(self, content: str, post_type: str) -> Path:
        """
        Save post to vault (fallback if no database).
        
        Args:
            content: Post content
            post_type: Type of post
            
        Returns:
            Path to saved file
        """
        posts_folder = self.vault_path / 'LinkedIn_Posts'
        posts_folder.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_file = posts_folder / f"POST_{post_type}_{timestamp}.md"
        
        post_content = f"""---
generated: {datetime.now().isoformat()}
type: {post_type}
status: pending_approval
---

# LinkedIn Post Draft

{content}

---
*Generated by AI Employee - Requires approval before posting*
"""
        post_file.write_text(post_content, encoding='utf-8')
        print(f"✅ Saved to vault: {post_file}")
        
        return post_file


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI LinkedIn Post Generator")
    parser.add_argument("--vault-path", help="Path to Obsidian vault")
    parser.add_argument("--user-id", help="User ID (for database save)")
    parser.add_argument("--count", type=int, default=1, help="Number of posts to generate")
    parser.add_argument("--type", choices=['achievement', 'insight', 'question', 'tip', 'update', 'motivation'],
                       help="Specific post type")
    parser.add_argument("--output", choices=['database', 'vault', 'both'], default='both',
                       help="Where to save generated posts")
    
    args = parser.parse_args()
    
    print("🤖 AI LinkedIn Post Generator")
    print("=" * 50)
    
    generator = AILinkedinGenerator(vault_path=args.vault_path)
    
    if args.count > 1:
        # Generate multiple posts
        if args.user_id:
            generator.generate_multiple_posts(args.user_id, args.count)
        else:
            print("❌ User ID required for multiple post generation")
    else:
        # Generate single post
        post_type = args.type
        if not post_type:
            import random
            post_type = random.choice(generator.POST_TYPES)
        
        print(f"\n📝 Generating {post_type} post...")
        
        content = generator.generate_post_with_ai(post_type)
        
        if content:
            print("\n" + "=" * 50)
            print("GENERATED POST:")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            # Save to vault
            generator.save_to_vault_only(content, post_type)
            
            # Save to database if user_id provided
            if args.user_id:
                generator.generate_and_save(args.user_id, post_type)


if __name__ == "__main__":
    main()
