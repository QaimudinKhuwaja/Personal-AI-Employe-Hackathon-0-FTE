# Development Tiers

**Choose Your Starting Point**

The Personal AI Employee is organized into four tiers, each building on the previous one. Start with Bronze and upgrade as needed.

---

## 🥉 Bronze Tier (Foundation)

**Time:** 8-12 hours | **Complexity:** Beginner

### What You Get

- ✅ Obsidian vault with Dashboard, Handbook, Goals
- ✅ File System Watcher (monitors drop folder)
- ✅ Qwen Code integration
- ✅ Basic folder structure

### Capabilities

```
Drop File → Watcher Detects → Qwen Processes → Task Complete
```

### Use Cases

- Document summarization
- File organization
- Manual task creation
- Basic automation

### Components

| Component | Script | Purpose |
|-----------|--------|---------|
| File System Watcher | `filesystem_watcher.py` | Monitor drop folders |
| Orchestrator | `orchestrator.py` | Trigger Qwen Code |
| Vault | `AI_Employee_Vault/` | Local storage |

### Setup Checklist

- [ ] Python 3.13+ installed
- [ ] Qwen Code installed
- [ ] Obsidian vault opened
- [ ] Company_Handbook.md reviewed
- [ ] File System Watcher running
- [ ] Orchestrator running

[→ Bronze Tier Guide](./guides/getting-started.md)

---

## 🥈 Silver Tier (Functional Assistant)

**Time:** 20-30 hours | **Complexity:** Intermediate

### What You Get (All Bronze +)

- ✅ Gmail Watcher (auto-detect emails)
- ✅ WhatsApp Watcher (urgent message alerts)
- ✅ LinkedIn Poster (auto-post business updates)
- ✅ Email sending with approval workflow
- ✅ Human-in-the-loop (HITL) approvals
- ✅ Basic scheduling

### Capabilities

```
Email Arrives → Gmail Detects → Qwen Drafts → Human Approves → Email Sent
WhatsApp Message → Watcher Detects → Qwen Alerts → Human Responds
Business Update → Qwen Creates Post → Human Approves → LinkedIn Posted
```

### Use Cases

- Email triage and responses
- Urgent WhatsApp monitoring
- Social media marketing
- Customer communication
- Task scheduling

### Components

| Component | Script | Purpose |
|-----------|--------|---------|
| Gmail Watcher | `gmail_watcher.py` | Monitor Gmail API |
| WhatsApp Watcher | `whatsapp_watcher.py` | Monitor WhatsApp Web |
| LinkedIn Poster | `linkedin_api_poster.py` | Post to LinkedIn |
| Email Approval Watcher | `email_approval_watcher.py` | Send approved emails |

### Additional Requirements

- Google Cloud account (Gmail API)
- LinkedIn Developer account
- Gmail API credentials
- LinkedIn access token

### Setup Checklist

- [ ] All Bronze Tier items
- [ ] Gmail API credentials created
- [ ] Gmail authenticated
- [ ] Gmail Watcher running
- [ ] WhatsApp Watcher running
- [ ] LinkedIn Developer app created
- [ ] LinkedIn access token generated
- [ ] LinkedIn test post successful
- [ ] Email Approval Watcher running

[→ Silver Tier Guide](./guides/silver-tier-setup.md)

---

## 🥇 Gold Tier (Autonomous Employee)

**Time:** 40+ hours | **Complexity:** Advanced

### What You Get (All Silver +)

- ✅ Odoo ERP integration (accounting, invoices)
- ✅ Facebook & Instagram auto-posting
- ✅ Weekly CEO Briefing generator
- ✅ Error recovery & graceful degradation
- ✅ Comprehensive audit logging
- ✅ Ralph Wiggum Loop (task persistence)
- ✅ Health monitoring

### Capabilities

```
Invoice Request → Qwen Creates in Odoo → Syncs to Vault → Logged
Monday 7 AM → CEO Briefing Generated → Email to CEO
Facebook Error → Retry Handler → Circuit Breaker → Quarantine
Task Detected → Ralph Wiggum Loop → Multi-Step Completion
```

### Use Cases

- Full business accounting
- Multi-platform social media
- Executive reporting
- Customer management
- Payment tracking
- Resilient operations

### Components

| Component | Script | Purpose |
|-----------|--------|---------|
| Odoo Connector | `odoo_connector.py` | ERP integration |
| Facebook Poster | `facebook_graph_poster.py` | Facebook/Instagram |
| CEO Briefing Generator | `ceo_briefing_generator.py` | Weekly reports |
| Audit Logger | `audit_logger.py` | Compliance logging |
| Retry Handler | `retry_handler.py` | Error recovery |
| Health Checker | `health_checker.py` | Process monitoring |
| Ralph Wiggum | `ralph_wiggum.py` | Task persistence |

### Additional Requirements

