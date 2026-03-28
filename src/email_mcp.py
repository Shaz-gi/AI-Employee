#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email MCP Server - Send emails via Gmail API.

This MCP server provides tools for:
- Sending emails via Gmail
- Drafting emails for review
- Managing email approvals

Setup Required:
1. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Create OAuth credentials with gmail.send scope
3. Download as credentials.json to src/ folder

Usage:
    # As MCP server (for Claude Code)
    python email_mcp.py
    
    # Test mode
    python email_mcp.py --test
"""

import sys
import os
import base64
import json
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"Error: Gmail dependencies not installed. {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


class EmailMCP:
    """
    Email MCP Server for sending emails via Gmail API.
    
    Provides tools for:
    - send_email: Send an email immediately
    - draft_email: Create a draft for review
    - list_drafts: List email drafts
    """
    
    # Gmail API scopes - includes send permission
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        """
        Initialize Email MCP.

        Args:
            credentials_path: Path to credentials.json
            token_path: Path to token.json (uses token.json by default for consistency with Gmail Watcher)
        """
        self.src_path = Path(__file__).parent
        self.credentials_path = Path(credentials_path) if credentials_path else self.src_path / 'credentials.json'
        # Use same token as Gmail Watcher and Gmail MCP Server for consistency
        self.token_path = Path(token_path) if token_path else self.src_path / 'token.json'
        
        self.service = None
        self.creds = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.
        
        Returns:
            True if successful
        """
        try:
            # Check credentials file
            if not self.credentials_path.exists():
                print(f"Error: Credentials file not found: {self.credentials_path}")
                return False
            
            # Load existing token
            if self.token_path.exists():
                self.creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
            
            # Refresh or get new token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0, prompt='consent')
                
                self.token_path.write_text(self.creds.to_json())
            
            # Build service
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.authenticated = True
            print("✓ Gmail authentication successful")
            return True
            
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[str] = None,
        attachment_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional, uses authenticated account)
            cc: CC recipient (optional)
            attachment_paths: List of file paths to attach (optional)
            
        Returns:
            Result dictionary with status and message_id
        """
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            if cc:
                message['cc'] = cc
            
            # Handle attachments (for Silver Tier, basic implementation)
            # Full attachment support would require MIME multipart
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            result = {
                "success": True,
                "message_id": sent_message['id'],
                "thread_id": sent_message['threadId'],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an email draft for review.
        
        Args:
            to: Recipient email
            subject: Subject
            body: Email body
            from_email: Sender email
            
        Returns:
            Result with draft_id
        """
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Encode
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return {
                "success": True,
                "draft_id": draft['id'],
                "message_id": draft['message']['id'],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_drafts(self, max_results: int = 10) -> Dict[str, Any]:
        """
        List email drafts.
        
        Args:
            max_results: Maximum drafts to return
            
        Returns:
            List of drafts
        """
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            results = self.service.users().drafts().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            drafts = results.get('drafts', [])
            draft_list = []
            
            for draft in drafts:
                draft_detail = self.service.users().drafts().get(
                    userId='me',
                    id=draft['id'],
                    format='metadata'
                ).execute()
                
                draft_list.append({
                    "draft_id": draft['id'],
                    "subject": draft_detail['message']['payload']['headers'][1]['value'],
                    "to": draft_detail['message']['payload']['headers'][0]['value']
                })
            
            return {
                "success": True,
                "drafts": draft_list
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# MCP Server Protocol Implementation
def run_mcp_server():
    """Run as MCP server for Claude Code."""
    email_mcp = EmailMCP()
    
    print("Email MCP Server running...", file=sys.stderr)
    print("Waiting for requests...", file=sys.stderr)
    
    # Read requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get('method')
            params = request.get('params', {})
            
            result = None
            
            if method == 'send_email':
                result = email_mcp.send_email(
                    to=params.get('to'),
                    subject=params.get('subject'),
                    body=params.get('body'),
                    from_email=params.get('from'),
                    cc=params.get('cc')
                )
            
            elif method == 'create_draft':
                result = email_mcp.create_draft(
                    to=params.get('to'),
                    subject=params.get('subject'),
                    body=params.get('body'),
                    from_email=params.get('from')
                )
            
            elif method == 'list_drafts':
                result = email_mcp.list_drafts(
                    max_results=params.get('max_results', 10)
                )
            
            elif method == 'authenticate':
                success = email_mcp.authenticate()
                result = {"success": success}
            
            else:
                result = {"error": f"Unknown method: {method}"}
            
            # Send response
            response = {
                "id": request.get('id'),
                "result": result
            }
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            error_response = {
                "id": request.get('id') if 'request' in dir() else None,
                "error": str(e)
            }
            print(json.dumps(error_response), flush=True)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Email MCP Server")
    parser.add_argument("--test", action="store_true", help="Test mode")
    parser.add_argument("--auth", action="store_true", help="Authenticate only")
    parser.add_argument("--credentials", "-c", help="Path to credentials.json")
    parser.add_argument("--send", action="store_true", help="Send test email")
    
    args = parser.parse_args()
    
    email_mcp = EmailMCP(credentials_path=args.credentials)
    
    if args.auth:
        # Authentication mode
        print("📧 Email MCP Authentication")
        print("=" * 50)
        if email_mcp.authenticate():
            print("✅ Authentication successful!")
            print(f"Token saved to: {email_mcp.token_path}")
        else:
            print("❌ Authentication failed")
            sys.exit(1)
    
    elif args.test:
        # Test mode
        print("📧 Email MCP Test Mode")
        print("=" * 50)
        
        if not email_mcp.authenticate():
            print("Failed to authenticate")
            sys.exit(1)
        
        # Test list drafts
        result = email_mcp.list_drafts()
        print(f"\nDrafts: {result}")
    
    elif args.send:
        # Send test email
        print("📧 Send Test Email")
        print("=" * 50)
        
        to = input("To: ")
        subject = input("Subject: ")
        body = input("Body: ")
        
        if not email_mcp.authenticate():
            print("Failed to authenticate")
            sys.exit(1)
        
        result = email_mcp.send_email(to=to, subject=subject, body=body)
        print(f"\nResult: {result}")
    
    else:
        # Run as MCP server
        run_mcp_server()


if __name__ == "__main__":
    main()
