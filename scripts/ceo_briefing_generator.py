"""
CEO Briefing Generator

Generates comprehensive weekly business reports for the CEO.
Aggregates data from Odoo (accounting), social media, tasks, and communications.

Usage:
    python scripts/ceo_briefing_generator.py --output AI_Employee_Vault/Briefings/weekly_briefing.md
    python scripts/ceo_briefing_generator.py --period 2026-02-01:2026-03-01
    python scripts/ceo_briefing_generator.py --auto-schedule

Features:
- Revenue analysis from Odoo
- Task completion summary
- Social media performance
- Cost optimization suggestions
- Upcoming deadlines
- Proactive recommendations
"""

import os
import sys
import json
import logging
import argparse
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class CEOBriefingGenerator:
    """
    Generates weekly CEO briefing reports.
    
    Aggregates data from multiple sources:
    - Odoo ERP (accounting, invoices, customers)
    - Social media (Facebook, LinkedIn)
    - Task management (Done folder)
    - Communications (Gmail, WhatsApp logs)
    """
    
    def __init__(
        self,
        vault_path: str = 'AI_Employee_Vault',
        odoo_enabled: bool = True,
        facebook_enabled: bool = True,
        linkedin_enabled: bool = True
    ):
        """
        Initialize briefing generator.
        
        Args:
            vault_path: Path to Obsidian vault
            odoo_enabled: Enable Odoo integration
            facebook_enabled: Enable Facebook integration
            linkedin_enabled: Enable LinkedIn integration
        """
        self.vault_path = Path(vault_path)
        self.odoo_enabled = odoo_enabled
        self.facebook_enabled = facebook_enabled
        self.linkedin_enabled = linkedin_enabled
        
        # Paths
        self.briefings_path = self.vault_path / 'Briefings'
        self.accounting_path = self.vault_path / 'Accounting'
        self.done_path = self.vault_path / 'Done'
        self.logs_path = self.vault_path / 'Logs'
        
        # Also check project-level Logs/ folder
        self.project_root = Path(__file__).parent.parent
        self.project_logs_path = self.project_root / 'Logs'
        
        # Ensure directories exist
        self.briefings_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized CEOBriefingGenerator')
        self.logger.info(f'Vault: {self.vault_path}')
    
    def _setup_logging(self):
        """Setup logging."""
        log_dir = Path('Logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'briefing_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('CEOBriefingGenerator')
    
    def generate_briefing(
        self,
        period_start: datetime = None,
        period_end: datetime = None,
        output_file: str = None
    ) -> str:
        """
        Generate CEO briefing report.
        
        Args:
            period_start: Start of reporting period
            period_end: End of reporting period
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated briefing file
        """
        if period_start is None:
            # Default: last 7 days
            period_end = datetime.now()
            period_start = period_end - timedelta(days=7)
        
        self.logger.info(f'Generating briefing for {period_start.date()} to {period_end.date()}')
        
        # Gather data from all sources
        data = {
            'period_start': period_start,
            'period_end': period_end,
            'generated_at': datetime.now(),
            'revenue': self._gather_revenue_data(period_start, period_end),
            'tasks': self._gather_task_data(period_start, period_end),
            'social_media': self._gather_social_media_data(period_start, period_end),
            'customers': self._gather_customer_data(period_start, period_end),
            'expenses': self._gather_expense_data(period_start, period_end),
            'deadlines': self._gather_deadlines_data(period_end),
            'recommendations': []
        }
        
        # Generate recommendations
        data['recommendations'] = self._generate_recommendations(data)
        
        # Generate markdown report
        report = self._generate_markdown_report(data)
        
        # Write to file
        if output_file is None:
            filename = f"Briefing_{period_end.strftime('%Y-%m-%d')}.md"
            output_file = str(self.briefings_path / filename)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f'Briefing generated: {output_file}')
        
        return output_file
    
    def _gather_revenue_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather revenue data from Odoo and local files."""
        revenue = {
            'total': 0.0,
            'invoices_count': 0,
            'paid_count': 0,
            'pending_count': 0,
            'invoices': [],
            'growth_rate': 0.0,
            'mrr': 0.0  # Monthly Recurring Revenue
        }
        
        if self.odoo_enabled:
            # Try to get data from Odoo
            try:
                # Add project root to path for imports
                project_root = Path(__file__).parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                from scripts.odoo_connector import OdooConnector
                connector = OdooConnector()

                if connector.authenticate():
                    invoices = connector.get_invoices(
                        last_days=(end - start).days
                    )
                    
                    if invoices:
                        for inv in invoices:
                            amount = float(inv.get('amount_total', 0))
                            revenue['total'] += amount
                            revenue['invoices_count'] += 1
                            
                            if inv.get('payment_state') == 'paid':
                                revenue['paid_count'] += 1
                            else:
                                revenue['pending_count'] += 1
                            
                            revenue['invoices'].append({
                                'name': inv.get('name', 'N/A'),
                                'customer': inv.get('partner_id', ['N/A', 'Unknown'])[1] if isinstance(inv.get('partner_id'), list) else inv.get('partner_id', 'Unknown'),
                                'amount': amount,
                                'date': inv.get('invoice_date', 'N/A'),
                                'status': inv.get('state', 'N/A'),
                                'payment': inv.get('payment_state', 'N/A')
                            })
                        
                        self.logger.info(f'Gathered {len(invoices)} invoices from Odoo')
            except Exception as e:
                self.logger.warning(f'Could not gather Odoo data: {e}')
        
        # Fallback: Read from synced accounting files
        if revenue['invoices_count'] == 0:
            revenue = self._gather_revenue_from_files(start, end, revenue)
        
        return revenue
    
    def _gather_revenue_from_files(self, start: datetime, end: datetime, revenue: Dict) -> Dict:
        """Gather revenue from local accounting files."""
        # Look for Odoo sync files
        if self.accounting_path.exists():
            for file in self.accounting_path.glob('odoo_invoices_*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    # Parse markdown table (simplified)
                    if 'Total Amount:' in content:
                        for line in content.split('\n'):
                            if 'Total Amount:' in line:
                                amount_str = line.split('$')[1].split()[0].replace(',', '')
                                revenue['total'] += float(amount_str)
                                break
                except Exception as e:
                    self.logger.warning(f'Could not parse {file.name}: {e}')
        
        # Look for payment logs
        if self.logs_path.exists():
            for log_file in self.logs_path.glob('odoo_*.log'):
                try:
                    content = log_file.read_text(encoding='utf-8')
                    # Count successful invoice creations
                    revenue['invoices_count'] += content.count('Invoice created')
                except:
                    pass
        
        return revenue
    
    def _gather_task_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather task completion data from Done folder."""
        tasks = {
            'completed': 0,
            'pending': 0,
            'overdue': 0,
            'by_category': {},
            'bottlenecks': [],
            'completed_tasks': []
        }
        
        if self.done_path.exists():
            for file in self.done_path.iterdir():
                if file.is_file() and file.suffix == '.md':
                    try:
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if start <= mtime <= end:
                            tasks['completed'] += 1
                            
                            # Try to extract category from filename
                            name = file.stem
                            if '_' in name:
                                category = name.split('_')[0]
                                tasks['by_category'][category] = tasks['by_category'].get(category, 0) + 1
                            
                            tasks['completed_tasks'].append({
                                'name': name,
                                'completed_at': mtime.isoformat()
                            })
                    except Exception as e:
                        self.logger.warning(f'Could not process {file.name}: {e}')
        
        # Count pending tasks
        needs_action_path = self.vault_path / 'Needs_Action'
        if needs_action_path.exists():
            tasks['pending'] = len(list(needs_action_path.glob('*.md')))
        
        return tasks
    
    def _gather_social_media_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather social media performance data."""
        social = {
            'facebook': {
                'posts': 0,
                'total_reach': 0,
                'engagement': 0,
                'post_details': []
            },
            'instagram': {
                'posts': 0,
                'followers_gained': 0,
                'avg_likes': 0
            },
            'linkedin': {
                'posts': 0,
                'impressions': 0,
                'connections': 0,
                'post_details': []
            }
        }
        
        # Check both vault Logs/ and project-level Logs/
        logs_paths_to_check = [self.logs_path]
        if self.project_logs_path.exists() and self.project_logs_path != self.logs_path:
            logs_paths_to_check.append(self.project_logs_path)
        
        for logs_path in logs_paths_to_check:
            if not logs_path.exists():
                continue
                
            # Facebook posts
            fb_log = logs_path / 'facebook_posts.jsonl'
            if fb_log.exists() and self.facebook_enabled:
                try:
                    with open(fb_log, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                post = json.loads(line)
                                ts = post.get('timestamp', '')
                                # Handle both ISO formats
                                if ts.endswith('Z'):
                                    post_date = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                                else:
                                    post_date = datetime.fromisoformat(ts)
                                
                                if start <= post_date <= end:
                                    social['facebook']['posts'] += 1
                                    # Store post details for report
                                    if post.get('result') == 'success':
                                        social['facebook']['post_details'].append({
                                            'date': post_date.strftime('%Y-%m-%d'),
                                            'message': post.get('parameters', {}).get('message', post.get('content', ''))[:80],
                                            'post_id': post.get('post_id', 'N/A')
                                        })
                            except (json.JSONDecodeError, ValueError) as e:
                                self.logger.warning(f'Could not parse Facebook log line: {e}')
                                continue
                    self.logger.info(f"Found {social['facebook']['posts']} Facebook posts in period from {logs_path}")
                except Exception as e:
                    self.logger.warning(f'Could not parse Facebook logs: {e}')

            # LinkedIn posts
            li_log = logs_path / 'linkedin_posts.jsonl'
            if li_log.exists() and self.linkedin_enabled:
                try:
                    with open(li_log, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                post = json.loads(line)
                                ts = post.get('timestamp', '')
                                # Handle both ISO formats
                                if ts.endswith('Z'):
                                    post_date = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                                else:
                                    post_date = datetime.fromisoformat(ts)
                                
                                if start <= post_date <= end:
                                    if post.get('success', False):
                                        social['linkedin']['posts'] += 1
                                        # Store post details for report
                                        social['linkedin']['post_details'].append({
                                            'date': post_date.strftime('%Y-%m-%d'),
                                            'content': post.get('content', '')[:80],
                                            'post_id': post.get('post_id', 'N/A')
                                        })
                            except (json.JSONDecodeError, ValueError) as e:
                                self.logger.warning(f'Could not parse LinkedIn log line: {e}')
                                continue
                    self.logger.info(f"Found {social['linkedin']['posts']} successful LinkedIn posts in period from {logs_path}")
                except Exception as e:
                    self.logger.warning(f'Could not parse LinkedIn logs: {e}')
        
        return social
    
    def _gather_customer_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather customer data."""
        customers = {
            'total': 0,
            'new_customers': 0,
            'active_customers': 0,
            'top_customers': []
        }
        
        if self.odoo_enabled:
            try:
                # Add project root to path for imports
                project_root = Path(__file__).parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                from scripts.odoo_connector import OdooConnector
                connector = OdooConnector()

                if connector.authenticate():
                    all_customers = connector.list_customers(limit=100)
                    
                    if all_customers:
                        customers['total'] = len(all_customers)
                        
                        # Count new customers (simplified - would need created_date)
                        customers['new_customers'] = 0  # Would need date filtering
                        
                        customers['top_customers'] = all_customers[:5]
                        
                        self.logger.info(f'Gathered {len(all_customers)} customers from Odoo')
            except Exception as e:
                self.logger.warning(f'Could not gather Odoo customer data: {e}')
        
        return customers
    
    def _gather_expense_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Gather expense data."""
        expenses = {
            'total': 0.0,
            'by_category': {},
            'subscriptions': [],
            'unusual_expenses': []
        }
        
        # Read from accounting files
        if self.accounting_path.exists():
            for file in self.accounting_path.glob('*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    # Look for expense indicators
                    if 'subscription' in content.lower():
                        # Extract subscription info
                        pass
                except Exception as e:
                    self.logger.warning(f'Could not parse {file.name}: {e}')
        
        return expenses
    
    def _gather_deadlines_data(self, current_date: datetime) -> Dict[str, Any]:
        """Gather upcoming deadlines."""
        deadlines = {
            'urgent': [],  # Within 7 days
            'upcoming': [],  # Within 30 days
            'overdue': []
        }
        
        # Read from Business_Goals.md
        goals_file = self.vault_path / 'Business_Goals.md'
        if goals_file.exists():
            try:
                content = goals_file.read_text(encoding='utf-8')
                # Parse deadlines from document (simplified)
                if 'Important Deadlines' in content:
                    # Extract deadline section
                    pass
            except Exception as e:
                self.logger.warning(f'Could not parse Business_Goals.md: {e}')
        
        # Add standard deadlines
        today = current_date.date()
        
        # Monthly deadlines
        if today.day <= 5:
            deadlines['upcoming'].append({
                'deadline': 'Invoice all clients',
                'due_date': today.replace(day=1).strftime('%Y-%m-%d'),
                'type': 'recurring'
            })
        
        # Quarterly tax deadline (example)
        if today.month in [1, 4, 7, 10] and today.day <= 15:
            deadlines['upcoming'].append({
                'deadline': 'Quarterly tax estimation',
                'due_date': f"{today.year}-{today.month}-15",
                'type': 'quarterly'
            })
        
        return deadlines
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate proactive recommendations based on data."""
        recommendations = []

        # Revenue recommendations
        revenue = data.get('revenue', {})
        if revenue.get('total', 0) == 0:
            recommendations.append({
                'category': 'Revenue',
                'priority': 'high',
                'issue': 'No revenue recorded this period',
                'action': 'Review Odoo integration and create first invoices',
                'impact': 'Establish baseline revenue tracking'
            })
        elif revenue.get('pending_count', 0) > 5:
            recommendations.append({
                'category': 'Revenue',
                'priority': 'high',
                'issue': f"{revenue['pending_count']} invoices awaiting payment",
                'action': 'Send payment reminder emails to overdue clients',
                'impact': 'Improve cash flow'
            })

        # Task recommendations
        tasks = data.get('tasks', {})
        tasks_completed = tasks.get('completed', 0)
        if tasks_completed == 0:
            recommendations.append({
                'category': 'Productivity',
                'priority': 'high',
                'issue': 'No tasks completed this period',
                'action': 'Review workflow and identify blockers',
                'impact': 'Resume productivity'
            })
        elif tasks.get('pending', 0) > 10:
            recommendations.append({
                'category': 'Productivity',
                'priority': 'medium',
                'issue': f"{tasks['pending']} tasks pending in Needs_Action",
                'action': 'Review and prioritize pending tasks',
                'impact': 'Reduce backlog'
            })

        # Social media recommendations
        social = data.get('social_media', {})
        fb_posts = social.get('facebook', {}).get('posts', 0)
        li_posts = social.get('linkedin', {}).get('posts', 0)
        total_posts = fb_posts + li_posts
        
        if total_posts == 0:
            recommendations.append({
                'category': 'Marketing',
                'priority': 'high',
                'issue': 'No social media activity this period',
                'action': 'Create and schedule social media content for next week',
                'impact': 'Maintain online presence'
            })
        elif total_posts < 3:
            recommendations.append({
                'category': 'Marketing',
                'priority': 'medium',
                'issue': f'Low social media activity ({total_posts} posts)',
                'action': 'Increase posting frequency to 3-5 times per week',
                'impact': 'Improve audience engagement'
            })
        else:
            recommendations.append({
                'category': 'Marketing',
                'priority': 'low',
                'issue': f'Good social media activity ({total_posts} posts)',
                'action': 'Consider cross-posting successful content to other platforms',
                'impact': 'Maximize content reach'
            })

        # Customer recommendations
        customers = data.get('customers', {})
        if customers.get('new_customers', 0) == 0 and customers.get('total', 0) == 0:
            recommendations.append({
                'category': 'Growth',
                'priority': 'medium',
                'issue': 'No customers in system',
                'action': 'Begin customer acquisition and onboarding',
                'impact': 'Business growth'
            })
        elif customers.get('new_customers', 0) == 0 and customers.get('total', 0) > 0:
            recommendations.append({
                'category': 'Growth',
                'priority': 'medium',
                'issue': 'No new customers this period',
                'action': 'Launch customer acquisition campaign',
                'impact': 'Business growth'
            })

        return recommendations
    
    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate markdown briefing report."""
        period_start = data['period_start'].strftime('%Y-%m-%d')
        period_end = data['period_end'].strftime('%Y-%m-%d')
        
        # Calculate totals
        revenue_total = data['revenue'].get('total', 0)
        tasks_completed = data['tasks'].get('completed', 0)
        
        report = f"""---
