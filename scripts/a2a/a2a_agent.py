"""
A2A Base Agent

Base class for all agents with A2A communication capabilities.
Provides message handling, task delegation, and coordination features.

Usage:
    from a2a.a2a_agent import A2AAgent

    class EmailAgent(A2AAgent):
        def __init__(self):
            super().__init__(
                agent_id="email-agent",
                capabilities=["email_send", "email_read", "email_draft"]
            )

        def handle_task_request(self, message):
            # Process task from another agent
            action = message['payload'].get('action')
            if action == 'send_email':
                result = self.send_email(message['payload'])
                self.send_task_response(message['from_agent'], message['message_id'], result)

    agent = EmailAgent()
    agent.start()
"""

import os
import sys
import json
import logging
import threading
import time
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a.a2a_client import A2AClient


class A2AAgent:
    """
    Base class for A2A-enabled agents.

    Provides:
    - Automatic registration with broker
    - Message processing loop
    - Task delegation to other agents
    - Heartbeat management
    - Message handlers for different message types
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        broker_url: str = 'http://localhost:8899',
        vault_path: str = 'AI_Employee_Vault',
        heartbeat_interval: int = 30,
        poll_interval: int = 5
    ):
        """
        Initialize A2A agent.

        Args:
            agent_id: Unique agent identifier
            capabilities: List of capabilities this agent provides
            broker_url: URL of A2A broker
            vault_path: Path to Obsidian vault
            heartbeat_interval: Seconds between heartbeats
            poll_interval: Seconds between message polls
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.broker_url = broker_url
        self.vault_path = Path(vault_path)
        self.heartbeat_interval = heartbeat_interval
        self.poll_interval = poll_interval

        # A2A client
        self.client = A2AClient(broker_url)

        # Message handlers
        self.handlers: Dict[str, Callable] = {
            'task_request': self._default_task_handler,
            'task_response': self._default_response_handler,
            'query': self._default_query_handler,
            'status_update': self._default_status_handler,
            'broadcast': self._default_broadcast_handler
        }

        # State
        self.running = False
        self.message_count = 0
        self.task_count = 0

        # Setup logging
        self.logger = logging.getLogger(f'Agent:{agent_id}')

    # ========== Message Handlers ==========

    def register_handler(self, message_type: str, handler: Callable):
        """Register custom handler for message type."""
        self.handlers[message_type] = handler
        self.logger.info(f'Handler registered: {message_type}')

    def _default_task_handler(self, message: dict):
        """Default task request handler - override in subclass."""
        self.logger.warning(f'No task handler implemented for: {message}')
        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            {'error': 'Task handler not implemented'},
            success=False
        )

    def _default_response_handler(self, message: dict):
        """Default task response handler."""
        result = message.get('payload', {})
        success = result.get('success', False)
        self.logger.info(f'Task response from {message["from_agent"]}: success={success}')

    def _default_query_handler(self, message: dict):
        """Default query handler - override in subclass."""
        question = message.get('payload', {}).get('question', '')
        self.logger.info(f'Query from {message["from_agent"]}: {question}')
        self.send_task_response(
            message['from_agent'],
            message.get('message_id'),
            {'answer': f'Query received: {question}'},
            success=True
        )

    def _default_status_handler(self, message: dict):
        """Default status update handler."""
        self.logger.info(f'Status from {message["from_agent"]}: {message.get("payload", {})}')

    def _default_broadcast_handler(self, message: dict):
        """Default broadcast handler."""
        self.logger.info(f'Broadcast from {message["from_agent"]}: {message.get("payload", {})}')

    # ========== Messaging ==========

    def send_message(self, to_agent: str, message_type: str, payload: dict = None,
                     priority: str = 'normal') -> dict:
        """Send message to another agent."""
        result = self.client.send_message(
            self.agent_id, to_agent, message_type, payload, priority
        )
        if 'error' not in result:
            self.message_count += 1
            self.logger.info(f'Message sent to {to_agent}: {message_type}')
        return result

    def send_task_request(self, to_agent: str, task: dict) -> dict:
        """Delegate task to another agent."""
        result = self.client.send_task_request(self.agent_id, to_agent, task)
        if 'error' not in result:
            self.task_count += 1
            self.logger.info(f'Task delegated to {to_agent}: {task.get("action")}')
        return result

    def send_task_response(self, to_agent: str, task_id: str, result: dict,
                           success: bool = True) -> dict:
        """Respond to delegated task."""
        return self.client.send_task_response(
            self.agent_id, to_agent, task_id, result, success
        )

    def send_query(self, to_agent: str, question: str) -> dict:
        """Query another agent."""
        return self.client.send_query(self.agent_id, to_agent, question)

    def broadcast_status(self, status: dict) -> dict:
        """Broadcast status to all agents."""
        return self.client.broadcast(self.agent_id, 'status_update', status)

    # ========== Discovery ==========

    def find_agents_with_capability(self, capability: str) -> List[dict]:
        """Find agents with specific capability."""
        result = self.client.find_by_capability(capability)
        return result.get('agents', [])

    def list_all_agents(self) -> List[dict]:
        """List all registered agents."""
        result = self.client.list_agents()
        return result.get('agents', [])

    # ========== Lifecycle ==========

    def start(self):
        """Start agent message processing loop."""
        self.logger.info(f'Starting agent: {self.agent_id}')

        # Register with broker
        result = self.client.register(self.agent_id, self.capabilities)
        if 'error' in result:
            self.logger.error(f'Failed to register: {result["error"]}')
            return

        self.logger.info(f'Agent registered: {self.agent_id}')
        self.running = True

        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()

        # Start message processing loop
        self._message_loop()

    def stop(self):
        """Stop agent."""
        self.running = False
        self.client.unregister(self.agent_id)
        self.logger.info(f'Agent stopped: {self.agent_id}')

    def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.running:
            try:
                self.client.heartbeat(self.agent_id)
            except Exception as e:
                self.logger.error(f'Heartbeat failed: {e}')
            time.sleep(self.heartbeat_interval)

    def _message_loop(self):
        """Poll for and process messages."""
        self.logger.info(f'Message loop started for {self.agent_id}')

        while self.running:
            try:
                # Get pending messages
                result = self.client.get_messages(self.agent_id)
                messages = result.get('messages', [])

                for message in messages:
                    self._process_message(message)

            except Exception as e:
                self.logger.error(f'Message loop error: {e}')

            time.sleep(self.poll_interval)

    def _process_message(self, message: dict):
        """Process a single message."""
        message_type = message.get('message_type', 'unknown')
        handler = self.handlers.get(message_type)

        if handler:
            try:
                handler(message)
            except Exception as e:
                self.logger.error(f'Handler error for {message_type}: {e}')
                # Send error response
                if 'from_agent' in message:
                    self.send_task_response(
                        message['from_agent'],
                        message.get('message_id'),
                        {'error': str(e)},
                        success=False
                    )
        else:
            self.logger.warning(f'No handler for message type: {message_type}')

    def get_status(self) -> dict:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'running': self.running,
            'message_count': self.message_count,
            'task_count': self.task_count,
            'timestamp': datetime.now().isoformat()
        }
