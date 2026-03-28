#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-User AI Orchestrator

This orchestrator:
1. Processes emails for ALL users simultaneously
2. Runs AI analysis on each user's emails
3. Creates draft responses per user
7. Handles approvals per user
8. Sends emails on behalf of each user
9. Runs continuously, checking every 30 seconds

Usage:
    python src/multi_user_orchestrator.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from openai import OpenAI
except ImportError as e:
    print(f"Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "requests", "openai"])
    import requests
    from openai import OpenAI


class MultiUserOrchestrator:
    """
    Multi-user AI orchestrator with rate limiting.
    
    Processes emails for all users with AI analysis,
    draft responses, and automated sending.
    Includes smart rate limiting to avoid API limits.
    """
    
    def __init__(self):
        """Initialize the multi-user orchestrator."""
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials required!")
        
        # Use service role key for admin operations
        self.admin_key = self.supabase_service_key or self.supabase_key
        
        # OpenRouter AI configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
        
        if not self.openrouter_api_key:
            print("⚠️  OPENROUTER_API_KEY not set - AI features disabled")
            self.ai_client = None
        else:
            self.ai_client = OpenAI(
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            print(f"✅ AI enabled: {self.openrouter_model}")
        
        # Rate limiting configuration
        self.rate_limit = 6  # Requests per minute (safe limit for Llama 3.2)
        self.request_times = []  # Track request timestamps
        self.retry_count = 0
        self.max_retries = 3
        
        # Supabase REST API endpoints
        self.api_url = self.supabase_url.rstrip('/')
        if '/ref/v1' in self.api_url:
            self.api_url = self.api_url.replace('/ref/v1', '')
        
        self.rest_url = f"{self.api_url}/rest/v1"
        
        # Headers for Supabase API
        self.headers = {
            'apikey': self.admin_key,
            'Authorization': f'Bearer {self.admin_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
            'X-Improve-Role': 'service_role'
        }
        
        print("✅ Multi-User AI Orchestrator initialized")
        print(f"   Supabase: {self.supabase_url}")
        print(f"   Processing all users every 30 seconds...")
        print(f"   AI analysis: {'Enabled' if self.ai_client else 'Disabled'}")
        print(f"   Rate limiting: {self.rate_limit} requests/minute")
    
    def wait_for_rate_limit(self):
        """
        Wait if we've hit the rate limit.
        
        Implements smart rate limiting to avoid 429 errors.
        """
        if not self.ai_client:
            return
        
        now = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # If we've hit the limit, wait
        if len(self.request_times) >= self.rate_limit:
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request) + 1  # Add 1 second buffer
            
            if wait_time > 0:
                print(f"   ⏳ Rate limit reached - waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                # Clean up again after waiting
                now = time.time()
                self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Record this request
        self.request_times.append(time.time())
    
    def analyze_email_with_ai(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single email with AI.
        
        Includes retry logic for rate limit errors.
        
        Args:
            email: Email data from database
            
        Returns:
            AI analysis results or None
        """
        if not self.ai_client:
            return None
        
        # Try up to max_retries times
        for attempt in range(self.max_retries):
            try:
                # Wait for rate limit before making request
                self.wait_for_rate_limit()
                
                subject = email.get('subject', 'No Subject')
                from_address = email.get('from_address', 'Unknown')
                preview = email.get('body_preview', '')
                
                # Create prompt for AI
                prompt = f"""Analyze this email and provide:
1. Brief analysis of the email content and intent
2. Whether it requires human approval before responding
3. A draft response (if no approval needed)

Email Details:
- From: {from_address}
- Subject: {subject}
- Preview: {preview}

Format your response as JSON:
{{
    "analysis": "Brief analysis of the email",
    "requires_approval": true/false,
    "category": "Inquiry/Support/Sales/Spam/Other",
    "priority": "High/Medium/Low",
    "draft_response": "Draft response text (if approval not required)"
}}"""

                # Call AI
                response = self.ai_client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=[
                        {"role": "system", "content": "You are an AI email assistant. Analyze emails and provide structured responses."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                # Reset retry count on success
                self.retry_count = 0
                
                # Parse AI response
                ai_response = response.choices[0].message.content.strip()
                
                # Try to parse as JSON
                try:
                    # Extract JSON from response
                    if '```json' in ai_response:
                        ai_response = ai_response.split('```json')[1].split('```')[0]
                    elif '```' in ai_response:
                        ai_response = ai_response.split('```')[1].split('```')[0]
                    
                    result = json.loads(ai_response)
                    return result
                except:
                    # Fallback if not valid JSON
                    return {
                        "analysis": ai_response[:200],
                        "requires_approval": True,
                        "category": "Other",
                        "priority": "Medium",
                        "draft_response": None
                    }
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if '429' in error_str or 'rate limit' in error_str.lower():
                    self.retry_count += 1
                    
                    if attempt < self.max_retries - 1:
                        # Wait longer each retry
                        wait_time = 10 * self.retry_count
                        print(f"   ⏳ Rate limit hit - retry {attempt + 1}/{self.max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ⚠️  Rate limit exceeded after {self.max_retries} retries")
                        return None
                else:
                    # Not a rate limit error - don't retry
                    print(f"   ❌ AI analysis error: {e}")
                    return None
        
        return None
    
    def supabase_query(self, table: str, method: str = 'GET', data: Optional[Dict] = None, 
                       params: Optional[Dict] = None) -> Any:
        """Make a request to Supabase REST API."""
        url = f"{self.rest_url}/{table}"
        
        # Build query parameters properly
        query_params = {}
        if params:
            for k, v in params.items():
                # Don't modify the value - Supabase REST API expects the operator in the value
                query_params[k] = v
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=query_params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PATCH':
                # For PATCH, we need to send the filter in the URL or headers
                # Supabase REST API requires filters for UPDATE operations
                if query_params:
                    # Add filters to URL
                    filter_parts = []
                    for k, v in query_params.items():
                        filter_parts.append(f"{k}={v}")
                    filter_string = "&".join(filter_parts)
                    url = f"{url}?{filter_string}"
                
                response = requests.patch(url, headers=self.headers, json=data)
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
    
    def get_pending_emails(self) -> List[Dict[str, Any]]:
        """
        Get all emails that need AI processing.
        
        Returns:
            List of emails across all users that need processing
        """
        print(f"\n📋 Fetching emails needing processing...")
        
        try:
            # Get emails with status 'new' that need AI analysis
            # Make sure to select ALL required fields including 'id'
            emails = self.supabase_query(
                'emails',
                params={
                    'status': 'eq.new',
                    'select': 'id,user_id,vault_id,subject,from_address,body_preview,requires_approval,ai_analysis'
                }
            )
            
            if not emails or not isinstance(emails, list):
                print(f"   ✓ No emails need processing")
                return []
            
            # Filter out emails without IDs
            valid_emails = [e for e in emails if e.get('id')]
            invalid_count = len(emails) - len(valid_emails)
            
            if invalid_count > 0:
                print(f"   ⚠️  {invalid_count} emails missing ID, skipping...")
            
            print(f"   ✓ Found {len(valid_emails)} emails to process")
            return valid_emails
            
        except Exception as e:
            print(f"   ❌ Error fetching emails: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def analyze_email_with_ai(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single email with AI.
        
        Args:
            email: Email data from database
            
        Returns:
            AI analysis results or None
        """
        if not self.ai_client:
            return None
        
        try:
            subject = email.get('subject', 'No Subject')
            from_address = email.get('from_address', 'Unknown')
            preview = email.get('body_preview', '')
            
            # Create prompt for AI
            prompt = f"""Analyze this email and provide:
1. Brief analysis of the email content and intent
2. Whether it requires human approval before responding
3. A draft response (if no approval needed)

Email Details:
- From: {from_address}
- Subject: {subject}
- Preview: {preview}

Format your response as JSON:
{{
    "analysis": "Brief analysis of the email",
    "requires_approval": true/false,
    "category": "Inquiry/Support/Sales/Spam/Other",
    "priority": "High/Medium/Low",
    "draft_response": "Draft response text (if approval not required)"
}}"""

            # Call AI
            response = self.ai_client.chat.completions.create(
                model=self.openrouter_model,
                messages=[
                    {"role": "system", "content": "You are an AI email assistant. Analyze emails and provide structured responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                # Extract JSON from response
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0]
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0]
                
                result = json.loads(ai_response)
                return result
            except:
                # Fallback if not valid JSON
                return {
                    "analysis": ai_response[:200],
                    "requires_approval": True,
                    "category": "Other",
                    "priority": "Medium",
                    "draft_response": None
                }
                
        except Exception as e:
            print(f"   ❌ AI analysis error: {e}")
            return None
    
    def process_email(self, email: Dict[str, Any]) -> bool:
        """
        Process a single email with AI.
        
        Args:
            email: Email data from database
            
        Returns:
            True if processed successfully
        """
        email_id = email.get('id')
        user_id = email.get('user_id')
        subject = email.get('subject', 'No Subject')
        
        # Debug: Print email data
        print(f"\n📧 Processing email: {subject}")
        print(f"   Email ID: {email_id}")
        print(f"   User ID: {user_id}")
        
        # Validate required fields
        if not email_id:
            print(f"   ❌ Skipping - No email ID in data: {email}")
            return False
        
        try:
            # Analyze with AI
            if self.ai_client:
                print(f"   🤖 Running AI analysis...")
                ai_result = self.analyze_email_with_ai(email)
                
                if ai_result:
                    analysis = ai_result.get('analysis', '')
                    requires_approval = ai_result.get('requires_approval', True)
                    category = ai_result.get('category', 'Other')
                    priority = ai_result.get('priority', 'Medium')
                    draft_response = ai_result.get('draft_response', '')
                    
                    print(f"   ✓ Analysis: {analysis[:100]}...")
                    print(f"   ✓ Category: {category}")
                    print(f"   ✓ Priority: {priority}")
                    print(f"   ✓ Requires Approval: {requires_approval}")
                    
                    # Update email with AI analysis
                    update_data = {
                        'ai_analysis': analysis,
                        'status': 'pending_approval' if requires_approval else 'approved',
                        'requires_approval': requires_approval
                    }
                    
                    if draft_response:
                        update_data['ai_draft_response'] = draft_response
                    
                    # Update in database with proper validation
                    print(f"   📝 Updating email {email_id}...")
                    result = self.supabase_query(
                        'emails',
                        method='PATCH',
                        data=update_data,
                        params={'id': f'eq.{email_id}'}
                    )
                    
                    if result and result.get('success'):
                        print(f"   ✅ Email processed successfully")
                        
                        # Create notification for user
                        self.create_notification(
                            user_id=user_id,
                            email_id=email_id,
                            message=f"New email processed: {subject}",
                            notification_type='email_processed'
                        )
                        
                        return True
                    else:
                        print(f"   ❌ Failed to update email - API returned: {result}")
                        return False
                else:
                    print(f"   ⚠️  AI analysis returned no result")
                    return False
            else:
                # No AI - just mark as pending approval
                print(f"   ⚠️  AI disabled - marking as pending approval")
                result = self.supabase_query(
                    'emails',
                    method='PATCH',
                    data={
                        'status': 'pending_approval',
                        'requires_approval': True
                    },
                    params={'id': f'eq.{email_id}'}
                )
                return result and result.get('success', False)
                
        except Exception as e:
            print(f"   ❌ Error processing email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_notification(self, user_id: str, email_id: str, message: str, 
                           notification_type: str = 'email_processed'):
        """Create a notification for the user (optional feature)."""
        try:
            notification_data = {
                'user_id': user_id,
                'email_id': email_id,
                'message': message,
                'type': notification_type,
                'read': False
            }
            
            # Try to create notification (table might not exist)
            result = self.supabase_query(
                'notifications',
                method='POST',
                data=notification_data
            )
            
            if result and result.get('success'):
                print(f"   🔔 Notification created for user")
                
        except:
            # Notifications table might not exist - that's OK, it's optional
            pass
    
    def process_approved_emails(self):
        """Process emails that have been approved and need to be sent."""
        print(f"\n📤 Processing approved emails...")

        try:
            # Get approved emails that haven't been sent yet
            # Include ALL approved emails (both those that required approval and those that didn't)
            emails = self.supabase_query(
                'emails',
                params={
                    'status': 'eq.approved',
                    'select': 'id,user_id,vault_id,subject,from_address,to_address,ai_draft_response,requires_approval'
                }
            )
            
            if not emails or not isinstance(emails, list):
                print(f"   ✓ No approved emails to send")
                return
            
            print(f"   ✓ Found {len(emails)} approved emails to send")

            # Send each approved email
            sent_count = 0
            skipped_count = 0

            for email in emails:
                email_id = email.get('id')
                user_id = email.get('user_id')
                subject = email.get('subject')
                from_address = email.get('from_address')  # Original sender
                to_address = email.get('to_address')
                draft_response = email.get('ai_draft_response')
                requires_approval = email.get('requires_approval', False)

                # Use from_address as to_address if to_address is empty
                recipient = to_address or from_address

                if not recipient:
                    print(f"   ⚠️  No recipient for: {subject} - marking as skipped")
                    # Mark as sent anyway (can't send without recipient)
                    self.supabase_query(
                        'emails',
                        method='PATCH',
                        data={
                            'status': 'sent',
                            'sent_at': datetime.now().isoformat(),
                            'notes': 'Skipped - no recipient found'
                        },
                        params={'id': f'eq.{email_id}'}
                    )
                    skipped_count += 1
                    continue

                if draft_response and draft_response.strip():
                    print(f"\n   📧 Sending: {subject}")
                    print(f"   To: {recipient}")

                    # Send email via Gmail API
                    send_result = self.send_email_via_gmail(
                        user_id=user_id,
                        to_address=recipient,
                        subject=f"Re: {subject}",
                        body=draft_response
                    )

                    if send_result and send_result.get('success'):
                        # Mark as sent
                        self.supabase_query(
                            'emails',
                            method='PATCH',
                            data={
                                'status': 'sent',
                                'sent_at': datetime.now().isoformat()
                            },
                            params={'id': f'eq.{email_id}'}
                        )
                        print(f"   ✅ Sent successfully!")
                        sent_count += 1
                    else:
                        print(f"   ⚠️  Failed to send: {send_result}")
                else:
                    # No draft response - check if it requires one
                    if requires_approval:
                        print(f"   ⚠️  No draft response for: {subject} (requires approval)")
                        # Skip - needs human review
                        skipped_count += 1
                    else:
                        print(f"   ✓ No reply needed for: {subject} - marking as sent")
                        # Mark as sent (no reply needed)
                        self.supabase_query(
                            'emails',
                            method='PATCH',
                            data={
                                'status': 'sent',
                                'sent_at': datetime.now().isoformat(),
                                'notes': 'No reply required'
                            },
                            params={'id': f'eq.{email_id}'}
                        )
                        sent_count += 1

            print(f"\n📊 Sent: {sent_count}, Skipped: {skipped_count} (Total: {len(emails)})")
            
        except Exception as e:
            print(f"   ❌ Error processing approved emails: {e}")
            import traceback
            traceback.print_exc()
    
    def send_email_via_gmail(self, user_id: str, to_address: str, 
                             subject: str, body: str) -> Optional[Dict]:
        """
        Send email via Gmail API.
        
        Args:
            user_id: User's ID
            to_address: Recipient email
            subject: Email subject
            body: Email body
            
        Returns:
            Send result or None
        """
        try:
            # Get Gmail credentials for this user
            # For now, we use the same Gmail account (the one that authenticated)
            # In production, each user would have their own Gmail OAuth token
            
            token_path = Path(__file__).parent / 'token.json'
            
            if not token_path.exists():
                print(f"   ⚠️  Gmail not authenticated - no token.json found")
                return None
            
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            import base64
            
            # Load credentials
            creds = Credentials.from_authorized_user_file(token_path, [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly'
            ])
            
            # Refresh if expired
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())
                else:
                    print(f"   ⚠️  Gmail credentials invalid")
                    return None
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            
            # Create email message
            message = MIMEText(body)
            message['to'] = to_address
            message['from'] = 'me'  # Will be replaced by Gmail with authenticated user
            message['subject'] = subject
            
            # Encode email
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send via Gmail API
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"   ✅ Gmail sent message ID: {sent_message.get('id')}")
            
            return {
                'success': True,
                'message_id': sent_message.get('id'),
                'thread_id': sent_message.get('threadId')
            }
            
        except Exception as e:
            print(f"   ❌ Error sending email: {e}")
            return None
    
    def run(self):
        """Main loop - continuously process emails for all users."""
        print("\n" + "=" * 60)
        print("🚀 Starting Multi-User AI Orchestrator")
        print("=" * 60)
        print("This will automatically:")
        print("  1. Check for new emails across ALL users")
        print("  2. Run AI analysis on each email")
        print("  3. Create draft responses")
        print("  4. Set approval flags")
        print("  5. Send approved emails")
        print("  6. Check every 30 seconds")
        print("=" * 60 + "\n")

        try:
            while True:
                # PRIORITY 1: Process approved emails FIRST (ready to send)
                print(f"\n{'='*60}")
                print("📤 PRIORITY: Checking approved emails to send...")
                self.process_approved_emails()

                # PRIORITY 2: Process new emails with AI
                emails = self.get_pending_emails()

                if not emails:
                    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] No new emails to process")
                else:
                    # Process emails (can be done in parallel for multiple users)
                    print(f"\n🔄 Processing {len(emails)} new emails with AI...")

                    processed_count = 0
                    for email in emails:
                        if self.process_email(email):
                            processed_count += 1

                    print(f"\n✅ Processed {processed_count}/{len(emails)} emails")

                # Wait 30 seconds before next check
                print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Waiting 30 seconds before next check...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping orchestrator...")
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            time.sleep(5)
            self.run()


def main():
    """Main entry point."""
    orchestrator = MultiUserOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
