# Architecture Overview

**Personal AI Employee System Design**

---

## 🎯 System Goals

The Personal AI Employee is designed to:

1. **Autonomously manage** personal and business affairs 24/7
2. **Local-first architecture** for privacy and control
3. **Human-in-the-loop** for sensitive actions
4. **Modular design** for easy extension
5. **Resilient operations** with error recovery

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                         │
│         Gmail │ WhatsApp │ Bank APIs │ File Systems         │
│         LinkedIn │ Facebook │ Instagram │ Odoo ERP          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PERCEPTION LAYER (Watchers)                    │
│   Lightweight Python scripts monitoring external sources    │
│   - Gmail Watcher                                           │
│   - WhatsApp Watcher                                        │
│   - File System Watcher                                     │
│   - (Future: Finance Watcher, Twitter Watcher)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT (Local Memory/GUI)              │
│  Markdown-based knowledge base with folder structure:       │
│  /Inbox/ → /Needs_Action/ → /Plans/ → /Done/                │
│  /Pending_Approval/ → /Approved/ → /Rejected/               │
│  /Briefings/ │ /Accounting/ │ /Logs/                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              REASONING LAYER (Qwen Code)                    │
│   AI agent that reads, thinks, plans, and acts:             │
│   - Reads action files from Needs_Action/                   │
│   - Consults Company_Handbook.md for rules                  │
│   - Creates plans in Plans/                                 │
│   - Requests approval for sensitive actions                 │
│   - Moves completed tasks to Done/                          │
└────────────────────┬────────────────────────────────────────┘
                     │
              ┌──────┴──────┐
              ▼             ▼
┌──────────────────┐  ┌────────────────────────────────────┐
│  HUMAN APPROVAL  │  │         ACTION LAYER (MCP)         │
│  Review & Move   │  │  Model Context Protocol servers:   │
│  Files between   │  │  - Email MCP (Gmail API)           │
│  folders         │  │  - LinkedIn MCP (LinkedIn API)     │
│                  │  │  - Facebook MCP (Graph API)        │
│                  │  │  - Odoo MCP (ERP operations)       │
│                  │  │  - Browser MCP (Web automation)    │
└──────────────────┘  └────────────────────────────────────┘
```

---

## 📦 Core Components

### 1. Watchers (Perception Layer)

**Purpose:** Monitor external sources and create action files

**Pattern:**
```python
class BaseWatcher:
    def run(self):
        while True:
            items = self.check_for_updates()
            for item in items:
                self.create_action_file(item)
            time.sleep(check_interval)
```

**Implementations:**
- **Gmail Watcher:** Monitors Gmail API for unread/important emails
- **WhatsApp Watcher:** Uses Playwright to monitor WhatsApp Web
- **File System Watcher:** Watches drop folders for new files
- **(Future) Finance Watcher:** Downloads bank transactions

### 2. Obsidian Vault (Memory/GUI)

**Purpose:** Local-first storage for all data, plans, and logs

**Folder Structure:**
```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status
├── Company_Handbook.md       # Rules and guidelines
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Pending action items
├── Plans/                    # Generated action plans
├── Done/                     # Completed tasks
├── Pending_Approval/         # Awaiting human review
├── Approved/                 # Approved, ready to execute
├── Rejected/                 # Rejected actions
├── Logs/                     # Audit logs (JSONL)
├── Accounting/               # Financial records
└── Briefings/                # CEO briefing reports
```

### 3. Orchestrator (Coordination)

**Purpose:** Detect action files and trigger Qwen Code

**Workflow:**
1. Monitor `Needs_Action/` folder
2. Detect new action files
3. Build prompt with context (action file + handbook + goals)
4. Trigger Qwen Code
5. Track completion
6. Update Dashboard.md

### 4. Qwen Code (Reasoning)

**Purpose:** AI reasoning engine that makes decisions

**Capabilities:**
- Read and understand action files
- Consult Company Handbook for rules
- Create structured plans
- Request human approval when needed
- Execute actions via MCP servers
- Log all actions for audit

### 5. MCP Servers (Action Layer)

**Purpose:** External system integration

**Model Context Protocol (MCP)** provides standardized interfaces for:
- **Email MCP:** Send, draft, search emails (Gmail API)
- **LinkedIn MCP:** Post updates, manage profile
- **Facebook MCP:** Post to Pages, Instagram Business
- **Odoo MCP:** Create invoices, manage customers, register payments
- **Browser MCP:** Web automation via Playwright

### 6. Human-in-the-Loop (HITL)

**Purpose:** Human oversight for sensitive actions

**Pattern:**
```markdown
1. AI detects sensitive action needed
2. Creates approval file in Pending_Approval/
3. Human reviews and moves to Approved/ or Rejected/
4. Orchestrator detects approval and executes
5. Result logged to audit trail
```

**Approval Triggers:**
- Email to new contacts
- Payments > $100
- First-time social posts
- New vendors/customers
- Irreversible actions

### 7. Ralph Wiggum Loop (Persistence)

**Purpose:** Keep Qwen Code working until task complete

**Pattern:**
1. Orchestrator creates task with prompt
2. Qwen Code works on task
3. Qwen tries to exit
4. Stop hook checks: Is task complete?
5. NO → Block exit, re-inject prompt (loop continues)
6. YES → Allow exit

**Completion Detection:**
- Files moved to `Done/`
- Completion promise in output
- No more items in `Needs_Action/`

---

## 🔄 Data Flow

### Example: Email Processing

```
1. Gmail Watcher detects new email
   ↓
