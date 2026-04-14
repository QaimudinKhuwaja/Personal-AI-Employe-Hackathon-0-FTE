"""
Health Checker

Monitors the health of AI Employee processes and services.
Automatically restarts failed processes and alerts on critical issues.

Usage:
    python scripts/health_checker.py
    python scripts/health_checker.py --watch orchestrator gmail_watcher facebook_watcher
    python scripts/health_checker.py --alert-email admin@example.com
"""

import os
import sys
import time
import signal
import logging
import argparse
import subprocess
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

try:
    import psutil
except ImportError:
    print("Warning: psutil not installed. Install with: pip install psutil")
    psutil = None

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class HealthChecker:
    """
    Monitors and manages AI Employee process health.
    
    Features:
    - Process monitoring (PID tracking)
    - Automatic restart on failure
    - Resource usage monitoring (CPU, memory)
    - Health endpoint checks
    - Alerting on critical issues
    """
    
    def __init__(
        self,
        vault_path: str = 'AI_Employee_Vault',
        check_interval: int = 30,
        alert_email: str = None,
        max_restarts_per_hour: int = 5
    ):
        """
        Initialize health checker.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between health checks
            alert_email: Email for critical alerts
            max_restarts_per_hour: Maximum restart attempts per hour
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.alert_email = alert_email
        self.max_restarts_per_hour = max_restarts_per_hour
        
        # Process definitions
        self.processes = {
            'orchestrator': {
                'command': 'python scripts/orchestrator.py AI_Employee_Vault',
                'pid_file': 'orchestrator.pid',
                'restart_delay': 5,
                'critical': True
            },
            'gmail_watcher': {
                'command': 'python scripts/gmail_watcher.py',
                'pid_file': 'gmail_watcher.pid',
                'restart_delay': 5,
                'critical': True
            },
            'whatsapp_watcher': {
                'command': 'python scripts/whatsapp_watcher.py',
                'pid_file': 'whatsapp_watcher.pid',
                'restart_delay': 5,
                'critical': False
            },
            'filesystem_watcher': {
                'command': 'python scripts/filesystem_watcher.py',
                'pid_file': 'filesystem_watcher.pid',
                'restart_delay': 5,
                'critical': False
            },
            'email_approval_watcher': {
                'command': 'python scripts/email_approval_watcher.py',
                'pid_file': 'email_approval_watcher.pid',
                'restart_delay': 5,
                'critical': True
            }
        }
        
        # Restart tracking
        self.restart_counts = {}
        self.last_hour_reset = datetime.now()
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized HealthChecker')
        self.logger.info(f'Watching {len(self.processes)} processes')
    
    def _setup_logging(self):
        """Setup logging."""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'health_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('HealthChecker')
    
    def check_process(self, name: str) -> Dict[str, Any]:
        """
        Check if a process is running.
        
        Args:
            name: Process name
            
        Returns:
            Process status dict
        """
        proc_def = self.processes.get(name)
        if not proc_def:
            return {'status': 'unknown', 'error': 'Process not defined'}
        
        pid_file = self.vault_path / proc_def['pid_file']
        
        # Check PID file
        if not pid_file.exists():
            return {'status': 'stopped', 'pid': None}
        
        try:
            pid = int(pid_file.read_text().strip())
            
            # Check if process exists
            if psutil:
                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    return {
                        'status': 'running',
                        'pid': pid,
                        'cpu_percent': proc.cpu_percent(),
                        'memory_percent': proc.memory_percent(),
                        'status_detail': proc.status()
                    }
                else:
                    return {'status': 'dead', 'pid': pid, 'error': 'PID does not exist'}
            else:
                # Fallback without psutil
                try:
                    os.kill(pid, 0)
                    return {'status': 'running', 'pid': pid}
                except OSError:
                    return {'status': 'dead', 'pid': pid, 'error': 'Process does not exist'}
        
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def start_process(self, name: str) -> bool:
        """
        Start a process.
        
        Args:
            name: Process name
            
        Returns:
            True if started successfully
        """
        proc_def = self.processes.get(name)
        if not proc_def:
            self.logger.error(f'Process {name} not defined')
            return False
        
        self.logger.info(f'Starting process: {name}')
        
        try:
            # Start process
            proc = subprocess.Popen(
                proc_def['command'],
                shell=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            # Write PID file
            pid_file = self.vault_path / proc_def['pid_file']
            pid_file.write_text(str(proc.pid), encoding='utf-8')
            
            self.logger.info(f'✅ Started {name} (PID: {proc.pid})')
            
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to start {name}: {e}')
            return False
    
    def stop_process(self, name: str) -> bool:
        """
        Stop a process.
        
        Args:
            name: Process name
            
        Returns:
            True if stopped successfully
        """
        proc_def = self.processes.get(name)
        if not proc_def:
            return False
        
        pid_file = self.vault_path / proc_def['pid_file']
        
        if not pid_file.exists():
            return True  # Already stopped
        
        try:
            pid = int(pid_file.read_text().strip())
            
            if psutil:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
            
            # Remove PID file
            pid_file.unlink()
            
            self.logger.info(f'✅ Stopped {name} (PID: {pid})')
            
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to stop {name}: {e}')
            return False
    
    def restart_process(self, name: str) -> bool:
        """
        Restart a process with rate limiting.
        
        Args:
            name: Process name
            
        Returns:
            True if restarted successfully
        """
        # Check restart rate limit
        self._check_restart_rate_limit()
        
        proc_def = self.processes.get(name)
        if not proc_def:
            return False
        
        # Increment restart count
        self.restart_counts[name] = self.restart_counts.get(name, 0) + 1
        
        self.logger.warning(f'Restarting {name} (attempt {self.restart_counts[name]})')
        
        # Stop if running
        self.stop_process(name)
        
        # Wait for restart delay
        time.sleep(proc_def.get('restart_delay', 5))
        
        # Start
        return self.start_process(name)
    
    def _check_restart_rate_limit(self):
        """Check and reset restart rate limit."""
        now = datetime.now()
        
        # Reset counts every hour
        if (now - self.last_hour_reset).total_seconds() >= 3600:
            self.restart_counts.clear()
            self.last_hour_reset = now
        
        # Check if any process exceeded limit
        for name, count in self.restart_counts.items():
            if count >= self.max_restarts_per_hour:
                self.logger.error(
                    f'🚨 Process {name} exceeded max restarts ({count}/{self.max_restarts_per_hour}/hour). '
                    f'Not restarting.'
                )
                # Send alert
                self._send_alert(
                    'critical',
                    f'Process {name} exceeded max restarts',
                    f'Restarted {count} times in the last hour'
                )
    
    def _send_alert(self, level: str, title: str, message: str):
        """
        Send alert notification.
        
        Args:
            level: Alert level (info, warning, critical)
            title: Alert title
            message: Alert message
        """
        self.logger.warning(f'ALERT [{level}]: {title} - {message}')
        
        # Email alert (if configured)
        if self.alert_email and level == 'critical':
            try:
                # Import email sender if available
                from scripts.email_sender import EmailSender
                sender = EmailSender()
                sender.send_email(
                    to=self.alert_email,
                    subject=f'🚨 AI Employee Alert: {title}',
                    body=f'{level.upper()}\n\n{message}\n\nTime: {datetime.now().isoformat()}'
                )
                self.logger.info(f'Alert email sent to {self.alert_email}')
            except Exception as e:
                self.logger.error(f'Failed to send alert email: {e}')
        
        # Write alert to file
        alert_file = self.vault_path / 'Needs_Action' / f'ALERT_{title.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d%H%M%S")}.md'
        
        content = f"""---
