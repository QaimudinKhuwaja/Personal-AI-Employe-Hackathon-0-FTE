"""
Quarantine Viewer - Inspect and Manage Quarantined Items

Provides a CLI interface to view, inspect, release, and purge quarantined items.

Usage:
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --list
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --status
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --inspect <filename>
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --release <filename>
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --purge --days 30
    python scripts/quarantine_viewer.py --vault AI_Employee_Vault --release-all
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Add scripts folder to path for imports
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import QuarantineManager
try:
    from retry_handler import QuarantineManager
    QUARANTINE_AVAILABLE = True
except ImportError:
    QUARANTINE_AVAILABLE = False
    QuarantineManager = None


# Colors for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_header(text: str):
    """Print formatted header."""
    width = 70
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(width)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*width}{Colors.RESET}\n")


def print_section(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- {text} {'-'*max(0, 50-len(text))}{Colors.RESET}")


def print_item(item_data: dict, index: int = 0):
    """Print quarantined item details."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Item #{index + 1}{Colors.RESET}")
    print(f"  {Colors.CYAN}File:{Colors.RESET}       {item_data.get('name', 'N/A')}")
    print(f"  {Colors.CYAN}Quarantined:{Colors.RESET} {item_data.get('quarantined_at', 'N/A')}")
    if 'size' in item_data:
        print(f"  {Colors.CYAN}Size:{Colors.RESET}       {item_data['size']} bytes")


def print_quarantine_record(filepath: Path):
    """Print full quarantine record from markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Parse frontmatter (simplified)
        if '---' in content:
            parts = content.split('---', 2)
            if len(parts) >= 2:
                frontmatter = parts[1].strip()
                body = parts[2].strip() if len(parts) > 2 else ''
                
                print(f"\n{Colors.BOLD}{Colors.BLUE}Frontmatter:{Colors.RESET}")
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        print(f"  {Colors.CYAN}{key.strip()}{Colors.RESET}: {value.strip()}")
                
                if body:
                    print(f"\n{Colors.BOLD}{Colors.BLUE}Details:{Colors.RESET}")
                    # Print first few lines of body
                    lines = body.split('\n')
                    for line in lines[:10]:
                        print(f"  {line}")
                    if len(lines) > 10:
                        print(f"  {Colors.DIM}... (truncated){Colors.RESET}")
        
    except Exception as e:
        print(f"  {Colors.RED}Error reading file: {e}{Colors.RESET}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Quarantine Viewer - Inspect and Manage Quarantined Items',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all quarantined items
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --list

  # Show quarantine status
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --status

  # Inspect a specific quarantined item
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --inspect action_EMAIL_20260227_165719_20260413_033557.md

  # Release an item back to Needs_Action
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --release action_EMAIL_20260227_165719_20260413_033557.md

  # Release all items
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --release-all

  # Purge items older than 30 days
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --purge --days 30

  # Export quarantine report as JSON
  py scripts/quarantine_viewer.py --vault AI_Employee_Vault --export report.json
"""
    )

    parser.add_argument('--vault', type=str, default='AI_Employee_Vault', help='Vault path')
    parser.add_argument('--list', action='store_true', help='List all quarantined items')
    parser.add_argument('--status', action='store_true', help='Show quarantine status')
    parser.add_argument('--inspect', type=str, help='Inspect a specific quarantined item')
    parser.add_argument('--release', type=str, help='Release a specific item back to Needs_Action')
    parser.add_argument('--release-all', action='store_true', help='Release all items back to Needs_Action')
    parser.add_argument('--purge', action='store_true', help='Purge old quarantined items')
    parser.add_argument('--days', type=int, default=30, help='Age threshold for purge (default: 30)')
    parser.add_argument('--export', type=str, help='Export quarantine data to JSON file')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color or sys.platform == 'win32':
        Colors.RED = Colors.GREEN = Colors.YELLOW = Colors.BLUE = ''
        Colors.MAGENTA = Colors.CYAN = Colors.WHITE = Colors.BOLD = Colors.DIM = Colors.RESET = ''

    # Validate vault path
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"{Colors.RED}Error: Vault path does not exist: {vault_path}{Colors.RESET}")
        sys.exit(1)

    # Check if QuarantineManager is available
    if not QUARANTINE_AVAILABLE:
        print(f"{Colors.RED}Error: QuarantineManager not available. Ensure retry_handler.py exists.{Colors.RESET}")
        sys.exit(1)

    # Initialize quarantine manager
    quarantine_dir = vault_path / 'Quarantine'
    qm = QuarantineManager(quarantine_dir=str(quarantine_dir))

    # Handle commands
    if args.list:
        cmd_list(qm, args.json)

    elif args.status:
        cmd_status(vault_path, qm, args.json)

    elif args.inspect:
        cmd_inspect(quarantine_dir, args.inspect, args.json)

    elif args.release:
        cmd_release(qm, args.release, vault_path, args.json)

    elif getattr(args, 'release_all'):
        cmd_release_all(qm, vault_path, args.json)

    elif args.purge:
        cmd_purge(qm, args.days, args.json)

    elif args.export:
        cmd_export(qm, args.export)

    else:
        # Default: show status
        print_header('QUARANTINE VIEWER')
        cmd_status(vault_path, qm, args.json)
        print(f"\n{Colors.DIM}Use --help for available commands{Colors.RESET}\n")


