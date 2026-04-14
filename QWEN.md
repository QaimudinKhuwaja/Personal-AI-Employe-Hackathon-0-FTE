# Personal AI Employee (Digital FTE)

A comprehensive blueprint for building an autonomous AI agent that manages personal and business affairs 24/7 using **Qwen Code** as the reasoning engine and **Obsidian** as the local-first dashboard.

## Project Overview

This project implements a "Digital Full-Time Equivalent (FTE)" - an AI employee that works autonomously to handle:
- **Personal Affairs**: Gmail, WhatsApp, banking notifications
- **Business Operations**: Social media posting, invoicing, task management, accounting

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                         │
│         Gmail │ WhatsApp │ Bank APIs │ File Systems         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 PERCEPTION LAYER (Watchers)                 │
│   Gmail Watcher │ WhatsApp Watcher │ Finance Watcher        │
│   (Python scripts using Playwright, Gmail API, etc.)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT (Local Memory/GUI)              │
│  /Needs_Action/ │ /Plans/ │ /Done/ │ /Pending_Approval/     │
│  Dashboard.md │ Company_Handbook.md │ Business_Goals.md     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              REASONING LAYER (Qwen Code)                    │
│   Read → Think → Plan → Write → Request Approval            │
│   Ralph Wiggum Loop for multi-step task persistence         │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
┌──────────────────────┐  ┌────────────────────────────────────┐
│  HUMAN-IN-THE-LOOP   │  │         ACTION LAYER (MCP)         │
│  Review & Approve    │  │  Email MCP │ Browser MCP │ Odoo    │
└──────────────────────┘  └────────────────────────────────────┘
```

### Key Design Principles

1. **Local-First**: All data stored locally in Obsidian Markdown vault for privacy
2. **Human-in-the-Loop (HITL)**: Sensitive actions require explicit approval via file movement
3. **Watcher-Based Triggers**: Lightweight Python scripts monitor external sources continuously
4. **Ralph Wiggum Loop**: Stop hook pattern keeps Qwen iterating until tasks complete
5. **Agent Skills**: All AI functionality implemented as Qwen Agent Skills

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Reasoning Engine** | Qwen Code | Primary AI agent |
| **Knowledge Base** | Obsidian v1.10.6+ | Local Markdown dashboard & long-term memory |
| **Orchestration** | Python 3.13+ | Watcher scripts, orchestrator, watchdog |
| **MCP Servers** | Node.js v24+ LTS | External system integration |
| **Browser Automation** | Playwright MCP | Web interactions, form filling |
| **Version Control** | GitHub Desktop | Vault synchronization |
| **ERP Integration** | Odoo Community (self-hosted) | Accounting & business management |

## Silver Tier Skills

The following agent skills are available for Silver Tier functionality:

| Skill | Description | Status |
|-------|-------------|--------|
| **browsing-with-playwright** | Browser automation for web interactions | ✅ Available |
| **gmail-watcher** | Monitor Gmail for new emails | ✅ Available |
| **whatsapp-watcher** | Monitor WhatsApp Web for messages | ✅ Available |
| **email-mcp** | Send emails via Gmail API or SMTP | ✅ Available |
| **linkedin-poster** | Post updates to LinkedIn | ✅ Available |
| **plan-generator** | Create structured action plans | ✅ Available |
| **hitl-approval** | Human-in-the-loop approval workflow | ✅ Available |
| **task-scheduler** | Schedule recurring tasks | ✅ Available |

### Skill Locations

```
.qwen/skills/
├── browsing-with-playwright/   # Browser automation
├── gmail-watcher/              # Gmail monitoring
├── whatsapp-watcher/           # WhatsApp monitoring
├── email-mcp/                  # Email sending
├── linkedin-poster/            # LinkedIn posting
├── plan-generator/             # Plan creation
├── hitl-approval/              # Approval workflow
└── task-scheduler/             # Task scheduling
```

## Project Structure

```
Personal-Ai-Employe-FTE/
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main blueprint
├── skills-lock.json          # Skill dependencies
├── QWEN.md                   # This file
└── .qwen/
    └── skills/
        └── browsing-with-playwright/  # Playwright MCP skill
            ├── SKILL.md
            ├── references/
            │   └── playwright-tools.md
            └── scripts/
                ├── mcp-client.py
                ├── start-server.sh
                ├── stop-server.sh
                └── verify.py
