"""
A2A Message Broker

Central HTTP server that routes messages between agents.
Supports:
- Direct messaging (agent-to-agent)
- Broadcast messaging (one-to-all)
- Task delegation with responses
- Agent registration and discovery
- Message queuing for offline agents

Usage:
    python scripts/a2a/a2a_broker.py
    python scripts/a2a/a2a_broker.py --port 8899
"""

import os
import sys
import json
import uuid
import logging
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MessageQueue:
    """In-memory message queue for offline agents."""

    def __init__(self):
        self.queues: Dict[str, List[dict]] = {}
        self.lock = threading.Lock()

    def enqueue(self, agent_id: str, message: dict):
        """Add message to agent's queue."""
        with self.lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = []
            self.queues[agent_id].append(message)

    def dequeue(self, agent_id: str) -> List[dict]:
        """Get and clear all messages for agent."""
        with self.lock:
            messages = self.queues.get(agent_id, [])
            self.queues[agent_id] = []
            return messages

    def peek(self, agent_id: str) -> int:
        """Count pending messages for agent."""
        with self.lock:
            return len(self.queues.get(agent_id, []))


class A2ARegistry:
    """Agent registration and discovery."""

    def __init__(self):
        self.agents: Dict[str, dict] = {}
        self.lock = threading.Lock()

    def register(self, agent_id: str, capabilities: List[str], endpoint: str = None) -> dict:
        """Register an agent."""
        with self.lock:
            self.agents[agent_id] = {
                'agent_id': agent_id,
                'capabilities': capabilities,
                'endpoint': endpoint,
                'status': 'online',
                'registered_at': datetime.now().isoformat(),
                'last_heartbeat': datetime.now().isoformat(),
                'message_count': 0
            }
            return self.agents[agent_id]

    def unregister(self, agent_id: str):
        """Unregister an agent."""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]['status'] = 'offline'

    def heartbeat(self, agent_id: str):
        """Update agent heartbeat."""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]['last_heartbeat'] = datetime.now().isoformat()
                self.agents[agent_id]['status'] = 'online'

    def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get agent details."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[dict]:
        """List all registered agents."""
        return list(self.agents.values())

    def find_by_capability(self, capability: str) -> List[dict]:
        """Find agents with specific capability."""
        return [
            agent for agent in self.agents.values()
            if capability in agent.get('capabilities', [])
        ]

    def increment_message_count(self, agent_id: str):
        """Track message count for agent."""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]['message_count'] += 1

    def check_stale_agents(self, timeout_seconds: int = 60):
        """Mark agents as stale if no heartbeat."""
        cutoff = datetime.now() - timedelta(seconds=timeout_seconds)
        with self.lock:
            for agent in self.agents.values():
                last_hb = datetime.fromisoformat(agent['last_heartbeat'])
                if last_hb < cutoff:
                    agent['status'] = 'stale'


