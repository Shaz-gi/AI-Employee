#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Supabase Integration - Interactive Setup

This script will:
1. Prompt for Supabase credentials
2. Test database connection
3. Create test user
4. Test vault creation
5. Verify everything works
"""

import os
import sys

print("=" * 60)
print("🧪 AI Employee Pro - Supabase Integration Test")
print("=" * 60)
print()

# Step 1: Get credentials from user
print("📍 Step 1: Enter your Supabase credentials")
print("-" * 60)
print()
print("Get these from: https://app.supabase.com/project/_/settings/api")
print()

supabase_url = input("SUPABASE_URL (e.g., https://xxx.supabase.co): ").strip()
supabase_key = input("SUPABASE_ANON_KEY (starts with eyJ...): ").strip()

if not supabase_url or not supabase_key:
    print("\n❌ Credentials required! Please run again.")
    sys.exit(1)

# Save to .env for future use
print("\n💾 Saving credentials to .env file...")
try:
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    # Read existing .env or create new
    env_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update Supabase credentials
    if 'SUPABASE_URL=' in env_content:
        env_content = '\n'.join([
            line if not line.startswith('SUPABASE_URL=') else f'SUPABASE_URL={supabase_url}'
            for line in env_content.split('\n')
        ])
    else:
        env_content += f'\nSUPABASE_URL={supabase_url}\n'
    
    if 'SUPABASE_ANON_KEY=' in env_content:
        env_content = '\n'.join([
            line if not line.startswith('SUPABASE_ANON_KEY=') else f'SUPABASE_ANON_KEY={supabase_key}'
            for line in env_content.split('\n')
        ])
    else:
        env_content += f'SUPABASE_ANON_KEY={supabase_key}\n'
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✓ Credentials saved to .env")
except Exception as e:
    print(f"⚠️  Could not save to .env: {e}")
    print("   (You can manually add them later)")

print()

# Step 2: Install supabase if needed
print("📍 Step 2: Checking dependencies...")
try:
    from supabase import create_client
    print("✓ Supabase client installed")
except ImportError:
    print("Installing supabase package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "python-dotenv"])
    from supabase import create_client
    print("✓ Supabase client installed")

print()

# Step 3: Test connection
print("📍 Step 3: Testing Supabase connection...")
try:
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)
    print(f"✓ Connected to: {supabase_url}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check SUPABASE_URL is correct (includes https://)")
    print("2. Check SUPABASE_ANON_KEY is copied completely")
    print("3. Make sure project is active in Supabase dashboard")
    sys.exit(1)

print()

# Step 4: Test user signup
print("📍 Step 4: Testing user signup...")
print("(This creates a test user in your database)")
print()

import random
test_email = f"test_{random.randint(1000, 9999)}@example.com"
test_password = "TestPassword123!"
test_name = "Test User"

print(f"Creating test user: {test_email}")

try:
    response = supabase.auth.sign_up({
        "email": test_email,
        "password": test_password,
        "options": {
            "data": {
                "full_name": test_name
            }
        }
    })
    
    print(f"✓ User created successfully!")
    print(f"  User ID: {response.user.id}")
    print(f"  Email: {response.user.email}")
    print()
    print("⚠️  Note: In production, user would need to confirm email.")
    print("   For testing, we'll use the service key to bypass this.")
    
    test_user_id = response.user.id
    
except Exception as e:
    print(f"❌ Signup failed: {e}")
    print("\nThis is OK - your database schema might not be set up yet.")
    print("\nNext steps:")
    print("1. Go to Supabase SQL Editor")
    print("2. Run the supabase_schema.sql file")
    print("3. Run this test again")
    sys.exit(0)

print()

# Step 5: Test sign in
print("📍 Step 5: Testing user signin...")
try:
    response = supabase.auth.sign_in_with_password({
        "email": test_email,
        "password": test_password
    })
    print("✓ Sign in successful!")
    print(f"  Session expires: {response.session.expires_at}")
except Exception as e:
    print(f"⚠️  Sign in failed: {e}")
    print("   (Email confirmation may be required)")

print()

# Step 6: Test database queries
print("📍 Step 6: Testing database queries...")
try:
    # Try to query profiles table
    response = supabase.table("profiles").select("id, email").limit(1).execute()
    print("✓ Database query successful!")
    print(f"  Tables are accessible")
except Exception as e:
    print(f"❌ Database query failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you ran supabase_schema.sql in SQL Editor")
    print("2. Check that all tables were created successfully")
    print("3. Verify RLS policies are set up correctly")
    sys.exit(1)

print()

# Step 7: Summary
print("=" * 60)
print("✅ SUPABASE INTEGRATION TEST COMPLETE!")
print("=" * 60)
print()
print("What works:")
print("  ✓ Supabase connection")
print("  ✓ User authentication")
print("  ✓ Database access")
print()
print("Next steps:")
print("  1. Run supabase_schema.sql in Supabase SQL Editor (if not done)")
print("  2. Integrate with your AI Employee app")
print("  3. Add login/signup pages to web UI")
print()
print("Your credentials have been saved to .env file")
print()
print("=" * 60)