generated: {data['generated_at'].isoformat()}
period: {period_start} to {period_end}
type: ceo_briefing
version: 1.0.0
---

# 📊 CEO Weekly Briefing

**Generated:** {data['generated_at'].strftime('%A, %B %d, %Y at %I:%M %p')}  
**Period:** {period_start} to {period_end}

---

## 🎯 Executive Summary

This week's performance overview with key highlights and areas requiring attention.

### Key Metrics at a Glance

| Metric | This Period | Status |
|--------|-------------|--------|
| **Revenue** | ${revenue_total:,.2f} | {"✅ On Track" if revenue_total > 0 else "⚠️ No Data"} |
| **Tasks Completed** | {tasks_completed} | {"✅ Good" if tasks_completed > 5 else "⚠️ Low"} |
| **New Customers** | {data['customers'].get('new_customers', 0)} | {"✅ Growing" if data['customers'].get('new_customers', 0) > 0 else "➡️ Stable"} |
| **Social Posts** | {data['social_media'].get('facebook', {}).get('posts', 0) + data['social_media'].get('linkedin', {}).get('posts', 0)} | {"✅ Active" if data['social_media'].get('facebook', {}).get('posts', 0) > 2 else "⚠️ Low"} |

---

## 💰 Revenue Analysis

### Financial Performance

