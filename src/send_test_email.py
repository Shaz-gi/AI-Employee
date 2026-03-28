#!/usr/bin/env python3
"""Quick Gmail Send Test - No input required."""
import os
import base64
from email.mime.text import MIMEText
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
src_path = Path(__file__).parent
token_path = src_path / 'token.json'

# Check if token exists
if not token_path.exists():
    print("❌ Token file not found. Run gmail_watcher authentication first.")
    exit(1)

# Load credentials
creds = Credentials.from_authorized_user_file(token_path)

# Build Gmail service
service = build('gmail', 'v1', credentials=creds)

# Test email details
to = "animepremier28@gmail.com"  # Send to yourself
subject = "🤖 AI Employee Test Email"
body = """
Hello!

This is a test email from your AI Employee Silver Tier system.

If you're reading this, it means:
✅ Gmail API is working
✅ Email sending is configured correctly
✅ Your AI Employee can now send emails!

Next steps:
1. Check Gmail Watcher is running
2. Set up scheduled tasks
3. Start using AI Employee for real emails!

Best regards,
Your AI Employee 🤖
"""

# Create message
message = MIMEText(body)
message['to'] = to
message['subject'] = subject

# Encode
raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

try:
    # Send
    sent = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    print(f"✅ Email sent successfully!")
    print(f"Message ID: {sent['id']}")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"\nCheck your inbox at {to}")
except Exception as e:
    print(f"❌ Failed to send: {e}")
