#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-Time Gmail Fetcher - Automatic Email Sync

This script runs in the background and:
1. Detects when users log in with Google
2. Automatically fetches their Gmail emails
3. Stores them in the database in real-time
4. Makes them immediately visible in the UI

Usage:
    python src/realtime_email_fetcher.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from supabase import create_client, Client
except ImportError as e:
    print(f"Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth", "google-auth-oauthlib", "google-api-python-client", "supabase"])
    from supabase import create_client, Client


class RealTimeEmailFetcher:
    """
    Real-time Gmail email fetcher.
    
    Automatically fetches emails for logged-in users and stores them in the database.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self):
        """Initialize the email fetcher."""
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials required! Set SUPABASE_URL and SUPABASE_ANON_KEY")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Gmail credentials
        self.credentials_path = Path(__file__).parent / 'credentials.json'
        
        # Track processed message IDs to avoid duplicates
        self.processed_ids = set()
        
        # Users to fetch emails for
        self.active_users = {}
        
        print("✅ Real-Time Email Fetcher initialized")
        print(f"   Supabase: {supabase_url}")
        print(f"   Checking every 30 seconds...")
    
    def get_gmail_service(self, user_id: str) -> Any:
        """
        Get Gmail API service for a user.
        
        In production, this would use stored OAuth tokens.
        For now, we'll use a service account or manual auth.
        """
        try:
            creds = None
            
            # Try to load existing token
            token_path = Path(__file__).parent / f'token_gmail_{user_id}.json'
            
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # If no valid credentials, try to refresh or get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Need to authenticate
                    print(f"⚠️  Need to authenticate Gmail for user {user_id}")
                    return None
                
                # Save refreshed token
                if creds:
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            return service
            
        except Exception as e:
            print(f"❌ Error getting Gmail service: {e}")
            return None
    
    def fetch_emails_for_user(self, user_email: str, user_id: str) -> int:
        """
        Fetch emails from Gmail for a specific user.
        
        Args:
            user_email: User's Gmail address
            user_id: User's Supabase ID
            
        Returns:
            Number of emails fetched
        """
        print(f"\n📧 Fetching emails for {user_email}...")
        
        try:
            # Get Gmail service
            service = self.get_gmail_service(user_id)
            
            if not service:
                print(f"⚠️  Skipping {user_email} - Gmail not authenticated")
                return 0
            
            # Get user's vault
            vaults = self.supabase.table('vaults').select('id').eq('user_id', user_id).limit(1).execute()
            
            if not vaults.data or len(vaults.data) == 0:
                print(f"⚠️  No vault found for {user_email}, creating one...")
                vault_result = self.supabase.table('vaults').insert({
                    'user_id': user_id,
                    'name': 'My Vault',
                    'storage_path': f'{user_id}/my_vault',
                    'is_active': True
                }).execute()
                vault_id = vault_result.data[0]['id']
            else:
                vault_id = vaults.data[0]['id']
            
            # Fetch emails from Gmail
            print(f"   Fetching from Gmail API...")
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print(f"   ✓ No new emails")
                return 0
            
            print(f"   Found {len(messages)} new emails")
            
            # Process each email
            emails_created = 0
            for message in messages:
                if message['id'] in self.processed_ids:
                    continue
                
                # Get full message details
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                
                # Extract headers
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                
                # Create email record in database
                email_data = {
                    'vault_id': vault_id,
                    'gmail_message_id': msg['id'],
                    'from_address': headers.get('From', ''),
                    'to_address': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'body_preview': msg.get('snippet', ''),
                    'status': 'new',
                    'requires_approval': False,
                    'received_at': headers.get('Date', datetime.now().isoformat())
                }
                
                # Insert into database
                result = self.supabase.table('emails').insert(email_data).execute()
                
                if result.data:
                    emails_created += 1
                    self.processed_ids.add(msg['id'])
                    print(f"   ✓ Created email: {headers.get('Subject', 'No Subject')}")
            
            # Update last sync time
            self.supabase.table('profiles').update({
                'gmail_last_sync': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
            print(f"   ✅ Fetched {emails_created} emails for {user_email}")
            return emails_created
            
        except Exception as e:
            print(f"   ❌ Error fetching emails: {e}")
            return 0
    
    def get_active_users(self) -> List[Dict[str, str]]:
        """
        Get list of users who have connected Gmail.
        
        Returns:
            List of users with their email and ID
        """
        try:
            # Get all users with Gmail connected
            result = self.supabase.table('profiles').select(
                'id, email, gmail_connected, gmail_last_sync'
            ).eq('gmail_connected', True).execute()
            
            users = result.data or []
            
            # Also get users who logged in recently (might have Gmail via Google OAuth)
            recent_users = self.supabase.table('profiles').select(
                'id, email, gmail_connected'
            ).gte('updated_at', (datetime.now() - timedelta(hours=1)).isoformat()).execute()
            
            for user in recent_users.data or []:
                if user not in users:
                    users.append(user)
            
            return users
            
        except Exception as e:
            print(f"❌ Error getting active users: {e}")
            return []
    
    def run(self):
        """
        Main loop - continuously fetch emails for active users.
        """
        print("\n" + "=" * 60)
        print("🚀 Starting Real-Time Email Fetcher")
        print("=" * 60)
        print("This will automatically:")
        print("  1. Check for active users every 30 seconds")
        print("  2. Fetch new emails from their Gmail")
        print("  3. Store in database for UI to display")
        print("=" * 60 + "\n")
        
        try:
            while True:
                # Get active users
                users = self.get_active_users()
                
                if not users:
                    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] No active users yet...")
                    print("   Users will appear here after they sign up with Google")
                else:
                    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Checking {len(users)} active user(s)...")
                    
                    # Fetch emails for each user
                    total_emails = 0
                    for user in users:
                        emails = self.fetch_emails_for_user(
                            user_email=user.get('email', 'unknown'),
                            user_id=user.get('id', '')
                        )
                        total_emails += emails
                    
                    if total_emails > 0:
                        print(f"\n🎉 Total: {total_emails} new emails fetched!")
                
                # Wait 30 seconds before next check
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping email fetcher...")
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            # Restart after 5 seconds
            time.sleep(5)
            self.run()


def main():
    """Main entry point."""
    fetcher = RealTimeEmailFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