| Metric | Value |
|--------|-------|
| **Total Revenue** | ${revenue_total:,.2f} |
| **Invoices Issued** | {data['revenue'].get('invoices_count', 0)} |
| **Paid Invoices** | {data['revenue'].get('paid_count', 0)} |
| **Pending Payment** | {data['revenue'].get('pending_count', 0)} |
| **Collection Rate** | {self._calculate_collection_rate(data['revenue']):.1f}% |

### Recent Invoices

"""
        
        # Add invoices table
        invoices = data['revenue'].get('invoices', [])
        if invoices:
            report += "| # | Invoice | Customer | Date | Amount | Status | Payment |\n"
            report += "|---|----------|----------|------|--------|--------|----------|\n"
            
            for i, inv in enumerate(invoices[:10], 1):  # Show top 10
                report += f"| {i} | {inv.get('name', 'N/A')} | {inv.get('customer', 'N/A')} | {inv.get('date', 'N/A')} | ${inv.get('amount', 0):,.2f} | {inv.get('status', 'N/A')} | {inv.get('payment', 'N/A')} |\n"
        else:
            report += "*No invoice data available. Ensure Odoo integration is configured.*\n"
        
        report += f"""
---

## ✅ Completed Tasks

### Task Summary

| Category | Completed |
|----------|-----------|
"""
        
        # Task breakdown by category
        by_category = data['tasks'].get('by_category', {})
        if by_category:
            for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                report += f"| {category} | {count} |\n"
        else:
            report += "| All Tasks | {} |\n".format(tasks_completed)
        
        report += f"""
