"""
A2A Agent Registry

Provides agent discovery and capability-based routing.
Agents can find each other by capability without knowing specific agent IDs.

Usage:
    from a2a.a2a_registry import A2ARegistry
    registry = A2ARegistry(broker_url="http://localhost:8899")

    # Find agent for specific capability
    agents = registry.find_by_capability("email_send")

    # Get best available agent for capability
    agent = registry.get_best_agent("email_send")

    # List all agents
    agents = registry.list_agents()
"""

import logging
from typing import Dict, List, Optional
from a2a.a2a_client import A2AClient


class A2ARegistry:
    """Agent discovery and capability-based routing."""

    def __init__(self, broker_url: str = 'http://localhost:8899'):
        """
        Initialize registry.

        Args:
            broker_url: URL of A2A broker
        """
        self.client = A2AClient(broker_url)
        self.logger = logging.getLogger('A2ARegistry')

    def list_agents(self) -> List[dict]:
        """List all registered agents."""
        result = self.client.list_agents()
        return result.get('agents', [])

    def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get specific agent details."""
        result = self.client.get_agent(agent_id)
        if 'error' in result:
            return None
        return result

    def find_by_capability(self, capability: str) -> List[dict]:
        """Find agents with specific capability."""
        result = self.client.find_by_capability(capability)
        agents = result.get('agents', [])
        self.logger.debug(f'Found {len(agents)} agents with capability: {capability}')
        return agents

    def get_best_agent(self, capability: str) -> Optional[dict]:
        """
        Get best available agent for capability.

        Selection criteria:
        1. Online status
        2. Lowest message count (load balancing)
        3. Most recent heartbeat

        Args:
            capability: Required capability

        Returns:
            Best agent dict or None
        """
        agents = self.find_by_capability(capability)

        if not agents:
            return None

        # Filter online agents
        online = [a for a in agents if a.get('status') == 'online']

        if not online:
            # Fall back to any agent
            online = agents

        if not online:
            return None

        # Select agent with lowest message count (load balancing)
        best = min(online, key=lambda a: a.get('message_count', 0))
        return best

    def get_capabilities_map(self) -> Dict[str, List[str]]:
        """Get map of capabilities to agent IDs."""
        agents = self.list_agents()
        cap_map = {}

        for agent in agents:
            for cap in agent.get('capabilities', []):
                if cap not in cap_map:
                    cap_map[cap] = []
                cap_map[cap].append(agent['agent_id'])

        return cap_map

    def is_agent_available(self, capability: str) -> bool:
        """Check if any agent has specific capability."""
        agents = self.find_by_capability(capability)
        return any(a.get('status') == 'online' for a in agents)

    def get_agent_status_summary(self) -> dict:
        """Get summary of all agent statuses."""
        agents = self.list_agents()

        summary = {
            'total': len(agents),
            'online': sum(1 for a in agents if a.get('status') == 'online'),
            'offline': sum(1 for a in agents if a.get('status') == 'offline'),
            'stale': sum(1 for a in agents if a.get('status') == 'stale'),
            'capabilities': self.get_capabilities_map()
        }

        return summary
