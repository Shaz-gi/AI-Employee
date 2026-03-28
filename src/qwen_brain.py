#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen Brain - AI reasoning engine using Qwen models via DashScope API.

This module replaces Claude Code as the reasoning engine for the AI Employee.
It processes action files, creates plans, and generates responses.

Supported Models:
- qwen-max: Best for complex reasoning
- qwen-plus: Balanced performance and cost
- qwen-turbo: Fast and cost-effective

Usage:
    from qwen_brain import QwenBrain
    
    brain = QwenBrain(api_key="your-key")
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
    import dashscope
    from dashscope import Generation
except ImportError:
    print("Error: dashscope not installed. Run: pip install dashscope")
    sys.exit(1)


class QwenBrain:
    """
    Qwen-based reasoning engine for AI Employee.
    
    Processes files from Needs_Action folder and generates:
    - Action plans
    - Email replies
    - Summaries
    - Task recommendations
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Qwen Brain.
        
        Args:
            api_key: DashScope API key (or set DASHSCOPE_API_KEY env var)
            model: Qwen model to use (qwen-max, qwen-plus, qwen-turbo)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        # Setup API key
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set DASHSCOPE_API_KEY env var or pass api_key parameter.\n"
                "Get your key at: https://dashscope.console.aliyun.com/"
            )
        
        dashscope.api_key = self.api_key
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # System prompt defines the AI Employee's role and behavior
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the AI Employee's role.
        
        This prompt establishes the persona and operating rules.
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
        
        # Call Qwen API
        response = self._call_qwen(user_prompt)
        
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
        
        response = self._call_qwen(user_prompt)
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
        
        response = self._call_qwen(prompt)
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
        
        response = self._call_qwen(prompt)
        return response.strip()
    
    def _build_prompt(
        self,
        action_content: str,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build the complete prompt for Qwen."""
        instructions = custom_instructions or "Process this action file and create a detailed plan."
        
        return f"""{self.system_prompt}

{instructions}

---
Action File Content:
{action_content}
---

Please analyze and provide your response in the specified format."""

    def _call_qwen(self, prompt: str) -> str:
        """
        Call Qwen API and get response.
        
        Args:
            prompt: User prompt
            
        Returns:
            Qwen's response text
        """
        try:
            response = Generation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                error_msg = f"Qwen API error: {response.code} - {response.message}"
                raise Exception(error_msg)
                
        except Exception as e:
            # Fallback for common errors
            if "API_KEY" in str(e).upper():
                raise ValueError(
                    "Invalid or missing API key. Check your DASHSCOPE_API_KEY.\n"
                    "Get your key at: https://dashscope.console.aliyun.com/"
                )
            raise
    
    def _parse_response(
        self,
        response_text: str,
        original_content: str
    ) -> Dict[str, Any]:
        """
        Parse Qwen's response into structured format.
        
        Args:
            response_text: Raw response from Qwen
            original_content: Original action file content
            
        Returns:
            Structured result dictionary
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
        current_section = None
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if line_lower.startswith('## analysis'):
                current_section = 'analysis'
                current_content = []
            elif line_lower.startswith('## suggested actions'):
                current_section = 'actions'
                current_content = []
            elif line_lower.startswith('## draft response'):
                current_section = 'draft'
                current_content = []
            elif line_lower.startswith('## approval required'):
                current_section = 'approval'
                current_content = []
            elif line_lower.startswith('## category'):
                current_section = 'category'
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Extract analysis
        if 'analysis' in result or current_section == 'analysis':
            # Find analysis in raw response
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
            result['raw_response'] = response_text
        
        return result
    
    def create_plan_file(
        self,
        action_file_path: str,
        output_dir: str,
        custom_instructions: Optional[str] = None
    ) -> Path:
        """
        Process an action file and create a plan file.
        
        Args:
            action_file_path: Path to action file in Needs_Action
            output_dir: Directory to write plan file (Plans/)
            custom_instructions: Optional additional instructions
            
        Returns:
            Path to created plan file
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
type: {metadata.get('type', 'qwen_processed')}
category: {result['category']}
approval_required: {str(result['approval_required']).lower()}
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

## Raw Qwen Response
```
{result['raw_response']}
```

---
*Generated by Qwen Brain ({self.model})*
"""
        
        # Write plan file
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content, encoding='utf-8')
        
        return plan_path


def main():
    """Test Qwen Brain with a sample action file."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwen Brain - AI Employee Reasoning Engine")
    parser.add_argument("action_file", help="Path to action file to process")
    parser.add_argument("--model", default="qwen-plus", help="Qwen model to use")
    parser.add_argument("--output-dir", help="Output directory for plan file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full response")
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("Error: DASHSCOPE_API_KEY environment variable not set")
        print("Get your API key at: https://dashscope.console.aliyun.com/")
        print("\nSet it with:")
        print("  set DASHSCOPE_API_KEY=your_key_here  (Windows)")
        print("  export DASHSCOPE_API_KEY=your_key_here  (Linux/Mac)")
        sys.exit(1)
    
    print(f"Processing: {args.action_file}")
    print(f"Model: {args.model}")
    print("-" * 50)
    
    brain = QwenBrain(api_key=api_key, model=args.model)
    
    try:
        result = brain.process_action_file(args.action_file)
        
        print(f"\n## Analysis")
        print(result['analysis'])
        
        print(f"\n## Suggested Actions")
        for action in result['suggested_actions']:
            print(f"  - [ ] {action}")
        
        if result['draft_response']:
            print(f"\n## Draft Response")
            print(result['draft_response'])
        
        print(f"\n## Approval Required: {'Yes' if result['approval_required'] else 'No'}")
        print(f"## Category: {result['category']}")
        
        if args.verbose:
            print(f"\n## Raw Response")
            print(result['raw_response'])
        
        # Create plan file if output directory specified
        if args.output_dir:
            plan_path = brain.create_plan_file(args.action_file, args.output_dir)
            print(f"\n## Plan File Created: {plan_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
