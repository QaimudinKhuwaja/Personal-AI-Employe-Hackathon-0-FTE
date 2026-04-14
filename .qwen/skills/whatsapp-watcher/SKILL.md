---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages containing keywords like "urgent", "invoice", "payment".
  Uses Playwright for browser automation to monitor WhatsApp Web sessions.
  Creates action files in the Obsidian vault for Qwen Code to process.
  Note: Be aware of WhatsApp's terms of service when using automation.
---

# WhatsApp Watcher Skill

Monitor WhatsApp Web for important messages and create action files automatically.

## Prerequisites

### 1. Install Playwright

```bash
npm install -g @playwright/mcp
playwright install chromium
```

### 2. Install Python Dependencies

```bash
pip install playwright
playwright install
```

### 3. Setup WhatsApp Web Session

First time setup will require QR code scan:
```bash
python scripts/whatsapp_watcher.py /path/to/vault --setup-session
```

## Usage

### Start WhatsApp Watcher

```bash
# Continuous monitoring (checks every 30 seconds)
python scripts/whatsapp_watcher.py /path/to/AI_Employee_Vault --session /path/to/session

# With custom keywords to monitor
python scripts/whatsapp_watcher.py /path/to/vault --session /path/to/session --keywords "urgent,asap,invoice,payment,help"

# Test mode (run once and exit)
python scripts/whatsapp_watcher.py /path/to/vault --session /path/to/session --once
```

## How It Works

1. **Monitors** WhatsApp Web for unread messages
2. **Filters** messages containing important keywords
3. **Creates** action files in `Needs_Action/` folder
4. **Tracks** processed messages to avoid duplicates
5. **Logs** all activity to `Logs/` folder

## Monitored Keywords

Default keywords that trigger action file creation:
- `urgent`
- `asap`
- `invoice`
- `payment`
- `help`
- `important`

Customize with `--keywords` flag.

## Action File Format

Each message creates a markdown file like:

```markdown
---
type: whatsapp_message
from: +1234567890
chat: John Doe
received: 2026-02-24T10:30:00
priority: high
status: pending
keywords: [urgent, invoice]
---

## Message Content

"Hey, can you send me the invoice urgently?"

## Suggested Actions
- [ ] Read message
- [ ] Prepare invoice
- [ ] Reply to sender
- [ ] Mark as done
```

## Configuration

### Environment Variables

```bash
# .env file
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session
WHATSAPP_CHECK_INTERVAL=30
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code expired | Re-run with --setup-session to scan new QR |
| Session not found | Verify session path is correct |
| No messages detected | Check keywords, ensure messages are unread |
| Browser crashes | Update Playwright: `playwright install` |

## Security Notes

- WhatsApp session contains authentication data - keep secure
- Never commit session files to version control
- Be aware of WhatsApp's terms of service
- Use responsibly and avoid spam detection

## Privacy Considerations

- This tool reads WhatsApp Web messages
- Ensure you have permission to automate your WhatsApp account
- Consider privacy implications of message processing
- Store session data securely
