#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watchdog - Health monitor for AI Employee processes.

The Watchdog monitors critical processes and automatically restarts them
if they crash or become unresponsive. This ensures the AI Employee
remains operational 24/7.

Features:
- Monitors orchestrator and watcher processes
- Auto-restart on crash
- PID file management
- Human notification on restart
- Health check via dashboard update

Usage:
    python watchdog.py /path/to/vault
    python watchdog.py /path/to/vault --check-interval 30
"""

import sys
import os
import json
import time
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class Watchdog:
    """
    Health monitor for AI Employee processes.
    
    Monitors and manages:
    - Orchestrator process
    - File system watcher
    - Other watcher processes (when added)
    """
    
    def __init__(
        self,
        vault_path: str,
        check_interval: int = 30,
        log_level: str = "INFO"
    ):
        """
        Initialize the watchdog.
        
        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between health checks
            log_level: Logging level
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.src_path = Path(__file__).parent
        
        # Core folders
        self.logs = self.vault_path / 'Logs'
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # PID files location (using temp folder)
        import tempfile
        self.pid_dir = Path(tempfile.gettempdir()) / 'ai_employee'
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging(log_level)
        
        # Process definitions
        self.processes = {
            'orchestrator': {
                'script': 'orchestrator.py',
                'args': [str(self.vault_path)],
                'pid_file': self.pid_dir / 'orchestrator.pid',
                'description': 'Main orchestration process'
            },
            'filesystem_watcher': {
                'script': 'filesystem_watcher.py',
                'args': [str(self.vault_path), '--check-interval', '5'],
                'pid_file': self.pid_dir / 'filesystem_watcher.pid',
                'description': 'File system drop folder watcher'
            }
        }
        
        # Running processes
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
        # Statistics
        self.stats = {
            'checks': 0,
            'restarts': 0,
            'errors': 0,
            'start_time': None
        }
        
        self.logger.info(f"Watchdog initialized for vault: {vault_path}")
    
    def _setup_logging(self, log_level: str) -> Any:
        """Setup logging configuration."""
        import logging
        
        logger = logging.getLogger("Watchdog")
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
            log_file = self.logs / f"watchdog_{today}.log"
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not create log file: {e}")
        
        return logger
    
    def _log_audit(self, action: str, details: dict):
        """Write an audit log entry."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action,
            "actor": "watchdog",
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
    
    def _is_process_running(self, pid_file: Path) -> bool:
        """
        Check if a process is running based on PID file.
        
        Args:
            pid_file: Path to PID file
            
        Returns:
            True if process is running, False otherwise
        """
        if not pid_file.exists():
            return False
        
        try:
            pid = int(pid_file.read_text().strip())
            
            # Check if process exists
            if sys.platform == 'win32':
                # Windows: use tasklist
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # Unix-like: use kill with signal 0
                os.kill(pid, 0)
                return True
                
        except (ValueError, OSError, subprocess.SubprocessError):
            return False
    
    def _get_pid(self, pid_file: Path) -> Optional[int]:
        """Get PID from file."""
        try:
            if pid_file.exists():
                return int(pid_file.read_text().strip())
        except (ValueError, OSError):
            pass
        return None
    
    def _start_process(self, name: str) -> Optional[subprocess.Popen]:
        """
        Start a monitored process.
        
        Args:
            name: Process name from self.processes
            
        Returns:
            Process handle if started, None if failed
        """
        proc_def = self.processes.get(name)
        if not proc_def:
            self.logger.error(f"Unknown process: {name}")
            return None
        
        script_path = self.src_path / proc_def['script']
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return None
        
        cmd = [sys.executable, str(script_path)] + proc_def['args']
        
        try:
            self.logger.info(f"Starting {name}: {' '.join(cmd)}")
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Write PID file
            proc_def['pid_file'].write_text(str(proc.pid))
            
            self.logger.info(f"{name} started with PID {proc.pid}")
            
            self._log_audit("process_started", {
                "name": name,
                "pid": proc.pid,
                "description": proc_def['description']
            })
            
            return proc
            
        except Exception as e:
            self.logger.error(f"Failed to start {name}: {e}")
            self._log_audit("process_start_failed", {
                "name": name,
                "error": str(e)
            })
            return None
    
    def _stop_process(self, name: str, force: bool = False) -> bool:
        """
        Stop a monitored process.
        
        Args:
            name: Process name
            force: Use SIGKILL instead of SIGTERM
            
        Returns:
            True if stopped, False if not running
        """
        proc_def = self.processes.get(name)
        if not proc_def:
            return False
        
        pid = self._get_pid(proc_def['pid_file'])
        if not pid:
            return False
        
        try:
            if sys.platform == 'win32':
                # Windows: use taskkill
                import subprocess
                flag = '/F' if force else ''
                subprocess.run(['taskkill', flag, '/PID', str(pid)], check=False)
            else:
                # Unix-like
                import signal
                os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
            
            # Clean up PID file
            proc_def['pid_file'].unlink(missing_ok=True)
            
            self.logger.info(f"{name} stopped (was PID {pid})")
            
            self._log_audit("process_stopped", {
                "name": name,
                "pid": pid,
                "forced": force
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop {name}: {e}")
            return False
    
    def check_and_restart(self):
        """
        Check all processes and restart any that are not running.
        """
        for name, proc_def in self.processes.items():
            if not self._is_process_running(proc_def['pid_file']):
                self.logger.warning(f"{name} not running, restarting...")
                
                # Clean up stale PID file
                proc_def['pid_file'].unlink(missing_ok=True)
                
                # Start the process
                proc = self._start_process(name)
                
                if proc:
                    self.running_processes[name] = proc
                    self.stats['restarts'] += 1
                    
                    self._log_audit("process_restarted", {
                        "name": name,
                        "pid": proc.pid
                    })
                else:
                    self.stats['errors'] += 1
    
    def update_dashboard(self):
        """Update Dashboard.md with watchdog status."""
        dashboard_file = self.vault_path / 'Dashboard.md'

        try:
            if not dashboard_file.exists():
                return

            # Read with explicit UTF-8 encoding for Windows
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Build process status table (using simple ASCII icons for Windows compatibility)
            status_lines = ["| Component | Status | PID |"]
            status_lines.append("|-----------|--------|-----|")

            for name, proc_def in self.processes.items():
                is_running = self._is_process_running(proc_def['pid_file'])
                pid = self._get_pid(proc_def['pid_file']) or '-'
                status_icon = '[OK]' if is_running else '[--]'
                status_text = 'Running' if is_running else 'Stopped'
                status_lines.append(f"| {name.replace('_', ' ').title()} | {status_icon} {status_text} | {pid} |")

            # Add watchdog stats
            uptime = ""
            if self.stats['start_time']:
                delta = datetime.now() - self.stats['start_time']
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime = f"{hours}h {minutes}m {seconds}s"

            status_lines.append("")
            status_lines.append("### Watchdog Stats")
            status_lines.append(f"- **Checks**: {self.stats['checks']}")
            status_lines.append(f"- **Restarts**: {self.stats['restarts']}")
            status_lines.append(f"- **Uptime**: {uptime}")

            status_section = "\n".join(status_lines)

            # Write updated dashboard with explicit UTF-8 encoding
            import re

            # Look for System Health section and update it
            if "## System Health" in content:
                pattern = r'## System Health.*?(?=##|\Z)'
                new_content = re.sub(
                    pattern,
                    f"## System Health\n\n{status_section}\n\n",
                    content,
                    flags=re.DOTALL
                )
                with open(dashboard_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            else:
                # Append before the last section
                lines = content.split('\n')
                lines.insert(-1, "\n## System Health\n\n" + status_section + "\n")
                with open(dashboard_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

            
            self.logger.debug("Dashboard updated with process status")
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")
    
    def run(self):
        """
        Main watchdog loop.
        
        Continuously monitors processes and restarts as needed.
        """
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("Starting Watchdog...")
        self._log_audit("watchdog_started", {
            "vault": str(self.vault_path),
            "check_interval": self.check_interval
        })
        
        # Start all processes initially
        self.logger.info("Starting all monitored processes...")
        for name in self.processes:
            if not self._is_process_running(self.processes[name]['pid_file']):
                proc = self._start_process(name)
                if proc:
                    self.running_processes[name] = proc
        
        # Setup signal handlers
        def signal_handler(sig, frame):
            self.logger.info("Received interrupt signal")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main loop
        try:
            while self.running:
                self.stats['checks'] += 1
                self.logger.debug(f"Health check {self.stats['checks']}")
                
                # Check and restart processes
                self.check_and_restart()
                
                # Update dashboard
                self.update_dashboard()
                
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.logger.error(f"Watchdog error: {e}")
            self.stats['errors'] += 1
            
        finally:
            self.running = False
            self.stop_all()
            
            self._log_audit("watchdog_stopped", {
                "checks": self.stats['checks'],
                "restarts": self.stats['restarts'],
                "errors": self.stats['errors']
            })
            
            self.logger.info("Watchdog stopped")
    
    def stop_all(self):
        """Stop all monitored processes."""
        self.logger.info("Stopping all monitored processes...")
        
        for name in list(self.running_processes.keys()):
            self._stop_process(name)
        
        self.running_processes.clear()
    
    def status(self) -> Dict[str, Any]:
        """
        Get current status of all monitored processes.
        
        Returns:
            Dictionary with process statuses
        """
        status = {}
        for name, proc_def in self.processes.items():
            is_running = self._is_process_running(proc_def['pid_file'])
            pid = self._get_pid(proc_def['pid_file'])
            
            status[name] = {
                'running': is_running,
                'pid': pid,
                'description': proc_def['description']
            }
        
        return status


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="AI Employee Watchdog - Health Monitor"
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
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status and exit"
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start all processes and exit"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all processes and exit"
    )
    
    args = parser.parse_args()
    
    watchdog = Watchdog(
        vault_path=args.vault_path,
        check_interval=args.check_interval,
        log_level=args.log_level
    )
    
    if args.status:
        status = watchdog.status()
        print("AI Employee Process Status:")
        print("-" * 50)
        for name, info in status.items():
            status_icon = "✓" if info['running'] else "✗"
            pid_str = f"PID {info['pid']}" if info['pid'] else "no PID"
            print(f"  {status_icon} {name.replace('_', ' ').title()}: {pid_str}")
        return
    
    if args.start:
        print("Starting all processes...")
        for name in watchdog.processes:
            watchdog._start_process(name)
        print("Done.")
        return
    
    if args.stop:
        print("Stopping all processes...")
        watchdog.stop_all()
        print("Done.")
        return
    
    print(f"Starting AI Employee Watchdog")
    print(f"Vault: {args.vault_path}")
    print(f"Check Interval: {args.check_interval}s")
    print("Press Ctrl+C to stop.\n")
    
    watchdog.run()


if __name__ == "__main__":
    main()
