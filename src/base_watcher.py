#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract base class for all AI Employee watchers.

Watchers are lightweight Python scripts that run continuously, monitoring
various inputs and creating actionable files for Claude to process.

This follows the Perception layer of the AI Employee architecture:
Perception → Reasoning → Action
"""

import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    All watchers follow this pattern:
    1. Continuously poll for updates (check_interval)
    2. When new items found, create .md files in Needs_Action folder
    3. Track processed items to avoid duplicates
    4. Log all activity for audit trail
    """
    
    def __init__(
        self, 
        vault_path: str, 
        check_interval: int = 60,
        log_level: str = "INFO"
    ):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        
        # Core folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs = self.vault_path / 'Logs'
        self.done = self.vault_path / 'Done'
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Setup logging
        self.logger = self._setup_logging(log_level)
        
        # Track processed items (in-memory for Bronze Tier)
        self.processed_ids: set = set()
        
        # Dry run mode (for testing)
        self.dry_run = False
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.needs_action, self.inbox, self.logs, self.done]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self, log_level: str) -> logging.Logger:
        """
        Setup logging with both file and console handlers.
        
        Args:
            log_level: Logging level string
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (daily rotating)
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f"watcher_{self.__class__.__name__.lower()}_{today}.log"
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(console_format)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create log file: {e}")
        
        return logger
    
    def _log_audit(self, action: str, details: dict):
        """
        Write an audit log entry in the required format.
        
        Required log format per Company Handbook:
        {
            "timestamp": "2026-01-07T10:30:00Z",
            "action_type": "email_send",
            "actor": "claude_code",
            "target": "client@example.com",
            "parameters": {"subject": "Invoice #123"},
            "approval_status": "approved",
            "approved_by": "human",
            "result": "success"
        }
        
        Args:
            action: Type of action being logged
            details: Dictionary of action details
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action,
            "actor": self.__class__.__name__.lower(),
            "result": "pending",
            **details
        }
        
        # Append to daily log file
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f"{today}.json"
        
        try:
            import json
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
    
    @abstractmethod
    def check_for_updates(self) -> list[Any]:
        """
        Check for new items to process.
        
        Returns:
            List of new items (format depends on watcher type)
            
        This method must be implemented by each watcher subclass.
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: Item to process (from check_for_updates)
            
        Returns:
            Path to created file, or None if failed
            
        This method must be implemented by each watcher subclass.
        """
        pass
    
    def run(self):
        """
        Main watcher loop.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        import time
        from retry_handler import with_retry, TransientError
        
        self.logger.info(f"Starting {self.__class__.__name__}")
        self._log_audit("watcher_started", {"check_interval": self.check_interval})
        
        @with_retry(max_attempts=3, base_delay=5)
        def process_items():
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f"Error processing items: {e}")
                raise TransientError(str(e))
        
        try:
            while True:
                try:
                    process_items()
                except TransientError as e:
                    self.logger.warning(f"Transient error, will retry: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    self._log_audit("watcher_error", {"error": str(e)})
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"{self.__class__.__name__} stopped by user")
            self._log_audit("watcher_stopped", {})
    
    def set_dry_run(self, enabled: bool = True):
        """
        Enable or disable dry run mode.
        
        In dry run mode, actions are logged but not executed.
        Useful for testing and development.
        
        Args:
            enabled: Whether to enable dry run mode
        """
        self.dry_run = enabled
        self.logger.info(f"Dry run mode: {'enabled' if enabled else 'disabled'}")


if __name__ == "__main__":
    # Example usage (for testing)
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python base_watcher.py <vault_path>")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    # Note: BaseWatcher is abstract, cannot be instantiated directly
    # This is for documentation purposes only
    print(f"BaseWatcher initialized for vault: {vault_path}")
    print("Subclass and implement check_for_updates() and create_action_file()")
