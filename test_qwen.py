#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Qwen Brain - Quick test script for Qwen AI integration.

Usage:
    python test_qwen.py "Summarize this: The quick brown fox jumps over the lazy dog"
    python test_qwen.py --file AI_Employee_Vault/Needs_Action/FILE_test_document.md
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
    
    parser = argparse.ArgumentParser(description="Test Qwen Brain")
    parser.add_argument("prompt", nargs="?", help="Text prompt to process")
    parser.add_argument("--file", "-f", help="Path to file to process")
    parser.add_argument("--model", default="qwen-plus", help="Qwen model")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full response")
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ Error: DASHSCOPE_API_KEY not set")
        print("\nGet your API key from: https://dashscope.console.aliyun.com/")
        print("\nSet it with:")
        print("  set DASHSCOPE_API_KEY=your_key  (Windows)")
        print("  export DASHSCOPE_API_KEY=your_key  (Linux/Mac)")
        sys.exit(1)
    
    print(f"✓ API Key found")
    print(f"✓ Model: {args.model}")
    print("-" * 50)
    
    # Import Qwen Brain
    try:
        from qwen_brain import QwenBrain
    except ImportError as e:
        print(f"❌ Error importing QwenBrain: {e}")
        print("Run: pip install dashscope")
        sys.exit(1)
    
    # Initialize
    brain = QwenBrain(api_key=api_key, model=args.model)
    
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
            print(f"\n💬 Processing prompt...")
            result = brain.process_text(args.prompt)
            
        else:
            # Interactive mode
            print("\n🤖 Qwen Brain Interactive Mode")
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
                print("-" * 50)
            
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
        
        print("\n✓ Success!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "API_KEY" in str(e).upper():
            print("\n💡 Hint: Check your DASHSCOPE_API_KEY is valid")
        sys.exit(1)


if __name__ == "__main__":
    main()
