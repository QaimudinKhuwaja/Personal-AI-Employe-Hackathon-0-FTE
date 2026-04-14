# Agent Skills Reference

**Reusable AI Capabilities**

---

## 📋 What Are Agent Skills?

Agent Skills are modular, reusable capabilities that extend Qwen Code's functionality. Each skill is documented with a `SKILL.md` file that describes:

- **Purpose:** What the skill does
- **Usage:** How to invoke it
- **Examples:** Sample use cases
- **Configuration:** Required setup

---

## 🎯 Available Skills

### Silver Tier Skills (8)

#### 1. Gmail Watcher
**Location:** `.qwen/skills/gmail-watcher/SKILL.md`

**Purpose:** Monitor Gmail for new emails automatically

**Capabilities:**
- Detect unread/important emails
- Create action files in `Needs_Action/`
- Filter by custom queries
- OAuth2 authenticated

**Usage:**
```bash
python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Example:**
```bash
# Custom query
python scripts/gmail_watcher.py AI_Employee_Vault \
  --credentials credentials.json \
  --query "from:client@example.com is:unread"
```

---

#### 2. WhatsApp Watcher
**Location:** `.qwen/skills/whatsapp-watcher/SKILL.md`

**Purpose:** Monitor WhatsApp Web for urgent messages

**Capabilities:**
- Keyword detection (urgent, asap, invoice, payment, help)
- Session persistence
- Action file creation
- Playwright-based automation

**Usage:**
```bash
python scripts/whatsapp_watcher.py AI_Employee_Vault
```

**Configuration:**
```python
# Edit keywords in script
self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help']
```

---

#### 3. Email MCP
**Location:** `.qwen/skills/email-mcp/SKILL.md`

**Purpose:** Send emails via Gmail API

**Capabilities:**
- Send emails with attachments
- Draft mode for approval
- Base64url encoding
- Message ID tracking

**Usage:**
```bash
python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Approval Flow:**
1. Create approval file in `Pending_Approval/`
2. Human moves to `Approved/`
3. Email sent automatically
4. Logged to audit trail

---

#### 4. LinkedIn Poster
**Location:** `.qwen/skills/linkedin-poster/SKILL.md`

**Purpose:** Post updates to LinkedIn

**Capabilities:**
- Text posts with hashtags
- Image posts
- Visibility control (PUBLIC, CONNECTIONS)
- Official LinkedIn API

**Usage:**
```bash
python scripts/linkedin_api_poster.py \
  --content "Hello LinkedIn!" \
  --hashtags "AI,Automation"
```

**Configuration:**
```bash
# .env file
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_PERSON_URN=urn:li:person:ABC123
```

---

#### 5. Plan Generator
**Location:** `.qwen/skills/plan-generator/SKILL.md`

**Purpose:** Create structured action plans

**Capabilities:**
- Task breakdown
- Step-by-step checkboxes
- Progress tracking
- Plan templates

**Example Plan:**
```markdown
---
type: plan
created: 2026-03-07T10:00:00Z
status: in_progress
---

# Plan: Process Customer Invoices

## Steps
- [ ] Extract customer info from requests
- [ ] Create invoices in Odoo
- [ ] Send invoices to customers
- [ ] Log all actions
- [ ] Move requests to Done/
```

---

#### 6. HITL Approval
**Location:** `.qwen/skills/hitl-approval/SKILL.md`

**Purpose:** Human-in-the-loop approval workflow

**Capabilities:**
- Create approval requests
- File-based approval (move to Approved/)
- Expiration tracking
- Audit trail

**Approval File Schema:**
```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
created: 2026-03-07T10:30:00Z
expires: 2026-03-08T10:30:00Z
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A
- Reference: Invoice #1234

## To Approve
Move this file to /Approved folder.
```

---

#### 7. Task Scheduler
**Location:** `.qwen/skills/task-scheduler/SKILL.md`

**Purpose:** Schedule recurring tasks

**Capabilities:**
- Windows Task Scheduler integration
- Cron-like scheduling
- Recurring task support
- Task templates

**Example:**
```bash
# Schedule CEO Briefing (Monday 7 AM)
python scripts/ceo_briefing_generator.py --schedule "0 7 * * 1"
```

---

#### 8. Browsing with Playwright
**Location:** `.qwen/skills/browsing-with-playwright/SKILL.md`

