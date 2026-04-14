---
name: gmail-watcher
description: |
  Monitor Gmail for new unread/important emails and create action files in the Obsidian vault.
  Uses Gmail API to fetch emails and creates markdown files in Needs_Action folder for Qwen Code to process.
  Requires Gmail API credentials setup.
---

# Gmail Watcher Skill

Monitor Gmail inbox and create action files for new emails automatically.

## Prerequisites

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials.json

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. Authenticate First Time

```bash
python scripts/auth_gmail.py
```

## Usage

### Start Gmail Watcher

```bash
# Continuous monitoring (checks every 120 seconds)
python scripts/gmail_watcher.py /path/to/AI_Employee_Vault --credentials /path/to/credentials.json

# With custom check interval (60 seconds)
python scripts/gmail_watcher.py /path/to/AI_Employee_Vault --credentials /path/to/credentials.json --interval 60

# Test mode (run once and exit)
python scripts/gmail_watcher.py /path/to/AI_Employee_Vault --credentials /path/to/credentials.json --once
```

## How It Works

1. **Monitors** Gmail for unread/important emails
2. **Creates** action files in `Needs_Action/` folder
3. **Tracks** processed email IDs to avoid duplicates
4. **Logs** all activity to `Logs/` folder

## Action File Format

Each email creates a markdown file like:

```markdown
---
type: email
from: client@example.com
subject: Invoice Request
received: 2026-02-24T10:30:00
priority: high
status: pending
email_id: 18d4f2a1b2c3d4e5
---

## Email Content

Client message snippet here...

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

## Configuration

### Environment Variables

```bash
# .env file
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_CHECK_INTERVAL=120
```

### Gmail Query Filters

By default, watches for: `is:unread is:important`

Customize in code:
```python
q='is:unread is:important from:important@client.com'
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gmail API 403 Error | Enable Gmail API in Google Cloud Console |
| Token expired | Re-run auth_gmail.py to refresh token |
| No emails detected | Check Gmail query filter, verify emails are unread |
| Credentials not found | Verify credentials.json path is correct |

## Security Notes

- Never commit credentials.json to version control
- Store token.json securely
- Use environment variables for sensitive data
- Rotate credentials regularly