type: alert
level: {level}
created: {datetime.now().isoformat()}
title: {title}
status: pending
---

# Alert: {title}

**Level:** {level}  
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Details

{message}

## Actions Required

- [ ] Review the issue
- [ ] Take corrective action
- [ ] Move to Done when resolved
"""
        
        alert_file.write_text(content, encoding='utf-8')
    
    def check_services(self) -> Dict[str, Any]:
        """
        Check all services health.
        
        Returns:
            Health status for all services
        """
        health = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'healthy',
            'issues': []
        }
        
        for name, proc_def in self.processes.items():
            status = self.check_process(name)
            health['services'][name] = status
            
            # Check for issues
            if status['status'] in ['stopped', 'dead', 'error']:
                if proc_def.get('critical', False):
                    health['overall_status'] = 'unhealthy'
                    health['issues'].append({
                        'service': name,
                        'issue': f"Critical service {name} is {status['status']}"
                    })
                    
                    # Auto-restart critical services
                    self.restart_process(name)
                else:
                    if health['overall_status'] == 'healthy':
                        health['overall_status'] = 'degraded'
                    
                    self.logger.warning(f'Degraded: {name} is {status["status"]}')
        
        return health
    
    def check_external_services(self) -> Dict[str, Any]:
        """
        Check external service connectivity.
        
        Returns:
            External service health status
        """
        health = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # Check Odoo
        try:
            import requests
            odoo_url = os.getenv('ODOO_URL', 'http://localhost:8069')
            response = requests.get(f'{odoo_url}/web/webclient/version_info', timeout=5)
            health['services']['odoo'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': odoo_url
            }
        except Exception as e:
            health['services']['odoo'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check internet connectivity
        try:
            response = requests.get('https://www.google.com', timeout=5)
            health['services']['internet'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy'
            }
        except Exception as e:
            health['services']['internet'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health
    
    def generate_health_report(self) -> str:
        """
        Generate health report markdown.
        
        Returns:
            Markdown health report
        """
        internal_health = self.check_services()
        external_health = self.check_external_services()
        
        report = f"""---
