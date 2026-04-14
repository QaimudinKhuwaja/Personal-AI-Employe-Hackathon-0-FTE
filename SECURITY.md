# 🔐 Security & Privacy Policy

**Personal AI Employee (Digital FTE) — Security Architecture**  
*Last Updated: 2026-04-13 | Version: 1.0.0*

---

## ⚠️ Important Notice

This system is an **autonomous AI agent** that acts on your behalf using your credentials and accounts. **You are fully responsible for all actions it takes.** Regular oversight and review are mandatory — not optional.

---

## 1. Credential Management

### Storage

| Credential Type | Storage Method | Location |
|----------------|---------------|----------|
| API Keys & Tokens | Environment variables | `.env` file (gitignored) |
| OAuth2 Access/Refresh Tokens | Separate cached files | Project root (gitignored) |
| Gmail OAuth Credentials | JSON file | `credentials.json` (gitignored) |
| Database Passwords | Environment variables | `.env` + Docker secrets |
| Odoo API Keys | Environment variables | `.env` file |

### What We Do

✅ **`.env` file is gitignored** — never committed to version control  
✅ **`.env.example` template provided** — safe to share, contains only placeholder keys  
✅ **OAuth tokens stored separately** — not mixed with code or vault data  
✅ **Credentials.json in .gitignore** — Gmail OAuth file excluded from repo  
✅ **No hardcoded secrets** — zero secrets in source code  
✅ **Session files excluded** — WhatsApp/browser sessions gitignored  

### What We Never Do

❌ **Never store credentials in Obsidian vault** (Markdown files are visible)  
❌ **Never commit `.env` or `credentials.json`** to Git  
❌ **Never log secret values** in console or log files  
❌ **Never send credentials to external AI** (Qwen Code reads local files only)  
❌ **Never share tokens across machines** without explicit rotation  

### Credential Rotation Schedule

| Credential | Rotation Frequency | Method |
|-----------|-------------------|--------|
| Gmail OAuth tokens | Every 90 days | Re-authenticate via Google Cloud Console |
| LinkedIn access token | Every 60 days | Regenerate via LinkedIn Developers Portal |
| Facebook access token | Every 60 days | Refresh via Facebook Graph API Explorer |
| Odoo API key | Every 90 days | Regenerate in Odoo user settings |
| All other tokens | Every 90 days | Regenerate from respective provider portals |

### If Credentials Are Compromised

1. **Immediately rotate** all affected credentials
2. **Revoke existing tokens** from provider dashboards
3. **Review audit logs** for unauthorized actions during exposure window
4. **Delete and regenerate** `.env` file from `.env.example` template
5. **Re-authenticate** all watchers and MCP servers
6. **Review Quarantine folder** for any suspicious quarantined items

---

## 2. Human-in-the-Loop (HITL) Approvals

### Philosophy

**The AI Employee never acts autonomously on sensitive operations.** All high-risk actions require explicit human review and approval before execution.

### Approval Workflow

```
1. AI detects action requiring approval
2. AI creates approval request file in Pending_Approval/
3. Human reviews the request details
4. Human moves file to Approved/  →  Action executes
   OR
   Human moves file to Rejected/  →  Action is cancelled
5. Result is logged to audit trail
6. File moved to Done/ for record
```

### Approval Matrix

| Action Category | Auto-Approved | Requires Human Approval |
|----------------|--------------|------------------------|
| **Email replies** | Known contacts, routine responses | New contacts, bulk sends (>5), sensitive topics |
| **Payments** | Recurring payments < $50 to known payees | All new payees, any payment > $100, unusual amounts |
| **Social media** | Pre-scheduled, pre-approved content | New/unscheduled posts, replies, DMs, controversial topics |
| **Invoicing** | Invoice generation for known clients | New client invoices, custom amounts > $5,000 |
| **File operations** | Create, read, move within vault | Delete files, move outside vault, modify system files |
| **Calendar events** | Internal meetings < 1 hour | External client meetings, full-day events, recurring > 4 weeks |
| **System config** | Dashboard updates, log rotation | Modify Company Handbook rules, change credentials |

### Approval File Schema

Every approval request follows this format:

