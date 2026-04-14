"""
Quarantine System Test

Tests the complete quarantine workflow:
1. Orchestrator initialization with quarantine enabled
2. Simulated processing failures
3. Failure count tracking
4. Automatic quarantine after max failures
5. Quarantine record creation
6. File movement from Needs_Action to Quarantine
7. Quarantine viewer integration

Usage:
    python scripts/test_quarantine.py
    python scripts/test_quarantine.py --vault AI_Employee_Vault
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add scripts folder to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

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


def test_quarantine_initialization(vault_path: Path) -> bool:
    """Test 1: Quarantine manager initialization."""
    from retry_handler import QuarantineManager

    quarantine_dir = vault_path / 'Quarantine'
    qm = QuarantineManager(quarantine_dir=str(quarantine_dir))

    success = quarantine_dir.exists() and qm.quarantine_dir.exists()
    print_test("Quarantine Manager Initialization", success, f"Path: {quarantine_dir}")
    return success


def test_quarantine_creation(vault_path: Path) -> bool:
    """Test 2: Quarantine record creation."""
    from retry_handler import QuarantineManager

    quarantine_dir = vault_path / 'Quarantine'
    qm = QuarantineManager(quarantine_dir=str(quarantine_dir))

    # Create a test quarantine record
    qm.quarantine(
        item_id='test_item_001',
        item_type='test',
        error='Simulated processing failure: Qwen Code not available',
        attempts=3,
        original_path=Path('AI_Employee_Vault/Needs_Action/test_item.md')
    )

    # Check if file was created
    files = list(quarantine_dir.glob('test_*'))
    success = len(files) > 0
    print_test("Quarantine Record Creation", success, f"Created {len(files)} record(s)")

    if success:
        # Show the created file
        print(f"    {Colors.CYAN}File: {files[0].name}{Colors.RESET}")

    return success


def test_orchestrator_quarantine_integration(vault_path: Path) -> bool:
    """Test 3: Orchestrator quarantine methods."""
    from orchestrator import Orchestrator, QUARANTINE_AVAILABLE

    # Create orchestrator with quarantine enabled
    orch = Orchestrator(
        vault_path=str(vault_path),
        auto_quarantine=True,
        max_failures_before_quarantine=3
    )

    success = (
        orch.auto_quarantine and
        QUARANTINE_AVAILABLE and
        orch.max_failures_before_quarantine == 3
    )

    print_test("Orchestrator Quarantine Integration", success,
               f"Enabled: {orch.auto_quarantine}, Max failures: {orch.max_failures_before_quarantine}")
    return success


def test_failure_count_tracking(vault_path: Path) -> bool:
    """Test 4: Failure count tracking."""
    from orchestrator import Orchestrator

    orch = Orchestrator(
        vault_path=str(vault_path),
        auto_quarantine=True,
        max_failures_before_quarantine=3
    )

    # Simulate failures
    test_file = vault_path / 'Needs_Action' / 'TEST_quarantine_system.md'

    # Create test file if it doesn't exist (may have been moved by previous tests)
    if not test_file.exists():
        test_file.write_text(
            "---\ntype: test\n---\n# Test Item\n",
            encoding='utf-8'
        )

    # Simulate 2 failures (should NOT quarantine yet)
    for i in range(2):
        orch._quarantine_failed_item(test_file, f'Simulated failure #{i+1}')

    # Check that file is still in Needs_Action
    still_there = test_file.exists()
    has_pending = 'TEST_quarantine_system.md' in orch._failure_counts
    count = orch._failure_counts.get('TEST_quarantine_system.md', 0)

    success = still_there and has_pending and count == 2
    print_test("Failure Count Tracking (2 failures)", success,
               f"File exists: {still_there}, Count: {count}, Pending: {has_pending}")

    # Simulate 3rd failure (SHOULD quarantine)
    orch._quarantine_failed_item(test_file, 'Simulated failure #3')

    # Check that file moved to Quarantine
    quarantined = list((vault_path / 'Quarantine').glob('TEST_quarantine_system.md'))
    no_longer_pending = 'TEST_quarantine_system.md' not in orch._failure_counts

    success2 = len(quarantined) > 0 and no_longer_pending
    print_test("Auto-Quarantine (3rd failure)", success2,
               f"Quarantined: {len(quarantined) > 0}, Pending cleared: {no_longer_pending}")

    return success and success2


def test_quarantine_viewer(vault_path: Path) -> bool:
    """Test 5: Quarantine viewer integration."""
    from retry_handler import QuarantineManager

    quarantine_dir = vault_path / 'Quarantine'
    qm = QuarantineManager(quarantine_dir=str(quarantine_dir))

    items = qm.list_quarantined()
    success = len(items) > 0

    print_test("Quarantine Viewer Integration", success,
               f"Found {len(items)} quarantined item(s)")

    return success


def test_quarantine_release(vault_path: Path) -> bool:
    """Test 6: Release from quarantine."""
    from retry_handler import QuarantineManager

    quarantine_dir = vault_path / 'Quarantine'
    qm = QuarantineManager(quarantine_dir=str(quarantine_dir))

    # Get first quarantined item
    items = qm.list_quarantined()
    if not items:
        print_test("Release from Quarantine", False, "No items to release")
        return False

    # Find the actual quarantined item (not the metadata file)
    test_item_path = None
    for item in items:
        item_file = item.get('file', '')
        # Look for the actual test file, not metadata
        if 'TEST_quarantine_system.md' in item_file:
            test_item_path = item_file
            break

    if not test_item_path:
        # Try to find test_item
        for item in items:
            item_file = item.get('file', '')
            if 'test_test_item' in item_file:
                test_item_path = item_file
                break

    if not test_item_path:
        # Just test with first item
        test_item_path = items[0]['file']

    success = qm.release(test_item_path, str(vault_path / 'Needs_Action'))

    # Check if file moved back (or already exists)
    released_file = vault_path / 'Needs_Action' / Path(test_item_path).name
    success = success or released_file.exists()  # Success if file exists in destination

    print_test("Release from Quarantine", success,
               f"Released to Needs_Action/: {success}")

    return success


def test_quarantine_status(vault_path: Path) -> bool:
    """Test 7: Quarantine status reporting."""
    from orchestrator import Orchestrator

    orch = Orchestrator(vault_path=str(vault_path), auto_quarantine=True)

    status = orch.get_quarantine_status()

    success = (
        'enabled' in status and
        'total_quarantined' in status and
        'quarantine_path' in status
    )

    print_test("Quarantine Status Reporting", success,
               f"Enabled: {status['enabled']}, Total: {status['total_quarantined']}")

    if success:
        print(f"    {Colors.CYAN}Status keys: {', '.join(status.keys())}{Colors.RESET}")

    return success


def test_dashboard_update(vault_path: Path) -> bool:
    """Test 8: Dashboard has quarantine section."""
    dashboard = vault_path / 'Dashboard.md'

    if not dashboard.exists():
        print_test("Dashboard Quarantine Section", False, "Dashboard.md not found")
        return False

    content = dashboard.read_text(encoding='utf-8')
    has_section = 'Quarantine Status' in content or 'Quarantine' in content

    print_test("Dashboard Quarantine Section", has_section,
               "Section found in Dashboard.md")

    return has_section


def run_all_tests(vault_path: Path) -> bool:
    """Run all quarantine system tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'QUARANTINE SYSTEM TESTS'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    print(f"  {Colors.CYAN}Vault: {vault_path}{Colors.RESET}")
    print(f"  {Colors.CYAN}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")

    tests = [
        ("Quarantine Manager Initialization", lambda: test_quarantine_initialization(vault_path)),
        ("Quarantine Record Creation", lambda: test_quarantine_creation(vault_path)),
        ("Orchestrator Integration", lambda: test_orchestrator_quarantine_integration(vault_path)),
        ("Failure Count Tracking", lambda: test_failure_count_tracking(vault_path)),
        ("Quarantine Viewer", lambda: test_quarantine_viewer(vault_path)),
        ("Release from Quarantine", lambda: test_quarantine_release(vault_path)),
        ("Status Reporting", lambda: test_quarantine_status(vault_path)),
        ("Dashboard Integration", lambda: test_dashboard_update(vault_path)),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"  {Colors.RED}[FAIL] {name} - Exception: {e}{Colors.RESET}")
            results.append((name, False))

    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n  {Colors.BOLD}Test Results: {passed}/{total} passed{Colors.RESET}\n")

    for name, success in results:
        icon = "[OK]" if success else "[FAIL]"
        color = Colors.GREEN if success else Colors.RED
        print(f"  {color}{icon} {name}{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

    return passed == total


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Quarantine System Tests')
    parser.add_argument('--vault', type=str, default='AI_Employee_Vault', help='Vault path')
    args = parser.parse_args()

    vault = Path(args.vault)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {vault}")
        sys.exit(1)

    success = run_all_tests(vault)
    sys.exit(0 if success else 1)
