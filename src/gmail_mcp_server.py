#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail MCP Server - Standalone MCP server for Gmail operations

This server provides tools for:
- Sending emails
- Creating drafts
- Listing drafts
- Searching emails

Usage:
    python gmail_mcp_server.py
    
Or as MCP server for Claude Code:
    claude --mcp "python gmail_mcp_server.py"
"""

import sys
import os
import json
import base64
from pathlib import Path
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


class GmailMCPServer:
    """
    Gmail MCP Server - Provides Gmail tools via MCP protocol.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        self.src_path = Path(__file__).parent
        # Use same credentials as Gmail Watcher
        self.credentials_path = Path(credentials_path) if credentials_path else self.src_path / 'credentials.json'
        # Use same token as Gmail Watcher for consistency
        self.token_path = Path(token_path) if token_path else self.src_path / 'token.json'
        
        self.service = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        try:
            if not self.credentials_path.exists():
                print(f"Credentials not found: {self.credentials_path}")
                return False
            
            # Try to load existing token
            if self.token_path.exists():
                try:
                    self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                    
                    # Check if valid
                    if self.creds and self.creds.valid:
                        self.service = build('gmail', 'v1', credentials=self.creds)
                        self.authenticated = True
                        print("✓ Authenticated with existing token")
                        return True
                    
                    # Try to refresh if expired
                    if self.creds and self.creds.expired and self.creds.refresh_token:
                        print("Token expired, refreshing...")
                        self.creds.refresh(Request())
                        self.service = build('gmail', 'v1', credentials=self.creds)
                        self.authenticated = True
                        print("✓ Token refreshed successfully")
                        return True
                        
                except Exception as e:
                    print(f"Existing token error: {e}")
                    # Will try to re-authenticate below
            
            # Need to re-authenticate
            print("Attempting OAuth authentication...")
            print(f"Credentials: {self.credentials_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            self.creds = flow.run_local_server(port=0, prompt='consent')
            
            # Save token
            self.token_path.write_text(self.creds.to_json())
            print(f"✓ Token saved to: {self.token_path}")
            
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.authenticated = True
            print("✓ Authentication successful!")
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def send_email(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> Dict[str, Any]:
        """Send an email via Gmail."""
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent = self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            
            return {
                "success": True,
                "message_id": sent['id'],
                "thread_id": sent['threadId'],
                "status": "sent"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_draft(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> Dict[str, Any]:
        """Create an email draft."""
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return {
                "success": True,
                "draft_id": draft['id'],
                "message_id": draft['message']['id']
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_drafts(self, max_results: int = 10) -> Dict[str, Any]:
        """List email drafts."""
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            results = self.service.users().drafts().list(userId='me', maxResults=max_results).execute()
            drafts = results.get('drafts', [])
            
            draft_list = []
            for draft in drafts:
                detail = self.service.users().drafts().get(
                    userId='me',
                    id=draft['id'],
                    format='metadata'
                ).execute()
                
                headers = {h['name']: h['value'] for h in detail['message']['payload']['headers']}
                draft_list.append({
                    "draft_id": draft['id'],
                    "subject": headers.get('Subject', 'No Subject'),
                    "to": headers.get('To', 'Unknown')
                })
            
            return {"success": True, "drafts": draft_list}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_emails(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search emails."""
        if not self.authenticated:
            if not self.authenticate():
                return {"success": False, "error": "Not authenticated"}
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for msg in messages:
                detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata'
                ).execute()
                
                headers = {h['name']: h['value'] for h in detail['payload']['headers']}
                email_list.append({
                    "id": msg['id'],
                    "subject": headers.get('Subject', 'No Subject'),
                    "from": headers.get('From', 'Unknown'),
                    "date": headers.get('Date', 'Unknown'),
                    "snippet": detail.get('snippet', '')
                })
            
            return {"success": True, "emails": email_list}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# MCP Protocol Implementation
def get_tools():
    """Return list of available tools."""
    return [
        {
            "name": "send_email",
            "description": "Send an email via Gmail",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body text"},
                    "from": {"type": "string", "description": "Sender email (optional)"}
                },
                "required": ["to", "subject", "body"]
            }
        },
        {
            "name": "search_emails",
            "description": "Search emails",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query"},
                    "max_results": {"type": "integer", "description": "Maximum results", "default": 10}
                },
                "required": ["query"]
            }
        }
    ]


def call_tool(name: str, arguments: Dict[str, Any], server: GmailMCPServer) -> Dict[str, Any]:
    """Call a tool and return result."""
    if name == "send_email":
        return server.send_email(
            to=arguments.get('to'),
            subject=arguments.get('subject'),
            body=arguments.get('body'),
            from_email=arguments.get('from')
        )
    elif name == "search_emails":
        return server.search_emails(
            query=arguments.get('query'),
            max_results=arguments.get('max_results', 10)
        )
    else:
        return {"error": f"Unknown tool: {name}"}


def run_mcp_server():
    """Run as MCP server (stdio protocol)."""
    server = GmailMCPServer()
    request_id = 0
    
    print("Gmail MCP Server running...", file=sys.stderr)
    print("Available tools:", [t['name'] for t in get_tools()], file=sys.stderr)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get('method')
            params = request.get('params', {})
            req_id = request.get('id')
            
            if method == 'initialize':
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "gmail-mcp", "version": "1.0.0"}
                    }
                }
                print(json.dumps(response), flush=True)
                
            elif method == 'tools/list':
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": get_tools()}
                }
                print(json.dumps(response), flush=True)
                
            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})
                
                result = call_tool(tool_name, tool_args, server)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
                print(json.dumps(response), flush=True)
                
            elif method == 'notifications/initialized':
                pass  # No response needed
                
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": req_id if 'req_id' in dir() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gmail MCP Server")
    parser.add_argument("--test", action="store_true", help="Test mode")
    parser.add_argument("--auth", action="store_true", help="Authenticate only")
    parser.add_argument("--send", action="store_true", help="Send test email")
    
    args = parser.parse_args()
    
    server = GmailMCPServer()
    
    if args.auth:
        print("Gmail MCP Authentication")
        print("=" * 50)
        if server.authenticate():
            print("Authentication successful!")
            print(f"Token saved to: {server.token_path}")
        else:
            print("Authentication failed")
            sys.exit(1)
    
    elif args.test:
        print("Gmail MCP Test")
        print("=" * 50)
        
        if not server.authenticate():
            print("Failed to authenticate")
            sys.exit(1)
        
        # Test list drafts
        result = server.list_drafts()
        print(f"Drafts: {result}")
    
    elif args.send:
        print("Send Test Email")
        print("=" * 50)
        
        to = input("To: ")
        subject = input("Subject: ")
        body = input("Body: ")
        
        if not server.authenticate():
            print("Failed to authenticate")
            sys.exit(1)
        
        result = server.send_email(to=to, subject=subject, body=body)
        print(f"Result: {result}")
    
    else:
        # Run as MCP server
        run_mcp_server()


if __name__ == "__main__":
    main()
