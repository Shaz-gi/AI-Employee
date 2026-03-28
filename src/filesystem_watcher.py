#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors local file drops for AI Employee.

This watcher uses the watchdog library to monitor a "drop folder" for new files.
When files are added, it creates corresponding action files in Needs_Action folder
for Claude to process.

Use cases:
- Drop a PDF invoice for processing
- Add a document for summarization
- Submit a file for conversion
- Queue a file for analysis

Usage:
    python filesystem_watcher.py /path/to/vault --drop-folder /path/to/drop
"""

import sys
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class DropFolderHandler:
    """
    Event handler for watchdog file system events.
    
    Monitors a specific folder for new files and processes them.
    """
    
    def __init__(self, watcher: 'FileSystemWatcher'):
        self.watcher = watcher
        self.logger = watcher.logger
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        source = Path(event.src_path)
        self.watcher.process_file(source)
    
    def on_modified(self, event):
        """Handle file modification events (optional)."""
        if event.is_directory:
            return
        
        # Only process if file was modified recently (within 5 seconds)
        source = Path(event.src_path)
        mtime = datetime.fromtimestamp(source.stat().st_mtime)
        if (datetime.now() - mtime).total_seconds() < 5:
            self.watcher.process_file(source)


class FileSystemWatcher(BaseWatcher):
    """
    Watcher that monitors a drop folder for new files.
    
    When files are added to the drop folder, this watcher:
    1. Copies the file to the vault
    2. Creates a metadata .md file in Needs_Action
    3. Logs the action for audit trail
    """
    
    def __init__(
        self, 
        vault_path: str,
        drop_folder: Optional[str] = None,
        check_interval: int = 5,
        log_level: str = "INFO"
    ):
        """
        Initialize the file system watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            drop_folder: Path to the drop folder (default: vault/Inbox/Drop)
            check_interval: Seconds between checks (default: 5 for file watcher)
            log_level: Logging level
        """
        super().__init__(vault_path, check_interval, log_level)
        
        # Setup drop folder
        if drop_folder:
            self.drop_folder = Path(drop_folder)
        else:
            self.drop_folder = self.inbox / 'Drop'
        
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed files by hash
        self.processed_files: Dict[str, str] = {}  # hash -> destination path
        
        self.logger.info(f"Drop folder: {self.drop_folder}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file for deduplication."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension."""
        extension_map = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.txt': 'Text File',
            '.md': 'Markdown File',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.csv': 'CSV File',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.gif': 'Image',
            '.zip': 'Archive',
            '.rar': 'Archive',
        }
        return extension_map.get(file_path.suffix.lower(), 'Unknown')
    
    def _suggest_action(self, file_path: Path) -> str:
        """Suggest an action based on file type and name."""
        name_lower = file_path.name.lower()
        
        if 'invoice' in name_lower:
            return 'Process invoice and extract details'
        elif 'receipt' in name_lower:
            return 'Process receipt for expense tracking'
        elif 'contract' in name_lower or 'agreement' in name_lower:
            return 'Review contract terms and summarize'
        elif 'resume' in name_lower or 'cv' in name_lower:
            return 'Extract candidate information'
        elif file_path.suffix == '.pdf':
            return 'Extract text and summarize content'
        else:
            return 'Review and process file content'
    
    def process_file(self, source: Path) -> Optional[Path]:
        """
        Process a dropped file.
        
        Args:
            source: Path to the source file
            
        Returns:
            Path to created action file, or None if skipped
        """
        if not source.exists():
            self.logger.warning(f"File no longer exists: {source}")
            return None
        
        # Check for duplicates
        file_hash = self._get_file_hash(source)
        if file_hash in self.processed_files:
            self.logger.info(f"Skipping duplicate file: {source.name}")
            return None
        
        # Generate destination path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest_name = f"FILE_{timestamp}_{source.name}"
        dest = self.vault_path / 'Inbox' / dest_name
        
        # Copy file to vault
        try:
            shutil.copy2(source, dest)
            self.logger.info(f"Copied {source.name} to vault")
        except Exception as e:
            self.logger.error(f"Failed to copy file: {e}")
            return None
        
        # Create action file
        action_file = self.create_action_file({
            'source': source,
            'destination': dest,
            'hash': file_hash
        })
        
        # Store in processed files
        self.processed_files[file_hash] = str(dest)
        
        # Optionally remove from drop folder
        try:
            source.unlink()
            self.logger.debug(f"Removed from drop folder: {source}")
        except Exception as e:
            self.logger.warning(f"Could not remove from drop folder: {e}")
        
        return action_file
    
    def check_for_updates(self) -> list:
        """
        Check drop folder for new files.
        
        Returns:
            List of file paths to process
        """
        new_files = []
        
        try:
            for file_path in self.drop_folder.iterdir():
                if file_path.is_file():
                    # Skip hidden files and temp files
                    if file_path.name.startswith('.') or file_path.suffix == '.tmp':
                        continue
                    
                    # Check if already processed
                    file_hash = self._get_file_hash(file_path)
                    if file_hash not in self.processed_files:
                        new_files.append(file_path)
                        
        except Exception as e:
            self.logger.error(f"Error scanning drop folder: {e}")
        
        return new_files
    
    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: Dictionary with file information
            
        Returns:
            Path to created action file, or None if failed
        """
        source = item['source']
        dest = item['destination']
        file_hash = item['hash']
        
        # Get file info
        file_size = source.stat().st_size
        file_type = self._get_file_type(source)
        suggested_action = self._suggest_action(source)
        
        # Create action file content
        timestamp = datetime.now().isoformat()
        content = f"""---