**Purpose:** Browser automation for web interactions

**Capabilities:**
- Navigate websites
- Click buttons
- Fill forms
- Take screenshots
- Session persistence

**Usage:**
```bash
# Start Playwright MCP server
npx @playwright/mcp@latest --port 8808 --shared-browser-context &
```

---

### Gold Tier Skills (4)

#### 9. Odoo Connector
**Location:** `.qwen/skills/odoo-connector/SKILL.md`

**Purpose:** Odoo ERP integration via JSON-RPC

**Capabilities:**
- Create invoices
- Manage customers
- Register payments
- Sync to vault
- Financial reports

**Usage:**
```bash
# Create invoice
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Client A" \
  --amount 500.00 \
  --description "Consulting Services"

# Sync invoices
python scripts/odoo_connector.py --sync-invoices --last-days 30
```

**Configuration:**
```bash
# .env file
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=ai-employee@localhost
ODOO_PASSWORD=your_api_key
```

---

#### 10. Facebook Poster
**Location:** `.qwen/skills/facebook-poster/SKILL.md`

**Purpose:** Post to Facebook Pages and Instagram Business

**Capabilities:**
- Facebook Page posting
- Instagram Business posting
- Photo and link sharing
- Scheduled posting
- Hashtag support

**Usage:**
```bash
# Facebook post
python scripts/facebook_graph_poster.py \
  --content "Hello from AI Employee! 🤖" \
  --page-id $FACEBOOK_PAGE_ID \
  --hashtags "AI,Automation"

# Instagram post
python scripts/facebook_graph_poster.py \
  --content "Instagram post! 📸" \
  --instagram \
  --media-path ./photo.jpg \
  --hashtags "AI,Instagram"
```

**Configuration:**
```bash
# .env file
FACEBOOK_PAGE_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_id
```

---

#### 11. CEO Briefing
**Location:** `.qwen/skills/ceo-briefing/SKILL.md`

**Purpose:** Generate weekly executive reports

**Capabilities:**
- Aggregate data from all sources
- Revenue analysis from Odoo
- Task completion summary
- Social media performance
- Proactive recommendations

**Usage:**
```bash
# Generate weekly briefing
python scripts/ceo_briefing_generator.py \
  --output AI_Employee_Vault/Briefings/weekly_briefing.md \
  --days 7
```

**Report Sections:**
- Executive Summary
- Revenue Analysis
- Task Summary
- Social Media Performance
- Customer Overview
- Upcoming Deadlines
- Proactive Recommendations

---

#### 12. Ralph Wiggum
**Location:** `.qwen/skills/ralph-wiggum/SKILL.md`

**Purpose:** Task persistence for multi-step automation

**Capabilities:**
- Keep Qwen Code working until complete
- Completion detection (file movement, promises)
- Configurable max iterations
- Error handling

**Usage:**
```bash
python scripts/ralph_wiggum.py \
  "Process all files in Needs_Action" \
  --vault AI_Employee_Vault \
  --max-iterations 10 \
  --completion-promise "TASK_COMPLETE"
```

---

## 📝 Creating New Skills

### Skill Template

```markdown
# Skill Name

**Purpose:** What the skill does

## Capabilities

- Feature 1
- Feature 2
- Feature 3

## Usage

```bash
command --flag value
```

## Configuration

```bash
# .env file
VARIABLE=value
```

## Examples

### Example 1: Basic Usage

```bash
command --basic
```

### Example 2: Advanced Usage

```bash
command --advanced --flags
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Error | Fix |

## References

- Link to documentation
```

---

## 🔧 Skill Management

### List Installed Skills

```bash
ls .qwen/skills/*/SKILL.md
```

### Enable a Skill

1. Ensure skill folder exists in `.qwen/skills/`
2. Read `SKILL.md` for configuration
3. Install any dependencies
4. Test the skill

### Disable a Skill

1. Rename skill folder (e.g., add `.disabled` suffix)
2. Qwen Code will not load disabled skills

### Update a Skill

1. Check for updates in repository
2. Review changelog
3. Update skill files
4. Test functionality

---

## 📚 Resources

- [Qwen Code Documentation](https://github.com/anthropics/qwen-code)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

*Agent Skills Reference - Personal AI Employee*
