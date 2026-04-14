"""
Audit Logger

Centralized audit logging system for the AI Employee.
All actions are logged in JSONL format for compliance and debugging.

Usage:
    from audit_logger import AuditLogger
    
    logger = AuditLogger()
    logger.log_action(
        action_type='email_send',
        actor='qwen_code',
        parameters={'to': 'client@example.com'},
        result='success'
    )
"""

import os
import json
import logging
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path


class AuditLogger:
    """
    Centralized audit logger for AI Employee.
    
    Features:
    - JSONL format for machine readability
    - Daily log rotation
    - 90-day retention
    - Structured logging with consistent schema
    - Multiple log levels (INFO, WARNING, ERROR)
    """
    
    def __init__(
        self,
        logs_dir: str = 'Logs',
        retention_days: int = 90
    ):
        """
        Initialize audit logger.
        
        Args:
            logs_dir: Directory for log files
            retention_days: Number of days to retain logs
        """
        self.logs_dir = Path(logs_dir)
        self.retention_days = retention_days
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Current log file
        self.current_log_file = self.logs_dir / f'audit_{datetime.now().strftime("%Y-%m-%d")}.jsonl'
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger('AuditLogger')
    
    def _setup_logging(self):
        """Setup Python logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    
    def _rotate_logs(self):
        """Remove logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.logs_dir.glob('audit_*.jsonl'):
            try:
                file_date = datetime.strptime(log_file.stem.split('_')[1], '%Y-%m-%d')
                if file_date < cutoff:
                    log_file.unlink()
                    self.logger.info(f'Deleted old log: {log_file.name}')
            except Exception as e:
                self.logger.warning(f'Could not process {log_file.name}: {e}')
    
    def log_action(
        self,
        action_type: str,
        actor: str,
        parameters: Dict[str, Any],
        result: str,
        approval_status: str = 'auto',
        approved_by: str = 'system',
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action (e.g., 'email_send', 'facebook_post')
            actor: Who performed the action (e.g., 'qwen_code', 'gmail_watcher')
            parameters: Action parameters
            result: Result ('success', 'failed', 'pending')
            approval_status: 'auto', 'approved', 'rejected'
            approved_by: Who approved ('system', 'human', email)
            error_message: Error message if failed
            duration_ms: Action duration in milliseconds
            metadata: Additional metadata
            
        Returns:
            Log entry ID
        """
        # Create log entry
        entry = {
            'timestamp': datetime.now().isoformat(),
            'log_id': str(uuid.uuid4()),
            'action_type': action_type,
            'actor': actor,
            'parameters': parameters,
            'approval_status': approval_status,
            'approved_by': approved_by,
            'result': result,
            'error_message': error_message,
            'duration_ms': duration_ms,
            'version': '1.0.0'
        }
        
        # Add metadata if provided
        if metadata:
            entry['metadata'] = metadata
        
        # Write to current log file
        log_file = self.logs_dir / f'audit_{datetime.now().strftime("%Y-%m-%d")}.jsonl'
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # Rotate old logs periodically
        self._rotate_logs()
        
        self.logger.info(f'Logged action: {action_type} - {result}')
        
        return entry['log_id']
    
    def get_logs(
        self,
        date: str = None,
        action_type: str = None,
        actor: str = None,
        result: str = None,
        limit: int = 100
    ) -> list:
        """
        Query audit logs.
        
        Args:
            date: Specific date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor
            result: Filter by result
            limit: Maximum entries to return
            
        Returns:
            List of log entries
        """
        logs = []
        
        # Determine which files to read
        if date:
            log_files = [self.logs_dir / f'audit_{date}.jsonl']
        else:
            # Read today's log file
            log_files = [self.logs_dir / f'audit_{datetime.now().strftime("%Y-%m-%d")}.jsonl']
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if action_type and entry.get('action_type') != action_type:
                                continue
                            if actor and entry.get('actor') != actor:
                                continue
                            if result and entry.get('result') != result:
                                continue
                            
                            logs.append(entry)
                            
                            if len(logs) >= limit:
                                return logs
                            
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.logger.warning(f'Could not read {log_file.name}: {e}')
        
        return logs
    
    def get_summary(self, date: str = None) -> Dict[str, Any]:
        """
        Get summary statistics for a date.
        
        Args:
            date: Date (YYYY-MM-DD), default today
            
        Returns:
            Summary statistics
        """
        logs = self.get_logs(date=date, limit=10000)
        
        summary = {
            'total_actions': len(logs),
            'by_result': {},
            'by_action_type': {},
            'by_actor': {},
            'error_rate': 0.0,
            'success_rate': 0.0
        }
        
        for log in logs:
            # Count by result
            result = log.get('result', 'unknown')
            summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
            
            # Count by action type
            action_type = log.get('action_type', 'unknown')
            summary['by_action_type'][action_type] = summary['by_action_type'].get(action_type, 0) + 1
            
            # Count by actor
            actor = log.get('actor', 'unknown')
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
        
        # Calculate rates
        total = summary['total_actions']
        if total > 0:
            summary['success_rate'] = (summary['by_result'].get('success', 0) / total) * 100
            summary['error_rate'] = (summary['by_result'].get('failed', 0) / total) * 100
        
        return summary
    
    def export_logs(
        self,
        start_date: str,
        end_date: str,
        output_file: str
    ) -> str:
        """
        Export logs to a file for compliance/audit.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_file: Output file path
            
        Returns:
            Output file path
        """
        from datetime import timedelta
        
        all_logs = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            logs = self.get_logs(date=date_str, limit=10000)
            all_logs.extend(logs)
            current += timedelta(days=1)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f'Exported {len(all_logs)} logs to {output_file}')
        
        return output_file


# Convenience functions for easy import
_default_logger = None

def get_logger() -> AuditLogger:
    """Get or create default audit logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger()
    return _default_logger

def log_action(**kwargs):
    """Log action using default logger."""
    return get_logger().log_action(**kwargs)

def get_logs(**kwargs):
    """Get logs using default logger."""
    return get_logger().get_logs(**kwargs)

def get_summary(**kwargs):
    """Get summary using default logger."""
    return get_logger().get_summary(**kwargs)


if __name__ == '__main__':
    # Test the audit logger
    logger = AuditLogger()
    
    # Log test entries
    logger.log_action(
        action_type='test_action',
        actor='audit_logger',
        parameters={'test': 'data'},
        result='success'
    )
    
    logger.log_action(
        action_type='test_action',
        actor='audit_logger',
        parameters={'test': 'data', 'error': 'simulated'},
        result='failed',
        error_message='This is a test error'
    )
    
    # Get summary
    summary = logger.get_summary()
    print(f"Today's summary: {json.dumps(summary, indent=2)}")
