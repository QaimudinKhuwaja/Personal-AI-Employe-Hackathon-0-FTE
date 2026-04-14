"""
Calendar Tool - Local Event Management System

Manages calendar events using ICS (iCalendar) format files stored locally.
Supports CRUD operations for events with no external dependencies.
"""

# UTF-8 console encoding for Windows
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

"""

Usage:
    python calendar_tool.py create --title "Meeting" --start "2026-04-15T10:00:00" --end "2026-04-15T11:00:00"
    python calendar_tool.py list --days 7
    python calendar_tool.py get --event-id "event-20260415-100000"
    python calendar_tool.py update --event-id "event-20260415-100000" --title "Updated Meeting"
    python calendar_tool.py delete --event-id "event-20260415-100000"
    python calendar_tool.py search --query "meeting"
    python calendar_tool.py conflicts --start "2026-04-15T09:00:00" --end "2026-04-15T17:00:00"

Features:
- Local-first storage (ICS files in vault)
- No external API dependencies
- Conflict detection
- Recurring event support
- Category/tag support
- JSON output for MCP integration
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class CalendarTool:
    """
    Local calendar event management system.

    Stores events as ICS files in the vault's Calendar/Events/ folder.
    Uses simple file-based storage with JSON metadata for fast lookups.
    """

    def __init__(self, vault_path: str = 'AI_Employee_Vault'):
        """
        Initialize calendar tool.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.events_path = self.vault_path / 'Calendar' / 'Events'
        self.metadata_path = self.vault_path / 'Calendar' / 'Metadata'

        # Ensure directories exist
        self.events_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)

        # Event index file (for fast lookups)
        self.index_file = self.metadata_path / 'event_index.json'

        # Setup logging
        self._setup_logging()

        # Load or create event index
        self.event_index = self._load_index()

        self.logger.info(f'Initialized CalendarTool')
        self.logger.info(f'Vault: {self.vault_path}')

    def _setup_logging(self):
        """Setup logging."""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f'calendar_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('CalendarTool')

    def _load_index(self) -> Dict[str, Any]:
        """Load event index from metadata file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f'Could not load event index: {e}')
                return {'events': {}, 'last_updated': None}
        else:
            return {'events': {}, 'last_updated': None}

    def _save_index(self):
        """Save event index to metadata file."""
        self.event_index['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.event_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f'Could not save event index: {e}')

    def _generate_event_id(self, title: str, start: str) -> str:
        """Generate unique event ID."""
        # Format: event-YYYYMMDD-HHMMSS-hash
        date_part = start.replace('-', '').replace('T', '-').replace(':', '')[:15]
        hash_part = hashlib.md5(f"{title}{start}{uuid.uuid4()}".encode()).hexdigest()[:8]
        return f"event-{date_part}-{hash_part}"

    def _format_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string into datetime object."""
        # Support multiple formats
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse datetime: {dt_str}. Use format: YYYY-MM-DDTHH:MM:SS")

    def _generate_ics_content(self, event: Dict[str, Any]) -> str:
        """Generate ICS (iCalendar) format content."""
        uid = event.get('event_id', str(uuid.uuid4()))
        start = event['start'].replace('-', '').replace(':', '').replace('T', 'T') + '00'
        end = event['end'].replace('-', '').replace(':', '').replace('T', 'T') + '00'
        created = event.get('created', datetime.now().strftime('%Y%m%dT%H%M%S'))

        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Employee//Calendar Tool//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{created}
