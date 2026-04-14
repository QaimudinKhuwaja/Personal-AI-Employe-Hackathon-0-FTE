# Personal AI Employee (Digital FTE)

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

[![Tier Status](https://img.shields.io/badge/Tier-Gold%20Tier%20Complete-brightgreen)](./docs/TIER_DECLARATION.md)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/Node.js-v24+-green.svg)](https://nodejs.org/)
[![Obsidian](https://img.shields.io/badge/Obsidian-v1.10.6+-purple.svg)](https://obsidian.md/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 🎯 What This Does

Your Personal AI Employee autonomously handles:

### Personal Affairs
- 📧 **Gmail** — Monitor, categorize, and respond to emails
- 💬 **WhatsApp** — Track urgent messages and keywords
- 📁 **Files** — Process documents dropped in your inbox
- 📅 **Calendar** — Schedule events, check conflicts, manage daily agenda

### Business Operations
- 📱 **Social Media** — Auto-post to LinkedIn, Facebook, Instagram, and Twitter/X
- 💰 **Accounting** — Manage invoices, customers, payments (Odoo ERP)
- 📊 **Reporting** — Generate weekly CEO briefings with actionable insights
- ✅ **Approvals** — Human-in-the-loop for all sensitive actions
- 🦺 **Quarantine** — Auto-isolate failed tasks for human review
- 🔗 **A2A Communication** — Agents coordinate directly without file-based triggering

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                          │
│  Gmail │ WhatsApp │ Twitter/X │ Bank APIs │ File Systems    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              PERCEPTION LAYER (Watchers)                     │
│  Gmail │ WhatsApp │ File System │ Facebook Comment Monitor  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           OBSIDIAN VAULT (Local Memory & Dashboard)          │
│  Dashboard │ Handbook │ Goals │ /Needs_Action │ /Done       │
│  /Calendar │ /Quarantine │ /Briefings (7 files) │ /Logs     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              REASONING LAYER (Qwen Code)                     │
│  Read → Think → Plan → Write → Request Approval              │
│  Ralph Wiggum Loop: multi-step persistence                  │
│  A2A Communication: direct inter-agent coordination         │
└───────────────────────┬─────────────────────────────────────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
┌──────────────────────┐  ┌────────────────────────────────────┐
│  HUMAN-IN-THE-LOOP   │  │         ACTION LAYER (MCP)         │
│  Review & Move Files │  │  Calendar (8) │ Odoo (7) │ Social  │
└──────────────────────┘  └────────────────────────────────────┘
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Qwen Code](https://github.com/anthropics/qwen-code) | Latest | AI reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers |
| [Docker](https://www.docker.com/products/docker-desktop/) | Latest | Odoo ERP (Gold Tier) |

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd Personal-AI-Employee-FTE
```

### Step 2: Open Obsidian Vault

```bash
# The vault is ready in AI_Employee_Vault/
# Open Obsidian → "Open folder as vault" → Select: AI_Employee_Vault/
```

**Vault Structure:**
```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status
├── Company_Handbook.md       # Rules for AI
├── Business_Goals.md         # Your objectives
├── Inbox/                    # Drop files here
├── Needs_Action/             # Pending tasks
├── Done/                     # 22 completed tasks
├── Pending_Approval/         # Awaiting your review
├── Approved/                 # Ready to execute
├── Calendar/                 # 2 scheduled events
├── Quarantine/               # Auto-isolated failures
├── Briefings/                # 7 CEO briefing reports
└── Logs/                     # Full audit trail
```

### Step 3: Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials (LinkedIn, Facebook, Twitter, etc.)
```

### Step 4: Start the System

**Minimum Setup (Bronze Tier):**
```bash
# Terminal 1: File System Watcher
py scripts/filesystem_watcher.py AI_Employee_Vault

# Terminal 2: Orchestrator
py scripts/orchestrator.py AI_Employee_Vault
```

**Full Gold Tier Setup:**
```bash
# Terminal 1: A2A Broker (for inter-agent communication)
py scripts/a2a/a2a_broker.py --port 8899

# Terminal 2: Calendar MCP
cd mcp-servers/calendar-mcp && node index.js

# Terminal 3: Gmail Watcher
py scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json

# Terminal 4: WhatsApp Watcher
py scripts/whatsapp_watcher.py AI_Employee_Vault

# Terminal 5: File System Watcher
py scripts/filesystem_watcher.py AI_Employee_Vault

# Terminal 6: Orchestrator (main brain)
py scripts/orchestrator.py AI_Employee_Vault

# Terminal 7: Email Approval Watcher
py scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

---

## 📊 Feature Matrix

### 🥉 Bronze Tier (Foundation — 8-12 hours)
- ✅ Obsidian vault with Dashboard, Handbook, Goals
- ✅ File System Watcher (drop folder monitoring)
- ✅ Qwen Code integration
- ✅ Basic folder structure (/Inbox, /Needs_Action, /Done)
- ✅ Agent Skills foundation

### 🥈 Silver Tier (Functional Assistant — 20-30 hours)
All Bronze +
- ✅ Gmail Watcher (auto-detect emails via API)
- ✅ WhatsApp Watcher (urgent message alerts via Playwright)
- ✅ LinkedIn Poster (auto-post via REST API — 4 successful posts)
- ✅ Facebook Poster (auto-post via Graph API v18.0)
- ✅ Email sending with approval workflow
- ✅ Human-in-the-loop (HITL) approvals
- ✅ Basic scheduling (task-scheduler skill)
- ✅ 8 Agent Skills

### 🥇 Gold Tier (Autonomous Employee — 40+ hours) ← **THIS PROJECT**
All Silver +
- ✅ **Odoo ERP integration** (Docker compose, 650-line connector, MCP server with 7 tools)
- ✅ **Twitter/X integration** (API v2, posting with hashtags, weekly summary generation)
- ✅ **Instagram support** (2-step Graph API upload flow)
- ✅ **Calendar MCP** (8 tools: create, list, search, conflicts, day schedule)
- ✅ **Weekly CEO Briefing** (7 briefing files generated with real data from logs)
- ✅ **Error recovery** (circuit breaker pattern, retry handler, exponential backoff)
- ✅ **Quarantine system** (auto-isolate after 3 failures, CLI viewer, Dashboard integration)
- ✅ **A2A Communication** (HTTP broker, agent discovery, task delegation, 8/8 tests)
- ✅ **Ralph Wiggum loop** (integrated into orchestrator, configurable iterations)
- ✅ **Comprehensive audit logging** (JSONL, 90-day retention, query/export)
- ✅ **Health monitoring** (process auto-restart, external service checks)
- ✅ **14 Agent Skills** (documented with SKILL.md files)
- ✅ **Full documentation** (20+ files including SECURITY.md)

---

## 📁 Project Structure

```
Personal-AI-Employee-FTE/
├── README.md                     # This file
├── SECURITY.md                   # Security & credential handling
├── .env.example                  # Environment template
├── docker-compose.yml            # Odoo + PostgreSQL
├── QWEN.md                       # Architecture blueprint
│
├── docs/                         # Documentation (20+ files)
│   ├── TIER_DECLARATION.md       # Gold tier submission declaration
│   ├── architecture/             # System design docs
│   ├── guides/                   # Setup guides (11 files)
│   └── reference/                # Reference docs (8 files)
│
├── scripts/                      # Python scripts (27 files, ~13,500 lines)
│   ├── a2a/                      # Agent-to-Agent communication
│   │   ├── a2a_broker.py         # HTTP message broker
│   │   ├── a2a_client.py         # Client library
│   │   ├── a2a_agent.py          # Base agent class
│   │   ├── a2a_registry.py       # Agent discovery
│   │   ├── example_agents.py     # Example agents
│   │   └── test_a2a.py           # Test suite (8/8 passing)
│   ├── base_watcher.py           # Watcher base class
│   ├── gmail_watcher.py          # Gmail API monitoring
│   ├── whatsapp_watcher.py       # WhatsApp Web monitoring
│   ├── filesystem_watcher.py     # File drop monitoring
│   ├── orchestrator.py           # Main orchestrator + Ralph Wiggum
│   ├── email_sender.py           # Email sending (Gmail API/SMTP)
│   ├── email_approval_watcher.py # HITL email approvals
│   ├── linkedin_api_poster.py    # LinkedIn REST API posting
│   ├── facebook_graph_poster.py  # Facebook/Instagram Graph API
│   ├── twitter_poster.py         # Twitter/X API v2 posting + summary
│   ├── odoo_connector.py         # Odoo ERP JSON-RPC connector
│   ├── calendar_tool.py          # Calendar management (ICS files)
│   ├── ceo_briefing_generator.py # Weekly CEO briefing reports
│   ├── quarantine_viewer.py      # Quarantine management CLI
│   ├── retry_handler.py          # Error recovery + circuit breaker
│   ├── health_checker.py         # Process monitoring + auto-restart
│   ├── ralph_wiggum.py           # Task persistence loop
│   ├── audit_logger.py           # JSONL audit logging
│   ├── test_quarantine.py        # Quarantine test suite (7/8 passing)
│   └── verify_gold_tier.py       # Gold tier verification
│
├── mcp-servers/                  # MCP servers (3 total)
│   ├── calendar-mcp/             # Calendar (8 tools, fully working)
│   │   ├── index.js
│   │   └── package.json
│   ├── odoo-mcp/                 # Odoo ERP (7 tools)
│   │   ├── index.js
│   │   └── package.json
│   └── facebook-mcp/             # Placeholder (posting via Python script)
│
├── .qwen/skills/                 # Agent Skills (14 total)
│   ├── browsing-with-playwright/
│   ├── gmail-watcher/
│   ├── whatsapp-watcher/
│   ├── email-mcp/
│   ├── linkedin-poster/
│   ├── twitter-poster/           # Twitter/X posting + summary
│   ├── facebook-poster/
│   ├── odoo-connector/
│   ├── calendar-mcp/
│   ├── ceo-briefing/
│   ├── plan-generator/
│   ├── hitl-approval/
│   ├── task-scheduler/
│   └── ralph-wiggum/
│
└── AI_Employee_Vault/            # Obsidian vault
    ├── Dashboard.md              # Real-time status
    ├── Company_Handbook.md       # Rules of engagement
    ├── Business_Goals.md         # Objectives and KPIs
    ├── Briefings/                # 7 generated CEO briefings
    ├── Calendar/                 # 2 events (ICS files)
    ├── Quarantine/               # Auto-isolated failed items
    ├── Done/                     # 22 completed tasks
    ├── Logs/                     # Full audit trail (75+ files)
    └── ...
```

---

## 🔧 Configuration

### Social Media Setup

| Platform | Setup Guide | Status |
|----------|-------------|--------|
| LinkedIn | [LinkedIn Setup Guide](./docs/guides/linkedin-setup.md) | ✅ Working (4 posts) |
| Facebook | [Facebook Setup Guide](./docs/guides/facebook-setup.md) | ✅ Working (1 post) |
| Twitter/X | Create app at [developer.twitter.com](https://developer.twitter.com/) | ⚠️ Needs credentials |
| Instagram | Via Facebook Graph API (same credentials) | ⚠️ Needs credentials |

### Odoo ERP Setup

```bash
# Start Docker containers
docker-compose up -d odoo db

# Access Odoo at http://localhost:8069
# Create database → Install Invoicing app
# Update .env with Odoo credentials

# Test connection
py scripts/odoo_connector.py --test-connection
```

See [Odoo Setup Guide](./docs/guides/odoo-setup.md) for full instructions.

### Twitter/X Setup

```bash
# 1. Create app at https://developer.twitter.com/en/portal/dashboard
# 2. Get Bearer Token and API credentials
# 3. Add to .env:
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret

# 4. Test connection
py scripts/twitter_poster.py --test-connection

# 5. Post a tweet
py scripts/twitter_poster.py --content "Hello from AI Employee!" --hashtags "AI,Automation"
```

---

## 🧪 Testing

### Verify Installation

```bash
# Silver Tier verification
py scripts/verify_silver_tier.py

# Gold Tier verification
py scripts/verify_gold_tier.py
```

### Test Individual Components

```bash
# Twitter/X (dry run)
py scripts/twitter_poster.py --dry-run --content "Test tweet" --hashtags "Test"

# CEO Briefing
py scripts/ceo_briefing_generator.py --days 7

# Calendar events
py scripts/calendar_tool.py --vault AI_Employee_Vault list --days 7

# A2A communication
py scripts/a2a/a2a_broker.py --port 8899  # Terminal 1
py scripts/a2a/test_a2a.py                # Terminal 2

# Quarantine system
py scripts/test_quarantine.py --vault AI_Employee_Vault
py scripts/quarantine_viewer.py --vault AI_Employee_Vault --status
```

---

## 🔐 Security

See [SECURITY.md](./SECURITY.md) for full security documentation.

**Key Principles:**
- ✅ Credentials stored in `.env` (never in vault or code)
- ✅ `.env` is gitignored — never committed
- ✅ Human-in-the-loop for all sensitive actions
- ✅ Rate limiting (max 10 emails/hr, 3 payments/hr, 5 social posts/hr)
- ✅ Full audit logging (JSONL, 90-day retention)
- ✅ Quarantine system isolates failed tasks
- ✅ Credential rotation every 60-90 days

---

## 📊 Monitoring & Maintenance

### Daily Checks (2 minutes)
```bash
# Check Dashboard
cat AI_Employee_Vault/Dashboard.md

# View recent logs
tail AI_Employee_Vault/Logs/audit_*.jsonl

# Check quarantine status
py scripts/quarantine_viewer.py --vault AI_Employee_Vault --status
```

### Weekly Tasks (15 minutes)
- Review CEO Briefing (auto-generated in `Briefings/`)
- Check `Pending_Approval/` folder
- Review audit logs for anomalies
- Check quarantine for items needing attention

### Monthly Tasks (1 hour)
- Rotate API credentials
- Review Company Handbook rules
- Backup vault and database
- Update Docker images
- Purge old quarantine items (>30 days)

---

## 📚 Documentation

### Getting Started
- [Quick Start](#-quick-start-5-minutes)
- [Architecture Overview](#️-architecture)
- [Bronze Tier Guide](./docs/guides/getting-started.md)
- [Silver Tier Guide](./docs/guides/silver-tier-setup.md)
- [Gold Tier Guide](./docs/guides/gold-tier-setup.md)

### Setup Guides
- [Email/Gmail Setup](./docs/guides/email-setup.md)
- [LinkedIn Setup](./docs/guides/linkedin-setup.md)
- [Facebook Setup](./docs/guides/facebook-setup.md)
- [Twitter/X Setup](./.qwen/skills/twitter-poster/SKILL.md)
- [Odoo Setup](./docs/guides/odoo-setup.md)

### Reference
- [Agent Skills](./docs/reference/agent-skills.md)
- [Calendar MCP](./docs/reference/calendar-mcp-complete.md)
- [A2A Communication](./docs/reference/a2a-system-complete.md)
- [Quarantine System](./docs/reference/quarantine-system-complete.md)
- [Ralph Wiggum Integration](./docs/reference/ralph-wiggum-integration.md)
- [CEO Briefing Generator](./docs/reference/ceo-briefing-complete.md)
- [Briefings Evidence](./docs/reference/briefings-evidence.md)
- [Troubleshooting](./docs/reference/troubleshooting.md)
- [Security Policy](./SECURITY.md)
- [Tier Declaration](./docs/TIER_DECLARATION.md)

---

## 🤝 Community & Support

### Weekly Research Meetings
- **When:** Wednesdays 10:00 PM PKT
- **Where:** [Zoom](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **Meeting ID:** 871 8870 7642 | **Passcode:** 744832
- **YouTube:** [Panaversity Channel](https://www.youtube.com/@panaversity)

---

## ⚖️ License

This project is part of the Personal AI Employee Hackathon. Share and learn with the community!

---

> **Remember:** You are responsible for your AI employee's actions. Regular oversight is essential.
>
> *"Your life and business on autopilot."*

---

*Built with ❤️ for the AI Employee Hackathon 2026 — Gold Tier Submission*
