---
name: calendar-mcp
description: |
  Calendar MCP Server for event management and scheduling.
  Create, read, update, delete, and search calendar events.
  Integrates with the AI Employee orchestrator for task scheduling.
  Uses local ICS file storage - no external API required.
---

# Calendar MCP Skill

Manage calendar events and schedule tasks for the AI Employee system.

## Purpose

Provide comprehensive calendar functionality:
- Create and manage events
- Detect scheduling conflicts
- Search and filter events
- Integration with task scheduling workflow
- Local-first storage (ICS files in vault)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CALENDAR MCP SERVER                       │
│                                                             │
│  MCP Tools:                                                 │
│  ├─ calendar_create_event                                   │
│  ├─ calendar_list_events                                    │
│  ├─ calendar_get_event                                      │
│  ├─ calendar_update_event                                   │
│  ├─ calendar_delete_event                                   │
│  ├─ calendar_search_events                                  │
│  ├─ calendar_check_conflicts                                │
│  └─ calendar_get_day_schedule                               │
│                                                             │
│  Storage:                                                   │
│  ├─ AI_Employee_Vault/Calendar/Events/*.ics                 │
│  └─ AI_Employee_Vault/Calendar/Metadata/event_index.json    │
│                                                             │
│  Python Tool:                                               │
│  └─ scripts/calendar_tool.py                                │
└─────────────────────────────────────────────────────────────┘
```

## MCP Server Setup

### 1. Install Dependencies

```bash
cd mcp-servers/calendar-mcp
npm install
```

### 2. Start Calendar MCP Server

```bash
cd mcp-servers/calendar-mcp
node index.js
```

Or set custom vault path:

```bash
VAULT_PATH=/path/to/vault node index.js
```

### 3. Configure in Qwen Code

Add to your MCP configuration:

```json
{
  "servers": [
    {
      "name": "calendar",
      "command": "node",
      "args": ["/path/to/mcp-servers/calendar-mcp/index.js"],
      "env": {
        "VAULT_PATH": "/path/to/AI_Employee_Vault"
      }
    }
  ]
}
```

## MCP Tools

### 1. calendar_create_event

Create a new calendar event.

**Parameters:**
- `title` (required): Event title
- `start` (required): Start datetime (YYYY-MM-DDTHH:MM:SS)
- `end` (required): End datetime (YYYY-MM-DDTHH:MM:SS)
- `description`: Event description
- `location`: Event location
- `categories`: Array of categories/tags
- `status`: CONFIRMED, TENTATIVE, or CANCELLED
- `priority`: 1-9 (1=highest, default: 5)
- `reminder_minutes`: Minutes before to remind (default: 15)
- `dry_run`: Simulate without creating

**Example:**
```json
{
  "title": "Team Meeting",
  "start": "2026-04-15T10:00:00",
  "end": "2026-04-15T11:00:00",
  "description": "Weekly sync meeting",
  "categories": ["meeting", "team"],
  "status": "CONFIRMED"
}
```

---

### 2. calendar_list_events

List upcoming calendar events.

**Parameters:**
- `days`: Days ahead to look (default: 7)
- `categories`: Filter by categories
- `status`: Filter by status
- `include_past`: Include past events

**Example:**
```json
{
  "days": 14,
  "categories": ["meeting"]
}
```

---

### 3. calendar_get_event

Get details for a specific event by ID.

**Parameters:**
- `event_id` (required): Unique event ID

**Example:**
```json
{
  "event_id": "event-20260415-100000-abc123"
}
```

---

### 4. calendar_update_event

Update an existing calendar event.

**Parameters:**
- `event_id` (required): Event ID to update
- `title`: New title
- `start`: New start time
- `end`: New end time
- `description`: New description
- `location`: New location
- `categories`: New categories
- `status`: New status
- `priority`: New priority

**Example:**
```json
{
  "event_id": "event-20260415-100000-abc123",
  "start": "2026-04-15T11:00:00",
  "end": "2026-04-15T12:00:00"
}
```

---

### 5. calendar_delete_event

Delete a calendar event.

**Parameters:**
- `event_id` (required): Event ID to delete

**Example:**
```json
{
  "event_id": "event-20260415-100000-abc123"
}
```

---

### 6. calendar_search_events

Search events by title, description, or categories.

**Parameters:**
- `query` (required): Search query string

**Example:**
```json
{
  "query": "meeting"
}
```

---

### 7. calendar_check_conflicts

Check for scheduling conflicts in a time range.

**Parameters:**
- `start` (required): Start of time range
- `end` (required): End of time range
- `exclude_id`: Event ID to exclude

**Example:**
```json
{
  "start": "2026-04-15T09:00:00",
  "end": "2026-04-15T17:00:00"
}
```

---

### 8. calendar_get_day_schedule

Get all events for a specific day.

**Parameters:**
- `date` (required): Date (YYYY-MM-DD)

**Example:**
```json
{
  "date": "2026-04-15"
}
```

---

## Python CLI Usage

You can also use the calendar tool directly from command line:

### Create Event

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault create \
  --title "Team Meeting" \
  --start "2026-04-15T10:00:00" \
  --end "2026-04-15T11:00:00" \
  --description "Weekly sync" \
  --categories meeting team
```

### List Events

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault list --days 7
```

### Search Events

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault search --query "meeting"
```

### Check Conflicts

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault conflicts \
  --start "2026-04-15T09:00:00" \
  --end "2026-04-15T17:00:00"
```

### Get Day Schedule

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault day --date "2026-04-15"
```

### Update Event

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault update \
  --event-id "event-20260415-100000-abc123" \
  --start "2026-04-15T11:00:00" \
  --end "2026-04-15T12:00:00"
```

### Delete Event

```bash
py scripts/calendar_tool.py --vault AI_Employee_Vault delete \
  --event-id "event-20260415-100000-abc123"
```

---

## Integration with Orchestrator

The calendar is integrated into the orchestrator for task scheduling:

### From Python Code

```python
from orchestrator import Orchestrator

orch = Orchestrator('AI_Employee_Vault')

# Schedule an event
event = orch.schedule_event(
    title="Client Meeting",
    start="2026-04-15T14:00:00",
    end="2026-04-15T15:00:00",
    description="Discuss project requirements",
    categories=["client", "meeting"]
)

# Get upcoming events
events = orch.get_upcoming_events(days=7)

# Check conflicts
conflicts = orch.check_schedule_conflicts(
    start="2026-04-15T14:00:00",
    end="2026-04-15T15:00:00"
)

# Get day schedule
day_events = orch.get_day_schedule("2026-04-15")
```

---

## Storage Structure

Events are stored as ICS files in the vault:

```
AI_Employee_Vault/
└── Calendar/
    ├── Events/
    │   ├── event-20260415-100000-abc123.ics
    │   ├── event-20260416-140000-def456.ics
    │   └── ...
    └── Metadata/
        └── event_index.json
```

### ICS File Format

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Employee//Calendar Tool//EN
BEGIN:VEVENT
UID:event-20260415-100000-abc123
DTSTAMP:20260413T035310
DTSTART:20260415T10000000
DTEND:20260415T11000000
SUMMARY:Team Meeting
DESCRIPTION:Weekly sync meeting
LOCATION:
CATEGORIES:meeting,team
STATUS:CONFIRMED
PRIORITY:5
END:VEVENT
END:VCALENDAR
```

### Event Index (JSON)

```json
{
  "events": {
    "event-20260415-100000-abc123": {
      "title": "Team Meeting",
      "start": "2026-04-15T10:00:00",
      "end": "2026-04-15T11:00:00",
      "categories": ["meeting", "team"],
      "status": "CONFIRMED",
      "file": "event-20260415-100000-abc123.ics"
    }
  },
  "last_updated": "2026-04-13T03:53:10"
}
```

---

## Workflow Examples

### Example 1: Schedule a Task with Conflict Check

```python
# 1. Check for conflicts first
conflicts = orch.check_schedule_conflicts(
    start="2026-04-15T14:00:00",
    end="2026-04-15T15:00:00"
)

if conflicts:
    print(f"⚠️  Conflicts detected: {[c['title'] for c in conflicts]}")
    # Suggest alternative time
else:
    # 2. Schedule the event
    event = orch.schedule_event(
        title="Task: Process invoices",
        start="2026-04-15T14:00:00",
        end="2026-04-15T15:00:00",
        categories=["task", "accounting"]
    )
    print(f"✅ Scheduled: {event['title']}")
```

### Example 2: Daily Briefing with Calendar

```python
# Get today's schedule
today = datetime.now().strftime('%Y-%m-%d')
events = orch.get_day_schedule(today)

print(f"📅 Today's Schedule ({today}):")
for event in events:
    print(f"  {event['start']} - {event['end']}: {event['title']}")
```

### Example 3: Weekly Planning

```python
# Get next 7 days
events = orch.get_upcoming_events(days=7)

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for event in events:
    for cat in event.get('categories', []):
        by_category[cat].append(event)

print("📊 Weekly Plan by Category:")
for category, cat_events in by_category.items():
    print(f"\n{category.upper()}:")
    for event in cat_events:
        print(f"  - {event['title']} ({event['start']})")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Calendar tool not found | Ensure `calendar_tool.py` exists in `scripts/` folder |
| Event creation fails | Check datetime format (YYYY-MM-DDTHH:MM:SS) |
| Conflicts not detected | Verify time ranges overlap correctly |
| ICS files missing | Check `Calendar/Events/` folder exists |
| Index corrupted | Delete `event_index.json` and recreate events |

---

## Best Practices

1. **Always Check Conflicts**: Before scheduling, check for time conflicts
2. **Use Categories**: Tag events for easy filtering and searching
3. **Set Reminders**: Use `reminder_minutes` for important events
4. **Descriptive Titles**: Make event titles clear and actionable
5. **Regular Cleanup**: Delete old/cancelled events to keep calendar clean
6. **Backup Calendar**: ICS files are plain text - easy to backup
7. **Use Dry Run**: Test scheduling with `dry_run=True` before committing

---

## Features

✅ **Local-First Storage**: All events stored as ICS files in vault  
✅ **Conflict Detection**: Automatic overlap checking  
✅ **Category Support**: Tag and filter events  
✅ **Search Functionality**: Full-text search across events  
✅ **JSON Output**: Easy integration with MCP and other tools  
✅ **No External Dependencies**: Pure Python implementation  
✅ **ICS Format Compatibility**: Standard iCalendar format  
✅ **Orchestrator Integration**: Built-in methods for scheduling  
✅ **CLI Support**: Direct command-line usage  
✅ **Audit Trail**: All operations logged  

---

*Calendar MCP Skill - AI Employee v1.0.0 (Gold Tier)*  
*"Never miss a meeting, always stay scheduled"*
