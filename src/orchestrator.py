#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for AI Employee.

The Orchestrator is the central coordination component that:
1. Manages watcher processes
2. Triggers Qwen Brain for reasoning tasks
3. Handles folder watching for approval workflows
4. Updates the Dashboard with current status
5. Coordinates the Perception → Reasoning → Action cycle

Usage:
    python orchestrator.py /path/to/vault
    python orchestrator.py /path/to/vault --dry-run
"""

import sys
import os
import json
import time
import signal
import subprocess
import shutil  # Added for file operations
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class Orchestrator:
    """
    Master orchestrator for the AI Employee system.

    Coordinates all components:
    - Watchers (Perception layer)
    - Qwen Brain (Reasoning layer)
    - MCP Servers (Action layer)
    - Dashboard updates
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 30,
        dry_run: bool = False,
        log_level: str = "INFO"
    ):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between orchestration cycles
            dry_run: Enable dry run mode (no external actions)
            log_level: Logging level
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.dry_run = dry_run

        # Core folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.accounting = self.vault_path / 'Accounting'
        self.dashboard_file = self.vault_path / 'Dashboard.md'

        # Ensure directories exist
        self._ensure_directories()

        # Setup logging
        self.logger = self._setup_logging(log_level)

        # Initialize AI Brain (OpenRouter)
        self.ai_brain = self._init_ai_brain()

        # Process tracking
        self.watcher_processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
        # Statistics
        self.stats = {
            'cycles': 0,
            'files_processed': 0,
            'plans_created': 0,
            'approvals_pending': 0,
            'actions_executed': 0,
            'errors': 0,
            'start_time': None
        }
        
        self.logger.info(f"Orchestrator initialized for vault: {vault_path}")
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.needs_action,
            self.plans,
            self.pending_approval,
            self.approved,
            self.done,
            self.logs,
            self.accounting
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self, log_level: str) -> Any:
        """Setup logging configuration."""
        import logging
        
        logger = logging.getLogger("Orchestrator")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = self.logs / f"orchestrator_{today}.log"
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not create log file: {e}")
        
        return logger

    def _init_ai_brain(self):
        """
        Initialize OpenRouter Brain reasoning engine.
        
        Returns:
            OpenRouterBrain instance or None if API key not configured
        """
        try:
            # Load environment variables from .env file
            from dotenv import load_dotenv
            load_dotenv()

            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                self.logger.warning("OPENROUTER_API_KEY not set - OpenRouter Brain disabled")
                return None

            from openrouter_brain import OpenRouterBrain

            model = os.getenv("OPENROUTER_MODEL", "")
            brain = OpenRouterBrain(api_key=api_key, model=model)
            self.logger.info(f"OpenRouter Brain initialized ({brain.model})")
            return brain

        except ImportError as e:
            self.logger.warning(f"OpenRouter Brain not available: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"OpenRouter Brain initialization failed: {e}")
            return None
    
    def _log_audit(self, action: str, details: dict):
        """Write an audit log entry."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action,
            "actor": "orchestrator",
            "result": "success",
            **details
        }
        
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f"{today}.json"
        
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(audit_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
    
    def _count_files(self, folder: Path) -> int:
        """Count .md files in a folder."""
        try:
            return len(list(folder.glob('*.md')))
        except Exception:
            return 0
    
    def update_dashboard(self):
        """
        Update the Dashboard.md with current status.

        This provides real-time visibility into system state.
        """
        try:
            # Count files in each folder
            inbox_count = self._count_files(self.vault_path / 'Inbox')
            needs_action_count = self._count_files(self.needs_action)
            pending_approval_count = self._count_files(self.pending_approval)
            approved_count = self._count_files(self.approved)
            done_count = self._count_files(self.done)

            # Calculate uptime
            uptime = ""
            if self.stats['start_time']:
                delta = datetime.now() - self.stats['start_time']
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime = f"{hours}h {minutes}m {seconds}s"

            timestamp = datetime.now().isoformat()
            status_icon = "🟢 Running" if self.running else "🟡 Idle"

            # Read current dashboard (with explicit UTF-8 encoding for Windows)
            if self.dashboard_file.exists():
                with open(self.dashboard_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = "# AI Employee Dashboard\n\n"

            # Update specific lines using regex
            import re

            # Update Executive Summary table
            content = re.sub(
                r'\| Pending Actions \|.*\| Items in Needs_Action \|',
                f'| Pending Actions | {needs_action_count} | Items in Needs_Action |',
                content
            )
            content = re.sub(
                r'\| Pending Approvals \|.*\| Awaiting human review \|',
                f'| Pending Approvals | {pending_approval_count} | Awaiting human review |',
                content
            )
            content = re.sub(
                r'\| Tasks Completed Today \|.*\| Moved to /Done \|',
                f'| Tasks Completed Today | {done_count} | Moved to /Done |',
                content
            )

            # Update System Health section
            content = re.sub(
                r'\| Orchestrator \|.*\| - \|',
                f'| Orchestrator | {status_icon} | - |',
                content
            )

            # Update last updated timestamp if present
            content = re.sub(
                r'\*Last updated:.*\*',
                f'*Last updated: {timestamp}*',
                content
            )

            # Write updated dashboard (with explicit UTF-8 encoding for Windows)
            with open(self.dashboard_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.debug("Dashboard updated")

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")
            self.stats['errors'] += 1
    
    def process_needs_action(self):
        """
        Process files in the Needs_Action folder.

        For each file, trigger AI Brain to:
        1. Read the file
        2. Create a plan in /Plans
        3. If approval required, create file in /Pending_Approval
        4. Move processed file to /Done
        """
        try:
            files = list(self.needs_action.glob('*.md'))

            for file_path in files:
                self.logger.info(f"Processing: {file_path.name}")

                # Create a plan file using AI Brain
                plan_path = self._create_plan(file_path)

                if plan_path:
                    self.stats['plans_created'] += 1
                    self.stats['files_processed'] += 1

                    # Check if plan requires approval
                    plan_content = Path(plan_path).read_text(encoding='utf-8')
                    
                    # Check for approval_required in plan metadata
                    import re
                    frontmatter_match = re.search(r'---\n(.*?)\n---', plan_content, re.DOTALL)
                    requires_approval = False
                    category = "Other"
                    draft_response = ""
                    
                    if frontmatter_match:
                        frontmatter = frontmatter_match.group(1)
                        for line in frontmatter.split('\n'):
                            if 'approval_required' in line.lower():
                                requires_approval = 'true' in line.lower()
                            if 'category:' in line.lower():
                                category = line.split(':', 1)[1].strip()
                    
                    # Extract draft response from plan body
                    if '## Draft Response' in plan_content:
                        start = plan_content.find('## Draft Response') + len('## Draft Response')
                        end = plan_content.find('##', start)
                        if end == -1:
                            end = len(plan_content)
                        draft_response = plan_content[start:end].strip()

                    # If approval required OR if there's a draft response (email reply), create approval file
                    if requires_approval or (draft_response and draft_response.strip() and draft_response.strip() != '*No draft response needed*' and 'No draft response' not in draft_response):
                        self._create_approval_file(plan_path, file_path)
                        self.logger.info(f"Created approval request: {file_path.name}")

                    # Move action file to Done
                    dest = self.done / file_path.name
                    try:
                        file_path.rename(dest)
                        self.logger.info(f"Moved {file_path.name} to Done")
                    except Exception as e:
                        self.logger.warning(f"Could not move file to Done: {e}")

                    # Log audit
                    self._log_audit("needs_action_processed", {
                        "file": file_path.name,
                        "plan_created": str(plan_path),
                        "approval_required": requires_approval,
                        "category": category
                    })

        except Exception as e:
            self.logger.error(f"Error processing Needs_Action: {e}")
            self.stats['errors'] += 1
    
    def _create_plan(self, action_file: Path) -> Optional[str]:
        """
        Create a plan file for an action item using Qwen Brain.

        Args:
            action_file: Path to the action file

        Returns:
            Path to created plan file, or None
        """
        try:
    
            if self.ai_brain:
                try:
                    plan_path = self.ai_brain.create_plan_file(
                        str(action_file),
                        str(self.plans)
                    )
                    self.logger.info(f"Created plan with OpenRouter Brain: {plan_path.name}")
                    return str(plan_path)
                except Exception as e:
                    self.logger.warning(f"OpenRouter Brain failed, using fallback: {e}")
                    # Fall through to basic plan creation

            # Fallback: Create basic plan template
            content = action_file.read_text(encoding='utf-8')

            # Extract metadata from frontmatter
            import re
            frontmatter_match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)

            metadata = {}
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

            # Create plan
            timestamp = datetime.now().isoformat()
            plan_name = f"PLAN_{action_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            plan_path = self.plans / plan_name

            plan_content = f"""---
created: {timestamp}
source: {action_file.name}
status: pending
type: {metadata.get('type', 'unknown')}
---

# Action Plan

## Source
- **File**: `{action_file.name}`
- **Type**: {metadata.get('type', 'unknown')}
- **Priority**: {metadata.get('priority', 'medium')}

## Objective
*Define the main objective here*

## Steps
- [ ] Review source file
- [ ] Identify required actions
- [ ] Execute actions (requires approval if sensitive)
- [ ] Move to /Done when complete

## Notes
*Add notes during processing*

## Completion
- [ ] All actions completed
- [ ] Files archived appropriately
- [ ] Dashboard updated

---
*Created by Orchestrator (Qwen Brain unavailable)*
"""

            plan_path.write_text(plan_content, encoding='utf-8')
            self.logger.info(f"Created plan (fallback): {plan_name}")

            return str(plan_path)

        except Exception as e:
            self.logger.error(f"Failed to create plan: {e}")
            return None

    def _create_approval_file(self, plan_path: str, original_action_file: Path):
        """
        Create an approval request file in Pending_Approval folder.

        Args:
            plan_path: Path to the plan file
            original_action_file: Path to the original action file
        """
        try:
            plan_content = Path(plan_path).read_text(encoding='utf-8')
            
            # Extract info from plan
            import re
            frontmatter_match = re.search(r'---\n(.*?)\n---', plan_content, re.DOTALL)
            
            metadata = {}
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

            # Extract analysis and draft response from plan
            analysis = ""
            draft_response = ""
            actions = []
            
            if '## Analysis' in plan_content:
                start = plan_content.find('## Analysis') + len('## Analysis')
                end = plan_content.find('##', start)
                if end == -1:
                    end = len(plan_content)
                analysis = plan_content[start:end].strip()

            if '## Draft Response' in plan_content:
                start = plan_content.find('## Draft Response') + len('## Draft Response')
                end = plan_content.find('##', start)
                if end == -1:
                    end = len(plan_content)
                draft_response = plan_content[start:end].strip()

            if '## Suggested Actions' in plan_content:
                start = plan_content.find('## Suggested Actions')
                end = plan_content.find('##', start)
                if end == -1:
                    end = len(plan_content)
                actions_section = plan_content[start:end]
                for line in actions_section.split('\n'):
                    line = line.strip()
                    if line.startswith('- [ ]') or line.startswith('- [x]'):
                        actions.append(line)

            # Create approval file
            timestamp = datetime.now().isoformat()
            approval_name = f"APPROVAL_{original_action_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            approval_path = self.pending_approval / approval_name

            approval_content = f"""---
created: {timestamp}
source: {original_action_file.name}
plan: {Path(plan_path).name}
type: {metadata.get('type', 'ai_processed')}
category: {metadata.get('category', 'General')}
status: pending_approval
---

# Approval Required

## Summary
{analysis if analysis else 'AI has processed this request and requires human approval before proceeding.'}

## Proposed Actions
{chr(10).join(actions) if actions else '- [ ] Review and execute proposed actions'}

## Draft Response
{draft_response if draft_response else '*No draft response generated*'}

## To Approve
1. Review the plan above
2. If approved, move this file to `/Approved` folder
3. The system will execute the actions automatically

## To Reject
1. Move this file to `/Rejected` folder
2. Add a note explaining why

---
*Created by AI Employee - Requires Human Approval*
"""

            approval_path.write_text(approval_content, encoding='utf-8')
            self.logger.debug(f"Created approval file: {approval_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create approval file: {e}")

    def process_approved(self):
        """
        Process files in the Approved folder.

        These are actions that have received human approval
        and are ready for execution.

        Silver Tier: Actually sends emails via Email MCP!
        """
        try:
            files = list(self.approved.glob('*.md'))

            for file_path in files:
                self.logger.info(f"Executing approved action: {file_path.name}")

                # Read approval file
                content = file_path.read_text(encoding='utf-8')
                
                # Extract metadata
                import re
                metadata = {}
                if '---' in content:
                    parts = content.split('---')
                    if len(parts) > 1:
                        frontmatter = parts[1]
                        for line in frontmatter.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                metadata[key.strip()] = value.strip()
                
                # Extract draft response
                draft_response = ''
                if '## Draft Response' in content:
                    start = content.find('## Draft Response') + len('## Draft Response')
                    end = content.find('##', start)
                    if end == -1:
                        end = len(content)
                    draft_response = content[start:end].strip()
                
                # Check if this is an email approval
                action_type = metadata.get('type', '').lower()
                
                if 'email' in action_type and draft_response:
                    # Try to extract recipient from multiple sources
                    original_to = metadata.get('to', '')
                    
                    # If not in metadata, try to extract from Summary section
                    if not original_to and '## Summary' in content:
                        # Extract from Summary - look for email patterns
                        summary_start = content.find('## Summary')
                        summary_end = content.find('##', summary_start + 1)
                        if summary_end == -1:
                            summary_end = len(content)
                        summary_text = content[summary_start:summary_end]
                        
                        # Look for email pattern in summary
                        import re
                        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
                        emails_found = re.findall(email_pattern, summary_text)
                        if emails_found:
                            original_to = emails_found[0]  # Use first email found
                    
                    # Still empty? Try from original email action file
                    if not original_to:
                        # Look for original email file reference
                        source_file = metadata.get('source', '')
                        if source_file:
                            original_email_path = self.needs_action / source_file
                            if not original_email_path.exists():
                                # Try in Done folder
                                original_email_path = self.done / source_file
                            
                            if original_email_path.exists():
                                email_content = original_email_path.read_text(encoding='utf-8')
                                # Extract from the email's "from" field (this is who we're replying to)
                                if 'from:' in email_content.lower():
                                    for line in email_content.split('\n'):
                                        if line.lower().startswith('from:'):
                                            original_to = line.split(':', 1)[1].strip()
                                            # Extract just the email address
                                            if '<' in original_to and '>' in original_to:
                                                original_to = original_to.split('<')[1].split('>')[0]
                                            break
                    
                    subject = metadata.get('subject', 'Re: Your Email')
                    
                    # If still no recipient, skip
                    if not original_to:
                        self.logger.warning("No recipient found, skipping email")
                        completion_note = """
---
## Execution
- **Status**: SKIPPED - No recipient found
- **Note**: Check approval file for recipient information
"""
                        # Move to Done anyway
                        dest = self.done / file_path.name
                        shutil.move(str(file_path), str(dest))
                        with open(dest, 'a', encoding='utf-8') as f:
                            f.write(completion_note)
                        continue
                    
                    # Clean up draft response (remove markdown code blocks and quotes)
                    email_body = draft_response
                    if '```' in email_body:
                        email_body = email_body.replace('```', '').strip()
                    
                    # Remove quote markers
                    lines = email_body.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        if line.strip().startswith('>'):
                            cleaned_lines.append(line.strip()[1:].strip())
                        else:
                            cleaned_lines.append(line)
                    email_body = '\n'.join(cleaned_lines).strip()
                    
                    # Remove any "Draft Response" headers
                    if 'Draft Response' in email_body:
                        email_body = email_body.split('Draft Response')[-1].strip()
                    if '(if applicable)' in email_body.lower():
                        email_body = email_body.split('(if applicable)')[-1].strip()
                    if 'This draft is ready' in email_body:
                        email_body = email_body.split('This draft is ready')[0].strip()
                    
                    self.logger.info(f"Sending email to: {original_to}")
                    self.logger.info(f"Subject: {subject}")
                    
                    # Send email via Gmail MCP Server
                    try:
                        from gmail_mcp_server import GmailMCPServer
                        mcp = GmailMCPServer()
                        
                        result = mcp.send_email(
                            to=original_to,
                            subject=subject,
                            body=email_body
                        )
                        
                        if result.get('success'):
                            self.logger.info(f"Email sent successfully! Message ID: {result.get('message_id')}")
                            
                            # Add success note
                            completion_note = f"""
---
## Execution
- **Executed At**: {datetime.now().isoformat()}
- **Status**: SENT SUCCESSFULLY
- **Message ID**: {result.get('message_id')}
- **Method**: Email MCP (Gmail API)
"""
                            self.stats['actions_executed'] += 1
                            
                            self._log_audit("email_sent", {
                                "to": original_to,
                                "subject": subject,
                                "message_id": result.get('message_id'),
                                "result": "success"
                            })
                        else:
                            error_msg = str(result.get('error', 'Unknown error'))
                            # Sanitize error message for Windows console
                            error_msg = error_msg.encode('cp1252', errors='replace').decode('cp1252')
                            self.logger.error(f"Email failed: {error_msg}")
                            completion_note = f"""
---
## Execution
- **Executed At**: {datetime.now().isoformat()}
- **Status**: FAILED
- **Error**: {error_msg[:200]}
"""
                            self._log_audit("email_sent", {
                                "to": original_to,
                                "result": "failed",
                                "error": error_msg[:200]
                            })
                        
                    except ImportError as e:
                        self.logger.error(f"Email MCP not available: {e}")
                        completion_note = f"""
---
## Execution
- **Executed At**: {datetime.now().isoformat()}
- **Status**: MCP NOT AVAILABLE
- **Note**: Install email dependencies
"""
                    except Exception as e:
                        error_msg = str(e).encode('cp1252', errors='replace').decode('cp1252')
                        self.logger.error(f"Error sending email: {error_msg}")
                        completion_note = f"""
---
## Execution
- **Executed At**: {datetime.now().isoformat()}
- **Status**: ERROR
- **Error**: {error_msg[:200]}
"""
                else:
                    # Not an email, just move to Done
                    self.logger.info(f"Non-email action, moving to Done")
                    completion_note = f"""
---
## Execution
- **Executed At**: {datetime.now().isoformat()}
- **Status**: Completed
- **Type**: {metadata.get('type', 'unknown')}
"""
                
                # Move to Done
                dest = self.done / file_path.name
                try:
                    shutil.move(str(file_path), str(dest))
                    
                    # Append completion note
                    with open(dest, 'a', encoding='utf-8') as f:
                        f.write(completion_note)
                    
                    self.logger.info(f"Moved to Done: {file_path.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to move file: {e}")

        except Exception as e:
            self.logger.error(f"Error processing Approved: {e}")
            self.stats['errors'] += 1
    
    def run_cycle(self):
        """
        Run one orchestration cycle.
        
        This is the main loop that:
        1. Processes Needs_Action folder
        2. Processes Approved folder
        3. Updates Dashboard
        4. Logs cycle completion
        """
        self.stats['cycles'] += 1
        self.logger.debug(f"Starting cycle {self.stats['cycles']}")
        
        # Process folders
        self.process_needs_action()
        self.process_approved()
        
        # Update dashboard
        self.update_dashboard()
        
        self.logger.debug(f"Cycle {self.stats['cycles']} complete")
    
    def start_watchers(self):
        """
        Start watcher subprocesses.
        
        In Bronze Tier, starts the FileSystemWatcher.
        """
        self.logger.info("Starting watcher processes...")
        
        # Start file system watcher
        try:
            watcher_script = Path(__file__).parent / 'filesystem_watcher.py'
            if watcher_script.exists():
                cmd = [
                    sys.executable,
                    str(watcher_script),
                    str(self.vault_path),
                    "--check-interval", "5"
                ]
                
                if self.dry_run:
                    cmd.append("--dry-run")
                
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.watcher_processes['filesystem'] = proc
                self.logger.info("FileSystemWatcher started")
                
        except Exception as e:
            self.logger.error(f"Failed to start FileSystemWatcher: {e}")
    
    def stop_watchers(self):
        """Stop all watcher processes."""
        self.logger.info("Stopping watcher processes...")
        
        for name, proc in self.watcher_processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
                self.logger.info(f"{name} stopped")
            except Exception as e:
                self.logger.error(f"Error stopping {name}: {e}")
                proc.kill()
        
        self.watcher_processes.clear()
    
    def run(self):
        """
        Main orchestration loop.
        
        Runs continuously until interrupted.
        """
        import signal
        import shutil
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("Starting Orchestrator...")
        self._log_audit("orchestrator_started", {
            "vault": str(self.vault_path),
            "dry_run": self.dry_run
        })
        
        # Start watcher processes
        self.start_watchers()
        
        # Setup signal handlers
        def signal_handler(sig, frame):
            self.logger.info("Received interrupt signal")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main loop
        try:
            while self.running:
                self.run_cycle()
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            self.stats['errors'] += 1
            
        finally:
            self.running = False
            self.stop_watchers()
            
            self._log_audit("orchestrator_stopped", {
                "cycles": self.stats['cycles'],
                "files_processed": self.stats['files_processed'],
                "errors": self.stats['errors']
            })
            
            self.logger.info("Orchestrator stopped")
    
    def run_once(self):
        """Run a single orchestration cycle (for testing)."""
        self.logger.info("Running single orchestration cycle...")
        self.run_cycle()
        self.logger.info(f"Cycle complete. Stats: {self.stats}")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="AI Employee Orchestrator"
    )
    parser.add_argument(
        "vault_path",
        help="Path to the Obsidian vault"
    )
    parser.add_argument(
        "--check-interval", "-i",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry run mode (no external actions)"
    )
    parser.add_argument(
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(
        vault_path=args.vault_path,
        check_interval=args.check_interval,
        dry_run=args.dry_run,
        log_level=args.log_level
    )
    
    print(f"Starting AI Employee Orchestrator (Bronze Tier)")
    print(f"Vault: {args.vault_path}")
    print(f"Check Interval: {args.check_interval}s")
    print(f"Dry Run: {args.dry_run}")
    print("Press Ctrl+C to stop.\n")
    
    if args.once:
        orchestrator.run_once()
    else:
        orchestrator.run()


if __name__ == "__main__":
    main()
