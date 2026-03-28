#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Scheduler - Schedule AI Employee tasks.

This script creates scheduled tasks for:
- Daily CEO Briefing generation
- Regular watcher execution
- LinkedIn post scheduling
- Email checking

For Windows: Uses Task Scheduler
For Linux/Mac: Uses cron

Usage:
    python scheduler.py install    # Install scheduled tasks
    python scheduler.py remove     # Remove scheduled tasks
    python scheduler.py status     # Show task status
    python scheduler.py run daily-briefing  # Run specific task
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, time


class TaskScheduler:
    """
    Cross-platform task scheduler.
    
    Windows: Uses schtasks (Task Scheduler)
    Linux/Mac: Uses cron
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize scheduler.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path).absolute()
        self.src_path = Path(__file__).parent.absolute()
        self.python_exe = sys.executable
        
        # Task definitions
        self.tasks = {
            'daily-briefing': {
                'name': 'AI_Employee_Daily_Briefing',
                'time': '08:00',
                'script': 'orchestrator.py',
                'args': f'{self.vault_path} --once',
                'description': 'Generate daily CEO briefing'
            },
            'gmail-check': {
                'name': 'AI_Employee_Gmail_Check',
                'time': '*/15 * * * *',  # Every 15 minutes (cron format)
                'script': 'gmail_watcher.py',
                'args': f'{self.vault_path}',
                'description': 'Check Gmail for new emails'
            },
            'linkedin-post': {
                'name': 'AI_Employee_Linkedin_Post',
                'time': '09:00',
                'script': 'linkedin_poster.py',
                'args': f'--generate --vault {self.vault_path}',
                'description': 'Generate and post LinkedIn update',
                'days': 'MON-FRI'  # Weekdays only
            },
            'orchestrator': {
                'name': 'AI_Employee_Orchestrator',
                'time': '*/5 * * * *',  # Every 5 minutes
                'script': 'orchestrator.py',
                'args': f'{self.vault_path}',
                'description': 'Run orchestrator cycle'
            }
        }
    
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return sys.platform == 'win32'
    
    def install_all(self) -> bool:
        """
        Install all scheduled tasks.
        
        Returns:
            True if all tasks installed successfully
        """
        success = True
        
        for task_id, task_config in self.tasks.items():
            print(f"Installing task: {task_config['name']}...")
            if self.install_task(task_id):
                print(f"  ✓ Installed")
            else:
                print(f"  ✗ Failed")
                success = False
        
        return success
    
    def install_task(self, task_id: str) -> bool:
        """
        Install a specific scheduled task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful
        """
        if task_id not in self.tasks:
            print(f"Unknown task: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        if self.is_windows():
            return self._install_task_windows(task)
        else:
            return self._install_task_cron(task)
    
    def _install_task_windows(self, task: dict) -> bool:
        """Install task using Windows Task Scheduler."""
        try:
            # Build schtasks command
            cmd = [
                'schtasks', '/Create',
                '/TN', task['name'],
                '/TR', f'"{self.python_exe}" "{self.src_path / task["script"]}" {task["args"]}',
                '/SC', 'DAILY',
                '/ST', task['time'],
                '/RL', 'HIGHEST',
                '/F'  # Force create (overwrite if exists)
            ]
            
            # Add day restriction if specified
            if task.get('days') == 'MON-FRI':
                cmd = [
                    'schtasks', '/Create',
                    '/TN', task['name'],
                    '/TR', f'"{self.python_exe}" "{self.src_path / task["script"]}" {task["args"]}',
                    '/SC', 'WEEKLY',
                    '/D', 'MON,TUE,WED,THU,FRI',
                    '/ST', task['time'],
                    '/RL', 'HIGHEST',
                    '/F'
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Exception: {e}")
            return False
    
    def _install_task_cron(self, task: dict) -> bool:
        """Install task using cron."""
        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ''
            
            # Create cron entry
            cron_time = task['time']
            script_path = self.src_path / task['script']
            cron_entry = f"{cron_time} {self.python_exe} {script_path} {task['args']} # {task['name']}\n"
            
            # Check if already exists
            if task['name'] in current_crontab:
                print(f"  Task already exists, skipping")
                return True
            
            # Add to crontab
            new_crontab = current_crontab + cron_entry
            
            result = subprocess.run(
                ['crontab', '-'],
                input=new_crontab,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Exception: {e}")
            return False
    
    def remove_all(self) -> bool:
        """
        Remove all scheduled tasks.
        
        Returns:
            True if all tasks removed successfully
        """
        success = True
        
        for task_id, task_config in self.tasks.items():
            print(f"Removing task: {task_config['name']}...")
            if self.remove_task(task_id):
                print(f"  ✓ Removed")
            else:
                print(f"  ✗ Failed")
                success = False
        
        return success
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a specific scheduled task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if self.is_windows():
            try:
                cmd = ['schtasks', '/Delete', '/TN', task['name'], '/F']
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
            except Exception:
                return False
        else:
            try:
                # Remove from crontab
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    new_lines = [l for l in lines if task['name'] not in l]
                    new_crontab = '\n'.join(new_lines)
                    
                    subprocess.run(
                        ['crontab', '-'],
                        input=new_crontab,
                        capture_output=True,
                        text=True
                    )
                return True
            except Exception:
                return False
    
    def status(self) -> dict:
        """
        Get status of all scheduled tasks.
        
        Returns:
            Dictionary of task statuses
        """
        statuses = {}
        
        if self.is_windows():
            for task_id, task_config in self.tasks.items():
                try:
                    cmd = ['schtasks', '/Query', '/TN', task_config['name'], '/FO', 'LIST']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    statuses[task_id] = {
                        'installed': result.returncode == 0,
                        'name': task_config['name'],
                        'description': task_config['description']
                    }
                except Exception:
                    statuses[task_id] = {'installed': False, 'name': task_config['name']}
        else:
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                crontab = result.stdout if result.returncode == 0 else ''
                
                for task_id, task_config in self.tasks.items():
                    statuses[task_id] = {
                        'installed': task_config['name'] in crontab,
                        'name': task_config['name'],
                        'description': task_config['description']
                    }
            except Exception:
                for task_id, task_config in self.tasks.items():
                    statuses[task_id] = {'installed': False, 'name': task_config['name']}
        
        return statuses
    
    def run_task(self, task_id: str) -> bool:
        """
        Run a task immediately.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task ran successfully
        """
        if task_id not in self.tasks:
            print(f"Unknown task: {task_id}")
            return False
        
        task = self.tasks[task_id]
        script_path = self.src_path / task['script']
        
        print(f"Running task: {task['name']}...")
        
        try:
            cmd = [self.python_exe, str(script_path)] + task['args'].split()
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Exception: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Employee Task Scheduler")
    parser.add_argument("action", choices=['install', 'remove', 'status', 'run'], help="Action to perform")
    parser.add_argument("task", nargs="?", help="Specific task (optional)")
    parser.add_argument("--vault", default="AI_Employee_Vault", help="Path to Obsidian vault")
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler(args.vault)
    
    if args.action == 'install':
        if args.task:
            success = scheduler.install_task(args.task)
        else:
            success = scheduler.install_all()
        
        if success:
            print("\n✅ Scheduled tasks installed successfully!")
        else:
            print("\n⚠️ Some tasks failed to install")
            sys.exit(1)
    
    elif args.action == 'remove':
        if args.task:
            scheduler.remove_task(args.task)
        else:
            scheduler.remove_all()
        print("✅ Scheduled tasks removed")
    
    elif args.action == 'status':
        print("📅 AI Employee Scheduled Tasks")
        print("=" * 60)
        
        statuses = scheduler.status()
        
        for task_id, status in statuses.items():
            icon = "✓" if status['installed'] else "✗"
            print(f"{icon} {status['name']}")
            print(f"  {status.get('description', '')}")
            print()
    
    elif args.action == 'run':
        if not args.task:
            print("Error: Task name required for 'run' action")
            sys.exit(1)
        
        success = scheduler.run_task(args.task)
        if success:
            print("✅ Task completed successfully")
        else:
            print("❌ Task failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
