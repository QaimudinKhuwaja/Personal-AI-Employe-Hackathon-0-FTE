# Silver Tier Setup Guide

**Add Communication & Social Media Automation**

This guide extends Bronze Tier with Gmail monitoring, WhatsApp alerts, LinkedIn posting, and email sending with human approval.

**Estimated Time:** 2-3 hours

---

## 🎯 What Silver Tier Adds

| Feature | Description | Status |
|---------|-------------|--------|
| **Gmail Watcher** | Monitor Gmail for new emails | ✅ |
| **WhatsApp Watcher** | Track urgent WhatsApp messages | ✅ |
| **LinkedIn Poster** | Auto-post business updates | ✅ |
| **Email Sending** | Send approved emails via Gmail API | ✅ |
| **HITL Approval** | Human-in-the-loop for sensitive actions | ✅ |

---

## 📋 Prerequisites

### Complete Bronze Tier First
- ✅ File System Watcher working
- ✅ Orchestrator running
- ✅ Obsidian vault configured

### Additional Requirements

| Software | Purpose | Link |
|----------|---------|------|
| **Google Account** | Gmail API access | [Google](https://gmail.com) |
| **LinkedIn Account** | LinkedIn posting | [LinkedIn](https://linkedin.com) |
| **Google Cloud Console** | API credentials | [Console](https://console.cloud.google.com/) |

---

## 🚀 Part 1: Gmail Integration

### Step 1: Create Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create new project:**
   - Click "Select a project" → "New Project"
   - Name: `AI Employee Gmail`
   - Click "Create"

### Step 2: Enable Gmail API

1. **In your project dashboard:**
2. **Go to "APIs & Services" → "Library"**
3. **Search for "Gmail API"**
4. **Click "Enable"**

### Step 3: Create OAuth2 Credentials

1. **Go to "APIs & Services" → "Credentials"**
2. **Click "Create Credentials" → "OAuth client ID"**
3. **Configure consent screen (if prompted):**
   - User Type: "External"
   - App name: `AI Employee`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this step
   - Test users: Add your Gmail address
   - Click "Save and Continue"

4. **Create OAuth Client ID:**
   - Application type: "Desktop app"
   - Name: `AI Employee Gmail Client`
   - Click "Create"

5. **Download credentials:**
   - Click "Download JSON"
   - Save as `credentials.json`
   - **Place in project root folder**

### Step 4: Authenticate Gmail (First Time)

```bash
# Run authentication
python scripts/gmail_watcher.py AI_Employee_Vault --auth-only
```

**What happens:**
1. Browser opens automatically
2. Sign in to your Google account
3. Grant Gmail API permissions
4. Token saved to `AI_Employee_Vault/.gmail_token.json`

### Step 5: Start Gmail Watcher

```bash
# Terminal 1: Gmail Watcher
python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Expected output:**
```
2026-03-07 11:00:00 - INFO - Starting GmailWatcher
2026-03-07 11:00:00 - INFO - Monitoring Gmail (interval: 120s)
2026-03-07 11:00:00 - INFO - Query: is:unread is:important
```

### Step 6: Test Gmail Watcher

1. **Send yourself an email** from another account
   - Subject: `Test Invoice Request`
   - Body: `Please send me the invoice for January services`

2. **Wait 2 minutes** for Gmail Watcher to detect

3. **Check Needs_Action/ folder:**
   ```bash
   dir AI_Employee_Vault\Needs_Action\EMAIL_*.md
   ```

4. **You should see a new file** like:
   ```markdown
   ---
   type: email
   from: test@example.com
   subject: Test Invoice Request
   received: 2026-03-07T11:02:00Z
   priority: high
   status: pending
   ---

   ### Email Content
   Please send me the invoice for January services

   ### Suggested Actions
   - [ ] Reply to sender
   - [ ] Forward to accounting
   - [ ] Archive after processing
   ```

---

## 🚀 Part 2: WhatsApp Integration

### Step 1: Install Playwright

```bash
# Install Playwright for browser automation
pip install playwright
playwright install chromium
```

### Step 2: Start WhatsApp Watcher

```bash
# Terminal 2: WhatsApp Watcher
python scripts/whatsapp_watcher.py AI_Employee_Vault
```

**Expected output:**
```
2026-03-07 11:05:00 - INFO - Starting WhatsAppWatcher
2026-03-07 11:05:00 - INFO - Monitoring WhatsApp Web (interval: 30s)
2026-03-07 11:05:00 - INFO - Keywords: urgent, asap, invoice, payment, help
```

**Note:** WhatsApp Web must be open in your browser. Scan QR code with your phone if not already logged in.

### Step 3: Test WhatsApp Watcher

1. **Send yourself a WhatsApp message** with keyword "urgent"
2. **Wait 30 seconds**
3. **Check Needs_Action/ folder:**
   ```bash
   dir AI_Employee_Vault\Needs_Action\WHATSAPP_*.md
   ```

---

## 🚀 Part 3: LinkedIn Integration

### Step 1: Create LinkedIn Developer App

1. **Go to [LinkedIn Developers](https://www.linkedin.com/developers/)**
2. **Sign in with your LinkedIn account**
3. **Click "Create app"**
4. **Fill in details:**
   - App name: `AI Employee Poster`
   - LinkedIn Page: Select or create one
   - App description: `Automated posting for AI Employee`
   - Business email: Your email
   - Click "Create app"

### Step 2: Enable Share on LinkedIn

1. **In your app dashboard:**
2. **Go to "Products" tab**
3. **Find "Share on LinkedIn"**
4. **Click "Request access" or "Enable"**

### Step 3: Generate Access Token

1. **Go to "Auth" tab**
2. **Under "OAuth 2.0 Access Tokens":**
3. **Click "Generate access token"**
4. **Select scopes:**
   - ✅ `w_member_social` - Post on behalf of member (REQUIRED)
   - ✅ `r_basicprofile` - Read basic profile info
5. **Click "Generate"**
6. **Copy the token immediately** (you won't see it again)

### Step 4: Get Your Person URN

Your Person URN is your unique LinkedIn identifier.

```bash
# Set token temporarily (replace with your actual token)
set LINKEDIN_ACCESS_TOKEN=AQEDAbcdefgh1234567890...

# Get your Person URN
python scripts/linkedin_api_poster.py --get-urn
```

**Output:**
```
✅ Person URN: urn:li:person:ABC123xyz
```

### Step 5: Configure .env File

Create or edit `.env` in project root:

```bash
# LinkedIn API Credentials
LINKEDIN_ACCESS_TOKEN=AQEDAbcdefgh1234567890...  # Your token
LINKEDIN_PERSON_URN=urn:li:person:ABC123xyz   # Your URN
```

### Step 6: Test LinkedIn Connection

```bash
# Test API connection
python scripts/linkedin_api_poster.py --test
```

**Expected output:**
```
✅ Connection successful! Person URN: urn:li:person:ABC123xyz
```

### Step 7: Create Test Post

```bash
# Simple test post
python scripts/linkedin_api_poster.py --content "Testing LinkedIn API integration! 🚀 #AI #Automation"
```

**Expected output:**
```
✅ Post published successfully!
Post ID: urn:li:share:123456789
```

**Check your LinkedIn profile** - the post should appear!

---

## 🚀 Part 4: Email Sending with Approval

### Step 1: Start Email Approval Watcher

```bash
# Terminal 3: Email Approval Watcher
python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Expected output:**
```
2026-03-07 11:10:00 - INFO - Starting EmailApprovalWatcher
2026-03-07 11:10:00 - INFO - Monitoring Approved/ folder (interval: 30s)
```

### Step 2: Test Email Approval Flow

1. **Create approval file** in `Pending_Approval/`:

```markdown
---
type: approval_request
action: email_send
to: test@example.com
subject: Test Email from AI Employee
created: 2026-03-07T11:15:00Z
status: pending
---

## Email Details
- To: test@example.com
- Subject: Test Email from AI Employee
- Body: This is a test email sent by your AI Employee.

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

2. **Move file to Approved/** (this triggers sending)

3. **Wait 30 seconds**

4. **Check Done/ folder:**
   ```bash
   dir AI_Employee_Vault\Done\EMAIL_*.md
   ```

5. **Check your Gmail Sent folder** - email should be there!

---

## 📊 Complete Silver Tier Setup

### Running All Watchers

You need **4 terminals** running simultaneously:

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

**Terminal 5: Email Approval Watcher** (optional, for sending emails)
```bash
python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

---

## 🧪 Test the Complete Flow

### Test Scenario: Email Response

1. **Send email to your Gmail** from another account
   - Subject: `Question about Services`
   - Body: `Hi, I'm interested in your services. Can you send me pricing?`

2. **Wait for Gmail Watcher** (within 2 minutes)
   - Creates: `Needs_Action/EMAIL_timestamp_subject.md`

3. **Orchestrator processes** with Qwen Code
   - Reads email + Company Handbook
   - Creates response draft
   - Moves to `Pending_Approval/` (new contact)

4. **Review approval file** in `Pending_Approval/`

5. **Move to Approved/** to send

6. **Email Approval Watcher sends** email
   - Moves to `Done/`
   - Logs to `Logs/sent_*.md`

### Test Scenario: LinkedIn Post

1. **Create post file** in `Needs_Action/`:

```markdown
---
type: linkedin_post
content: |
  Excited to announce our AI Employee system!

  Automate your life and business with:
  - Email monitoring
  - Social media posting
  - Accounting integration

#hashtags: AI,Automation,Business
status: pending
---

## Post Content

Excited to announce our AI Employee system!

Automate your life and business with:
- Email monitoring
- Social media posting
- Accounting integration

#AI #Automation #Business

## To Post

Move this file to /Approved to publish.
```

2. **Move to Approved/** (HITL approval)

3. **Orchestrator triggers** LinkedIn Poster

4. **Post published** to LinkedIn

5. **Check Logs/** for confirmation

---

## 🔧 Configuration

### Gmail Query Customization

```bash
# Only from specific senders
python gmail_watcher.py AI_Employee_Vault --query "from:client@example.com is:unread"

# With specific subject
python gmail_watcher.py AI_Employee_Vault --query "subject:invoice is:unread"

# Exclude newsletters
python gmail_watcher.py AI_Employee_Vault --query "is:unread -subject:(unsubscribe OR newsletter)"
```

### WhatsApp Keywords

Edit `scripts/whatsapp_watcher.py` to customize:

```python
self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'question']
```

### Company Handbook Rules

Update `AI_Employee_Vault/Company_Handbook.md`:

```markdown
## Email Rules
- Auto-reply to client emails within 4 hours
- Forward invoices to accounting
- Flag urgent emails immediately

## LinkedIn Rules
- Post only during business hours (9 AM - 5 PM)
- Use 3-5 hashtags per post
- No political or controversial content

## Approval Rules
- Email to new contacts: Require approval
- Email to known contacts: Auto-approve
- LinkedIn posts: Require approval (first-time)
```

---

## 🐛 Troubleshooting

### Gmail Issues

| Issue | Solution |
|-------|----------|
| "Credentials not found" | Ensure `credentials.json` is in project root |
| "Token expired" | Delete `.gmail_token.json` and re-authenticate |
| "Gmail API error 403" | Enable Gmail API in Google Cloud Console |
| No emails detected | Check query string, verify emails are unread |

### WhatsApp Issues

| Issue | Solution |
|-------|----------|
| "Login required" | Open WhatsApp Web in browser, scan QR code |
| "Session expired" | Re-run WhatsApp Watcher |
| Browser crashes | Update Playwright: `playwright install` |

### LinkedIn Issues

| Issue | Solution |
|-------|----------|
| "Invalid access token" | Token expired - regenerate in LinkedIn Developer |
| "Missing permissions" | Ensure `w_member_social` scope is selected |
| "Post button not found" | Try visible mode: `--visible` flag |
| "Session expired" | Re-run setup session |

### Email Sending Issues

| Issue | Solution |
|-------|----------|
| "Insufficient permissions" | Re-authenticate with correct scopes |
| Email stuck in Approved/ | Ensure Email Approval Watcher is running |
| "Unicode error" | Already fixed in latest version |

---

## 📊 Silver Tier Checklist

- [ ] Gmail API credentials created
- [ ] `credentials.json` placed in project root
- [ ] Gmail authenticated (token created)
- [ ] Gmail Watcher running
- [ ] WhatsApp Watcher running
- [ ] LinkedIn Developer app created
- [ ] LinkedIn access token generated
- [ ] Person URN obtained
- [ ] `.env` file configured
- [ ] LinkedIn test post successful
- [ ] Email Approval Watcher running
- [ ] Test email sent successfully
- [ ] Company Handbook updated with rules

---

## 📈 What's Next?

### Upgrade to Gold Tier

Add business automation:

- 💰 **Odoo ERP** - Accounting, invoices, customers
- 📘 **Facebook/Instagram** - Additional social platforms
- 📊 **CEO Briefing** - Weekly automated reports
- 🔄 **Error Recovery** - Resilient operations
- 📝 **Audit Logging** - Comprehensive compliance

[→ Gold Tier Setup Guide](./gold-tier-setup.md)

### Optimize Silver Tier

1. **Set up scheduling** - Run watchers at specific times
2. **Create email templates** - For common responses
3. **Customize LinkedIn posts** - Match your brand voice
4. **Add more WhatsApp keywords** - Catch important messages

---

## 📚 Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/)
- [Playwright Documentation](https://playwright.dev/)
- [Main README](../README.md)
- [QWEN.md](../QWEN.md)

---

*Silver Tier Setup Guide - Personal AI Employee v1.0.0*
