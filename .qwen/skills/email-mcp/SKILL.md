---
name: email-mcp
description: |
  Send emails via Gmail API or SMTP. Supports sending, drafting, and searching emails.
  Requires Gmail API credentials or SMTP configuration.
  Use for responding to emails, sending invoices, notifications, and business communication.
---

# Email MCP Skill

Send and manage emails through the AI Employee system.

## Prerequisites

### Option 1: Gmail API (Recommended)

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Option 2: SMTP

```bash
pip install aiosmtplib
```

## Configuration

### Gmail API Setup

1. Enable Gmail API in Google Cloud Console
2. Download credentials.json
3. Authenticate first time:
   ```bash
   python scripts/auth_gmail.py
   ```

### Environment Variables

```bash
# Gmail API
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json

# SMTP (alternative)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Usage

### Send Email

```bash
python scripts/email_sender.py \
  --to recipient@example.com \
  --subject "Invoice #123" \
  --body "Please find attached your invoice..." \
  --attachment /path/to/invoice.pdf
```

### Send from Action File

```bash
python scripts/email_sender.py --action-file /path/to/approved_email.md
```

## Email Action File Format

```markdown
---
type: email_send
to: client@example.com
cc: manager@example.com
bcc: records@company.com
subject: Invoice #123 - February 2026
priority: normal
status: approved
---

## Email Body

Dear Client,

Please find attached your invoice for February 2026.

Best regards,
Your Company

## Attachments
- /path/to/invoice.pdf

## To Send
This email has been approved. Execute send.
```

## Features

- ✅ Send emails with attachments
- ✅ CC/BCC support
- ✅ HTML and plain text
- ✅ Reply threading
- ✅ Draft mode (don't send, just prepare)
- ✅ Rate limiting (configurable)
- ✅ Retry on failure

## Rate Limiting

Default limits to avoid Gmail API quotas:
- Max 10 emails per hour
- Max 100 emails per day

Configure in `.env`:
```bash
MAX_EMAILS_PER_HOUR=10
MAX_EMAILS_PER_DAY=100
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run auth_gmail.py |
| Attachment too large | Gmail limit is 25MB |
| Rate limit exceeded | Wait and retry, or increase limits |
| SMTP error | Check credentials and app password |