def cmd_list(qm: QuarantineManager, json_output: bool = False):
    """List all quarantined items."""
    items = qm.list_quarantined()

    if json_output:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return

    print_header('QUARANTINED ITEMS')

    if not items:
        print(f"  {Colors.GREEN}✓{Colors.RESET} No items in quarantine")
        print()
        return

    print(f"  Found {Colors.BOLD}{len(items)}{Colors.RESET} quarantined item(s):\n")

    for i, item in enumerate(items, 1):
        print_item(item, i)

    print()


def cmd_status(vault_path: Path, qm: QuarantineManager, json_output: bool = False):
    """Show quarantine status."""
    quarantine_dir = vault_path / 'Quarantine'

    status = {
        'quarantine_enabled': True,
        'quarantine_path': str(quarantine_dir),
        'total_quarantined': 0,
        'oldest_item': None,
        'newest_item': None,
        'items': []
    }

    # Count items
    if quarantine_dir.exists():
        items = list(quarantine_dir.glob('*.md'))
        status['total_quarantined'] = len(items)

        if items:
            # Get oldest and newest
            items_with_mtime = [(item, item.stat().st_mtime) for item in items]
            items_with_mtime.sort(key=lambda x: x[1])

            status['oldest_item'] = items_with_mtime[0][0].name
            status['newest_item'] = items_with_mtime[-1][0].name

            # List items
            for item, mtime in items_with_mtime:
                status['items'].append({
                    'name': item.name,
                    'quarantined_at': datetime.fromtimestamp(mtime).isoformat()
                })

    if json_output:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    print_header('QUARANTINE STATUS')

    print(f"  {Colors.CYAN}Quarantine Enabled:{Colors.RESET}  {Colors.GREEN}✓{Colors.RESET} Yes")
    print(f"  {Colors.CYAN}Quarantine Path:{Colors.RESET}     {quarantine_dir}")
    print(f"  {Colors.CYAN}Total Quarantined:{Colors.RESET}   {Colors.BOLD}{status['total_quarantined']}{Colors.RESET}")

    if status['total_quarantined'] > 0:
        print(f"  {Colors.CYAN}Oldest Item:{Colors.RESET}       {status['oldest_item']}")
        print(f"  {Colors.CYAN}Newest Item:{Colors.RESET}       {status['newest_item']}")

    print()


def cmd_inspect(quarantine_dir: Path, filename: str, json_output: bool = False):
    """Inspect a specific quarantined item."""
    filepath = quarantine_dir / filename

    if not filepath.exists():
        print(f"{Colors.RED}Error: File not found: {filename}{Colors.RESET}")
        sys.exit(1)

    if json_output:
        # Output as JSON
        content = filepath.read_text(encoding='utf-8')
        data = {
            'file': filename,
            'size': filepath.stat().st_size,
            'quarantined_at': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            'content': content
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print_header(f'INSPECTING: {filename}')
    print_quarantine_record(filepath)
    print()


def cmd_release(qm: QuarantineManager, filename: str, vault_path: Path, json_output: bool = False):
    """Release a specific item from quarantine."""
    # Build full path if just filename provided
    if not Path(filename).is_absolute():
        filepath = qm.quarantine_dir / filename
    else:
        filepath = Path(filename)

    if not filepath.exists():
        print(f"{Colors.RED}Error: File not found: {filename}{Colors.RESET}")
        sys.exit(1)

    success = qm.release(str(filepath), str(vault_path / 'Needs_Action'))

    if json_output:
        print(json.dumps({'released': success, 'file': filename}, indent=2))
        return

    if success:
        print(f"{Colors.GREEN}✓ Released: {filepath.name} → Needs_Action/{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ Failed to release: {filepath.name}{Colors.RESET}")
        sys.exit(1)


def cmd_release_all(qm: QuarantineManager, vault_path: Path, json_output: bool = False):
    """Release all items from quarantine."""
    items = qm.list_quarantined()
    released = 0
    failed = 0

    for item in items:
        success = qm.release(item['file'], str(vault_path / 'Needs_Action'))
        if success:
            released += 1
        else:
            failed += 1

    if json_output:
        print(json.dumps({'released': released, 'failed': failed}, indent=2))
        return

    print_header('RELEASE ALL')
    print(f"  {Colors.GREEN}✓ Released: {released} items → Needs_Action/{Colors.RESET}")
    if failed > 0:
        print(f"  {Colors.RED}✗ Failed: {failed} items{Colors.RESET}")
    print()


def cmd_purge(qm: QuarantineManager, days: int, json_output: bool = False):
    """Purge old quarantined items."""
    quarantine_dir = qm.quarantine_dir
    cutoff = datetime.now() - timedelta(days=days)
    purged = 0

    for item_file in quarantine_dir.glob('*.md'):
        mtime = datetime.fromtimestamp(item_file.stat().st_mtime)
        if mtime < cutoff:
            item_file.unlink()
            purged += 1

    if json_output:
        print(json.dumps({'purged': purged, 'age_threshold_days': days}, indent=2))
        return

    print_header('PURGE OLD ITEMS')
    print(f"  {Colors.GREEN}✓ Purged: {purged} items older than {days} days{Colors.RESET}")
    print()


def cmd_export(qm: QuarantineManager, output_file: str):
    """Export quarantine data to JSON."""
    items = qm.list_quarantined()
    export_data = {
        'exported_at': datetime.now().isoformat(),
        'total_items': len(items),
        'items': items
    }

    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"{Colors.GREEN}✓ Exported {len(items)} items to: {output_file}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error exporting: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()