generated: {internal_health['timestamp']}
type: health_report
---

# 🏥 AI Employee Health Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Overall Status:** {'✅ Healthy' if internal_health['overall_status'] == 'healthy' else '⚠️ ' + internal_health['overall_status'].title()}

---

## Internal Services

| Service | Status | PID | CPU | Memory |
|---------|--------|-----|-----|--------|
"""
        
        for name, status in internal_health['services'].items():
            status_icon = {
                'running': '✅',
                'stopped': '❌',
                'dead': '💀',
                'error': '⚠️',
                'unknown': '❓'
            }.get(status.get('status', 'unknown'), '❓')
            
            pid = status.get('pid', 'N/A')
            cpu = f"{status.get('cpu_percent', 0):.1f}%" if 'cpu_percent' in status else 'N/A'
            memory = f"{status.get('memory_percent', 0):.1f}%" if 'memory_percent' in status else 'N/A'
            
            report += f"| {status_icon} {name} | {status.get('status', 'unknown')} | {pid} | {cpu} | {memory} |\n"
        
        report += f"""
---

## External Services

| Service | Status |
|---------|--------|
"""
        
        for name, status in external_health['services'].items():
            status_icon = '✅' if status.get('status') == 'healthy' else '❌'
            report += f"| {status_icon} {name.title()} | {status.get('status', 'unknown')} |\n"
        
        # Add issues
        if internal_health['issues']:
            report += f"""
---

## ⚠️ Issues Detected

"""
            for issue in internal_health['issues']:
                report += f"- **{issue['service']}:** {issue['issue']}\n"
        
        report += f"""
---

## Restart Statistics (Last Hour)

| Service | Restarts |
|---------|----------|
"""
        
        for name in self.processes.keys():
            count = self.restart_counts.get(name, 0)
            report += f"| {name} | {count} |\n"
        
        report += f"""
---

*Health check runs every {self.check_interval} seconds*
"""
        
        return report
    
    def run(self):
        """Main health check loop."""
        self.logger.info('Starting Health Checker')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    # Check health
                    health = self.check_services()
                    
                    # Log status
                    self.logger.info(
                        f"Health: {health['overall_status']} | "
                        f"Services: {len([s for s in health['services'].values() if s['status'] == 'running'])}/{len(health['services'])} running"
                    )
                    
                    # Generate report every 5 minutes
                    if datetime.now().second == 0:  # On the minute
                        report = self.generate_health_report()
                        report_file = self.vault_path / 'Updates' / f'health_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
                        report_file.parent.mkdir(exist_ok=True)
                        report_file.write_text(report, encoding='utf-8')
                    
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f'Error in health check: {e}', exc_info=True)
                    time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            self.logger.info('Health Checker stopped by user')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='AI Employee Health Checker')
    parser.add_argument(
        '--watch',
        nargs='+',
        help='Specific processes to watch'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds'
    )
    parser.add_argument(
        '--alert-email',
        type=str,
        help='Email for critical alerts'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate single health report and exit'
    )
    parser.add_argument(
        '--start',
        type=str,
        help='Start a specific process'
    )
    parser.add_argument(
        '--stop',
        type=str,
        help='Stop a specific process'
    )
    parser.add_argument(
        '--restart',
        type=str,
        help='Restart a specific process'
    )
    
    args = parser.parse_args()
    
    # Create health checker
    checker = HealthChecker(
        check_interval=args.interval,
        alert_email=args.alert_email
    )
    
    # Filter processes if specified
    if args.watch:
        checker.processes = {
            k: v for k, v in checker.processes.items() if k in args.watch
        }
    
    # Single report
    if args.report:
        report = checker.generate_health_report()
        print(report)
        return
    
    # Start process
    if args.start:
        success = checker.start_process(args.start)
        sys.exit(0 if success else 1)
    
    # Stop process
    if args.stop:
        success = checker.stop_process(args.stop)
        sys.exit(0 if success else 1)
    
    # Restart process
    if args.restart:
        success = checker.restart_process(args.restart)
        sys.exit(0 if success else 1)
    
    # Run health checker
    checker.run()


if __name__ == '__main__':
    main()