```yaml
---
type: approval_request
action: email_send / payment / social_post / calendar_event
recipient: client@example.com
amount: 500.00  # (if applicable)
created: 2026-04-13T10:30:00Z
expires: 2026-04-14T10:30:00Z  # 24-hour expiry
status: pending  # → approved / rejected / expired
---

## Action Details
- Summary of what will happen
- All relevant details for review

## To Approve
Move this file to /Approved/ folder.

## To Reject
Move this file to /Rejected/ folder.
```

### Expiration Policy

- Approval requests expire after **24 hours** if not reviewed
- Expired requests are moved to `Rejected/` automatically
- Critical actions generate email/SMS alerts to human
- Expired actions must be re-created with fresh details

### Emergency Stop

The human operator can immediately halt all autonomous operations by:

1. **Pressing `Ctrl+C`** in any running orchestrator/watcher terminal
2. **Setting `DRY_RUN=true`** in the `.env` file
3. **Moving all pending files** from `Approved/` to `Rejected/`
4. **Stopping process manager** (PM2/systemd) if running in production

---

## 3. Rate Limiting

### Purpose

Rate limiting prevents the AI Employee from overwhelming external services or taking excessive autonomous actions that could trigger account restrictions.

### Hard Limits

| Action Type | Limit per Hour | Limit per Day | Consequence When Exceeded |
|------------|---------------|--------------|--------------------------|
| **Email sends** | 10 | 50 | Queue remaining emails for next window |
| **Email replies** | 20 | 100 | Queue remaining replies for next window |
| **Payments** | 3 | 10 | Halt all payment processing, alert human |
| **LinkedIn posts** | 5 | 15 | Queue remaining posts for next window |
| **Facebook posts** | 5 | 15 | Queue remaining posts for next window |
| **Instagram posts** | 5 | 15 | Queue remaining posts for next window |
| **Twitter/X posts** | 10 | 30 | Queue remaining tweets for next window |
| **Calendar events** | 20 | 50 | Queue remaining events for next window |
| **Odoo API calls** | 60 | 500 | Slow down, retry with backoff |

### Implementation

Rate limiting is enforced at three levels:

1. **Script-level**: Each action script tracks its own action count
2. **Orchestrator-level**: Central coordinator tracks aggregate action counts
3. **API-level**: External service rate limits are respected with exponential backoff

```python
# Example: Email rate limiting in email_sender.py
class RateLimiter:
    def __init__(self, max_per_hour=10):
        self.max_per_hour = max_per_hour
        self.action_log = []  # Timestamps of recent actions

    def can_act(self) -> bool:
        now = datetime.now()
        # Count actions in last hour
        recent = [t for t in self.action_log if now - t < timedelta(hours=1)]
        self.action_log = recent  # Clean old entries
        return len(recent) < self.max_per_hour
```

### What Happens When Limits Are Hit

1. **Action is queued** — not discarded
2. **Human is notified** — via Dashboard update and optional email alert
3. **Processing continues** — other unrelated actions proceed normally
4. **Queue drains** — when the time window resets, queued actions execute
5. **Audit logged** — rate limit event recorded with full context

---

## 4. Audit Logging

### What We Log

Every action the AI Employee takes is recorded in a structured, machine-readable format:

| Field | Description | Example |
|-------|------------|---------|
| `timestamp` | ISO 8601 datetime | `2026-04-13T10:30:00Z` |
| `log_id` | Unique UUID for the log entry | `a1b2c3d4-...` |
| `action_type` | Type of action performed | `email_send`, `facebook_post`, `odoo_invoice` |
| `actor` | Which component performed the action | `orchestrator`, `gmail_watcher`, `linkedin_api_poster` |
| `target` | Who/what was affected | `client@example.com`, `Invoice #1234` |
| `parameters` | Action details (sanitized, no secrets) | `{"subject": "Invoice #1234"}` |
| `approval_status` | How the action was authorized | `auto`, `approved`, `rejected` |
| `approved_by` | Who authorized the action | `human`, `system` |
| `result` | Outcome of the action | `success`, `failed`, `pending` |
| `error_message` | Error details if failed | `SMTP connection timeout` |
| `duration_ms` | How long the action took | `1234` |

### Log Storage

```
Logs/
├── audit_2026-03-02.jsonl          # Daily audit log (JSONL format)
├── audit_2026-03-03.jsonl
├── facebook_2026-03-02.log
├── linkedin_api_2026-02-28.log
├── odoo_2026-03-02.log
└── ...
```

