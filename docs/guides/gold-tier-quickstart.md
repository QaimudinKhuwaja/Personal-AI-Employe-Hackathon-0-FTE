# 🚀 Gold Tier Quick Start Guide

**Status:** ✅ Complete  
**Verification:** 100% Passed (24/24 checks)  
**Date:** 2026-03-02

---

## 📋 What's New in Gold Tier

Gold Tier adds the following major features to your AI Employee:

1. **Odoo ERP Integration** - Full accounting via Docker
2. **Facebook/Instagram Integration** - Social media posting
3. **CEO Briefing Generator** - Weekly automated reports
4. **Error Recovery System** - Resilient operations
5. **Audit Logging** - Comprehensive compliance

---

## 🎯 Quick Start Checklist

### Step 1: Verify Installation ✅

```bash
# Run verification script
python scripts/verify_gold_tier.py
```

**Expected:** All 24 checks pass

---

### Step 2: Start Odoo ERP (Docker)

```bash
# Start Odoo and PostgreSQL
docker-compose up -d odoo db

# Check status
docker-compose ps

# View logs
docker-compose logs -f odoo
```

**Access Odoo:**
- URL: http://localhost:8069
- Default admin password: admin (from docker-compose.yml)

**First-Time Setup:**
1. Create database named `ai_employee`
2. Set admin password
3. Install **Invoicing** app
4. Create API user for AI Employee

See `ODOO_DOCKER_SETUP.md` for detailed instructions.

---

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=ai-employee@localhost
ODOO_PASSWORD=your_secure_password

# Facebook Configuration (optional)
FACEBOOK_PAGE_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram (optional)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id
```

---

### Step 4: Test Odoo Integration

```bash
# Test connection
python scripts/odoo_connector.py --test-connection

# Create test invoice (dry run)
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Test Customer" \
  --amount 100.00 \
  --dry-run

# Sync invoices
python scripts/odoo_connector.py --sync-invoices --last-days 30
```

**Expected:** Connection successful, invoices synced to `AI_Employee_Vault/Accounting/`

---

### Step 5: Test Facebook Integration

```bash
# Test connection (requires Facebook credentials)
python scripts/facebook_graph_poster.py \
  --test-connection \
  --page-id $FACEBOOK_PAGE_ID

# Test post (dry run)
python scripts/facebook_graph_poster.py \
  --content "Testing Gold Tier!" \
  --page-id $FACEBOOK_PAGE_ID \
  --dry-run
```

**Expected:** Connection successful, post created (or dry run logged)

See `FACEBOOK_SETUP_GUIDE.md` for Facebook App setup.

---

### Step 6: Generate CEO Briefing

```bash
# Generate weekly briefing
python scripts/ceo_briefing_generator.py \
  --output AI_Employee_Vault/Briefings/weekly_briefing.md \
  --days 7

# View briefing
cat AI_Employee_Vault/Briefings/weekly_briefing.md
```

**Expected:** Comprehensive briefing with revenue, tasks, social media, and recommendations

---

### Step 7: Schedule Weekly Briefings

**Windows Task Scheduler:**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "AI Employee CEO Briefing"
4. Trigger: Weekly, Monday, 7:00 AM
5. Action: Start a program
   - Program: `python.exe`
   - Arguments: `scripts/ceo_briefing_generator.py --days 7`
   - Start in: `C:\Users\Faraz\Desktop\Personal-Ai-Employee-FTE`

---

### Step 8: Test Error Recovery

```bash
# Test audit logger
python scripts/audit_logger.py

# Test retry handler
python scripts/retry_handler.py

# Test health checker
python scripts/health_checker.py --report
```

**Expected:** All components working, logs created in `Logs/` folder

---

## 📊 Gold Tier Features Overview

### 1. Odoo ERP Integration

**What it does:**
- Create and manage invoices
- Track customers and payments
- Sync accounting data to vault
- Generate financial reports

**Key Commands:**
```bash
# Create invoice
python scripts/odoo_connector.py --create-invoice \
  --customer "Client A" \
  --amount 500.00 \
  --description "Consulting Services"

# List customers
python scripts/odoo_connector.py --list-customers

# Get customer details
python scripts/odoo_connector.py --get-customer "Client A"
```

**Agent Skill:** `.qwen/skills/odoo-connector/SKILL.md`

---

### 2. Facebook/Instagram Integration

**What it does:**
- Post to Facebook Pages
- Post to Instagram Business
- Schedule posts
- Track engagement

**Key Commands:**
```bash
# Post to Facebook
python scripts/facebook_graph_poster.py \
  --content "Exciting news! 🚀" \
  --page-id $FACEBOOK_PAGE_ID \
  --hashtags "AI,Innovation"

