"""
Example A2A Agents

Demonstrates inter-agent communication with practical examples:
- Email Agent: Handles email operations
- Social Media Agent: Handles social media posting
- Calendar Agent: Handles calendar operations

Usage:
    # Start broker first
    python scripts/a2a/a2a_broker.py

    # Start example agents in separate terminals
    python scripts/a2a/example_agents.py --agent email
    python scripts/a2a/example_agents.py --agent social
    python scripts/a2a/example_agents.py --agent calendar

    # Test inter-agent communication
    python scripts/a2a/test_a2a.py
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from a2a.a2a_agent import A2AAgent


class EmailAgent(A2AAgent):
    """Email handling agent with A2A capabilities."""

    def __init__(self, vault_path='AI_Employee_Vault'):
        super().__init__(
            agent_id='email-agent',
            capabilities=['email_send', 'email_read', 'email_draft', 'email_approve'],
            vault_path=vault_path
        )

        # Register custom handlers
        self.register_handler('task_request', self.handle_email_task)
        self.register_handler('query', self.handle_email_query)

    def handle_email_task(self, message):
        """Handle email task requests from other agents."""
        payload = message.get('payload', {})
        action = payload.get('action')

        self.logger.info(f'Email task received: {action}')

        if action == 'send_email':
            result = self._simulate_send_email(payload)
        elif action == 'draft_email':
            result = self._simulate_draft_email(payload)
        elif action == 'read_emails':
            result = self._simulate_read_emails(payload)
        else:
            result = {'error': f'Unknown action: {action}'}

        # Send response
        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            result,
            success='error' not in result
        )

    def handle_email_query(self, message):
        """Handle email queries."""
        question = message.get('payload', {}).get('question', '')
        self.logger.info(f'Email query: {question}')

        response = {
            'answer': f'Email agent status: operational. Query: {question}',
            'unread_count': 5,
            'pending_approvals': 2
        }

        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            response,
            success=True
        )

    def _simulate_send_email(self, payload):
        """Simulate sending email."""
        to = payload.get('to', 'unknown')
        subject = payload.get('subject', 'No subject')
        self.logger.info(f'Simulating email send: {to} - {subject}')
        return {
            'sent': True,
            'to': to,
            'subject': subject,
            'message_id': f'email-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }

    def _simulate_draft_email(self, payload):
        """Simulate drafting email."""
        return {
            'drafted': True,
            'subject': payload.get('subject', 'Draft'),
            'pending_approval': True
        }

    def _simulate_read_emails(self, payload):
        """Simulate reading emails."""
        return {
            'unread_count': 5,
            'important_count': 2,
            'emails': [
                {'from': 'client@example.com', 'subject': 'Invoice Request'},
                {'from': 'boss@example.com', 'subject': 'Meeting Tomorrow'}
            ]
        }


class SocialMediaAgent(A2AAgent):
    """Social media handling agent with A2A capabilities."""

    def __init__(self, vault_path='AI_Employee_Vault'):
        super().__init__(
            agent_id='social-agent',
            capabilities=['linkedin_post', 'facebook_post', 'instagram_post', 'social_schedule'],
            vault_path=vault_path
        )

        self.register_handler('task_request', self.handle_social_task)
        self.register_handler('query', self.handle_social_query)

    def handle_social_task(self, message):
        """Handle social media task requests."""
        payload = message.get('payload', {})
        action = payload.get('action')

        self.logger.info(f'Social task received: {action}')

        if action == 'post_linkedin':
            result = self._simulate_linkedin_post(payload)
        elif action == 'post_facebook':
            result = self._simulate_facebook_post(payload)
        elif action == 'post_instagram':
            result = self._simulate_instagram_post(payload)
        elif action == 'get_schedule':
            result = self._get_social_schedule()
        else:
            result = {'error': f'Unknown action: {action}'}

        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            result,
            success='error' not in result
        )

    def handle_social_query(self, message):
        """Handle social media queries."""
        response = {
            'linkedin_posts_this_week': 4,
            'facebook_posts_this_week': 1,
            'instagram_posts_this_week': 0,
            'next_scheduled_post': '2026-04-15T10:00:00'
        }

        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            response,
            success=True
        )

    def _simulate_linkedin_post(self, payload):
        """Simulate LinkedIn post."""
        content = payload.get('content', '')[:50]
        self.logger.info(f'Simulating LinkedIn post: {content}...')
        return {
            'posted': True,
            'platform': 'linkedin',
            'post_id': f'li-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }

    def _simulate_facebook_post(self, payload):
        """Simulate Facebook post."""
        return {
            'posted': True,
            'platform': 'facebook',
            'post_id': f'fb-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }

    def _simulate_instagram_post(self, payload):
        """Simulate Instagram post."""
        return {
            'posted': True,
            'platform': 'instagram',
            'post_id': f'ig-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }

    def _get_social_schedule(self):
        """Get social media schedule."""
        return {
            'scheduled_posts': [
                {'platform': 'linkedin', 'time': '2026-04-15T10:00:00'},
                {'platform': 'facebook', 'time': '2026-04-15T14:00:00'}
            ]
        }


class CalendarAgent(A2AAgent):
    """Calendar management agent with A2A capabilities."""

    def __init__(self, vault_path='AI_Employee_Vault'):
        super().__init__(
            agent_id='calendar-agent',
            capabilities=['calendar_create', 'calendar_read', 'calendar_check_conflicts'],
            vault_path=vault_path
        )

        self.register_handler('task_request', self.handle_calendar_task)
        self.register_handler('query', self.handle_calendar_query)

    def handle_calendar_task(self, message):
        """Handle calendar task requests."""
        payload = message.get('payload', {})
        action = payload.get('action')

        self.logger.info(f'Calendar task received: {action}')

        if action == 'create_event':
            result = self._simulate_create_event(payload)
        elif action == 'check_availability':
            result = self._simulate_check_availability(payload)
        elif action == 'check_conflicts':
            result = self._simulate_check_conflicts(payload)
        else:
            result = {'error': f'Unknown action: {action}'}

        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            result,
            success='error' not in result
        )

    def handle_calendar_query(self, message):
        """Handle calendar queries."""
        response = {
            'events_today': 3,
            'events_this_week': 8,
            'next_event': 'Team Meeting at 2026-04-15T10:00:00'
        }

        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            response,
            success=True
        )

    def _simulate_create_event(self, payload):
        """Simulate event creation."""
        title = payload.get('title', 'Untitled')
        self.logger.info(f'Simulating event creation: {title}')
        return {
            'created': True,
            'event_id': f'cal-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'title': title
        }

    def _simulate_check_availability(self, payload):
        """Simulate availability check."""
        return {
            'available': True,
            'suggested_times': [
                '2026-04-15T14:00:00',
                '2026-04-15T15:00:00',
                '2026-04-16T10:00:00'
            ]
        }

    def _simulate_check_conflicts(self, payload):
        """Simulate conflict check."""
        return {
            'has_conflicts': False,
            'conflicts': []
        }


def main():
    """Start example agent."""
    parser = argparse.ArgumentParser(description='Example A2A Agents')
    parser.add_argument('--agent', type=str, required=True,
                        choices=['email', 'social', 'calendar'],
                        help='Agent to start')
    parser.add_argument('--vault', type=str, default='AI_Employee_Vault',
                        help='Vault path')
    parser.add_argument('--broker', type=str, default='http://localhost:8899',
                        help='Broker URL')
    parser.add_argument('--log-level', type=str, default='INFO',
                        help='Log level')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Start agent
    if args.agent == 'email':
        agent = EmailAgent(vault_path=args.vault)
    elif args.agent == 'social':
        agent = SocialMediaAgent(vault_path=args.vault)
    elif args.agent == 'calendar':
        agent = CalendarAgent(vault_path=args.vault)
    else:
        print(f"Unknown agent: {args.agent}")
        return

    print(f"Starting {args.agent} agent...")
    agent.start()


if __name__ == '__main__':
    main()
