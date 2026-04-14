"""
A2A (Agent-to-Agent) Communication Protocol

Enables direct inter-agent communication without file-based triggering.
Supports task delegation, queries, broadcasts, and status updates.

Architecture:
- A2ABroker: Central HTTP message router (a2a_broker.py)
- A2AAgent: Base class with A2A capabilities (a2a_agent.py)
- A2AClient: HTTP client for agent communication (a2a_client.py)
- A2ARegistry: Agent discovery and capability registration (a2a_registry.py)

Usage:
    # Start broker
    python scripts/a2a/a2a_broker.py

    # Use in agents
    from a2a.a2a_agent import A2AAgent
    agent = A2AAgent(agent_id="email-agent", capabilities=["email_send", "email_read"])
    agent.start()

    # Send message to another agent
    response = agent.send_message("social-agent", "task_request", {"action": "post", "content": "Hello"})
"""

from .a2a_broker import A2ABroker
from .a2a_agent import A2AAgent
from .a2a_client import A2AClient
from .a2a_registry import A2ARegistry

__all__ = ['A2ABroker', 'A2AAgent', 'A2AClient', 'A2ARegistry']
