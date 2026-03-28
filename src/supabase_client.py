#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Client - Database & Authentication for AI Employee Pro

FREE TIER:
- Supabase Free Plan: 50K MAU, 500MB DB, 1GB Storage
- No credit card required
- Production-ready

Setup:
1. Create account at https://supabase.com
2. Create new project
3. Get credentials from Settings → API
4. Install: pip install supabase
5. Run supabase_schema.sql in Supabase SQL Editor
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing Supabase client...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client, Client


class SupabaseClient:
    """
    Supabase client for AI Employee Pro.
    
    Handles:
    - User authentication
    - Vault management
    - Email tracking
    - Usage limits
    - Audit logging
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            supabase_url: Your Supabase project URL
            supabase_key: Your Supabase anon/public key
        """
        # Get from environment or parameters
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials required!\n"
                "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables\n"
                "or pass them as parameters.\n\n"
                "Get them from: https://app.supabase.com/project/_/settings/api"
            )
        
        # Initialize client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.user = None
        self.user_id = None
        
        print(f"✓ Connected to Supabase: {self.supabase_url}")
    
    # ============================================
    # AUTHENTICATION
    # ============================================
    
    def sign_up(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user account.
        
        Args:
            email: User email
            password: User password
            full_name: Optional full name
            
        Returns:
            User data or error
        """
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name or email.split('@')[0]
                    }
                }
            })
            
            print(f"✓ User created: {email}")
            return {"success": True, "user": response.user.dict(), "message": "Check email for confirmation"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in existing user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Session data or error
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            self.user = response.user
            self.user_id = response.user.id
            
            print(f"✓ Signed in: {email}")
            return {
                "success": True,
                "user": response.user.dict(),
                "session": response.session.dict() if response.session else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_out(self):
        """Sign out current user."""
        try:
            self.client.auth.sign_out()
            self.user = None
            self.user_id = None
            print("✓ Signed out")
        except Exception as e:
            print(f"Sign out error: {e}")
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data."""
        if not self.user_id:
            return None
        
        try:
            response = self.client.table("profiles").select("*").eq("id", self.user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception:
            return None
    
    # ============================================
    # VAULT MANAGEMENT
    # ============================================
    
    def create_vault(self, name: str = "My Vault") -> Dict[str, Any]:
        """
        Create a new vault for current user.
        
        Args:
            name: Vault name
            
        Returns:
            Vault data or error
        """
        if not self.user_id:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            storage_path = f"{self.user_id}/{name.replace(' ', '_').lower()}"
            
            response = self.client.table("vaults").insert({
                "user_id": self.user_id,
                "name": name,
                "storage_path": storage_path
            }).execute()
            
            print(f"✓ Vault created: {name}")
            return {"success": True, "vault": response.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_vaults(self) -> List[Dict[str, Any]]:
        """Get all vaults for current user."""
        if not self.user_id:
            return []
        
        try:
            response = self.client.table("vaults").select("*").eq("user_id", self.user_id).execute()
            return response.data or []
        except Exception:
            return []
    
    def get_vault(self, vault_id: str) -> Optional[Dict[str, Any]]:
        """Get specific vault."""
        if not self.user_id:
            return None
        
        try:
            response = self.client.table("vaults").select("*").eq("id", vault_id).eq("user_id", self.user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception:
            return None
    
    # ============================================
    # EMAIL TRACKING
    # ============================================
    
    def track_email(self, vault_id: str, from_address: str, subject: str, 
                    gmail_message_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Track a processed email.
        
        Args:
            vault_id: Vault ID
            from_address: Sender email
            subject: Email subject
            gmail_message_id: Gmail message ID
            **kwargs: Additional fields
            
        Returns:
            Email record or error
        """
        if not self.user_id:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            data = {
                "vault_id": vault_id,
                "from_address": from_address,
                "subject": subject,
                "gmail_message_id": gmail_message_id,
                **kwargs
            }
            
            response = self.client.table("emails").insert(data).execute()
            return {"success": True, "email": response.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_emails(self, vault_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get emails for a vault."""
        if not self.user_id:
            return []
        
        try:
            query = self.client.table("emails").select("*").eq("vault_id", vault_id)
            
            if status:
                query = query.eq("status", status)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception:
            return []
    
    def update_email_status(self, email_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """Update email status."""
        try:
            data = {"status": status, **kwargs}
            if status == 'sent':
                data['sent_at'] = datetime.now().isoformat()
            
            response = self.client.table("emails").update(data).eq("id", email_id).execute()
            return {"success": True, "email": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # LINKEDIN POSTS
    # ============================================
    
    def schedule_post(self, vault_id: str, content: str, 
                      scheduled_for: Optional[datetime] = None,
                      image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Schedule a LinkedIn post.
        
        Args:
            vault_id: Vault ID
            content: Post content
            scheduled_for: When to post
            image_url: Optional image URL
            
        Returns:
            Post data or error
        """
        if not self.user_id:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            data = {
                "vault_id": vault_id,
                "content": content,
                "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
                "image_url": image_url,
                "status": "scheduled" if scheduled_for else "draft"
            }
            
            response = self.client.table("linkedin_posts").insert(data).execute()
            
            # Track usage
            self.track_usage("post_scheduled", 1)
            
            print(f"✓ Post scheduled: {content[:50]}...")
            return {"success": True, "post": response.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_posts(self, vault_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get posts for a vault."""
        if not self.user_id:
            return []
        
        try:
            query = self.client.table("linkedin_posts").select("*").eq("vault_id", vault_id)
            
            if status:
                query = query.eq("status", status)
            
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception:
            return []
    
    # ============================================
    # USAGE TRACKING
    # ============================================
    
    def track_usage(self, usage_type: str, quantity: int = 1):
        """Track usage for billing."""
        if not self.user_id:
            return
        
        try:
            self.client.rpc("track_usage", {
                "p_user_id": self.user_id,
                "p_usage_type": usage_type,
                "p_quantity": quantity
            }).execute()
        except Exception:
            pass  # Don't fail if tracking fails
    
    def check_usage_limit(self, usage_type: str) -> Dict[str, Any]:
        """
        Check if user has exceeded usage limits.
        
        Args:
            usage_type: 'email_sent' or 'post_scheduled'
            
        Returns:
            Usage info with limit check
        """
        if not self.user_id:
            return {"current_usage": 0, "limit_value": 0, "is_exceeded": True}
        
        try:
            response = self.client.rpc("check_usage_limit", {
                "p_user_id": self.user_id,
                "p_usage_type": usage_type
            }).execute()
            
            if response.data:
                return response.data[0]
            
            return {"current_usage": 0, "limit_value": 0, "is_exceeded": False}
            
        except Exception:
            return {"current_usage": 0, "limit_value": 999999, "is_exceeded": False}
    
    def can_send_email(self) -> bool:
        """Check if user can send more emails this month."""
        result = self.check_usage_limit("email_sent")
        return not result.get("is_exceeded", True)
    
    def can_schedule_post(self) -> bool:
        """Check if user can schedule more posts this month."""
        result = self.check_usage_limit("post_scheduled")
        return not result.get("is_exceeded", True)
    
    # ============================================
    # AUDIT LOGGING
    # ============================================
    
    def log_audit(self, action_type: str, resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None, details: Optional[Dict] = None,
                  status: str = "success") -> bool:
        """Log an action for audit trail."""
        if not self.user_id:
            return False
        
        try:
            self.client.table("audit_logs").insert({
                "user_id": self.user_id,
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "status": status
            }).execute()
            return True
        except Exception:
            return False
    
    # ============================================
    # FILE STORAGE (Supabase Storage)
    # ============================================
    
    def upload_file(self, vault_id: str, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """
        Upload file to vault storage.
        
        Args:
            vault_id: Vault ID
            file_path: Path within vault
            file_content: File bytes
            
        Returns:
            Upload result
        """
        if not self.user_id:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            storage_path = f"{vault_id}/{file_path}"
            
            self.client.storage.from_("vaults").upload(
                storage_path,
                file_content,
                {"upsert": "true"}
            )
            
            print(f"✓ File uploaded: {file_path}")
            return {"success": True, "path": storage_path}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_file(self, vault_id: str, file_path: str) -> Optional[bytes]:
        """Download file from vault storage."""
        if not self.user_id:
            return None
        
        try:
            storage_path = f"{vault_id}/{file_path}"
            return self.client.storage.from_("vaults").download(storage_path)
        except Exception:
            return None
    
    def delete_file(self, vault_id: str, file_path: str) -> bool:
        """Delete file from vault storage."""
        try:
            storage_path = f"{vault_id}/{file_path}"
            self.client.storage.from_("vaults").remove([storage_path])
            return True
        except Exception:
            return False


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    # Example usage
    print("AI Employee Pro - Supabase Client Test")
    print("=" * 50)
    
    # Initialize (credentials from environment)
    try:
        supabase = SupabaseClient()
    except ValueError as e:
        print(e)
        print("\nSet environment variables:")
        print("  export SUPABASE_URL=https://your-project.supabase.co")
        print("  export SUPABASE_ANON_KEY=your-anon-key")
        sys.exit(1)
    
    # Sign up new user
    print("\n1. Sign up test user...")
    result = supabase.sign_up(
        email="test@example.com",
        password="SecurePassword123!",
        full_name="Test User"
    )
    print(f"   Result: {result}")
    
    # Sign in
    print("\n2. Sign in...")
    result = supabase.sign_in(
        email="test@example.com",
        password="SecurePassword123!"
    )
    print(f"   Result: {result}")
    
    if result.get("success"):
        # Create vault
        print("\n3. Create vault...")
        result = supabase.create_vault("My First Vault")
        print(f"   Result: {result}")
        
        vault_id = result.get("vault", {}).get("id")
        
        if vault_id:
            # Track email
            print("\n4. Track email...")
            result = supabase.track_email(
                vault_id=vault_id,
                from_address="client@example.com",
                subject="Inquiry about services"
            )
            print(f"   Result: {result}")
            
            # Check usage
            print("\n5. Check usage limits...")
            can_send = supabase.can_send_email()
            print(f"   Can send email: {can_send}")
            
            # Audit log
            print("\n6. Log audit...")
            supabase.log_audit(
                action_type="email_processed",
                resource_type="email",
                status="success"
            )
            print("   ✓ Audit logged")
    
    print("\n" + "=" * 50)
    print("✓ Test complete!")