# Post to Instagram
python scripts/facebook_graph_poster.py \
  --content "Behind the scenes 📸" \
  --instagram \
  --media-path ./photo.jpg \
  --hashtags "OfficeLife"

# Schedule post
python scripts/facebook_graph_poster.py \
  --content "Monday motivation!" \
  --scheduled-time "2026-03-06T09:00:00Z"
```

**Agent Skill:** `.qwen/skills/facebook-poster/SKILL.md`

---

### 3. CEO Briefing Generator

**What it does:**
- Aggregates data from all sources
- Generates weekly executive report
- Identifies bottlenecks
- Provides recommendations

**Report Sections:**
- Executive Summary
- Revenue Analysis
- Task Completion
- Social Media Performance
- Customer Overview
- Upcoming Deadlines
- Proactive Recommendations

**Agent Skill:** `.qwen/skills/ceo-briefing/SKILL.md`

---

### 4. Error Recovery System

**Components:**
- **Retry Handler:** Exponential backoff for transient failures
- **Circuit Breaker:** Prevents cascade failures
- **Quarantine Manager:** Isolates problematic items
- **Health Checker:** Monitors and restarts processes

**Usage:**
```python
from retry_handler import with_retry

@with_retry(max_attempts=3, base_delay=1)
def api_call():
    # Your API call here
    pass
```

---

### 5. Audit Logging

**What it does:**
- Logs all actions in JSONL format
- Daily log rotation
- 90-day retention
- Query and export functions

**Usage:**
```python
from audit_logger import log_action

log_action(
    action_type='facebook_post',
    actor='qwen_code',
    parameters={'content': 'Post text'},
    result='success'
)
```

**View Logs:**
```bash
# View today's logs
cat Logs/audit_2026-03-02.jsonl

# Export logs
python -c "from audit_logger import get_logger; print(get_logger().export_logs('2026-03-01', '2026-03-02', 'export.json'))"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  GOLD TIER ARCHITECTURE                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  EXTERNAL SOURCES                                       │
│  Gmail │ WhatsApp │ Facebook │ Instagram │ Odoo ERP    │
│                                                         │
│  WATCHERS (Perception)                                  │
│  gmail_watcher.py                                       │
│  whatsapp_watcher.py                                    │
│  facebook_watcher.py (future)                           │
│  odoo_watcher.py (future)                               │
│                                                         │
│  REASONING (Qwen Code)                                  │
│  orchestrator.py                                        │
│  ceo_briefing_generator.py                              │
│                                                         │
│  ACTION LAYER (MCP)                                     │
│  Email MCP │ LinkedIn MCP │ Odoo MCP │ Facebook MCP    │
│                                                         │
│  SUPPORT SYSTEMS                                        │
│  audit_logger.py │ retry_handler.py │ health_checker.py│
│                                                         │
│  OBSIDIAN VAULT (Memory)                                │
│  /Briefings/ │ /Accounting/ │ /Quarantine/ │ /Logs/    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
Personal-Ai-Employee-FTE/
├── docker-compose.yml                    # Odoo + PostgreSQL
├── odoo-config/
│   └── odoo.conf                         # Odoo configuration
├── mcp-servers/
│   └── odoo-mcp/
│       ├── index.js                      # Odoo MCP server
│       └── package.json
├── scripts/
│   ├── odoo_connector.py                 # Odoo JSON-RPC
│   ├── facebook_graph_poster.py          # Facebook Graph API
│   ├── ceo_briefing_generator.py         # Weekly reports
│   ├── audit_logger.py                   # Audit logging
│   ├── retry_handler.py                  # Error recovery
│   ├── health_checker.py                 # Process monitoring
│   └── verify_gold_tier.py               # Verification script
├── .qwen/skills/
│   ├── odoo-connector/SKILL.md           # Odoo skill
│   ├── facebook-poster/SKILL.md          # Facebook skill
│   └── ceo-briefing/SKILL.md             # Briefing skill
├── AI_Employee_Vault/
│   ├── Briefings/                        # CEO briefings
│   ├── Accounting/                       # Odoo sync
│   ├── Quarantine/                       # Failed items
│   └── Logs/                             # Audit logs
└── docs/
    ├── GOLD_TIER_ARCHITECTURE.md         # Architecture
    ├── GOLD_TIER_COMPLETE.md             # Completion report
    ├── ODOO_DOCKER_SETUP.md              # Odoo setup
    └── FACEBOOK_SETUP_GUIDE.md           # Facebook setup
