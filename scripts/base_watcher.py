"""
Base Watcher Module

Abstract base class for all watcher scripts in the AI Employee system.
All watchers follow the same pattern: monitor → detect → create action file.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers.
    
    Watchers are lightweight Python scripts that run continuously,
    monitoring various inputs and creating actionable files for
    Qwen Code to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs = self.vault_path / 'Logs'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        self.logger.info(f'Initialized {self.__class__.__name__}')
    
    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items to process.
        
        Returns:
            List of new items that need action
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement check_for_updates()"
        )
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to created file, or None if creation failed
            
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement create_action_file()"
        )
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        for item in items:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f'Created action file: {filepath.name}')
                    time.sleep(self.check_interval)
                except Exception as e:
                    self.logger.error(f'Error processing items: {e}', exc_info=True)
                    time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise
    
    def get_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now().isoformat()
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