- Docker Desktop
- Facebook Developer account
- Odoo ERP (self-hosted)

### Setup Checklist

- [ ] All Silver Tier items
- [ ] Docker Desktop installed
- [ ] Odoo containers running
- [ ] Odoo database created
- [ ] Odoo connection tested
- [ ] Facebook app created
- [ ] Facebook connection tested
- [ ] CEO Briefing tested
- [ ] Error recovery tested
- [ ] Audit logging tested

[→ Gold Tier Guide](./guides/gold-tier-setup.md)

---

## ⭐ Platinum Tier (Production)

**Time:** 60+ hours | **Complexity:** Expert

### What You Get (All Gold +)

- ☁️ Cloud deployment (24/7 always-on)
- 🔄 Vault synchronization (Git/Syncthing)
- 🔐 Work-zone specialization (Cloud vs Local)
- 🌐 Odoo on cloud with HTTPS & backups
- 📨 A2A messaging (direct agent communication)

### Capabilities

```
Cloud: Email Triage → Draft Replies → Sync to Local
Local: Review Drafts → Approve → Send via MCP
Agents: Communicate via Vault Files or A2A Messages
```

### Use Cases

- Production deployment
- Team collaboration
- Multi-domain operations
- Enterprise-scale automation

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Cloud VM      │         │   Local Machine │
│  (Always-On)    │◄───────►│   (Your Laptop) │
│                 │  Git/Sync│                 │
│ Email Watcher   │         │ Approval Review │
│ Draft Replies   │         │ Final Send      │
│ Social Drafts   │         │ Payments        │
└─────────────────┘         └─────────────────┘
```

### Components

| Component | Purpose |
|-----------|---------|
| Cloud VM | Oracle/AWS free tier |
| Vault Sync | Git or Syncthing |
| Domain Ownership | Cloud vs Local rules |
| HTTPS Setup | SSL certificates |
| A2A Protocol | Agent-to-agent messaging |

### Setup Checklist

- [ ] All Gold Tier items
- [ ] Cloud VM provisioned
- [ ] Watchers deployed to cloud
- [ ] Vault sync configured
- [ ] Domain rules defined
- [ ] HTTPS configured
- [ ] A2A messaging tested

[→ Platinum Tier Guide](./docs/platinum-tier.md) *(Coming Soon)*

---

## 📊 Tier Comparison

| Feature | Bronze | Silver | Gold | Platinum |
|---------|--------|--------|------|----------|
| **File Monitoring** | ✅ | ✅ | ✅ | ✅ |
| **Gmail Integration** | ❌ | ✅ | ✅ | ✅ |
| **WhatsApp Integration** | ❌ | ✅ | ✅ | ✅ |
| **LinkedIn Posting** | ❌ | ✅ | ✅ | ✅ |
| **Email Sending** | ❌ | ✅ | ✅ | ✅ |
| **Facebook/Instagram** | ❌ | ❌ | ✅ | ✅ |
| **Odoo ERP** | ❌ | ❌ | ✅ | ✅ |
| **CEO Briefing** | ❌ | ❌ | ✅ | ✅ |
| **Error Recovery** | ❌ | ❌ | ✅ | ✅ |
| **Audit Logging** | ❌ | ❌ | ✅ | ✅ |
| **Ralph Wiggum** | ❌ | ❌ | ✅ | ✅ |
| **Cloud Deployment** | ❌ | ❌ | ❌ | ✅ |
| **Vault Sync** | ❌ | ❌ | ❌ | ✅ |
| **A2A Messaging** | ❌ | ❌ | ❌ | ☐ |

---

## 🎯 Which Tier Should You Start With?

### Choose Bronze If:
- You're new to the project
- You want to understand the basics
- You primarily need document processing
- You have limited time (8-12 hours)

### Choose Silver If:
- You're a solopreneur or consultant
- You need email automation
- You want social media posting
- You have 20-30 hours to invest

### Choose Gold If:
- You run a small business
- You need full accounting integration
- You want multi-platform social media
- You have 40+ hours to invest

### Choose Platinum If:
- You need 24/7 operation
- You're deploying for production
- You have team members
- You have 60+ hours to invest

---

## 📈 Upgrade Path

```
Bronze (Foundation)
  ↓
  Add: Gmail, WhatsApp, LinkedIn
  ↓
Silver (Functional)
  ↓
  Add: Odoo, Facebook, Briefings
  ↓
Gold (Autonomous)
  ↓
  Add: Cloud, Sync, A2A
  ↓
Platinum (Production)
```

**Recommendation:** Master each tier before upgrading to the next.

---

## 📚 Resources

- [Getting Started](./guides/getting-started.md) - Bronze Tier
- [Silver Tier Setup](./guides/silver-tier-setup.md)
- [Gold Tier Setup](./guides/gold-tier-setup.md)
- [Architecture Overview](./architecture/overview.md)

---

*Development Tiers - Personal AI Employee*