type: file_drop
original_name: {source.name}
vault_path: {dest.relative_to(self.vault_path)}
file_type: {file_type}
file_size: {file_size}
file_hash: {file_hash}
received: {timestamp}
priority: medium
status: pending
---

# File Dropped for Processing

## File Information
- **Original Name**: {source.name}
- **File Type**: {file_type}
- **Size**: {self._format_size(file_size)}
- **Received**: {timestamp}
- **Vault Location**: `{dest.relative_to(self.vault_path)}`

## Suggested Action
{suggested_action}

## Processing Notes
*Add any specific instructions for Claude here*

## Checklist
- [ ] Review file content
- [ ] Extract relevant information
- [ ] Take appropriate action
- [ ] File in appropriate location
- [ ] Update Dashboard if needed

---
*Created by FileSystemWatcher*
"""
        
        # Write action file
        action_name = f"FILE_{source.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        action_file = self.needs_action / action_name
        
        try:
            action_file.write_text(content)
            self.logger.info(f"Created action file: {action_file.name}")
            
            # Log audit
            self._log_audit("file_drop_processed", {
                "file_name": source.name,
                "file_size": file_size,
                "destination": str(dest),
                "action_file": str(action_file)
            })
            
            return action_file
            
        except Exception as e:
            self.logger.error(f"Failed to create action file: {e}")
            return None
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def run_with_watchdog(self):
        """
        Run using the watchdog library for real-time file monitoring.
        
        This is more efficient than polling for file changes.
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class WatchdogHandler(FileSystemEventHandler):
                def __init__(self, watcher):
                    self.watcher = watcher
                
                def on_created(self, event):
                    if not event.is_directory:
                        self.watcher.process_file(Path(event.src_path))
                
                def on_modified(self, event):
                    if not event.is_directory:
                        source = Path(event.src_path)
                        # Only process recent modifications
                        mtime = datetime.fromtimestamp(source.stat().st_mtime)
                        if (datetime.now() - mtime).total_seconds() < 5:
                            self.watcher.process_file(source)
            
            observer = Observer()
            handler = WatchdogHandler(self)
            observer.schedule(handler, str(self.drop_folder), recursive=False)
            observer.start()
            
            self.logger.info(f"Watching {self.drop_folder} (using watchdog)")
            self._log_audit("watcher_started", {
                "type": "filesystem",
                "drop_folder": str(self.drop_folder),
                "mode": "watchdog"
            })
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                self.logger.info("File system watcher stopped")
            
            observer.join()
            
        except ImportError:
            self.logger.warning("watchdog not installed, using polling mode")
            self.run_polling()  # Fall back to polling
    
    def run_polling(self):
        """
        Run using polling mode (check interval based).
        
        This is the fallback when watchdog is not installed.
        """
        import time
        from retry_handler import with_retry, TransientError
        
        self.logger.info(f"Starting {self.__class__.__name__} (polling mode)")
        self._log_audit("watcher_started", {
            "check_interval": self.check_interval,
            "mode": "polling"
        })
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        # Process file directly (item is a Path object)
                        self.process_file(item)
                except TransientError as e:
                    self.logger.warning(f"Transient error, will retry: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    self._log_audit("watcher_error", {"error": str(e)})
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"{self.__class__.__name__} stopped by user")
            self._log_audit("watcher_stopped", {})


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="File System Watcher for AI Employee"
    )
    parser.add_argument(
        "vault_path",
        help="Path to the Obsidian vault"
    )
    parser.add_argument(
        "--drop-folder", "-d",
        help="Path to the drop folder (default: vault/Inbox/Drop)"
    )
    parser.add_argument(
        "--check-interval", "-i",
        type=int,
        default=5,
        help="Check interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry run mode (no file operations)"
    )
    
    args = parser.parse_args()
    
    watcher = FileSystemWatcher(
        vault_path=args.vault_path,
        drop_folder=args.drop_folder,
        check_interval=args.check_interval,
        log_level=args.log_level
    )
    
    if args.dry_run:
        watcher.set_dry_run(True)
    
    print(f"Starting File System Watcher...")
    print(f"Vault: {args.vault_path}")
    print(f"Drop Folder: {watcher.drop_folder}")
    print(f"Drop a file into the drop folder to trigger processing.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        watcher.run_polling()
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


if __name__ == "__main__":
    main()