### Retention Policy

| Log Type | Retention Period | Reason |
|----------|----------------|--------|
| **Audit logs** (`audit_*.jsonl`) | 90 days | Compliance and review |
| **Social media logs** | 90 days | Performance tracking |
| **Orchestrator logs** | 30 days | Operational debugging |
| **Watcher logs** | 30 days | Operational debugging |
| **Quarantine records** | Indefinite (manual review required) | Failed items need human attention |

### Querying Logs

The audit logger supports structured queries:

```bash
# View today's audit log
cat Logs/audit_2026-04-13.jsonl

# Query by action type (using Python)
python scripts/audit_logger.py --query --action-type email_send --date 2026-04-13

# Query by result (success/failed)
python scripts/audit_logger.py --query --result failed --date 2026-04-13

# Export for compliance audit
python scripts/audit_logger.py --export audit_report_2026-Q1.json --period 2026-01-01:2026-03-31

# Get summary statistics
python scripts/audit_logger.py --summary --days 7
```

### Log Integrity

- Logs are **append-only** — never modified after creation
- Each entry has a **unique UUID** — tampering is detectable
- Daily log rotation prevents single-file corruption from losing all history
- Logs are **included in vault backups** for disaster recovery

### What Is NOT Logged

For security, we explicitly **never log**:

- ❌ Passwords or API keys
- ❌ OAuth2 token values
- ❌ Full email body content (only subject and sender are logged)
- ❌ WhatsApp message content (only keywords detected are logged)
- ❌ Banking transaction details (only amounts and statuses)
- ❌ Browser session cookies or authentication tokens

---

## 5. Data Privacy

### Local-First Architecture

All primary data storage is **local to your machine**:

| Data Type | Storage Location | External Transmission? |
|-----------|-----------------|----------------------|
| Obsidian vault | Local filesystem | No |
| Action files | Local filesystem | No |
| Audit logs | Local filesystem | No |
| Calendar events | Local ICS files | No |
| Quarantined items | Local filesystem | No |
| Email content | Only when sending via Gmail API | Yes (intended) |
| Social media posts | Only when posting via API | Yes (intended) |
| Odoo data | Local Docker container | No (unless cloud-deployed) |

### What Data Leaves Your Machine

| Data Type | Destination | Purpose |
|-----------|------------|---------|
| Email content | Gmail API (Google servers) | Sending/receiving emails |
| Social media posts | LinkedIn/Facebook APIs | Publishing content |
| WhatsApp messages | WhatsApp Web | Reading/sending messages |
| Odoo data | Local Docker (or cloud if deployed) | Accounting operations |

### AI Model Data Handling

- **Qwen Code reads local files only** — your vault, handbook, and action files
- **No vault data is sent to cloud AI models** unless you explicitly configure it
- **Qwen Code output is local** — processed in your terminal, stored in your vault
- **No training data collection** — your data is not used to train any AI models

### Encryption

| Data State | Method |
|-----------|--------|
| **At rest (vault)** | Standard filesystem permissions; optional full-disk encryption |
| **In transit (APIs)** | HTTPS/TLS 1.2+ for all external API calls |
| **OAuth tokens** | Stored as separate files with filesystem permissions |
| **Backups** | Encrypted if stored externally (recommended) |

---

## 6. Sandboxing & Isolation

### Development Mode

```bash
# Set in .env to prevent real external actions
DRY_RUN=true
```

When `DRY_RUN=true`:
- ✅ All watchers still detect and create action files
- ✅ Orchestrator still processes items
- ✅ Approval workflow still functions
- ❌ **No emails are actually sent**
- ❌ **No social media posts are published**
- ❌ **No payments are processed**
- ❌ **No calendar events are created**
- ✅ All intended actions are **logged** for review

### Test Mode

```bash
TEST_MODE=true
```

Additional restrictions in test mode:
- Processes only test files (prefixed with `TEST_`)
- No production data is accessed
- Safe for development and debugging

### Environment Isolation

- **Python virtual environment** recommended (`python -m venv .venv`)
- **Docker containers** for Odoo and PostgreSQL (isolated network)
- **Separate test accounts** recommended for Gmail, LinkedIn, Facebook during development
- **Never use production credentials** in `DRY_RUN=false` mode until thoroughly tested