2. Creates action file in Needs_Action/
   ↓
3. Orchestrator detects file
   ↓
4. Triggers Qwen Code with prompt
   ↓
5. Qwen reads email + Company Handbook
   ↓
6. Qwen creates response draft
   ↓
7. For new contact: Creates approval request in Pending_Approval/
   ↓
8. Human reviews and moves to Approved/
   ↓
9. Email Approval Watcher detects approval
   ↓
10. Sends email via Gmail API
    ↓
11. Moves file to Done/
    ↓
12. Logs action to audit trail
```

---

## 🛡️ Security Architecture

### Credential Management

```bash
# NEVER store in vault or commit to git
.env (in .gitignore)
credentials.json (in .gitignore)
*.token.json (in .gitignore)

# Use environment variables
export GMAIL_CLIENT_ID="your_client_id"
export ODOO_PASSWORD="secure_password"
```

### Permission Boundaries

| Action Category | Auto-Approve | Requires Approval |
|----------------|--------------|-------------------|
| Email replies | Known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs, first-time |
| File operations | Create, read | Delete, move outside vault |

### Sandboxing

- **DEV_MODE flag:** Prevents real external actions during development
- **Dry Run:** All action scripts support `--dry-run`
- **Rate Limiting:** Max actions per hour (e.g., 10 emails, 3 payments)

---

## 📊 Reliability Features

### Error Recovery

1. **Retry Handler:** Exponential backoff for transient failures
2. **Circuit Breaker:** Prevents cascade failures
3. **Quarantine Manager:** Isolates problematic items
4. **Graceful Degradation:** System continues on partial failures

### Audit Logging

- **Format:** JSONL (machine-readable)
- **Rotation:** Daily log files
- **Retention:** 90 days
- **Schema:**
  ```json
  {
    "timestamp": "2026-03-07T12:00:00Z",
    "log_id": "uuid",
    "action_type": "facebook_post",
    "actor": "qwen_code",
    "parameters": {...},
    "approval_status": "approved",
    "result": "success",
    "duration_ms": 1234
  }
  ```

### Health Monitoring

- **Process Monitoring:** Watch all watcher processes
- **Auto-Restart:** Restart on failure (with rate limiting)
- **Resource Monitoring:** CPU, memory usage
- **External Service Checks:** API connectivity

---

## 📈 Scalability

### Vertical Scaling

- **More Watchers:** Add new perception sources
- **More MCP Servers:** Add new action capabilities
- **More Agent Skills:** Extend Qwen Code functionality

### Horizontal Scaling

- **Multiple Vaults:** Separate vaults for different domains
- **Vault Synchronization:** Git-based sync for multi-agent
- **Cloud Deployment:** 24/7 always-on operation (Platinum Tier)

---

## 🎓 Development Tiers

### Bronze Tier (Foundation)
- File System Watcher
- Basic Qwen Code integration
- Simple folder structure

### Silver Tier (Functional)
- Gmail Watcher
- WhatsApp Watcher
- LinkedIn Poster
- Email sending with HITL

### Gold Tier (Autonomous)
- Odoo ERP integration
- Facebook/Instagram posting
- CEO Briefing generator
- Error recovery & audit logging
- Ralph Wiggum Loop

### Platinum Tier (Production)
- Cloud deployment (24/7)
- Work-zone specialization
- Vault synchronization
- A2A messaging

---

## 📚 References

- **QWEN.md:** Comprehensive project context
- **Hackathon Brief:** Original requirements
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Ralph Wiggum Pattern:** https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum

---

*Architecture Overview - Personal AI Employee*
