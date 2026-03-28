#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitor Gmail for new important emails.

This watcher uses the Gmail API to:
1. Check for new unread emails every 2 minutes
2. Filter for important messages
3. Create action files in Needs_Action folder for AI processing

Setup Required:
1. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Create OAuth credentials
3. Download credentials.json to src/ folder
4. Run once to authorize: python gmail_watcher.py /path/to/vault --auth

Usage:
    python gmail_watcher.py /path/to/vault
"""

import sys
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from email import message_from_bytes

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher

try:
    from google.oauth2 import credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Error: Gmail dependencies not installed. {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher for monitoring new emails.
    
    Monitors Gmail inbox for unread, important messages and creates
    action files for AI processing.
    """
    
    # Gmail API scopes - includes send permission for Email MCP
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(
        self, 
        vault_path: str,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        check_interval: int = 120,
        log_level: str = "INFO"
    ):
        """
        Initialize Gmail Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to credentials.json (default: src/credentials.json)
            token_path: Path to store token.json (default: src/token.json)
            check_interval: Seconds between checks (default: 120)
            log_level: Logging level
        """
        super().__init__(vault_path, check_interval, log_level)
        
        # Setup paths
        self.src_path = Path(__file__).parent
        self.credentials_path = Path(credentials_path) if credentials_path else self.src_path / 'credentials.json'
        self.token_path = Path(token_path) if token_path else self.src_path / 'token.json'
        
        # Gmail service
        self.service = None
        self.creds = None
        
        # Track processed message IDs
        self.processed_ids = set()
        
        # Keywords for filtering important emails
        self.important_keywords = [
            'urgent', 'asap', 'invoice', 'payment', 'meeting',
            'interview', 'deadline', 'important', 'action required'
        ]
        
        self.logger.info(f"Gmail Watcher initialized")
        self.logger.info(f"Credentials: {self.credentials_path}")
        self.logger.info(f"Token: {self.token_path}")
    
    def authenticate(self):
        """
        Authenticate with Gmail API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if credentials file exists
            if not self.credentials_path.exists():
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                self.logger.error("Download credentials.json from Google Cloud Console")
                return False
            
            # Load existing token or create new credentials
            if self.token_path.exists():
                self.creds = credentials.Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
            
            # Refresh token if expired
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Run OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save token for future use
                self.token_path.write_text(self.creds.to_json())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def _decode_message(self, message: Dict) -> str:
        """
        Decode Gmail message body.
        
        Args:
            message: Gmail message object
            
        Returns:
            Decoded message text
        """
        try:
            if 'parts' in message['payload']:
                # Multipart message - find plain text part
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Simple message or HTML fallback
            if 'body' in message['payload']:
                data = message['payload']['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            
            return message['snippet']
            
        except Exception as e:
            self.logger.warning(f"Failed to decode message: {e}")
            return message.get('snippet', '')
    
    def _extract_headers(self, message: Dict) -> Dict[str, str]:
        """
        Extract email headers from Gmail message.
        
        Args:
            message: Gmail message object
            
        Returns:
            Dictionary of headers
        """
        headers = {}
        for header in message['payload'].get('headers', []):
            name = header['name'].lower()
            value = header['value']
            if name in ['from', 'to', 'subject', 'date']:
                headers[name] = value
        return headers
    
    def check_for_updates(self) -> List[Dict]:
        """
        Check Gmail for new unread messages.
        
        Returns:
            List of new message dictionaries
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []
            
            for msg in messages:
                # Skip already processed
                if msg['id'] in self.processed_ids:
                    continue
                
                # Get full message details
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extract info
                headers = self._extract_headers(message)
                body = self._decode_message(message)
                
                # Check if important
                is_important = any(
                    keyword in body.lower() or keyword in headers.get('subject', '').lower()
                    for keyword in self.important_keywords
                )
                
                # Always include first 5 messages, filter rest by importance
                if len(new_messages) < 5 or is_important:
                    new_messages.append({
                        'id': msg['id'],
                        'from': headers.get('from', 'Unknown'),
                        'to': headers.get('to', ''),
                        'subject': headers.get('subject', 'No Subject'),
                        'date': headers.get('date', ''),
                        'snippet': message.get('snippet', ''),
                        'body': body,
                        'important': is_important
                    })
                    
                    # Mark as processed
                    self.processed_ids.add(msg['id'])
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            # Try to re-authenticate on error
            self.service = None
            return []
    
    def create_action_file(self, item: Dict) -> Optional[Path]:
        """
        Create action file for new email.
        
        Args:
            item: Email message dictionary
            
        Returns:
            Path to created action file
        """
        timestamp = datetime.now().isoformat()
        
        # Determine priority
        priority = 'high' if item['important'] else 'medium'
        
        # Create action file content
        content = f"""---
type: email
from: {item['from']}
subject: {item['subject']}
received: {timestamp}
priority: {priority}
status: pending
gmail_id: {item['id']}
---

# Email Received

## Sender Information
- **From**: {item['from']}
- **To**: {item['to']}
- **Date**: {item['date']}
- **Priority**: {priority.title()}

## Email Content
{item['body'] if item['body'] else item['snippet']}

## Suggested Actions
- [ ] Review email content
- [ ] Draft response (requires approval)
- [ ] Forward to relevant party
- [ ] Archive after processing

## Notes
*Add any additional context or instructions here*

---
*Created by GmailWatcher*
"""
        
        # Generate filename
        safe_subject = "".join(c if c.isalnum() else "_" for c in item['subject'][:30])
        filename = f"EMAIL_{safe_subject}_{item['id']}.md"
        filepath = self.needs_action / filename
        
        try:
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created action file: {filename}")
            
            # Log audit
            self._log_audit("email_received", {
                "from": item['from'],
                "subject": item['subject'],
                "priority": priority,
                "action_file": str(filepath)
            })
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to create action file: {e}")
            return None


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gmail Watcher for AI Employee")
    parser.add_argument("vault_path", help="Path to Obsidian vault")
    parser.add_argument("--credentials", "-c", help="Path to credentials.json")
    parser.add_argument("--token", "-t", help="Path to token.json")
    parser.add_argument("--check-interval", "-i", type=int, default=120, help="Check interval in seconds")
    parser.add_argument("--auth", action="store_true", help="Run authentication only")
    parser.add_argument("--log-level", "-l", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    watcher = GmailWatcher(
        vault_path=args.vault_path,
        credentials_path=args.credentials,
        token_path=args.token,
        check_interval=args.check_interval,
        log_level=args.log_level
    )
    
    if args.auth:
        # Authentication mode
        print("📧 Gmail Authentication")
        print("=" * 50)
        print("Opening browser for authentication...")
        
        if watcher.authenticate():
            print("✅ Authentication successful!")
            print(f"Token saved to: {watcher.token_path}")
            print("\nYou can now run the watcher:")
            print(f"  python gmail_watcher.py {args.vault_path}")
        else:
            print("❌ Authentication failed")
            sys.exit(1)
    else:
        # Watcher mode
        print(f"📧 Starting Gmail Watcher...")
        print(f"Vault: {args.vault_path}")
        print(f"Check Interval: {args.check_interval}s")
        print("Press Ctrl+C to stop.\n")
        
        try:
            watcher.run()
        except KeyboardInterrupt:
            print("\nWatcher stopped.")


if __name__ == "__main__":
    main()