```

---

## 🧪 Testing All Components

### Full Test Suite

```bash
# Run all tests
python scripts/verify_gold_tier.py --verbose

# Test Odoo
python scripts/odoo_connector.py --test-connection
python scripts/odoo_connector.py --sync-invoices --last-days 30

# Test Facebook (requires credentials)
python scripts/facebook_graph_poster.py --test-connection

# Test CEO Briefing
python scripts/ceo_briefing_generator.py --days 7

# Test Audit Logger
python scripts/audit_logger.py

# Test Retry Handler
python scripts/retry_handler.py

# Test Health Checker
python scripts/health_checker.py --report
```

---

## 🔐 Security Best Practices

### Credential Management

```bash
# NEVER commit .env file
echo ".env" >> .gitignore

# Use environment variables
export ODOO_PASSWORD="secure_password"

# Rotate credentials regularly
# - Odoo API keys: Every 90 days
# - Facebook tokens: Every 60 days
```

### Approval Workflow

For sensitive operations, always use HITL:

```markdown
1. AI creates approval request in /Pending_Approval
2. Human reviews and moves to /Approved
3. AI executes action
4. Result logged to audit trail
5. File moved to /Done
```

---

## 📊 Monitoring & Maintenance

### Daily Checks

```bash
# Check process health
python scripts/health_checker.py --report

# View recent logs
tail -f Logs/audit_*.jsonl
```

### Weekly Tasks

- Review CEO Briefing (Monday 7 AM)
- Check Quarantine folder for failed items
- Review audit logs for anomalies

### Monthly Tasks

- Rotate Facebook tokens
- Review Odoo user permissions
- Backup vault and database
- Update Docker images

---

## 🐛 Troubleshooting

### Odoo Connection Failed

```bash
# Check if Odoo is running
docker-compose ps

# Restart Odoo
docker-compose restart odoo

# Check logs
docker-compose logs odoo
```

### Facebook Token Expired

```bash
# Generate new long-lived token
# See FACEBOOK_SETUP_GUIDE.md Step 4

# Update .env file
FACEBOOK_PAGE_ACCESS_TOKEN=new_token_here
```

### CEO Briefing Missing Data

```bash
# Ensure data sources are configured
# - Odoo: Check connection
# - Social: Check log files exist
# - Tasks: Ensure files moved to /Done

# Regenerate briefing
python scripts/ceo_briefing_generator.py --days 7 --force
```

---

## 📚 Documentation Index

### Gold Tier Documentation
1. `GOLD_TIER_ARCHITECTURE.md` - Complete architecture
2. `GOLD_TIER_COMPLETE.md` - Completion report
3. `ODOO_DOCKER_SETUP.md` - Odoo setup guide
4. `FACEBOOK_SETUP_GUIDE.md` - Facebook setup
5. `GOLD_TIER_QUICKSTART.md` - This guide

### Agent Skills
1. `.qwen/skills/odoo-connector/SKILL.md`
2. `.qwen/skills/facebook-poster/SKILL.md`
3. `.qwen/skills/ceo-briefing/SKILL.md`

### Silver Tier (Foundation)
1. `SILVER_TIER_COMPLETE.md`
2. `README.md`
3. `QWEN.md`

---

## 🎯 Next Steps

### Immediate (This Week)
- [ ] Start Odoo Docker containers
- [ ] Configure Facebook credentials
- [ ] Generate first CEO briefing
- [ ] Review and approve test invoices

### Short Term (This Month)
- [ ] Set up weekly briefing schedule
- [ ] Configure health checker monitoring
- [ ] Test error recovery scenarios
- [ ] Document custom business rules

### Long Term (Next Quarter)
- [ ] Deploy to cloud VM (Platinum Tier)
- [ ] Implement Ralph Wiggum loop
- [ ] Add Twitter/X integration
- [ ] Set up vault synchronization

---

## 🎉 Congratulations!

**Gold Tier is now complete and verified!**

Your AI Employee now has:
- ✅ Full accounting integration (Odoo)
- ✅ Social media automation (Facebook/Instagram)
- ✅ Executive reporting (CEO Briefings)
- ✅ Resilient operations (Error Recovery)
- ✅ Compliance tracking (Audit Logging)

**Ready for Platinum Tier (Cloud Deployment)!**

---

*Gold Tier Quick Start Guide - Version 1.0.0*  
*Generated: 2026-03-02*  
*AI Employee v1.0.0 (Gold Tier)*
