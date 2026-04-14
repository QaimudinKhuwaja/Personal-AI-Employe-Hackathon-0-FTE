"""
File System Watcher Module

Monitors a drop folder for new files and creates action files
for Qwen Code to process. This is the simplest watcher for
the Bronze tier implementation.

Usage:
    python filesystem_watcher.py /path/to/vault

Or with custom interval:
    python filesystem_watcher.py /path/to/vault --interval 30
"""

import os
import sys
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class FileDropItem:
    """Represents a file dropped for processing."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.name = filepath.name
        self.size = filepath.stat().st_size
        self.created = filepath.stat().st_ctime
        self.modified = filepath.stat().st_mtime
        self.content_hash = self._compute_hash()
        self.path = str(filepath)  # Add path attribute
    
    def _compute_hash(self) -> str:
        """Compute MD5 hash of file content."""
        hash_md5 = hashlib.md5()
        try:
            with open(self.filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for action file creation."""
        return {
            'name': self.name,
            'size': self.size,
            'created': datetime.fromtimestamp(self.created).isoformat(),
            'modified': datetime.fromtimestamp(self.modified).isoformat(),
            'hash': self.content_hash,
            'path': str(self.filepath)
        }
    
    def get_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now().isoformat()


class FilesystemWatcher(BaseWatcher):
    """
    Watches a drop folder for new files.

    When a file is added to the Inbox folder, creates an action file
    in Needs_Action for Qwen Code to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 30):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            check_interval: Seconds between checks (default: 30)
        """
        super().__init__(vault_path, check_interval)
        
        # Track processed files by hash to avoid duplicates
        self.processed_hashes: set = set()
        
        # Load previously processed files from cache
        self._load_processed_cache()
    
    def _load_processed_cache(self):
        """Load cache of previously processed files."""
        cache_file = self.vault_path / '.processed_files.cache'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.processed_hashes = set(f.read().strip().split('\n'))
                self.logger.info(f'Loaded {len(self.processed_hashes)} processed file hashes')
            except Exception as e:
                self.logger.warning(f'Could not load processed cache: {e}')
                self.processed_hashes = set()
    
    def _save_processed_cache(self):
        """Save cache of processed files."""
        cache_file = self.vault_path / '.processed_files.cache'
        try:
            with open(cache_file, 'w') as f:
                f.write('\n'.join(self.processed_hashes))
        except Exception as e:
            self.logger.warning(f'Could not save processed cache: {e}')
    
    def check_for_updates(self) -> List[FileDropItem]:
        """
        Check the Inbox folder for new files.
        
        Returns:
            List of new FileDropItem objects
        """
        new_items = []
        
        if not self.inbox.exists():
            self.inbox.mkdir(parents=True, exist_ok=True)
            return new_items
        
        # Get all files in inbox (not directories)
        for filepath in self.inbox.iterdir():
            if filepath.is_file() and not filepath.name.startswith('.'):
                item = FileDropItem(filepath)
                
                # Skip if already processed
                if item.content_hash in self.processed_hashes:
                    continue
                
                new_items.append(item)
                self.processed_hashes.add(item.content_hash)
        
        # Save updated cache
        if new_items:
            self._save_processed_cache()
        
        return new_items
    
    def create_action_file(self, item: FileDropItem) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The FileDropItem to create an action file for
            
        Returns:
            Path to created file, or None if creation failed
        """
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.sanitize_filename(item.name)
            filename = f"FILE_{timestamp}_{safe_name}.md"
            filepath = self.needs_action / filename
            
            # Determine file type for suggested actions
            file_ext = Path(item.name).suffix.lower()
            suggested_actions = self._get_suggested_actions(file_ext)
            
            # Create action file content
            content = f'''---
type: file_drop
source: filesystem
file_name: {item.name}
file_size: {item.size} bytes
file_hash: {item.content_hash}
received: {self.get_timestamp()}
status: pending
priority: normal
---

# 📁 File Drop: {item.name}

## File Details

| Property | Value |
|----------|-------|
| **Original Name** | {item.name} |
| **Size** | {item.size} bytes |
| **Received** | {item.get_timestamp()} |
| **Location** | {item.path} |

## Description

A new file has been dropped into the Inbox for processing.

## Suggested Actions

{suggested_actions}

## Notes

<!-- Add any additional context or instructions here -->

---
*Created by FilesystemWatcher*
'''
            
            # Write action file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f'Created action file for: {item.name}')
            return filepath
            
        except Exception as e:
            self.logger.error(f'Failed to create action file: {e}')
            return None
    
    def _get_suggested_actions(self, file_ext: str) -> str:
        """
        Get suggested actions based on file extension.
        
        Args:
            file_ext: File extension (e.g., '.pdf', '.txt')
            
        Returns:
            Markdown formatted list of suggested actions
        """
        actions = {
            '.pdf': [
                '- [ ] Read and summarize content',
                '- [ ] Extract key information',
                '- [ ] Categorize and file appropriately',
                '- [ ] Take any required action'
            ],
            '.txt': [
                '- [ ] Read content',
                '- [ ] Process any instructions',
                '- [ ] Respond or take action as needed'
            ],
            '.doc': [
                '- [ ] Read and understand document',
                '- [ ] Extract action items',
                '- [ ] File or respond as appropriate'
            ],
            '.docx': [
                '- [ ] Read and understand document',
                '- [ ] Extract action items',
                '- [ ] File or respond as appropriate'
            ],
            '.xlsx': [
                '- [ ] Analyze spreadsheet data',
                '- [ ] Extract key metrics',
                '- [ ] Create summary or report'
            ],
            '.csv': [
                '- [ ] Parse and analyze data',
                '- [ ] Import to tracking system if needed',
                '- [ ] Generate insights'
            ],
            '.jpg': [
                '- [ ] Analyze image content',
                '- [ ] Extract any text (OCR)',
                '- [ ] Describe and categorize'
            ],
            '.jpeg': [
                '- [ ] Analyze image content',
                '- [ ] Extract any text (OCR)',
                '- [ ] Describe and categorize'
            ],
            '.png': [
                '- [ ] Analyze image content',
                '- [ ] Extract any text (OCR)',
                '- [ ] Describe and categorize'
            ],
            '.md': [
                '- [ ] Read markdown content',
                '- [ ] Process any instructions',
                '- [ ] Update relevant documents'
            ],
        }
        
        return '\n'.join(actions.get(file_ext, [
            '- [ ] Review file content',
            '- [ ] Determine required action',
            '- [ ] Process and file appropriately'
        ]))


def main():
    """Main entry point for the filesystem watcher."""
    parser = argparse.ArgumentParser(
        description='File System Watcher for AI Employee'
    )
    parser.add_argument(
        'vault_path',
        type=str,
        help='Path to the Obsidian vault root directory'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate vault path
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)
    
    # Create and run watcher
    watcher = FilesystemWatcher(str(vault), args.interval)
    
    if args.once:
        # Test mode: run once and exit
        print("Running in test mode (once)...")
        items = watcher.check_for_updates()
        print(f"Found {len(items)} new file(s)")
        for item in items:
            filepath = watcher.create_action_file(item)
            print(f"  Created: {filepath}")
    else:
        # Normal mode: run continuously
        watcher.run()


if __name__ == '__main__':
    main()
