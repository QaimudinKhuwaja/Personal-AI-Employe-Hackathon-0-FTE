# Gold Tier Setup Guide

**Full Business Automation with Accounting & Social Media**

This guide extends Silver Tier with Odoo ERP integration, Facebook/Instagram posting, CEO briefings, error recovery, and audit logging.

**Estimated Time:** 4-6 hours

---

## 🎯 What Gold Tier Adds

| Feature | Description | Status |
|---------|-------------|--------|
| **Odoo ERP** | Accounting, invoices, customers, payments | ✅ |
| **Facebook Poster** | Auto-post to Facebook Pages | ✅ |
| **Instagram Poster** | Auto-post to Instagram Business | ✅ |
| **CEO Briefing** | Weekly automated executive reports | ✅ |
| **Error Recovery** | Retry logic, circuit breakers | ✅ |
| **Audit Logging** | Comprehensive compliance logs | ✅ |
| **Ralph Wiggum** | Multi-step task persistence | ✅ |

---

## 📋 Prerequisites

### Complete Silver Tier First
- ✅ Gmail Watcher working
- ✅ WhatsApp Watcher working
- ✅ LinkedIn Poster working
- ✅ Email sending working

### Additional Requirements

| Software | Purpose | Link |
|----------|---------|------|
| **Docker Desktop** | Run Odoo ERP | [Download](https://www.docker.com/products/docker-desktop/) |
| **Facebook Developer** | Facebook/Instagram API | [Console](https://developers.facebook.com/) |
| **Business Manager** | Facebook Business (recommended) | [Business](https://business.facebook.com) |

---

## 🚀 Part 1: Odoo ERP Integration

### Step 1: Configure Environment Variables

Create or edit `.env` in project root:

```bash
# Odoo Configuration
ODOO_ADMIN_PASSWORD=your_secure_admin_password
ODOO_DB_PASSWORD=your_secure_db_password
```

**⚠️ Security Warning:** Change default passwords before production use!

### Step 2: Start Odoo with Docker

```bash
# Navigate to project directory
cd C:\Users\Faraz\Desktop\Personal-Ai-Employe-Hackathon-0-FTE

# Start Odoo and PostgreSQL
docker-compose up -d odoo db

# Check status
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS         PORTS
ai_employee_odoo        Up (healthy)   0.0.0.0:8069->8069/tcp
ai_employee_odoo_db     Up (healthy)   5432/tcp
```

### Step 3: Access Odoo

1. **Open browser:** http://localhost:8069
2. **Create database:**
   - Master Password: (from `.env`)
   - Database Name: `ai_employee`
   - Email: your email
   - Password: your admin password
   - Language: English (US)
   - Country: Your country
   - Demo Data: ✅ Check for testing
3. **Click "Create Database"**

### Step 4: Install Accounting Modules

1. **Go to Apps** (main menu)
2. **Search and install:**
   - ✅ **Invoicing** (free accounting)
   - ✅ **Contacts** (customer management)
   - ✅ **Products** (product catalog)

### Step 5: Create API User

1. **Activate Developer Mode:**
   - Go to **Settings**
   - Scroll to bottom
   - Click "Activate the developer mode"

2. **Create API User:**
   - Go to **Settings → Users & Companies → Users**
   - Click "Create"
   - Fill in:
     - **Name:** AI Employee
     - **Email:** ai-employee@localhost
     - **Password:** generate secure password
   - Set **Access Rights:**
     - **Invoicing / User**
     - **Contacts / User**
   - Click "Save"

3. **Generate API Key:**
   - Click your profile (top right)
   - Click "Preferences"
   - Click "Generate API Key"
   - **Save this key**

### Step 6: Configure Odoo in .env

Add to your `.env` file:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=ai-employee@localhost
ODOO_PASSWORD=your_api_key_or_password
```

### Step 7: Test Odoo Connection

```bash
# Test connection
python scripts/odoo_connector.py --test-connection
```

**Expected output:**
```
✅ Connected to Odoo 19.0
✅ Database: ai_employee
✅ User: AI Employee
✅ Available models: account.move, res.partner, product.template, ...
```

### Step 8: Create Test Invoice

```bash
# Create test invoice (dry run)
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Test Customer" \
  --amount 100.00 \
  --description "Consulting Services" \
  --dry-run

# Create actual invoice
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Test Customer" \
  --amount 100.00 \
  --description "Consulting Services"
```

### Step 9: Sync Invoices to Vault

```bash
# Sync all invoices
python scripts/odoo_connector.py --sync-invoices

# Sync last 30 days
python scripts/odoo_connector.py --sync-invoices --last-days 30
```

**Check:** `AI_Employee_Vault/Accounting/` folder for synced invoices

---

## 🚀 Part 2: Facebook Integration

### Step 1: Create Facebook App

1. **Go to [Facebook Developers](https://developers.facebook.com/)**
2. **Click "My Apps" → "Create App"**
3. **Select use case:** "Other" → "Next"
4. **Select app type:** "Business" → "Next"
5. **Fill in details:**
   - App Name: `AI Employee Social Media`
   - App Contact Email: your-email@example.com
   - Click "Create App"

### Step 2: Add Graph API Product

1. **In your app dashboard:**
2. **Scroll to "Add Products to Your App"**
3. **Click "+" next to "Graph API"**

### Step 3: Get Page Access Token

#### For Testing (Short-lived Token):

1. **Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)**
2. **Select your app from dropdown**
3. **Click "Get Token" → "Get Page Access Token"**
4. **Select your Page**
5. **Choose permissions:**
   - ✅ `pages_manage_posts`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
   - ✅ `instagram_basic` (for Instagram)
   - ✅ `instagram_content_publish` (for Instagram)
6. **Click "Generate Token"**
7. **Copy the Access Token**

#### For Production (Long-lived Token):

```bash
# Use the token exchange script
python scripts/facebook_exchange_token.py \
  --app-id YOUR_APP_ID \
  --app-secret YOUR_APP_SECRET \
  --short-token YOUR_SHORT_TOKEN
```

### Step 4: Get Your Page ID

1. **Go to your Facebook Page**
2. **Click "About"**
3. **Find "Facebook Page ID"**

Or use Graph API Explorer:
```
GET /me/accounts
```

### Step 5: Configure .env

Add to your `.env` file:

```bash
# Facebook Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your_long_lived_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram Configuration (optional)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id
```

### Step 6: Test Facebook Connection

```bash
# Test connection
python scripts/facebook_graph_poster.py --test-connection --page-id $FACEBOOK_PAGE_ID
```

**Expected output:**
```
✅ Connected to Facebook Page
   Name: Your Page Name
   Username: @yourpage
   Category: Business
```

### Step 7: Create Test Post

```bash
# Test post (dry run)
python scripts/facebook_graph_poster.py \
  --content "Testing Gold Tier! 🚀" \
  --page-id $FACEBOOK_PAGE_ID \
  --dry-run

# Actual post
python scripts/facebook_graph_poster.py \
  --content "Testing Gold Tier! 🚀" \
  --page-id $FACEBOOK_PAGE_ID \
  --hashtags "AI,Automation,GoldTier"
```

**Expected output:**
```
✅ Facebook post published!
   Post ID: 123456789_987654321
   Permalink: https://www.facebook.com/123456789/posts/987654321
```

---

## 🚀 Part 3: Instagram Integration

### Step 1: Connect Instagram to Facebook Page

1. **Go to your Facebook Page**
2. **Click "Settings" → "Instagram"**
3. **Click "Connect Account"**
4. **Log in to Instagram**
5. **Select Instagram Business account**

### Step 2: Get Instagram Business Account ID

1. **Use Graph API Explorer:**
   ```
   GET /{page-id}?fields=instagram_business_account
   ```

2. **Copy the `instagram_business_account.id`**

3. **Add to `.env`:**
   ```bash
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_business_account_id
   ```

### Step 3: Test Instagram Post

```bash
# Post to Instagram (requires image)
python scripts/facebook_graph_poster.py \
  --content "Instagram post from AI Employee! 📸" \
  --instagram \
  --media-path ./test_image.jpg \
  --hashtags "AI,Instagram,Automation"
```

**Expected output:**
```
✅ Instagram post published!
   Post ID: 12345678901234567
   Permalink: https://www.instagram.com/p/ABC123DEF45/
```

---

## 🚀 Part 4: CEO Briefing Generator

### Step 1: Test Briefing Generation

```bash
# Generate weekly briefing
python scripts/ceo_briefing_generator.py \
  --output AI_Employee_Vault/Briefings/weekly_briefing.md \
  --days 7

# View briefing
cat AI_Employee_Vault/Briefings/weekly_briefing.md
```

**Expected output:**
```markdown
---
generated: 2026-03-07T07:00:00Z
period: 2026-03-01 to 2026-03-07
---

# Monday Morning CEO Briefing

## Executive Summary
Strong week with revenue ahead of target.

## Revenue
- **This Week**: $2,450
- **MTD**: $4,500 (45% of $10,000 target)
- **Trend**: On track

## Completed Tasks
- [x] Client A invoice sent and paid
- [x] Project Alpha milestone 2 delivered

## Social Media Performance
- Facebook: 3 posts, 150 engagements
- LinkedIn: 3 posts, 200 impressions
- Instagram: 2 posts, 100 likes
```

### Step 2: Schedule Weekly Briefings

**Windows Task Scheduler:**

1. **Open Task Scheduler**
2. **Create Basic Task**
3. **Name:** "AI Employee CEO Briefing"
4. **Trigger:** Weekly, Monday, 7:00 AM
5. **Action:** Start a program
   - **Program:** `python.exe`
   - **Arguments:** `scripts/ceo_briefing_generator.py --days 7`
   - **Start in:** `C:\Users\Faraz\Desktop\Personal-Ai-Employee-FTE`

---

## 🚀 Part 5: Error Recovery & Audit Logging

### Step 1: Test Retry Handler

```bash
# Test retry handler
python scripts/retry_handler.py
```

**Expected output:**
```
✅ Retry Handler Test
   Testing transient failure...
   Attempt 1: Failed
   Attempt 2: Failed
   Attempt 3: Success!
```

### Step 2: Test Circuit Breaker

```bash
# Test circuit breaker
python scripts/retry_handler.py --test-circuit-breaker
```

### Step 3: Test Audit Logger

```bash
# Test audit logging
python scripts/audit_logger.py

# View logs
cat AI_Employee_Vault/Logs/audit_*.jsonl
```

**Expected output:**
```json
{
  "timestamp": "2026-03-07T12:00:00Z",
  "log_id": "uuid",
  "action_type": "facebook_post",
  "actor": "qwen_code",
  "parameters": {"content": "Test post"},
  "result": "success",
  "duration_ms": 1234
}
```

### Step 4: Test Health Checker

```bash
# Test health monitoring
python scripts/health_checker.py --report
```

**Expected output:**
```
✅ Health Check Report
   Gmail Watcher: Running
   WhatsApp Watcher: Running
   Orchestrator: Running
   Odoo: Connected
   Facebook: Connected
   LinkedIn: Connected
```

---

## 🚀 Part 6: Ralph Wiggum Loop

### Step 1: Test Ralph Wiggum

```bash
# Test task persistence
python scripts/ralph_wiggum.py "Process all files in Needs_Action"
```

**Expected output:**
```
============================================================
RALPH WIGGUM LOOP - Task Persistence Mode
============================================================
Task: Process all files in Needs_Action
Max iterations: 10
Completion signal: TASK_COMPLETE
============================================================

[Iteration 1/10]
[Running Qwen Code...]

[Iteration 2/10]
[Running Qwen Code...]

[OK] Task complete: All items processed

[SUCCESS] Task completed successfully!
```

---

## 📊 Complete Gold Tier Setup

### Running All Components

You need **multiple terminals** running simultaneously:

**Terminal 1: Gmail Watcher**
```bash
python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Terminal 2: WhatsApp Watcher**
```bash
python scripts/whatsapp_watcher.py AI_Employee_Vault
```

**Terminal 3: File System Watcher**
```bash
python scripts/filesystem_watcher.py AI_Employee_Vault
```

**Terminal 4: Orchestrator**
```bash
python scripts/orchestrator.py AI_Employee_Vault
```

**Terminal 5: Email Approval Watcher**
```bash
python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Terminal 6: Health Checker** (optional, monitoring)
```bash
python scripts/health_checker.py --interval 300
```

### Docker Services

```bash
# Check Odoo status
docker-compose ps

# View Odoo logs
docker-compose logs -f odoo

# Restart if needed
docker-compose restart odoo
```

---

## 🧪 Test the Complete Flow

### Test Scenario: Invoice Creation

1. **Create invoice request** in `Needs_Action/`:

```markdown
---
type: invoice_request
customer: Test Customer
amount: 500.00
description: Consulting Services - January 2026
due_date: 2026-03-30
priority: normal
---

## Invoice Details
- Customer: Test Customer
- Amount: $500.00
- Description: Consulting Services - January 2026
- Due: March 30, 2026

## To Process

Move this file to /Approved to create invoice in Odoo.
```

2. **Move to Approved/** (HITL approval)

3. **Orchestrator triggers** Odoo Connector

4. **Invoice created** in Odoo

5. **Sync to vault:** `AI_Employee_Vault/Accounting/`

### Test Scenario: Weekly Briefing

1. **Wait for Monday 7 AM** (scheduled time)

2. **Or check manually:**
   ```bash
   python scripts/ceo_briefing_generator.py --days 7
   ```

3. **Review briefing** in `AI_Employee_Vault/Briefings/`

4. **Check sections:**
   - Revenue from Odoo
   - Tasks from Done/
   - Social media from Logs/
   - Recommendations from AI

---

## 🔧 Configuration

### Company Handbook Updates

Add Gold Tier rules to `AI_Employee_Vault/Company_Handbook.md`:

```markdown
## Gold Tier Rules

### Facebook Posting
- Auto-approve: Scheduled posts, business updates
- Require approval: First-time posts, promotional content, responses

### Odoo Accounting
- Auto-approve: Invoices < $100 to existing customers
- Require approval: New customers, amounts > $500, all payments

### CEO Briefing
- Generate every Monday at 7 AM
- Include revenue, tasks, social media, recommendations
- Email to CEO automatically
```

### Business Goals Updates

Add Gold Tier metrics to `AI_Employee_Vault/Business_Goals.md`:

```markdown
## Social Media Targets
- Facebook posts/week: 3-5
- LinkedIn posts/week: 3-5
- Instagram posts/week: 3-7

## Accounting Targets
- Monthly Revenue: $10,000
- Invoice collection rate: > 90%
- Monthly expenses: < $5,000
```

---

## 🐛 Troubleshooting

### Odoo Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check Docker: `docker-compose ps` |
| "Database not found" | Create database in Odoo setup |
| "Authentication failed" | Verify API user credentials |
| Odoo won't start | Check logs: `docker-compose logs odoo` |

### Facebook Issues

| Issue | Solution |
|-------|----------|
| "Invalid access token" | Token expired - get new one from Graph API Explorer |
| "Missing permissions" | Re-generate token with all required scopes |
| "Page not found" | Verify Page ID is correct |
| Post not appearing | Check Page role permissions |

### Instagram Issues

| Issue | Solution |
|-------|----------|
| "Instagram account not connected" | Connect Instagram to Facebook Page |
| "Business account ID not set" | Get ID from Graph API, add to .env |
| "Photo upload failed" | Check format (JPG/PNG) and size (< 20MB) |

### CEO Briefing Issues

| Issue | Solution |
|-------|----------|
| "No data in briefing" | Ensure data sources are configured |
| "Odoo data missing" | Check Odoo connection |
| "Social media missing" | Verify log files exist |

### Ralph Wiggum Issues

| Issue | Solution |
|-------|----------|
| "Loop runs max iterations" | Increase max_iterations |
| "Loop exits immediately" | Use more specific completion promise |
| "Qwen Code errors" | Check Qwen installation |

---

## 📊 Gold Tier Checklist

- [ ] Docker Desktop installed and running
- [ ] Odoo containers started (`docker-compose ps`)
- [ ] Odoo database created
- [ ] Accounting modules installed
- [ ] API user created in Odoo
- [ ] `.env` configured with Odoo credentials
- [ ] Odoo connection tested
- [ ] Test invoice created
- [ ] Facebook app created
- [ ] Page access token obtained
- [ ] Facebook connection tested
- [ ] Facebook test post successful
- [ ] Instagram connected to Facebook (optional)
- [ ] Instagram Business ID obtained
- [ ] CEO Briefing tested
- [ ] Error recovery tested
- [ ] Audit logging tested
- [ ] Ralph Wiggum tested
- [ ] Company Handbook updated
- [ ] Business Goals updated

---

## 📈 What's Next?

### Upgrade to Platinum Tier

Add production deployment:

- ☁️ **Cloud VM** - 24/7 always-on operation
- 🔄 **Vault Sync** - Git-based multi-agent communication
- 🔐 **Work-Zone Specialization** - Cloud vs Local domain ownership
- 🌐 **Odoo on Cloud** - HTTPS with backups
- 📨 **A2A Messaging** - Direct agent-to-agent communication

### Optimize Gold Tier

1. **Set up PM2** - Process management for production
2. **Configure alerts** - Get notified of issues
3. **Customize briefings** - Add your specific metrics
4. **Add more integrations** - Twitter/X, other platforms

---

## 📚 Resources

- [Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Main README](../README.md)
- [QWEN.md](../QWEN.md)

---

*Gold Tier Setup Guide - Personal AI Employee v1.0.0*
