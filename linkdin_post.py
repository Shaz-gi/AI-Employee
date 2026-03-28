#!/usr/bin/env python3
"""
LinkedIn Poster - Easy Command Line Interface

Usage:
    python linkdin_post.py login          # Test login
    python linkdin_post.py post "Text"    # Post text
    python linkdin_post.py file post.txt  # Post from file
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from linkedin_auto_post import LinkedInAutoPoster

def main():
    if len(sys.argv) < 2:
        print("🤖 LinkedIn Poster")
        print("=" * 50)
        print("\nUsage:")
        print("  python linkdin_post.py login              # Test login")
        print("  python linkdin_post.py post \"Your text\"   # Post text")
        print("  python linkdin_post.py file post.txt      # Post from file")
        print("\nOr use the Web UI (easiest):")
        print("  http://localhost:5000 → LinkedIn tab")
        return
    
    command = sys.argv[1].lower()
    poster = LinkedInAutoPoster()
    
    if command == 'login':
        print("🔗 Testing LinkedIn login...")
        if poster.login():
            print("\n✅ Login successful! Session saved.")
        else:
            print("\n❌ Login failed")
        poster.close()
        
    elif command == 'post':
        if len(sys.argv) < 3:
            print("❌ Error: Post content required")
            print("Usage: python linkdin_post.py post \"Your text\"")
            return
        
        content = ' '.join(sys.argv[2:])
        print(f"📝 Posting to LinkedIn ({len(content)} chars)...")
        
        if poster.login():
            result = poster.post(content)
            if result.get('success'):
                print("\n✅ POSTED SUCCESSFULLY!")
                print(f"Content: {result.get('content')}")
            else:
                print(f"\n❌ Post failed: {result.get('error')}")
        else:
            print("\n❌ Login failed")
        poster.close()
        
    elif command == 'file':
        if len(sys.argv) < 3:
            print("❌ Error: File path required")
            return
        
        file_path = sys.argv[2]
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return
        
        content = Path(file_path).read_text(encoding='utf-8')
        print(f"📝 Posting from file: {file_path}")
        
        if poster.login():
            result = poster.post(content)
            if result.get('success'):
                print("\n✅ POSTED SUCCESSFULLY!")
            else:
                print(f"\n❌ Post failed: {result.get('error')}")
        else:
            print("\n❌ Login failed")
        poster.close()
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Use: login, post, or file")

if __name__ == "__main__":
    main()