```

## Getting Started

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Qwen Code](https://github.com/anthropics/qwen-code) | Latest | Reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers |
| [GitHub Desktop](https://desktop.github.com/download/) | Latest | Version control |

### Initial Setup

1. **Create Obsidian Vault**:
   ```bash
   mkdir AI_Employee_Vault
   cd AI_Employee_Vault
   ```

2. **Set up folder structure**:
   ```
   /Inbox          # Raw incoming items
   /Needs_Action   # Items requiring Qwen's attention
   /Plans          # Generated action plans
   /Done           # Completed tasks
   /Pending_Approval  # Awaiting human approval
   /Approved       # Approved actions ready to execute
   /Rejected       # Rejected actions
   /Logs           # Audit logs
   /Accounting     # Financial records
   /Briefings      # CEO briefing reports
   ```

3. **Verify Qwen Code**:
   ```bash
   qwen --version
   ```

4. **Set up Python environment** (using UV or venv):
   ```bash
   # Initialize Python project
   uv init
   # Or: python -m venv .venv
   ```

5. **Install Playwright** (for browser automation):
   ```bash
   npm install -g @playwright/mcp
   playwright install
   ```

## Key Components

### 1. Watchers (Perception Layer)

Lightweight Python scripts that run continuously, monitoring external sources:

- **Gmail Watcher**: Monitors unread/important emails via Gmail API
- **WhatsApp Watcher**: Uses Playwright to monitor WhatsApp Web for keywords
- **File System Watcher**: Watches drop folders for new files
- **Finance Watcher**: Downloads bank transactions, monitors accounting

**Base Pattern**:
```python
class BaseWatcher(ABC):
    def run(self):
        while True:
            items = self.check_for_updates()
            for item in items:
                self.create_action_file(item)
            time.sleep(check_interval)
```

### 2. Reasoning (Qwen Code)

Qwen Code reads from `/Needs_Action/` and `/Accounting/`, then:
1. Creates `Plan.md` with step-by-step checkboxes
2. Writes to `Dashboard.md` for status updates
3. Creates approval requests in `/Pending_Approval/` for sensitive actions

### 3. Human-in-the-Loop (HITL)

For sensitive actions (payments, emails to new contacts):
1. Qwen Code creates approval file in `/Pending_Approval/`
2. Human reviews and moves file to `/Approved/` or `/Rejected/`
3. Orchestrator detects approval and executes via MCP

**Approval File Schema**:
```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A
- Reference: Invoice #1234

## To Approve
Move this file to /Approved folder.
```

### 4. Ralph Wiggum Loop (Persistence)

A Stop hook pattern that keeps Qwen Code working until task completion:

1. Orchestrator creates state file with prompt
2. Qwen Code works on task
3. Qwen Code tries to exit
4. Stop hook checks: Is task file in `/Done`?
5. If NO → Block exit, re-inject prompt (loop continues)
6. Repeat until complete or max iterations

Reference: [ralph-wiggum plugin](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)

### 5. MCP Servers (Action Layer)

Model Context Protocol servers provide Qwen Code's "hands":

| Server | Capabilities | Use Case |
|--------|-------------|----------|
| `filesystem` | Read, write, list files | Built-in vault operations |
| `email-mcp` | Send, draft, search emails | Gmail integration |
| `browser-mcp` | Navigate, click, fill forms | Payment portals, web automation |
| `calendar-mcp` | Create, update events | Scheduling |
| `odoo-mcp` | Accounting operations | Odoo ERP integration |

**MCP Configuration** (`~/.config/qwen-code/settings.json`):
```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@anthropic/browser-mcp"],
      "env": {
        "HEADLESS": "true"
      }
    }
  ]
}
```

## Development Tiers

### Bronze Tier (8-12 hours)
- [ ] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [ ] One working Watcher script (Gmail OR file system)
- [ ] Claude reading/writing to vault
- [ ] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`

### Silver Tier (20-30 hours)
- [ ] All Bronze + 
- [ ] Two or more Watcher scripts
- [ ] Auto-post to LinkedIn
- [ ] Plan.md generation
- [ ] One working MCP server
- [ ] HITL approval workflow
- [ ] Basic scheduling (cron/Task Scheduler)

### Gold Tier (40+ hours)
- [ ] All Silver +
- [ ] Full cross-domain integration (Personal + Business)
- [ ] Odoo accounting integration via MCP
- [ ] Facebook/Instagram/Twitter integration
- [ ] Weekly CEO Briefing generation
- [ ] Error recovery & graceful degradation
- [ ] Comprehensive audit logging
- [ ] Ralph Wiggum loop implementation

### Platinum Tier (60+ hours)
- [ ] All Gold +
- [ ] Cloud VM deployment (24/7 always-on)
- [ ] Work-Zone Specialization (Cloud vs Local)
- [ ] Delegation via Synced Vault (Git/Syncthing)
- [ ] Odoo on Cloud with HTTPS & backups
- [ ] A2A upgrade (optional)

## Security & Privacy

### Credential Management

**NEVER** store credentials in plain text or vault:
```bash
# Use environment variables
export GMAIL_CLIENT_ID="your_client_id"
export BANK_API_TOKEN="your_token"

# Use .env file (add to .gitignore)
# .env structure:
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
BANK_API_TOKEN=your_token
WHATSAPP_SESSION_PATH=/secure/path/session
```

### Sandboxing

- **DEV_MODE flag**: Prevents real external actions during development
- **Dry Run**: All action scripts support `--dry-run`
- **Rate Limiting**: Max actions per hour (e.g., 10 emails, 3 payments)

### Permission Boundaries

| Action Category | Auto-Approve | Requires Approval |
|----------------|--------------|-------------------|
| Email replies | Known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

## Key Templates