**Total Completed:** {tasks_completed}  
**Pending:** {data['tasks'].get('pending', 0)}  

### Recent Completed Tasks

"""
        
        # List recent completed tasks
        completed_tasks = data['tasks'].get('completed_tasks', [])
        if completed_tasks:
            for task in completed_tasks[:10]:  # Show last 10
                report += f"- [x] {task.get('name', 'Task')} ({task.get('completed_at', 'N/A')[:10]})\n"
        else:
            report += "*No completed tasks found in this period.*\n"
        
        report += f"""
---

## 📱 Social Media Performance

### Facebook

| Metric | Value |
|--------|-------|
| **Posts** | {data['social_media'].get('facebook', {}).get('posts', 0)} |
| **Total Reach** | {data['social_media'].get('facebook', {}).get('total_reach', 'N/A')} |
| **Engagement** | {data['social_media'].get('facebook', {}).get('engagement', 'N/A')} |

"""
        
        # Add Facebook post details if available
        fb_posts = data['social_media'].get('facebook', {}).get('post_details', [])
        if fb_posts:
            report += "\n#### Recent Facebook Posts\n\n"
            report += "| Date | Content | Post ID |\n"
            report += "|------|---------|----------|\n"
            for post in fb_posts[-5:]:  # Show last 5
                report += f"| {post['date']} | {post['message']} | {post['post_id']} |\n"
            report += "\n"
        
        report += f"""### LinkedIn

