#!/usr/bin/env python3
"""Quick Gmail Test - Send an email using existing Gmail Watcher token."""
import os
import base64
from email.mime.text import MIMEText
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
src_path = Path(__file__).parent
token_path = src_path / 'token.json'  # Use same token as Gmail Watcher
credentials_path = src_path / 'credentials.json'

# Check if token exists
if not token_path.exists():
    print("❌ Token file not found. Run gmail_watcher authentication first.")
    exit(1)

# Load credentials
creds = Credentials.from_authorized_user_file(token_path)

# Build Gmail service
service = build('gmail', 'v1', credentials=creds)

# Get email details
print("📧 Send Test Email")
print("=" * 50)
to = input("To: ")
subject = input("Subject: ")
body = input("Body: ")

# Create message
message = MIMEText(body)
message['to'] = to
message['subject'] = subject

# Encode
raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

try:
    # Send
    sent = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    print(f"\n✅ Email sent successfully!")
    print(f"Message ID: {sent['id']}")
except Exception as e:
    print(f"\n❌ Failed to send: {e}")
    print("\nNote: Gmail Watcher token may not have 'send' scope.")
    print("You may need to re-authenticate with send scope.")
