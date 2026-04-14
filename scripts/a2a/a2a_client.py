"""
A2A Client Library

HTTP client for agent-to-agent communication via the A2A broker.
Used by all agents to send messages, query registry, and receive messages.

Usage:
    from a2a.a2a_client import A2AClient
    client = A2AClient(broker_url="http://localhost:8899")

    # Register agent
    client.register("email-agent", ["email_send", "email_read"])

    # Send message
    client.send_message("email-agent", "social-agent", "task_request", {"action": "post"})

    # Broadcast
    client.broadcast("orchestrator", "status_update", {"status": "healthy"})

    # Find agents
    agents = client.find_by_capability("email_send")

    # Get pending messages
    messages = client.get_messages("email-agent")
"""

import json
import logging
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from datetime import datetime


class A2AClient:
    """HTTP client for A2A broker."""

    def __init__(self, broker_url: str = 'http://localhost:8899'):
        """
        Initialize A2A client.

        Args:
            broker_url: URL of A2A broker
        """
        self.broker_url = broker_url.rstrip('/')
        self.logger = logging.getLogger('A2AClient')

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make HTTP request to broker."""
        url = f'{self.broker_url}{path}'

        try:
            if method == 'GET':
                req = Request(url)
            elif method == 'POST':
                body = json.dumps(data, ensure_ascii=False).encode('utf-8') if data else b'{}'
                req = Request(url, data=body, method='POST')
                req.add_header('Content-Type', 'application/json')
            else:
                raise ValueError(f'Unsupported method: {method}')

            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))

        except HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            self.logger.error(f'HTTP error {e.code}: {error_body}')
            try:
                return json.loads(error_body)
            except:
                return {'error': f'HTTP {e.code}: {error_body}'}

        except URLError as e:
            self.logger.error(f'Connection error: {e}')
            return {'error': f'Connection failed: {str(e)}'}

        except Exception as e:
            self.logger.error(f'Request error: {e}')
            return {'error': str(e)}

    # ========== Agent Registration ==========

    def register(self, agent_id: str, capabilities: List[str], endpoint: str = None) -> dict:
        """Register agent with broker."""
        return self._request('POST', '/register', {
            'agent_id': agent_id,
            'capabilities': capabilities,
            'endpoint': endpoint
        })

    def unregister(self, agent_id: str) -> dict:
        """Unregister agent from broker."""
        return self._request('POST', '/unregister', {'agent_id': agent_id})

    def heartbeat(self, agent_id: str) -> dict:
        """Send heartbeat to broker."""
        return self._request('POST', '/heartbeat', {'agent_id': agent_id})

    # ========== Messaging ==========

    def send_message(self, from_agent: str, to_agent: str, message_type: str,
                     payload: dict = None, priority: str = 'normal') -> dict:
        """
        Send message to specific agent.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            message_type: Type of message (task_request, task_response, query, etc.)
            payload: Message payload
            priority: Message priority (low, normal, high, urgent)

        Returns:
            Response with status and message_id
        """
        return self._request('POST', '/send', {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'message_type': message_type,
            'payload': payload or {},
            'priority': priority
        })

    def broadcast(self, from_agent: str, message_type: str, payload: dict = None) -> dict:
        """
        Broadcast message to all agents.

        Args:
            from_agent: Sender agent ID
            message_type: Type of message
            payload: Message payload

        Returns:
            Response with delivered/queued counts
        """
        return self._request('POST', '/broadcast', {
            'from_agent': from_agent,
            'message_type': message_type,
            'payload': payload or {}
        })

    def get_messages(self, agent_id: str) -> dict:
        """
        Get pending messages for agent.

        Args:
            agent_id: Agent ID to get messages for

        Returns:
            Response with messages list
        """
        return self._request('GET', f'/messages/{agent_id}')

    # ========== Discovery ==========

    def list_agents(self) -> dict:
        """List all registered agents."""
        return self._request('GET', '/agents')

    def get_agent(self, agent_id: str) -> dict:
        """Get specific agent details."""
        return self._request('GET', f'/agents/{agent_id}')

    def find_by_capability(self, capability: str) -> dict:
        """Find agents with specific capability."""
        return self._request('GET', f'/find?capability={capability}')

    # ========== Health & Status ==========

    def health_check(self) -> dict:
        """Check broker health."""
        return self._request('GET', '/health')

    def get_message_log(self, limit: int = 50) -> dict:
        """Get recent message log."""
        return self._request('GET', f'/log?limit={limit}')

    # ========== Convenience Methods ==========

    def send_task_request(self, from_agent: str, to_agent: str, task: dict) -> dict:
        """Send task delegation request."""
        return self.send_message(from_agent, to_agent, 'task_request', {
            'action': task.get('action'),
            'parameters': task.get('parameters', {}),
            'deadline': task.get('deadline'),
            'priority': task.get('priority', 'normal')
        })

    def send_task_response(self, from_agent: str, to_agent: str, task_id: str,
                           result: dict, success: bool = True) -> dict:
        """Send task completion response."""
        return self.send_message(from_agent, to_agent, 'task_response', {
            'task_id': task_id,
            'success': success,
            'result': result,
            'completed_at': datetime.now().isoformat()
        })

    def send_query(self, from_agent: str, to_agent: str, question: str) -> dict:
        """Send information query."""
        return self.send_message(from_agent, to_agent, 'query', {
            'question': question
        })

    def send_status_update(self, from_agent: str, status: dict, broadcast: bool = False) -> dict:
        """Send status update."""
        if broadcast:
            return self.broadcast(from_agent, 'status_update', status)
        else:
            # Status updates go to orchestr by default
            return self.send_message(from_agent, 'orchestrator', 'status_update', status)