class A2ABroker:
    """
    A2A Message Broker

    Central router for agent-to-agent communication.
    """

    def __init__(self, host: str = 'localhost', port: int = 8899):
        self.host = host
        self.port = port
        self.registry = A2ARegistry()
        self.message_queue = MessageQueue()
        self.message_log: List[dict] = []
        self.lock = threading.Lock()

        # Setup logging
        self.logger = logging.getLogger('A2ABroker')

        # Create request handler class with broker reference
        self.handler_class = self._create_handler_class()

    def _create_handler_class(self):
        """Create HTTP request handler with broker access."""
        broker = self

        class A2ARequestHandler(BaseHTTPRequestHandler):
            """HTTP request handler for A2A broker."""

            def log_message(self, format, *args):
                """Suppress default logging."""
                broker.logger.debug(format % args)

            def _send_json_response(self, status_code: int, data: dict):
                """Send JSON response."""
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

            def _read_body(self) -> dict:
                """Read and parse JSON body."""
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))

            def do_GET(self):
                """Handle GET requests."""
                parsed = urlparse(self.path)
                path = parsed.path
                params = parse_qs(parsed.query)

                try:
                    # Health check
                    if path == '/health':
                        self._send_json_response(200, {
                            'status': 'healthy',
                            'agents': len(broker.registry.list_agents()),
                            'uptime': 'running'
                        })

                    # List all agents
                    elif path == '/agents':
                        agents = broker.registry.list_agents()
                        self._send_json_response(200, {'agents': agents})

                    # Get specific agent
                    elif path.startswith('/agents/'):
                        agent_id = path.split('/')[-1]
                        agent = broker.registry.get_agent(agent_id)
                        if agent:
                            self._send_json_response(200, agent)
                        else:
                            self._send_json_response(404, {'error': f'Agent not found: {agent_id}'})

                    # Find agents by capability
                    elif path == '/find':
                        capability = params.get('capability', [None])[0]
                        if capability:
                            agents = broker.registry.find_by_capability(capability)
                            self._send_json_response(200, {'agents': agents})
                        else:
                            self._send_json_response(400, {'error': 'capability parameter required'})

                    # Get pending messages for agent
                    elif path.startswith('/messages/'):
                        agent_id = path.split('/')[-1]
                        messages = broker.message_queue.dequeue(agent_id)
                        self._send_json_response(200, {
                            'agent_id': agent_id,
                            'messages': messages,
                            'count': len(messages)
                        })

                    # Get message log
                    elif path == '/log':
                        limit = int(params.get('limit', [50])[0])
                        with broker.lock:
                            log = broker.message_log[-limit:]
                        self._send_json_response(200, {'log': log})

                    else:
                        self._send_json_response(404, {'error': 'Not found'})

                except Exception as e:
                    broker.logger.error(f'GET error: {e}')
                    self._send_json_response(500, {'error': str(e)})

            def do_POST(self):
                """Handle POST requests."""
                parsed = urlparse(self.path)
                path = parsed.path

                try:
                    body = self._read_body()

                    # Register agent
                    if path == '/register':
                        agent_id = body.get('agent_id')
                        capabilities = body.get('capabilities', [])
                        endpoint = body.get('endpoint')

                        if not agent_id:
                            self._send_json_response(400, {'error': 'agent_id required'})
                            return

                        agent = broker.registry.register(agent_id, capabilities, endpoint)
                        broker.logger.info(f'Agent registered: {agent_id}')
                        self._send_json_response(200, agent)

                    # Heartbeat
                    elif path == '/heartbeat':
                        agent_id = body.get('agent_id')
                        if agent_id:
                            broker.registry.heartbeat(agent_id)
                            self._send_json_response(200, {'status': 'ok'})
                        else:
                            self._send_json_response(400, {'error': 'agent_id required'})

                    # Send message
                    elif path == '/send':
                        result = broker._handle_send_message(body)
                        self._send_json_response(200, result)

                    # Broadcast message
                    elif path == '/broadcast':
                        result = broker._handle_broadcast(body)
                        self._send_json_response(200, result)

                    # Unregister agent
                    elif path == '/unregister':
                        agent_id = body.get('agent_id')
                        if agent_id:
                            broker.registry.unregister(agent_id)
                            broker.logger.info(f'Agent unregistered: {agent_id}')
                            self._send_json_response(200, {'status': 'ok'})
                        else:
                            self._send_json_response(400, {'error': 'agent_id required'})

                    else:
                        self._send_json_response(404, {'error': 'Not found'})

                except Exception as e:
                    broker.logger.error(f'POST error: {e}')
                    self._send_json_response(500, {'error': str(e)})

        return A2ARequestHandler

    def _handle_send_message(self, body: dict) -> dict:
        """Handle direct message sending."""
        from_agent = body.get('from_agent')
        to_agent = body.get('to_agent')
        message_type = body.get('message_type')
        payload = body.get('payload', {})
        priority = body.get('priority', 'normal')

        if not from_agent or not to_agent or not message_type:
            return {'error': 'from_agent, to_agent, and message_type required'}

        # Create message
        message = {
            'message_id': str(uuid.uuid4()),
            'from_agent': from_agent,
            'to_agent': to_agent,
            'message_type': message_type,
            'payload': payload,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }

        # Check if target agent is online
        target = self.registry.get_agent(to_agent)
        if target and target['status'] == 'online':
            message['status'] = 'delivered'
            self.logger.info(f'Message delivered: {from_agent} -> {to_agent} ({message_type})')
        else:
            # Queue for offline agent
            self.message_queue.enqueue(to_agent, message)
            message['status'] = 'queued'
            self.logger.info(f'Message queued: {from_agent} -> {to_agent} ({message_type})')

        # Log message
        with self.lock:
            self.message_log.append(message)
            # Keep only last 1000 messages
            if len(self.message_log) > 1000:
                self.message_log = self.message_log[-1000:]

        # Increment message count
        self.registry.increment_message_count(from_agent)

        return {
            'status': message['status'],
            'message_id': message['message_id'],
            'to_agent': to_agent
        }

    def _handle_broadcast(self, body: dict) -> dict:
        """Handle broadcast message to all agents."""
        from_agent = body.get('from_agent')
        message_type = body.get('message_type')
        payload = body.get('payload', {})

        if not from_agent or not message_type:
            return {'error': 'from_agent and message_type required'}

        agents = self.registry.list_agents()
        delivered = 0
        queued = 0

        for agent in agents:
            if agent['agent_id'] == from_agent:
                continue  # Don't send to self

            message = {
                'message_id': str(uuid.uuid4()),
                'from_agent': from_agent,
                'to_agent': agent['agent_id'],
                'message_type': message_type,
                'payload': payload,
                'priority': 'broadcast',
                'timestamp': datetime.now().isoformat(),
                'status': 'delivered' if agent['status'] == 'online' else 'queued'
            }

            if agent['status'] == 'online':
                delivered += 1
            else:
                self.message_queue.enqueue(agent['agent_id'], message)
                queued += 1

            with self.lock:
                self.message_log.append(message)

        self.logger.info(f'Broadcast: {from_agent} -> {delivered} delivered, {queued} queued')

        return {
            'delivered': delivered,
            'queued': queued,
            'total_agents': len(agents) - 1
        }

    def start(self):
        """Start the broker server."""
        server = HTTPServer((self.host, self.port), self.handler_class)
        self.logger.info(f'A2A Broker starting on {self.host}:{self.port}')

        # Start stale agent checker
        stale_checker = threading.Thread(target=self._check_stale_agents, daemon=True)
        stale_checker.start()

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info('Broker shutting down')
            server.shutdown()

    def _check_stale_agents(self):
        """Periodically check for stale agents."""
        while True:
            try:
                self.registry.check_stale_agents(timeout_seconds=60)
            except Exception as e:
                self.logger.error(f'Stale check error: {e}')
            time.sleep(30)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='A2A Message Broker')
    parser.add_argument('--host', type=str, default='localhost', help='Bind host')
    parser.add_argument('--port', type=int, default=8899, help='Bind port')
    parser.add_argument('--log-level', type=str, default='INFO', help='Log level')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and start broker
    broker = A2ABroker(host=args.host, port=args.port)
    print(f"A2A Broker running on http://{args.host}:{args.port}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print(f"List agents: http://{args.host}:{args.port}/agents")
    broker.start()


if __name__ == '__main__':
    main()