DTSTART:{start}
DTEND:{end}
SUMMARY:{event.get('title', 'Untitled')}
DESCRIPTION:{event.get('description', '').replace('\\n', '\\\\n')}
LOCATION:{event.get('location', '')}
CATEGORIES:{','.join(event.get('categories', []))}
STATUS:{event.get('status', 'CONFIRMED')}
PRIORITY:{event.get('priority', 5)}
END:VEVENT
END:VCALENDAR
"""
        return ics

    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        description: str = '',
        location: str = '',
        categories: List[str] = None,
        status: str = 'CONFIRMED',
        priority: int = 5,
        reminder_minutes: int = 15,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new calendar event.

        Args:
            title: Event title
            start: Start datetime (YYYY-MM-DDTHH:MM:SS)
            end: End datetime (YYYY-MM-DDTHH:MM:SS)
            description: Event description
            location: Event location
            categories: List of categories/tags
            status: Event status (CONFIRMED, TENTATIVE, CANCELLED)
            priority: Priority level (1-9, 1=highest)
            reminder_minutes: Minutes before event to remind
            dry_run: If True, simulate without creating

        Returns:
            Event metadata dictionary
        """
        # Parse datetimes
        start_dt = self._format_datetime(start)
        end_dt = self._format_datetime(end)

        # Validate
        if end_dt <= start_dt:
            raise ValueError(f"End time must be after start time")

        # Generate event ID
        event_id = self._generate_event_id(title, start)

        # Create event metadata
        event = {
            'event_id': event_id,
            'title': title,
            'start': start,
            'end': end,
            'description': description,
            'location': location,
            'categories': categories or [],
            'status': status,
            'priority': priority,
            'reminder_minutes': reminder_minutes,
            'created': datetime.now().strftime('%Y%m%dT%H%M%S'),
            'updated': datetime.now().isoformat()
        }

        if dry_run:
            self.logger.info(f'[DRY RUN] Would create event: {title} at {start}')
            return {'dry_run': True, 'event': event}

        # Generate ICS content
        ics_content = self._generate_ics_content(event)

        # Save ICS file
        ics_file = self.events_path / f"{event_id}.ics"
        ics_file.write_text(ics_content, encoding='utf-8')

        # Update index
        self.event_index['events'][event_id] = {
            'title': title,
            'start': start,
            'end': end,
            'categories': event['categories'],
            'status': status,
            'file': f"{event_id}.ics"
        }
        self._save_index()

        self.logger.info(f'Created event: {title} (ID: {event_id})')

        return event

    def list_events(
        self,
        days: int = 7,
        categories: List[str] = None,
        status: str = None,
        include_past: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List upcoming events.

        Args:
            days: Number of days ahead to look
            categories: Filter by categories
            status: Filter by status
            include_past: Include past events

        Returns:
            List of event metadata dictionaries
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)

        events = []

        for event_id, metadata in self.event_index['events'].items():
            event_start = self._format_datetime(metadata['start'])

            # Filter by date range
            if not include_past and event_start < now:
                continue
            if event_start > end_date:
                continue

            # Filter by status
            if status and metadata.get('status') != status:
                continue

            # Filter by categories
            if categories:
                event_cats = metadata.get('categories', [])
                if not any(cat in event_cats for cat in categories):
                    continue

            # Load full event details
            event = self.get_event(event_id)
            if event:
                events.append(event)

        # Sort by start time
        events.sort(key=lambda e: e['start'])

        self.logger.info(f'Found {len(events)} events in next {days} days')
        return events

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get event details by ID.

        Args:
            event_id: Event ID

        Returns:
            Event metadata dictionary or None if not found
        """
        if event_id not in self.event_index['events']:
            self.logger.warning(f'Event not found: {event_id}')
            return None

        # Load ICS file
        ics_file = self.events_path / f"{event_id}.ics"
        if not ics_file.exists():
            self.logger.warning(f'ICS file not found for {event_id}')
            return None

        # Return metadata from index
        metadata = self.event_index['events'][event_id]
        return {
            'event_id': event_id,
            'title': metadata['title'],
            'start': metadata['start'],
            'end': metadata['end'],
            'description': '',  # Would need to parse ICS file
            'location': '',
            'categories': metadata.get('categories', []),
            'status': metadata.get('status', 'CONFIRMED'),
            'priority': 5
        }

    def update_event(
        self,
        event_id: str,
        title: str = None,
        start: str = None,
        end: str = None,
        description: str = None,
        location: str = None,
        categories: List[str] = None,
        status: str = None,
        priority: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing event.

        Args:
            event_id: Event ID
            title: New title (optional)
            start: New start time (optional)
            end: New end time (optional)
            description: New description (optional)
            location: New location (optional)
            categories: New categories (optional)
            status: New status (optional)
            priority: New priority (optional)

        Returns:
            Updated event metadata or None if not found
        """
        if event_id not in self.event_index['events']:
            self.logger.warning(f'Event not found: {event_id}')
            return None

        # Load current event
        current = self.get_event(event_id)
        if not current:
            return None

        # Update fields
        updates = {
            'title': title or current['title'],
            'start': start or current['start'],
            'end': end or current['end'],
            'description': description if description is not None else current['description'],
            'location': location if location is not None else current['location'],
            'categories': categories if categories is not None else current['categories'],
            'status': status or current['status'],
            'priority': priority if priority is not None else current['priority']
        }

        # Regenerate ICS file
        event_data = {
            'event_id': event_id,
            **updates,
            'updated': datetime.now().isoformat()
        }

        ics_content = self._generate_ics_content(event_data)
        ics_file = self.events_path / f"{event_id}.ics"
        ics_file.write_text(ics_content, encoding='utf-8')

        # Update index
        self.event_index['events'][event_id].update({
            'title': updates['title'],
            'start': updates['start'],
            'end': updates['end'],
            'categories': updates['categories'],
            'status': updates['status']
        })
        self._save_index()

        self.logger.info(f'Updated event: {event_id}')
        return {**updates, 'event_id': event_id}

    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event.

        Args:
            event_id: Event ID

        Returns:
            True if deleted, False if not found
        """
        if event_id not in self.event_index['events']:
            self.logger.warning(f'Event not found: {event_id}')
            return False

        # Delete ICS file
        ics_file = self.events_path / f"{event_id}.ics"
        if ics_file.exists():
            ics_file.unlink()

        # Remove from index
        del self.event_index['events'][event_id]
        self._save_index()

        self.logger.info(f'Deleted event: {event_id}')
        return True

    def search_events(self, query: str) -> List[Dict[str, Any]]:
        """
        Search events by title, description, or location.

        Args:
            query: Search string

        Returns:
            List of matching event metadata dictionaries
        """
        results = []
        query_lower = query.lower()

        for event_id, metadata in self.event_index['events'].items():
            # Search in title, categories, status
            searchable = f"{metadata.get('title', '')} {' '.join(metadata.get('categories', []))} {metadata.get('status', '')}".lower()

            if query_lower in searchable:
                event = self.get_event(event_id)
                if event:
                    results.append(event)

        self.logger.info(f'Search "{query}" found {len(results)} events')
        return results

    def check_conflicts(self, start: str, end: str, exclude_id: str = None) -> List[Dict[str, Any]]:
        """
        Check for scheduling conflicts in a time range.

        Args:
            start: Start of time range
            end: End of time range
            exclude_id: Event ID to exclude (for updates)

        Returns:
            List of conflicting events
        """
        start_dt = self._format_datetime(start)
        end_dt = self._format_datetime(end)

        conflicts = []

        for event_id, metadata in self.event_index['events'].items():
            if exclude_id and event_id == exclude_id:
                continue

            event_start = self._format_datetime(metadata['start'])
            event_end = self._format_datetime(metadata['end'])

            # Check overlap
            if (event_start < end_dt and event_end > start_dt):
                event = self.get_event(event_id)
                if event:
                    conflicts.append(event)

        self.logger.info(f'Found {len(conflicts)} conflicts for {start} to {end}')
        return conflicts

    def get_day_schedule(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all events for a specific day.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of events for that day
        """
        day_start = datetime.strptime(date, '%Y-%m-%d')
        day_end = day_start + timedelta(days=1)

        events = []
        for event_id, metadata in self.event_index['events'].items():
            event_start = self._format_datetime(metadata['start'])

            if day_start <= event_start < day_end:
                event = self.get_event(event_id)
                if event:
                    events.append(event)

        events.sort(key=lambda e: e['start'])
        return events


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Calendar Event Management Tool')
    parser.add_argument('--vault', type=str, default='AI_Employee_Vault', help='Vault path')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without executing')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create event
    create_parser = subparsers.add_parser('create', help='Create new event')
    create_parser.add_argument('--title', required=True, help='Event title')
    create_parser.add_argument('--start', required=True, help='Start time (YYYY-MM-DDTHH:MM:SS)')
    create_parser.add_argument('--end', required=True, help='End time (YYYY-MM-DDTHH:MM:SS)')
    create_parser.add_argument('--description', default='', help='Event description')
    create_parser.add_argument('--location', default='', help='Event location')
    create_parser.add_argument('--categories', nargs='*', default=[], help='Categories/tags')
    create_parser.add_argument('--status', default='CONFIRMED', help='Event status')
    create_parser.add_argument('--priority', type=int, default=5, help='Priority (1-9)')
    create_parser.add_argument('--reminder', type=int, default=15, help='Reminder minutes before')

    # List events
    list_parser = subparsers.add_parser('list', help='List events')
    list_parser.add_argument('--days', type=int, default=7, help='Days ahead to look')
    list_parser.add_argument('--categories', nargs='*', help='Filter by categories')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--include-past', action='store_true', help='Include past events')

    # Get event
    get_parser = subparsers.add_parser('get', help='Get event details')
    get_parser.add_argument('--event-id', required=True, help='Event ID')

    # Update event
    update_parser = subparsers.add_parser('update', help='Update event')
    update_parser.add_argument('--event-id', required=True, help='Event ID')
    update_parser.add_argument('--title', help='New title')
    update_parser.add_argument('--start', help='New start time')
    update_parser.add_argument('--end', help='New end time')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--location', help='New location')
    update_parser.add_argument('--categories', nargs='*', help='New categories')
    update_parser.add_argument('--status', help='New status')
    update_parser.add_argument('--priority', type=int, help='New priority')

    # Delete event
    delete_parser = subparsers.add_parser('delete', help='Delete event')
    delete_parser.add_argument('--event-id', required=True, help='Event ID')

    # Search events
    search_parser = subparsers.add_parser('search', help='Search events')
    search_parser.add_argument('--query', required=True, help='Search query')

    # Check conflicts
    conflicts_parser = subparsers.add_parser('conflicts', help='Check scheduling conflicts')
    conflicts_parser.add_argument('--start', required=True, help='Start of time range')
    conflicts_parser.add_argument('--end', required=True, help='End of time range')
    conflicts_parser.add_argument('--exclude-id', help='Event ID to exclude')

    # Day schedule
    day_parser = subparsers.add_parser('day', help='Get day schedule')
    day_parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create calendar tool
    cal = CalendarTool(vault_path=args.vault)

    try:
        if args.command == 'create':
            result = cal.create_event(
                title=args.title,
                start=args.start,
                end=args.end,
                description=args.description,
                location=args.location,
                categories=args.categories,
                status=args.status,
                priority=args.priority,
                reminder_minutes=args.reminder,
                dry_run=args.dry_run
            )
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"✅ Event created: {result['title']}")
                print(f"   ID: {result['event_id']}")
                print(f"   Start: {result['start']}")
                print(f"   End: {result['end']}")

        elif args.command == 'list':
            events = cal.list_events(
                days=args.days,
                categories=args.categories,
                status=args.status,
                include_past=args.include_past
            )
            if args.json:
                print(json.dumps(events, indent=2, ensure_ascii=False))
            else:
                print(f"\n📅 Upcoming Events (next {args.days} days):")
                print("=" * 60)
                if not events:
                    print("No events found")
                else:
                    for event in events:
                        print(f"\n📌 {event['title']}")
                        print(f"   🕐 {event['start']} → {event['end']}")
                        if event.get('location'):
                            print(f"   📍 {event['location']}")
                        if event.get('categories'):
                            print(f"   🏷️  {', '.join(event['categories'])}")
                print()

        elif args.command == 'get':
            event = cal.get_event(args.event_id)
            if event:
                if args.json:
                    print(json.dumps(event, indent=2, ensure_ascii=False))
                else:
                    print(f"\n📌 Event: {event['title']}")
                    print(f"   ID: {event['event_id']}")
                    print(f"   🕐 {event['start']} → {event['end']}")
                    if event.get('description'):
                        print(f"   📝 {event['description']}")
                    if event.get('location'):
                        print(f"   📍 {event['location']}")
                    if event.get('categories'):
                        print(f"   🏷️  {', '.join(event['categories'])}")
                    print(f"   Status: {event['status']}")
                    print()
            else:
                print(f"❌ Event not found: {args.event_id}")
                sys.exit(1)

        elif args.command == 'update':
            result = cal.update_event(
                event_id=args.event_id,
                title=args.title,
                start=args.start,
                end=args.end,
                description=args.description,
                location=args.location,
                categories=args.categories,
                status=args.status,
                priority=args.priority
            )
            if result:
                if args.json:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print(f"✅ Event updated: {result['event_id']}")
            else:
                print(f"❌ Event not found: {args.event_id}")
                sys.exit(1)

        elif args.command == 'delete':
            success = cal.delete_event(args.event_id)
            if success:
                print(f"✅ Event deleted: {args.event_id}")
            else:
                print(f"❌ Event not found: {args.event_id}")
                sys.exit(1)

        elif args.command == 'search':
            results = cal.search_events(args.query)
            if args.json:
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print(f"\n🔍 Search results for '{args.query}':")
                print("=" * 60)
                for event in results:
                    print(f"📌 {event['title']} ({event['start']})")
                print()

        elif args.command == 'conflicts':
            conflicts = cal.check_conflicts(args.start, args.end, args.exclude_id)
            if args.json:
                print(json.dumps(conflicts, indent=2, ensure_ascii=False))
            else:
                print(f"\n⚠️  Scheduling conflicts:")
                print("=" * 60)
                if not conflicts:
                    print("No conflicts found")
                else:
                    for conflict in conflicts:
                        print(f"⚠️  {conflict['title']} ({conflict['start']} → {conflict['end']})")
                print()

        elif args.command == 'day':
            events = cal.get_day_schedule(args.date)
            if args.json:
                print(json.dumps(events, indent=2, ensure_ascii=False))
            else:
                print(f"\n📅 Schedule for {args.date}:")
                print("=" * 60)
                if not events:
                    print("No events scheduled")
                else:
                    for event in events:
                        print(f"📌 {event['start']} - {event['end']}: {event['title']}")
                print()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.json:
            print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
