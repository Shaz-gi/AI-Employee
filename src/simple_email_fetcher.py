#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Real-Time Gmail Fetcher - FIXED Version

Fixed issues:
- 401 Unauthorized: Using correct API key headers
- 400 Bad Request: Proper data formatting
- Vault creation: Using service role key for admin operations
"""

import os
import sys
import time
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import requests
    from google.oauth2.credentials import Credentials
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


class SimpleEmailFetcher:
    """
    Simple Gmail email fetcher using direct HTTP requests.
    
    FIXED: Proper authentication and data formatting
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self):
        """Initialize the email fetcher."""
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials required! Set SUPABASE_URL and SUPABASE_ANON_KEY")
        
        # Use service role key for admin operations (creating vaults)
        self.admin_key = self.supabase_service_key or self.supabase_key
        
        # Gmail credentials
        self.credentials_path = Path(__file__).parent / 'credentials.json'
        
        # Track processed message IDs
        self.processed_ids = set()
        
        # Supabase REST API endpoints
        self.api_url = self.supabase_url.rstrip('/')
        if '/ref/v1' in self.api_url:
            self.api_url = self.api_url.replace('/ref/v1', '')
        
        self.rest_url = f"{self.api_url}/rest/v1"
        
        print("✅ Simple Email Fetcher initialized")
        print(f"   Supabase URL: {self.supabase_url}")
        print(f"   Using admin key: {bool(self.supabase_service_key)}")
        print(f"   Checking every 30 seconds...")
    
    def supabase_query(self, table: str, method: str = 'GET', data: Optional[Dict] = None, 
                       params: Optional[Dict] = None, use_admin_key: bool = False) -> Dict:
        """
        Make a request to Supabase REST API.
        
        Args:
            table: Table name
            method: HTTP method (GET, POST, PATCH, DELETE)
            data: Request body (for POST/PATCH)
            params: Query parameters
            use_admin_key: Use service role key instead of anon key
            
        Returns:
            Response data
        """
        url = f"{self.rest_url}/{table}"
        
        # Use appropriate key
        key = self.admin_key if use_admin_key else self.supabase_key
        
        # Headers for Supabase API
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Bypass RLS when using admin key
        if use_admin_key:
            headers['X-Improve-Role'] = 'service_role'
        
        # Add query params if provided
        if params:
            # Convert Python values to Supabase format
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
            
            # Print detailed error for debugging
            if response.status_code >= 400:
                print(f"   ❌ API Error {response.status_code}: {response.text[:200]}")
            
            response.raise_for_status()
            
            if method == 'GET':
                return response.json()
            else:
                return {'success': True, 'data': response.json()}
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Supabase API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_gmail_service(self, user_email: str) -> Any:
        """
        Get Gmail API service.
        """
        try:
            creds = None
            
            # Try to load existing token
            token_path = Path(__file__).parent / 'token.json'
            
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    print(f"\n🔐 Gmail authentication required!")
                    print(f"Opening browser for authentication...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    
                    # Save token for future use
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())
                    print(f"✅ Gmail authenticated!")
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            return service
            
        except Exception as e:
            print(f"❌ Error getting Gmail service: {e}")
            return None
    
    def get_or_create_vault(self) -> Optional[str]:
        """
        Get existing vault or create a new one.
        
        Returns:
            Vault ID or None
        """
        try:
            # Try to get existing vault
            print(f"   Looking for existing vault...")
            vaults = self.supabase_query('vaults', params={'limit': 1}, use_admin_key=True)
            
            if vaults and len(vaults) > 0:
                vault_id = vaults[0].get('id')
                print(f"   ✓ Found vault: {vault_id}")
                return vault_id
            
            # Create new vault
            print(f"   Creating new vault...")
            vault_data = {
                'user_id': '00000000-0000-0000-0000-000000000000',
                'name': 'Default Vault',
                'storage_path': 'default_vault',
                'is_active': True
            }
            
            result = self.supabase_query('vaults', method='POST', data=vault_data, use_admin_key=True)
            
            if result.get('success'):
                vault_id = result['data'][0].get('id')
                print(f"   ✓ Created vault: {vault_id}")
                return vault_id
            else:
                print(f"   ❌ Failed to create vault")
                return None
                
        except Exception as e:
            print(f"   ❌ Error with vault: {e}")
            return None
    
    def fetch_and_store_emails(self, max_results: int = 20) -> int:
        """
        Fetch emails from Gmail and store in Supabase database.
        """
        print(f"\n📧 Fetching emails from Gmail...")
        
        try:
            # Get Gmail service
            service = self.get_gmail_service('default')
            
            if not service:
                print(f"⚠️  Gmail not authenticated")
                return 0
            
            # Fetch emails from Gmail
            print(f"   Fetching up to {max_results} emails...")
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print(f"   ✓ No new emails")
                return 0
            
            print(f"   Found {len(messages)} emails")
            
            # Get or create vault
            vault_id = self.get_or_create_vault()
            
            if not vault_id:
                print(f"   ❌ No vault available, cannot store emails")
                return 0
            
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
                
                # Parse date
                received_at = headers.get('Date', datetime.now().isoformat())
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(received_at)
                    received_at = dt.isoformat()
                except:
                    received_at = datetime.now().isoformat()
                
                # Create email record with proper formatting
                email_data = {
                    'vault_id': vault_id,
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
                
                if result.get('success'):
                    emails_created += 1
                    self.processed_ids.add(msg['id'])
                    subject = headers.get('Subject', 'No Subject')[:50]
                    print(f"   ✓ Created email: {subject}")
                else:
                    print(f"   ⚠️  Failed to create email: {result.get('error', 'Unknown error')}")
            
            print(f"   ✅ Fetched {emails_created} emails")
            return emails_created
            
        except Exception as e:
            print(f"   ❌ Error fetching emails: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run(self):
        """
        Main loop - continuously fetch emails.
        """
        print("\n" + "=" * 60)
        print("🚀 Starting Simple Real-Time Email Fetcher")
        print("=" * 60)
        print("This will automatically:")
        print("  1. Connect to Gmail API")
        print("  2. Fetch new emails every 30 seconds")
        print("  3. Store in Supabase database")
        print("  4. Emails will appear in UI automatically")
        print("=" * 60 + "\n")
        
        try:
            while True:
                # Fetch emails
                emails_fetched = self.fetch_and_store_emails(max_results=20)
                
                if emails_fetched > 0:
                    print(f"\n🎉 Success! {emails_fetched} new emails fetched!")
                
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
    fetcher = SimpleEmailFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
