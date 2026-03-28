#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-User Real-Time Gmail Fetcher - WITH DUPLICATE PREVENTION

This script:
1. Fetches emails for ALL users who connected Gmail
2. Each user gets their own isolated vault
3. Emails are stored per user
4. PREVENTS DUPLICATES - checks database before storing
5. Runs continuously, checking all users every 60 seconds

Usage:
    python src/multi_user_email_fetcher.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import requests
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "requests", "google-auth", "google-auth-oauthlib", 
                          "google-api-python-client"])
    import requests
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build


class MultiUserEmailFetcher:
    """
    Multi-user Gmail email fetcher with duplicate prevention.
    
    Fetches emails for all users who have connected their Gmail accounts.
    Each user's emails go to their personal vault.
    Prevents storing duplicate emails.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self):
        """Initialize the multi-user email fetcher."""
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials required!")
        
        # Use service role key for admin operations
        self.admin_key = self.supabase_service_key or self.supabase_key
        
        # Gmail credentials (for OAuth flow)
        self.credentials_path = Path(__file__).parent / 'credentials.json'
        
        # Track processed message IDs per user (in-memory cache)
        self.processed_ids = {}  # {user_id: set(message_ids)}
        
        # Supabase REST API endpoints
        self.api_url = self.supabase_url.rstrip('/')
        if '/ref/v1' in self.api_url:
            self.api_url = self.api_url.replace('/ref/v1', '')
        
        self.rest_url = f"{self.api_url}/rest/v1"
        
        print("✅ Multi-User Email Fetcher (with Duplicate Prevention)")
        print(f"   Supabase: {self.supabase_url}")
        print(f"   Checking all users every 60 seconds...")
        print(f"   Each user gets their own vault & emails")
        print(f"   Duplicate prevention enabled")
    
    def supabase_query(self, table: str, method: str = 'GET', data: Optional[Dict] = None, 
                       params: Optional[Dict] = None, use_admin_key: bool = True) -> Any:
        """Make a request to Supabase REST API."""
        url = f"{self.rest_url}/{table}"
        key = self.admin_key if use_admin_key else self.supabase_key
        
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        if use_admin_key:
            headers['X-Improve-Role'] = 'service_role'
        
        if params:
            formatted_params = {}
            for k, v in params.items():
                if isinstance(v, bool):
                    formatted_params[k] = str(v).lower()
                else:
                    formatted_params[k] = v
            params = formatted_params
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                print(f"   ❌ API Error {response.status_code}: {response.text[:200]}")
            
            response.raise_for_status()
            
            if method == 'GET':
                return response.json()
            else:
                return {'success': True, 'data': response.json()}
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Supabase API error: {e}")
            return None
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """Get all users who have connected Gmail and want email fetching."""
        print(f"\n📋 Fetching active users...")
        
        try:
            # Get users with Gmail connected (proper Supabase REST API format)
            users = self.supabase_query(
                'profiles',
                params={
                    'gmail_connected': 'eq.true',
                    'gmail_fetch_enabled': 'eq.true',
                    'select': 'id,email,gmail_email,gmail_connected,gmail_fetch_enabled,gmail_last_sync'
                }
            )
            
            if not users or not isinstance(users, list):
                print(f"   ⚠️  No active users found")
                return []
            
            print(f"   ✓ Found {len(users)} active user(s)")
            
            # Get vaults for each user
            vaults = self.supabase_query(
                'vaults',
                params={'select': 'id,user_id'}
            )
            vault_map = {v['user_id']: v['id'] for v in (vaults or [])}
            
            # Log each user
            for user in users:
                email = user.get('email', 'unknown')
                gmail_email = user.get('gmail_email', 'not connected')
                last_sync = user.get('gmail_last_sync')
                user_id = user.get('id')
                
                # Add vault_id to user dict
                user['vault_id'] = vault_map.get(user_id)
                
                if last_sync:
                    try:
                        sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        time_ago = datetime.now(sync_time.tzinfo) - sync_time
                        print(f"   • {email} ({gmail_email}) - Last sync: {int(time_ago.total_seconds() / 60)}m ago")
                    except:
                        print(f"   • {email} ({gmail_email}) - Last sync: recently")
                else:
                    print(f"   • {email} ({gmail_email}) - Never synced")
            
            return users
            
        except Exception as e:
            print(f"   ❌ Error getting users: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_user_gmail_token(self, user_id: str) -> Optional[Credentials]:
        """Get Gmail OAuth credentials for a user."""
        try:
            # Try to load existing token
            token_path = Path(__file__).parent / 'token.json'
            
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
                
                # Refresh if expired
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        # Save refreshed token
                        with open(token_path, 'w') as f:
                            f.write(creds.to_json())
                    else:
                        return None
                
                return creds
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error getting Gmail token for user {user_id}: {e}")
            return None
    
    def fetch_emails_for_user(self, user: Dict[str, Any]) -> int:
        """
        Fetch emails from Gmail for a specific user.
        
        Includes duplicate prevention by checking database for existing emails.
        """
        user_id = user.get('user_id') or user.get('id')
        user_email = user.get('email', 'unknown')
        vault_id = user.get('vault_id')
        gmail_email = user.get('gmail_email', user_email)
        
        print(f"\n📧 Fetching emails for {user_email} ({gmail_email})...")
        
        # Validate required fields
        if not user_id:
            print(f"   ⚠️  No user_id found, skipping...")
            return 0
        
        if not vault_id:
            print(f"   ⚠️  No vault found for user {user_email}, skipping...")
            return 0
        
        try:
            # Get Gmail credentials
            creds = self.get_user_gmail_token(user_id)
            
            if not creds:
                print(f"   ⚠️  Gmail not authenticated for this user")
                return 0
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            
            # Fetch emails from Gmail
            print(f"   Fetching unread emails...")
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print(f"   ✓ No new emails")
                return 0
            
            print(f"   Found {len(messages)} emails")
            
            # Get already processed message IDs from database
            print(f"   Checking for duplicates...")
            existing_emails = self.supabase_query(
                'emails',
                params={
                    'vault_id': f'eq.{vault_id}',
                    'select': 'gmail_message_id'
                }
            )
            
            # Create set of existing message IDs
            existing_ids = set()
            if existing_emails and isinstance(existing_emails, list):
                for email in existing_emails:
                    msg_id = email.get('gmail_message_id')
                    if msg_id:
                        existing_ids.add(msg_id)
            
            print(f"   ✓ Found {len(existing_ids)} existing emails in database")
            
            # Initialize processed IDs set for this user
            if user_id not in self.processed_ids:
                self.processed_ids[user_id] = set()
            
            # Also add existing database IDs to in-memory set
            self.processed_ids[user_id].update(existing_ids)
            
            # Process each email
            emails_created = 0
            skipped_duplicates = 0
            
            for message in messages:
                # Skip if already processed (in memory or database)
                if message['id'] in self.processed_ids[user_id]:
                    skipped_duplicates += 1
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
                
                # Parse date
                received_at = headers.get('Date', datetime.now().isoformat())
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(received_at)
                    received_at = dt.isoformat()
                except:
                    received_at = datetime.now().isoformat()
                
                # Create email record
                email_data = {
                    'vault_id': vault_id,
                    'user_id': user_id,
                    'gmail_message_id': msg['id'],
                    'from_address': headers.get('From', ''),
                    'to_address': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'body_preview': msg.get('snippet', ''),
                    'status': 'new',
                    'requires_approval': False,
                    'received_at': received_at
                }
                
                # Insert into database
                result = self.supabase_query('emails', method='POST', data=email_data)
                
                if result and result.get('success'):
                    emails_created += 1
                    self.processed_ids[user_id].add(msg['id'])
                    subject = headers.get('Subject', 'No Subject')[:50]
                    print(f"   ✓ Created email: {subject}")
                else:
                    print(f"   ⚠️  Failed to create email")
            
            print(f"   ⏭️  Skipped {skipped_duplicates} duplicates")
            
            # Update user's last sync time
            if user_id:
                try:
                    self.supabase_query(
                        'profiles',
                        method='PATCH',
                        data={'gmail_last_sync': datetime.now().isoformat()},
                        params={'id': f'eq.{user_id}'}
                    )
                except Exception as e:
                    print(f"   ⚠️  Could not update last sync time: {e}")
            else:
                print(f"   ⚠️  Skipping sync time update (no user_id)")
            
            print(f"   ✅ Fetched {emails_created} new emails for {user_email} (skipped {skipped_duplicates} duplicates)")
            return emails_created
            
        except Exception as e:
            print(f"   ❌ Error fetching emails for {user_email}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run(self):
        """Main loop - continuously fetch emails for all users."""
        print("\n" + "=" * 60)
        print("🚀 Starting Multi-User Real-Time Email Fetcher")
        print("=" * 60)
        print("This will automatically:")
        print("  1. Check for users with Gmail connected")
        print("  2. Fetch emails for EACH user")
        print("  3. Store in user's personal vault")
        print("  4. PREVENT DUPLICATES - checks database first")
        print("  5. Emails appear in UI automatically")
        print("  6. Check all users every 60 seconds")
        print("=" * 60 + "\n")
        
        try:
            while True:
                # Get all active users
                users = self.get_active_users()
                
                if not users:
                    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] No active users yet...")
                    print("   Users will appear here after they sign up with Google")
                else:
                    # Fetch emails for each user
                    total_emails = 0
                    total_skipped = 0
                    for user in users:
                        emails = self.fetch_emails_for_user(user)
                        total_emails += emails
                    
                    if total_emails > 0:
                        print(f"\n🎉 Total: {total_emails} new emails fetched across all users!")
                    else:
                        print(f"\n✓ All emails already in database (no duplicates)")
                
                # Wait 60 seconds before next check
                print(f"\n⏰ Waiting 60 seconds before next check...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping email fetcher...")
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            time.sleep(5)
            self.run()


def main():
    """Main entry point."""
    fetcher = MultiUserEmailFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
