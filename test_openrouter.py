#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OpenRouter Brain - Quick test script for OpenRouter AI integration.

FREE API - Multiple models including Qwen!

Usage:
    python test_openrouter.py "Summarize this: The quick brown fox jumps over the lazy dog"
    python test_openrouter.py --file AI_Employee_Vault/Needs_Action/FILE_test_document.md
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
    
    parser = argparse.ArgumentParser(description="Test OpenRouter Brain (FREE API)")
    parser.add_argument("prompt", nargs="?", help="Text prompt to process")
    parser.add_argument("--file", "-f", help="Path to file to process")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument("--list-models", action="store_true", help="Show available models")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full response")
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not set")
        print("\n📋 Get your FREE API key from: https://openrouter.ai/keys")
        print("\nSet it with:")
        print("  set OPENROUTER_API_KEY=your_key  (Windows)")
        print("  export OPENROUTER_API_KEY=your_key  (Linux/Mac)")
        sys.exit(1)
    
    print("🧠 OpenRouter Brain (FREE API)")
    print("=" * 60)
    print("✓ API Key found")
    
    # Import OpenRouter Brain
    try:
        from openrouter_brain import OpenRouterBrain
    except ImportError as e:
        print(f"❌ Error importing OpenRouterBrain: {e}")
        print("Run: pip install openai")
        sys.exit(1)
    
    # Initialize
    brain = OpenRouterBrain(api_key=api_key, model=args.model)
    print(f"✓ Model: {brain.model}")
    print("=" * 60)
    
    # List models if requested
    if args.list_models:
        models = brain.list_models()
        print("\n🆓 FREE Models:")
        for m in models['free']:
            marker = " <-- CURRENT" if m == models['current'] else ""
            print(f"  • {m}{marker}")
        print("\n💰 Paid Models (very cheap):")
        for m in models['paid'][:5]:
            marker = " <-- CURRENT" if m == models['current'] else ""
            print(f"  • {m}{marker}")
        return
    
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
            print("\n🤖 Interactive Mode")
            print("Type your message (or 'quit' to exit):\n")
            
            while True:
                user_input = input("> ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
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
        
        print("\n✅ Success!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "API_KEY" in str(e).upper():
            print("\n💡 Hint: Check your OPENROUTER_API_KEY is valid")
            print("Get FREE key at: https://openrouter.ai/keys")
        elif "insufficient_quota" in str(e).lower():
            print("\n💡 Free tier may be exhausted.")
            print("   Try:")
            print("   1. Wait for daily reset")
            print("   2. Add $1 credit at: https://openrouter.ai/credits")
            print("   3. Try a different free model")
        sys.exit(1)


if __name__ == "__main__":
    main()