---

## 7. Permission Boundaries

### What the AI Employee CAN Do Without Approval

1. Read and categorize incoming emails
2. Log transactions from bank statements
3. Create action files for new tasks
4. Update `Dashboard.md` with status
5. Generate routine reports (daily/weekly briefings)
6. Move processed files from `Needs_Action/` to `Done/`
7. Send pre-approved scheduled content (only if previously approved)
8. Process file drops to `/Inbox`
9. Monitor external sources (Gmail, WhatsApp, filesystem)
10. Check for scheduling conflicts in Calendar

### What the AI Employee MUST NEVER Do Without Approval

1. Send money or make payments to **new recipients**
2. Sign contracts or legal documents
3. Share personal or client data externally
4. Delete files outside the vault
5. Install software or modify system settings
6. Respond to legal or medical inquiries
7. Engage in negotiations or disputes
8. Commit to deadlines or promises on behalf of human
9. Access accounts not explicitly authorized
10. Any **irreversible action**

### Escalation Triggers

Immediately alert human when:

| Trigger Category | Examples | Response |
|----------------|----------|----------|
| **Financial** | Transaction > $500, unusual pattern, potential fraud | Pause all financial actions, create approval request |
| **Legal** | Contract received, legal notice, subpoena | Quarantine item, alert human immediately |
| **Medical** | Health-related emergency message | Quarantine item, alert human immediately |
| **Security** | Suspicious login, data breach notification | Pause all external API calls, alert human |
| **Emotional** | Condolence, conflict, sensitive personal matter | Quarantine item, request human review |
| **Technical** | System failure, data corruption, repeated errors | Auto-restart, quarantine failing items, alert human |

---

## 8. Oversight Schedule

| Frequency | Activity | Duration |
|-----------|----------|----------|
| **Daily** | Review Dashboard.md, check Pending_Approval/ folder | 2 minutes |
| **Weekly** | Review CEO Briefing, audit action logs | 15 minutes |
| **Monthly** | Comprehensive audit review, rotate credentials | 1 hour |
| **Quarterly** | Full security audit, review all permissions | 2 hours |
| **After incidents** | Review quarantine folder, check for patterns | As needed |

### What to Check During Reviews

**Daily (2 min):**
- [ ] Any items in `Pending_Approval/`?
- [ ] Dashboard status shows green?
- [ ] Any quarantine alerts?

**Weekly (15 min):**
- [ ] Review CEO Briefing for anomalies
- [ ] Check `Logs/audit_*.jsonl` for errors
- [ ] Review `Quarantine/` for items needing attention
- [ ] Verify `Done/` items are legitimate

**Monthly (1 hour):**
- [ ] Rotate all API credentials
- [ ] Review Company Handbook for rule updates
- [ ] Backup vault and database
- [ ] Update Docker images
- [ ] Review rate limit statistics

**Quarterly (2 hours):**
- [ ] Full audit of all autonomous actions
- [ ] Review and update approval matrix
- [ ] Check for unused subscriptions to cancel
- [ ] Verify all watchers and MCP servers are healthy
- [ ] Test disaster recovery (restore from backup)

---

## 9. Reporting Security Issues

If you discover a security vulnerability in this project:

1. **Do NOT open a public issue** — this could expose the vulnerability
2. **Contact the maintainer directly** via private channel
3. **Include details**: what you found, how to reproduce it, potential impact
4. **Allow reasonable time** for a fix before public disclosure

We take security seriously and will respond promptly to all reports.

---

## 10. Disclaimer

> This system autonomously performs actions on your behalf using your credentials and accounts. **You are solely responsible for all actions it takes.** The maintainers of this project are not liable for any damages, account suspensions, financial losses, or legal issues arising from its use.
>
> Always:
> - Review the AI's actions regularly
> - Keep credentials secure
> - Start with `DRY_RUN=true` and test thoroughly
> - Use test/sandbox accounts during development
> - Consult legal counsel for business use cases
> - Understand your local laws regarding AI automation

---

*Security & Privacy Policy v1.0.0 — Personal AI Employee (Digital FTE)*  
*"Automate responsibly. Stay in control."*
