#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Brain - AI reasoning engine using Google Gemini API.

Google Gemini provides an excellent FREE tier:
- 60 requests per minute (free)
- 1,500 requests per day (free)
- No credit card required for free tier

Models:
- gemini-1.5-flash: Fast, efficient (Recommended)
- gemini-1.5-pro: More capable
- gemini-2.0-flash-exp: Experimental

Get FREE API key at: https://aistudio.google.com/app/apikey

Usage:
    from gemini_brain import GeminiBrain
    
    brain = GeminiBrain(api_key="your-key")
    response = brain.process_action_file("path/to/action_file.md")
    print(response)
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import google.generativeai as genai
except ImportError:
    print("Error: google-generativeai not installed. Run: pip install google-generativeai")
    sys.exit(1)


class GeminiBrain:
    """
    Google Gemini-based reasoning engine for AI Employee.
    
    Processes files from Needs_Action folder and generates:
    - Action plans
    - Email replies
    - Summaries
    - Task recommendations
    
    FREE Tier Limits:
    - 60 requests/minute
    - 1,500 requests/day
    - No credit card required
    """

    # Available Gemini models (stable production models)
    MODELS = {
        "flash": "gemini-1.5-flash-002",      # Fast & efficient (Recommended)
        "pro": "gemini-1.5-pro-002",          # More capable
        "flash-8b": "gemini-1.5-flash-8b-001", # Even faster
    }
    
    # Fallback models if primary not available
    FALLBACK_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "flash",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Gemini Brain with automatic model fallback.

        Args:
            api_key: Google API key (or set GEMINI_API_KEY env var)
            model: Model to use ("flash", "pro", or "flash-8b")
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        # Setup API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GEMINI_API_KEY env var or pass api_key parameter.\n"
                "Get FREE key at: https://aistudio.google.com/app/apikey"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Resolve model name and find working model
        if model in self.MODELS:
            preferred_model = self.MODELS[model]
        else:
            preferred_model = model

        # Try preferred model first, then fallbacks
        all_models_to_try = [preferred_model] + self.FALLBACK_MODELS
        self.model_name = None
        self.model = None

        for model_name in all_models_to_try:
            try:
                test_model = genai.GenerativeModel(model_name)
                # Quick test to see if model works
                test_model.generate_content("Hi")
                self.model_name = model_name
                self.model = test_model
                break
            except Exception:
                continue

        if not self.model:
            raise ValueError(
                f"No Gemini models available. Tried: {', '.join(all_models_to_try)}\n"
                f"Check your API key at: https://aistudio.google.com/app/apikey"
            )

        self.temperature = temperature
        self.max_tokens = max_tokens

        # System prompt defines the AI Employee's role and behavior
        self.system_prompt = self._get_system_prompt()

        # Generation config
        self.generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=0.95,
        )
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the AI Employee's role.
        """
        return """You are an AI Employee assistant helping manage personal and business tasks.

Your Role:
- Process incoming requests from files (emails, documents, messages)
- Create structured action plans
- Draft professional responses
- Identify items requiring human approval
- Maintain a helpful, professional tone

Operating Rules:
1. Always be polite and professional in communications
2. Flag any payment or financial transaction for human approval
3. Never commit to payments over $100 without approval
4. For unknown contacts, require human review before responding
5. Keep responses concise and actionable
6. If unsure about something, ask for clarification

Output Format:
When processing an action file, structure your response as:

## Analysis
[Brief analysis of the request]

## Suggested Actions
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

## Draft Response (if applicable)
[Draft reply if response is needed]

## Approval Required
[Yes/No - indicate if human approval is needed]