| Metric | Value |
|--------|-------|
| **Posts** | {data['social_media'].get('linkedin', {}).get('posts', 0)} |
| **Impressions** | {data['social_media'].get('linkedin', {}).get('impressions', 'N/A')} |
| **New Connections** | {data['social_media'].get('linkedin', {}).get('connections', 'N/A')} |

"""
        
        # Add LinkedIn post details if available
        li_posts = data['social_media'].get('linkedin', {}).get('post_details', [])
        if li_posts:
            report += "\n#### Recent LinkedIn Posts\n\n"
            report += "| Date | Content | Post ID |\n"
            report += "|------|---------|----------|\n"
            for post in li_posts[-5:]:  # Show last 5
                report += f"| {post['date']} | {post['content']} | {post['post_id']} |\n"
            report += "\n"
        
        report += f"""### Instagram

| Metric | Value |
|--------|-------|
| **Posts** | {data['social_media'].get('instagram', {}).get('posts', 0)} |
| **Followers Gained** | {data['social_media'].get('instagram', {}).get('followers_gained', 'N/A')} |
| **Average Likes** | {data['social_media'].get('instagram', {}).get('avg_likes', 'N/A')} |

---

## 👥 Customer Overview

| Metric | Value |
|--------|-------|
| **Total Customers** | {data['customers'].get('total', 0)} |
| **New Customers** | {data['customers'].get('new_customers', 0)} |
| **Active Customers** | {data['customers'].get('active_customers', 0)} |