### Company_Handbook.md
```markdown
---
last_updated: 2026-01-07
---

## Rules of Engagement

1. Always be polite on WhatsApp
2. Flag any payment over $500 for approval
3. No auto-payments to new recipients
4. Response time target: < 24 hours for client messages
```

### Business_Goals.md
```markdown
---
last_updated: 2026-01-07
review_frequency: weekly
---

## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $4,500

### Key Metrics to Track
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |
```

### CEO Briefing (Generated Output)
```markdown
---
generated: 2026-01-06T07:00:00Z
period: 2025-12-30 to 2026-01-05
---

# Monday Morning CEO Briefing

## Executive Summary
Strong week with revenue ahead of target. One bottleneck identified.

## Revenue
- **This Week**: $2,450
- **MTD**: $4,500 (45% of $10,000 target)
- **Trend**: On track

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |

## Proactive Suggestions

### Cost Optimization
- **Notion**: No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription? Move to /Pending_Approval
```

## Running the System

### Start Watchers
```bash
# Gmail Watcher
python gmail_watcher.py

# WhatsApp Watcher (requires Playwright)
python whatsapp_watcher.py

# File System Watcher
python filesystem_watcher.py
```

### Start Playwright MCP Server
```bash
# Using helper script
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Or manually
npx @playwright/mcp@latest --port 8808 --shared-browser-context &
```

### Start Orchestrator
```bash
python orchestrator.py
```

### Start Watchdog (Process Monitor)
```bash
python watchdog.py
```

### Using PM2 for Production
```bash
# Install PM2
npm install -g pm2

# Start watchers
pm2 start gmail_watcher.py --interpreter python3
pm2 start whatsapp_watcher.py --interpreter python3
pm2 start orchestrator.py --interpreter python3

# Save and enable startup
pm2 save
pm2 startup
```

## Testing & Verification

### Verify Playwright MCP
```bash
python .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Test Dry Run Mode
```bash
export DRY_RUN=true
python email_sender.py --dry-run
```

### Check Process Health
```bash
# Check if watchers are running
pgrep -f "gmail_watcher"
pgrep -f "whatsapp_watcher"

# Check MCP server
pgrep -f "@playwright/mcp"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Qwen Code "command not found" | Ensure Qwen Code is installed and in PATH |
| Obsidian vault not being read | Run Qwen Code from vault directory or use `--cwd` flag |
| Gmail API 403 Forbidden | Enable Gmail API in Google Cloud Console, verify OAuth consent |
| Watchers stop overnight | Use PM2 or supervisord for process management |
| Qwen Code making wrong decisions | Review Company_Handbook.md, add more specific rules |
| MCP server won't connect | Check server is running, verify absolute paths in settings |

## Learning Resources

### Prerequisites
- [Qwen Code Documentation](https://github.com/anthropics/qwen-code)
- [Obsidian Fundamentals](https://help.obsidian.md/Getting+started)
- [MCP Introduction](https://modelcontextprotocol.io/introduction)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Core Learning
- [Qwen Code + Obsidian Integration](https://www.youtube.com/watch?v=sCIS05Qt79Y)
- [Building MCP Servers](https://modelcontextprotocol.io/quickstart)
- [Gmail API Setup](https://developers.google.com/gmail/api/quickstart)
- [Playwright Automation](https://playwright.dev/python/docs/intro)

### Silver Tier Skills Documentation
- [Gmail Watcher](./.qwen/skills/gmail-watcher/SKILL.md)
- [WhatsApp Watcher](./.qwen/skills/whatsapp-watcher/SKILL.md)
- [Email MCP](./.qwen/skills/email-mcp/SKILL.md)
- [LinkedIn Poster](./.qwen/skills/linkedin-poster/SKILL.md)
- [Plan Generator](./.qwen/skills/plan-generator/SKILL.md)
- [HITL Approval](./.qwen/skills/hitl-approval/SKILL.md)
- [Task Scheduler](./.qwen/skills/task-scheduler/SKILL.md)

### Reference Implementations
- [MCP Servers](https://github.com/anthropics/mcp-servers)
- [Ralph Wiggum Plugin](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [Odoo MCP Server](https://github.com/AlanOgic/mcp-odoo-adv)

## Community & Support

- **Weekly Research Meeting**: Wednesdays 10:00 PM on Zoom
  - Meeting ID: 871 8870 7642
  - Passcode: 744832
  - [Zoom Link](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)

- **YouTube**: [Panaversity Channel](https://www.youtube.com/@panaversity)

## Ethics & Responsible Automation

### When AI Should NOT Act Autonomously
- Emotional contexts (condolences, conflicts)
- Legal matters (contracts, filings)
- Medical decisions
- Financial edge cases (unusual transactions)
- Irreversible actions

### Oversight Schedule
1. **Daily**: 2-minute dashboard check
2. **Weekly**: 15-minute action log review
3. **Monthly**: 1-hour comprehensive audit
4. **Quarterly**: Full security and access review

**Remember**: You are responsible for your AI employee's actions. Regular oversight is essential.