## Category
[Email Reply / Document Processing / Task / Payment / Meeting / Other]"""

    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about current model.
        
        Returns:
            Dictionary with model details
        """
        return {
            "name": self.model_name,
            "provider": "Google",
            "tier": "FREE (with paid options)",
            "limits": "60 req/min, 1,500 req/day"
        }

    def process_action_file(
        self,
        file_path: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an action file from Needs_Action folder.
        
        Args:
            file_path: Path to the action file
            custom_instructions: Additional instructions for this request
            
        Returns:
            Dictionary with analysis, actions, draft response, and approval flag
        """
        # Read action file
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Action file not found: {file_path}")
        
        action_content = file_path.read_text(encoding='utf-8')
        
        # Build the prompt
        user_prompt = self._build_prompt(action_content, custom_instructions)
        
        # Call Gemini API
        response = self._call_gemini(user_prompt)
        
        # Parse the response
        result = self._parse_response(response, action_content)
        
        return result
    
    def process_text(
        self,
        text: str,
        task: str = "Process this request and create an action plan."
    ) -> Dict[str, Any]:
        """
        Process arbitrary text with a specific task.
        
        Args:
            text: Text to process
            task: Task description
            
        Returns:
            Dictionary with analysis and actions
        """
        user_prompt = f"""{self.system_prompt}

{task}

---
Content to process:
{text}
"""
        
        response = self._call_gemini(user_prompt)
        result = self._parse_response(response, text)
        
        return result
    
    def summarize_document(self, text: str) -> str:
        """
        Summarize a document.
        
        Args:
            text: Document text to summarize
            
        Returns:
            Summary string
        """
        prompt = f"""Please summarize the following document in 3-5 bullet points:

---
{text}
---

Summary:"""
        
        response = self._call_gemini(prompt)
        return response.strip()
    
    def draft_email_reply(
        self,
        original_email: str,
        tone: str = "professional",
        additional_context: Optional[str] = None
    ) -> str:
        """
        Draft a reply to an email.
        
        Args:
            original_email: Original email content
            tone: Reply tone (professional, friendly, formal)
            additional_context: Any additional context for the reply
            
        Returns:
            Draft email reply
        """
        context = f"Additional context: {additional_context}\n" if additional_context else ""
        
        prompt = f"""Draft a {tone} email reply to the following message:

---
{original_email}
---

{context}
Guidelines:
- Keep it concise and professional
- Address all points from the original message
- Include appropriate greeting and sign-off
- Do not commit to any payments or sensitive actions

Draft Reply:"""
        
        response = self._call_gemini(prompt)
        return response.strip()
    
    def _build_prompt(
        self,
        action_content: str,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build the complete prompt for Gemini."""
        instructions = custom_instructions or "Process this action file and create a detailed plan."
        
        return f"""{self.system_prompt}

{instructions}

---
Action File Content:
{action_content}
---

Please analyze and provide your response in the specified format."""

    def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API and get response.
        
        Args:
            prompt: User prompt
            
        Returns:
            Model's response text
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return response.text
                
        except Exception as e:
            error_str = str(e)
            
            # Handle common errors
            if "API_KEY" in error_str.upper() or "api key" in error_str.lower():
                raise ValueError(
                    "Invalid or missing API key. Check your GEMINI_API_KEY.\n"
                    "Get FREE key at: https://aistudio.google.com/app/apikey"
                )
            elif "quota" in error_str.lower() or "rate limit" in error_str.lower():
                raise ValueError(
                    "Rate limit exceeded. Gemini free tier: 60 req/min, 1,500 req/day.\n"
                    "Wait a minute or upgrade at: https://ai.google.dev/pricing"
                )
            raise
    
    def _parse_response(
        self,
        response_text: str,
        original_content: str
    ) -> Dict[str, Any]:
        """
        Parse model's response into structured format.
        """
        result = {
            "analysis": "",
            "suggested_actions": [],
            "draft_response": "",
            "approval_required": False,
            "category": "Other",
            "raw_response": response_text,
            "timestamp": datetime.now().isoformat()
        }
        
        # Parse sections from response
        lines = response_text.split('\n')
        
        # Extract analysis
        if '## Analysis' in response_text:
            start = response_text.find('## Analysis') + len('## Analysis')
            end = response_text.find('##', start)
            if end == -1:
                end = len(response_text)
            result['analysis'] = response_text[start:end].strip()
        
        # Extract actions
        if '## Suggested Actions' in response_text:
            start = response_text.find('## Suggested Actions')
            end = response_text.find('##', start + 1)
            if end == -1:
                end = len(response_text)
            actions_section = response_text[start:end]
            
            for line in actions_section.split('\n'):
                line = line.strip()
                if line.startswith('- [ ]') or line.startswith('- [x]') or line.startswith('- '):
                    action = line.lstrip('- ').strip()
                    if action:
                        result['suggested_actions'].append(action)
        
        # Extract draft response
        if '## Draft Response' in response_text:
            start = response_text.find('## Draft Response') + len('## Draft Response')
            end = response_text.find('##', start)
            if end == -1:
                end = len(response_text)
            result['draft_response'] = response_text[start:end].strip()
        
        # Extract approval flag
        if '## Approval Required' in response_text:
            start = response_text.find('## Approval Required') + len('## Approval Required')
            end = response_text.find('\n', start)
            if end == -1:
                end = len(response_text)
            approval_text = response_text[start:end].strip().lower()
            result['approval_required'] = 'yes' in approval_text or 'true' in approval_text
        
        # Extract category
        if '## Category' in response_text:
            start = response_text.find('## Category') + len('## Category')
            end = response_text.find('\n', start)
            if end == -1:
                end = len(response_text)
            result['category'] = response_text[start:end].strip()
        
        # If parsing failed, use raw response
        if not result['analysis'] and not result['suggested_actions']:
            result['analysis'] = "See raw response for details"
        
        return result
    
    def create_plan_file(
        self,
        action_file_path: str,
        output_dir: str,
        custom_instructions: Optional[str] = None
    ) -> Path:
        """
        Process an action file and create a plan file.
        """
        # Process the action file
        result = self.process_action_file(action_file_path, custom_instructions)
        
        # Read original action file for metadata
        action_path = Path(action_file_path)
        action_content = action_path.read_text(encoding='utf-8')
        
        # Extract metadata from frontmatter
        import re
        frontmatter_match = re.search(r'---\n(.*?)\n---', action_content, re.DOTALL)
        metadata = {}
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        # Create plan file content
        timestamp = datetime.now().isoformat()
        plan_name = f"PLAN_{action_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        plan_path = Path(output_dir) / plan_name
        
        # Build actions checklist
        actions_md = '\n'.join([f"- [ ] {action}" for action in result['suggested_actions']])
        if not actions_md:
            actions_md = "- [ ] Review and process request"
        
        plan_content = f"""---
created: {timestamp}
source: {action_path.name}
status: pending
type: {metadata.get('type', 'gemini_processed')}
category: {result['category']}
approval_required: {str(result['approval_required']).lower()}
model: {self.model_name}
---

# Action Plan

## Analysis
{result['analysis']}

## Suggested Actions
{actions_md}

## Draft Response
{result['draft_response'] if result['draft_response'] else '*No draft response needed*'}

## Approval Status
- **Approval Required**: {'Yes' if result['approval_required'] else 'No'}
- **Category**: {result['category']}
- **Model**: Google Gemini ({self.model_name})

## Raw Response
```
{result['raw_response']}
```

---
*Generated by Gemini Brain ({self.model_name})*
"""
        
        # Write plan file
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content, encoding='utf-8')
        
        return plan_path