---

## 📅 Upcoming Deadlines

"""
        
        # Add deadlines
        deadlines = data.get('deadlines', {})
        if deadlines.get('upcoming'):
            report += "| Deadline | Due Date | Type |\n"
            report += "|----------|----------|------|\n"
            for deadline in deadlines['upcoming']:
                report += f"| {deadline['deadline']} | {deadline['due_date']} | {deadline['type']} |\n"
        else:
            report += "*No upcoming deadlines identified.*\n"
        
        report += f"""
---

## 💡 Proactive Recommendations

"""
        
        # Add recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec.get('priority', 'low'), '⚪')
                report += f"""
### {priority_emoji} {i}. {rec.get('category', 'General')}

- **Issue:** {rec.get('issue', 'N/A')}
- **Recommended Action:** {rec.get('action', 'N/A')}
- **Expected Impact:** {rec.get('impact', 'N/A')}

"""
        else:
            report += "*No specific recommendations at this time. Business operating normally.*\n"
        
        report += f"""
---

## 📈 Week-over-Week Comparison

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Revenue | ${revenue_total:,.2f} | $0.00 | - |
| Tasks Completed | {tasks_completed} | - | - |
| Social Posts | {data['social_media'].get('facebook', {}).get('posts', 0) + data['social_media'].get('linkedin', {}).get('posts', 0)} | - | - |

*Note: Historical comparison requires multiple briefing periods.*

---

## 📝 Notes & Comments

<!-- CEO can add notes here during review -->

---

*Briefing generated by AI Employee v1.0.0 (Gold Tier)*  
*Next briefing scheduled for: {(data['period_end'] + timedelta(days=7)).strftime('%Y-%m-%d')}*
"""
        
        return report
    
    def _calculate_collection_rate(self, revenue: Dict) -> float:
        """Calculate invoice collection rate."""
        total = revenue.get('invoices_count', 0)
        if total == 0:
            return 0.0
        return (revenue.get('paid_count', 0) / total) * 100


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--period', type=str, help='Period as YYYY-MM-DD:YYYY-MM-DD')
    parser.add_argument('--days', type=int, default=7, help='Number of days (default: 7)')
    parser.add_argument('--no-odoo', action='store_true', help='Disable Odoo integration')
    parser.add_argument('--no-facebook', action='store_true', help='Disable Facebook integration')
    parser.add_argument('--no-linkedin', action='store_true', help='Disable LinkedIn integration')
    parser.add_argument('--auto-schedule', action='store_true', help='Schedule weekly generation')
    
    args = parser.parse_args()
    
    # Create generator
    generator = CEOBriefingGenerator(
        odoo_enabled=not args.no_odoo,
        facebook_enabled=not args.no_facebook,
        linkedin_enabled=not args.no_linkedin
    )
    
    # Parse period
    if args.period:
        start_str, end_str = args.period.split(':')
        period_start = datetime.strptime(start_str, '%Y-%m-%d')
        period_end = datetime.strptime(end_str, '%Y-%m-%d')
    else:
        period_end = datetime.now()
        period_start = period_end - timedelta(days=args.days)
    
    # Generate briefing
    output_file = generator.generate_briefing(
        period_start=period_start,
        period_end=period_end,
        output_file=args.output
    )
    
    print(f"✅ CEO Briefing generated successfully!")
    print(f"   Output: {output_file}")
    print(f"   Period: {period_start.date()} to {period_end.date()}")
    
    if args.auto_schedule:
        print("\n📅 To schedule weekly generation, add to Task Scheduler:")
        print(f"   python scripts/ceo_briefing_generator.py --days 7")
        print(f"   Schedule: Every Monday at 7:00 AM")


if __name__ == '__main__':
    main()
