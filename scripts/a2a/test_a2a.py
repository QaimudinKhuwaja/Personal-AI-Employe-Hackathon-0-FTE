"""
A2A Communication Test Suite

Tests agent-to-agent communication end-to-end:
1. Broker startup and health
2. Agent registration
3. Direct messaging
4. Broadcast messaging
5. Task delegation
6. Agent discovery
7. Message queuing
8. Capability-based routing

Usage:
    # Start broker first
    python scripts/a2a/a2a_broker.py &

    # Run tests
    python scripts/a2a/test_a2a.py
    python scripts/a2a/test_a2a.py --broker http://localhost:8899
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from a2a.a2a_client import A2AClient
from a2a.a2a_registry import A2ARegistry


# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_test(name, status, detail=''):
    """Print test result."""
    icon = "[OK]" if status else "[FAIL]"
    color = Colors.GREEN if status else Colors.RED
    print(f"  {color}{icon} {name}{Colors.RESET}")
    if detail:
        print(f"     {Colors.CYAN}{detail}{Colors.RESET}")


class A2ATestSuite:
    """A2A communication test suite."""

    def __init__(self, broker_url='http://localhost:8899'):
        self.client = A2AClient(broker_url)
        self.registry = A2ARegistry(broker_url)
        self.results = []

    def test_broker_health(self):
        """Test 1: Broker health check."""
        result = self.client.health_check()
        success = 'error' not in result and result.get('status') == 'healthy'
        print_test("Broker Health Check", success,
                   f"Status: {result.get('status', 'unknown')}")
        self.results.append(('Broker Health', success))
        return success

    def test_agent_registration(self):
        """Test 2: Agent registration."""
        # Register test agents
        agents = [
            ('test-email-agent', ['email_send', 'email_read']),
            ('test-social-agent', ['linkedin_post', 'facebook_post']),
            ('test-calendar-agent', ['calendar_create', 'calendar_read']),
            ('test-orchestrator', ['orchestrate', 'delegate'])
        ]

        success = True
        for agent_id, caps in agents:
            result = self.client.register(agent_id, caps)
            if 'error' in result:
                success = False
                print_test(f"Register: {agent_id}", False, result['error'])
            else:
                print_test(f"Register: {agent_id}", True,
                           f"Capabilities: {', '.join(caps)}")

        self.results.append(('Agent Registration', success))
        return success

    def test_direct_messaging(self):
        """Test 3: Direct agent-to-agent messaging."""
        result = self.client.send_message(
            'test-orchestrator',
            'test-email-agent',
            'task_request',
            {
                'action': 'send_email',
                'to': 'client@example.com',
                'subject': 'Test Message'
            }
        )

        success = 'error' not in result and result.get('status') in ['delivered', 'queued']
        print_test("Direct Messaging", success,
                   f"Status: {result.get('status', 'unknown')}, ID: {result.get('message_id', 'N/A')[:8]}...")
        self.results.append(('Direct Messaging', success))
        return success

    def test_broadcast_messaging(self):
        """Test 4: Broadcast to all agents."""
        result = self.client.broadcast(
            'test-orchestrator',
            'status_update',
            {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
        )

        success = 'error' not in result
        delivered = result.get('delivered', 0)
        queued = result.get('queued', 0)

        print_test("Broadcast Messaging", success,
                   f"Delivered: {delivered}, Queued: {queued}")
        self.results.append(('Broadcast Messaging', success))
        return success

    def test_task_delegation(self):
        """Test 5: Task delegation workflow."""
        # Send task request
        task_result = self.client.send_task_request(
            'test-orchestrator',
            'test-social-agent',
            {
                'action': 'post_linkedin',
                'content': 'Test post from A2A delegation',
                'priority': 'normal'
            }
        )

        success = 'error' not in task_result
        print_test("Task Delegation", success,
                   f"Status: {task_result.get('status', 'unknown')}")
        self.results.append(('Task Delegation', success))
        return success

    def test_agent_discovery(self):
        """Test 6: Agent discovery by capability."""
        # Find email agents
        result = self.client.find_by_capability('email_send')
        agents = result.get('agents', [])
        success = len(agents) > 0
        print_test("Discovery by Capability", success,
                   f"Found {len(agents)} agent(s) with email_send")

        # Find social agents
        result = self.client.find_by_capability('linkedin_post')
        agents = result.get('agents', [])
        success2 = len(agents) > 0
        print_test("Discovery: Social Agents", success2,
                   f"Found {len(agents)} agent(s) with linkedin_post")

        # List all agents
        result = self.client.list_agents()
        all_agents = result.get('agents', [])
        success3 = len(all_agents) >= 4
        print_test("List All Agents", success3,
                   f"Total: {len(all_agents)} agents registered")

        success = success and success2 and success3
        self.results.append(('Agent Discovery', success))
        return success

    def test_message_queuing(self):
        """Test 7: Message queuing for offline agents."""
        # Register temporary agent
        self.client.register('offline-agent', ['test_capability'])

        # Unregister (simulate going offline)
        self.client.unregister('offline-agent')

        # Send message to offline agent
        result = self.client.send_message(
            'test-orchestrator',
            'offline-agent',
            'task_request',
            {'action': 'test'}
        )

        success = 'error' not in result and result.get('status') == 'queued'
        print_test("Message Queuing", success,
                   f"Status: {result.get('status', 'unknown')}")
        self.results.append(('Message Queuing', success))
        return success

    def test_capability_routing(self):
        """Test 8: Capability-based routing."""
        registry = A2ARegistry()

        # Find best agent for email
        best = registry.get_best_agent('email_send')
        success = best is not None
        print_test("Capability Routing: Email", success,
                   f"Best agent: {best.get('agent_id', 'N/A')}" if best else "No agent found")

        # Find best agent for social
        best = registry.get_best_agent('linkedin_post')
        success2 = best is not None
        print_test("Capability Routing: Social", success2,
                   f"Best agent: {best.get('agent_id', 'N/A')}" if best else "No agent found")

        # Get capabilities map
        cap_map = registry.get_capabilities_map()
        success3 = len(cap_map) > 0
        print_test("Capabilities Map", success3,
                   f"{len(cap_map)} capabilities mapped")

        success = success and success2 and success3
        self.results.append(('Capability Routing', success))
        return success

    def run_all_tests(self):
        """Run all A2A tests."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'A2A COMMUNICATION TESTS'.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        print(f"  {Colors.CYAN}Broker: {self.client.broker_url}{Colors.RESET}")
        print(f"  {Colors.CYAN}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")

        tests = [
            ("Broker Health", self.test_broker_health),
            ("Agent Registration", self.test_agent_registration),
            ("Direct Messaging", self.test_direct_messaging),
            ("Broadcast Messaging", self.test_broadcast_messaging),
            ("Task Delegation", self.test_task_delegation),
            ("Agent Discovery", self.test_agent_discovery),
            ("Message Queuing", self.test_message_queuing),
            ("Capability Routing", self.test_capability_routing)
        ]

        for name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"  {Colors.RED}[FAIL] {name} - Exception: {e}{Colors.RESET}")
                self.results.append((name, False))
            time.sleep(0.2)  # Small delay between tests

        # Summary
        passed = sum(1 for _, s in self.results if s)
        total = len(self.results)

        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"\n  {Colors.BOLD}Test Results: {passed}/{total} passed{Colors.RESET}\n")

        for name, success in self.results:
            icon = "[OK]" if success else "[FAIL]"
            color = Colors.GREEN if success else Colors.RED
            print(f"  {color}{icon} {name}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

        if passed == total:
            print(f"  {Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED - A2A System Operational!{Colors.RESET}\n")
        else:
            print(f"  {Colors.YELLOW}{Colors.BOLD}{total - passed} test(s) failed - check broker and agents{Colors.RESET}\n")

        return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='A2A Communication Tests')
    parser.add_argument('--broker', type=str, default='http://localhost:8899',
                        help='Broker URL')
    args = parser.parse_args()

    suite = A2ATestSuite(args.broker)
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