def main():
    """Test Gemini Brain."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini Brain - AI Employee Reasoning Engine")
    parser.add_argument("prompt", nargs="?", help="Text prompt to process")
    parser.add_argument("--file", "-f", help="Path to action file to process")
    parser.add_argument("--model", default="flash", help="Model: flash, pro, or flash-exp")
    parser.add_argument("--output-dir", help="Output directory for plan file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full response")
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("\n📋 Get your FREE API key at: https://aistudio.google.com/app/apikey")
        print("\nSet it with:")
        print("  set GEMINI_API_KEY=your_key_here  (Windows)")
        print("  export GEMINI_API_KEY=your_key_here  (Linux/Mac)")
        sys.exit(1)
    
    print("🧠 Google Gemini Brain")
    print("=" * 50)
    
    brain = GeminiBrain(api_key=api_key, model=args.model)
    
    model_info = brain.get_model_info()
    print(f"✓ Model: {model_info['name']}")
    print(f"✓ Provider: {model_info['provider']}")
    print(f"✓ Tier: {model_info['tier']}")
    print(f"✓ Limits: {model_info['limits']}")
    print("=" * 50)
    
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
            print("\n🤖 Interactive Mode (type 'quit' to exit)")
            print("-" * 50)
            
            while True:
                user_input = input("\n> ").strip()
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
        
        # Create plan file if output directory specified
        if args.output_dir and args.file:
            plan_path = brain.create_plan_file(args.file, args.output_dir)
            print(f"\n✅ Plan File Created: {plan_path}")
        
        print("\n✅ Success!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
