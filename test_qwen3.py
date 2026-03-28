#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Qwen3 4B on OpenRouter

This script tests your specific Qwen3 4B (free) model on OpenRouter.

Usage:
    python test_qwen3.py "Hello Qwen!"
    python test_qwen3.py --file AI_Employee_Vault/Needs_Action/FILE_test.md
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Qwen3 4B on OpenRouter")
    parser.add_argument("prompt", nargs="?", help="Text prompt to process")
    parser.add_argument("--file", "-f", help="Path to file to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full response")
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not set in .env")
        print("\n📝 Edit .env file and add your OpenRouter API key:")
        print("   OPENROUTER_API_KEY=sk-or-v1-your_key_here")
        print("\n🔑 Get FREE key at: https://openrouter.ai/keys")
        sys.exit(1)
    
    print("🧠 Qwen3 4B Test (OpenRouter)")
    print("=" * 60)
    print(f"✓ API Key found")
    print(f"✓ Model: qwen/qwen-3-4b")
    print("=" * 60)
    
    # Import OpenRouter Brain
    try:
        from openrouter_brain import OpenRouterBrain
    except ImportError as e:
        print(f"❌ Error importing OpenRouterBrain: {e}")
        print("Run: pip install openai")
        sys.exit(1)
    
    # Initialize with Qwen3 4B
    try:
        brain = OpenRouterBrain(
            api_key=api_key,
            model="qwen/qwen-3-4b"
        )
        print(f"✓ Connected to OpenRouter")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        sys.exit(1)
    
    try:
        if args.file:
            # Process file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)
            
            print(f"\n📄 Processing file: {file_path.name}")
            result = brain.process_action_file(str(file_path))
            
        elif args.prompt:
            # Process text prompt
            print(f"\n💬 Processing: {args.prompt}")
            result = brain.process_text(args.prompt)
            
        else:
            # Interactive mode
            print("\n🤖 Interactive Mode - Qwen3 4B")
            print("Type your message (or 'quit' to exit):\n")
            
            while True:
                user_input = input("> ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                try:
                    result = brain.process_text(user_input)
                    print(f"\n📋 Analysis: {result['analysis']}")
                    print(f"\n📝 Suggested Actions:")
                    for action in result['suggested_actions']:
                        print(f"  - [ ] {action}")
                    if result['draft_response']:
                        print(f"\n💬 Draft Response:")
                        print(f"  {result['draft_response']}")
                    print(f"\n⚠️  Approval Required: {'Yes' if result['approval_required'] else 'No'}")
                    print(f"📁 Category: {result['category']}")
                    print("-" * 60)
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            return
        
        # Display result
        print(f"\n📋 Analysis:")
        print(result['analysis'])
        
        print(f"\n📝 Suggested Actions:")
        for action in result['suggested_actions']:
            print(f"  - [ ] {action}")
        
        if result['draft_response']:
            print(f"\n💬 Draft Response:")
            print(result['draft_response'])
        
        print(f"\n⚠️  Approval Required: {'Yes' if result['approval_required'] else 'No'}")
        print(f"📁 Category: {result['category']}")
        
        if args.verbose:
            print(f"\n📄 Raw Response:")
            print(result['raw_response'])
        
        print("\n✅ Success! Qwen3 4B is working!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {e}")
        
        if "404" in error_msg or "No endpoints found" in error_msg:
            print("\n" + "=" * 60)
            print("⚠️  Model Endpoint Issue")
            print("=" * 60)
            print("\nThe model 'qwen/qwen-3-4b' was not found.")
            print("\n💡 Try these steps:")
            print("   1. Check available models on OpenRouter:")
            print("      https://openrouter.ai/models")
            print("   2. Search for 'Qwen' models")
            print("   3. Copy the exact model ID")
            print("   4. Update .env file:")
            print("      OPENROUTER_MODEL=qwen/qwen-3-4b")
            print("\n📝 Alternative Qwen models to try:")
            print("   - qwen/qwen-2.5-7b-instruct:free")
            print("   - qwen/qwen-2-7b-instruct:free")
            print("   - qwen/qwen-max (paid)")
            print("   - qwen/qwen-plus (paid)")
        elif "API_KEY" in error_msg.upper() or "authentication" in error_msg.lower():
            print("\n💡 Hint: Check your OPENROUTER_API_KEY is valid")
            print("Get FREE key at: https://openrouter.ai/keys")
        elif "insufficient_quota" in error_msg.lower():
            print("\n💡 Free tier may be exhausted.")
            print("   Try:")
            print("   1. Wait for daily reset (midnight UTC)")
            print("   2. Add $1 credit at: https://openrouter.ai/credits")
            print("   3. Try a different Qwen model")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
