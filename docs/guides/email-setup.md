# Email Setup Guide

**Gmail Integration for AI Employee**

This guide covers complete Gmail API setup for receiving and sending emails.

---

## 📋 What You'll Set Up

- ✅ Gmail Watcher - Monitor incoming emails
- ✅ Email Sender - Send approved emails
- ✅ HITL Approval - Human review for sensitive emails

---

## 🚀 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Click "Select a project" → "New Project"**
3. **Name:** `AI Employee Gmail`
4. **Click "Create"**

### Step 2: Enable Gmail API

1. **In project dashboard:**
2. **Go to "APIs & Services" → "Library"**
3. **Search for "Gmail API"**
4. **Click "Enable"**

### Step 3: Configure OAuth Consent Screen

1. **Go to "APIs & Services" → "OAuth consent screen"**
2. **User Type:** "External"
3. **Fill in:**
   - App name: `AI Employee`
   - User support email: Your email
   - Developer contact: Your email
4. **Click "Save and Continue"**
5. **Scopes:** Skip this step
6. **Test users:** Add your Gmail address
7. **Click "Save and Continue"**

### Step 4: Create OAuth Credentials

1. **Go to "APIs & Services" → "Credentials"**
2. **Click "Create Credentials" → "OAuth client ID"**
3. **Application type:** "Desktop app"
4. **Name:** `AI Employee Gmail Client`
5. **Click "Create"**
6. **Download JSON** → Save as `credentials.json`
7. **Place in project root folder**

### Step 5: Authenticate (First Time)

```bash
# Run authentication
python scripts/gmail_watcher.py AI_Employee_Vault --auth-only
```

**What happens:**
1. Browser opens automatically
2. Sign in to your Google account
3. Grant Gmail API permissions
4. Token saved to `AI_Employee_Vault/.gmail_token.json`

### Step 6: Start Gmail Watcher

```bash
python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Expected output:**
```
2026-03-07 11:00:00 - INFO - Starting GmailWatcher
2026-03-07 11:00:00 - INFO - Monitoring Gmail (interval: 120s)
```

### Step 7: Start Email Approval Watcher

```bash
python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
```

**Expected output:**
```
2026-03-07 11:05:00 - INFO - Starting EmailApprovalWatcher
2026-03-07 11:05:00 - INFO - Monitoring Approved/ folder (interval: 30s)
```

---

## 🧪 Testing

### Test Receiving Emails

1. **Send email** to your Gmail from another account
2. **Wait 2 minutes**
3. **Check Needs_Action/** for new file

### Test Sending Emails

1. **Create approval file** in `Pending_Approval/`:

```markdown
---
type: approval_request
action: email_send
to: test@example.com
subject: Test Email
created: 2026-03-07T11:15:00Z
status: pending
---

## Email Details
- To: test@example.com
- Subject: Test Email
- Body: This is a test.

## To Approve
Move to /Approved folder.
```

2. **Move to Approved/**
3. **Wait 30 seconds**
4. **Check Done/** - file should be there
5. **Check Gmail Sent** - email should be there

---

## 🔧 Configuration

### Custom Gmail Query

```bash
# Only from specific senders
python gmail_watcher.py AI_Employee_Vault --query "from:client@example.com is:unread"

# With specific subject
python gmail_watcher.py AI_Employee_Vault --query "subject:invoice is:unread"

# Exclude newsletters
python gmail_watcher.py AI_Employee_Vault --query "is:unread -subject:(unsubscribe OR newsletter)"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Credentials not found" | Ensure `credentials.json` is in project root |
| "Token expired" | Delete `.gmail_token.json` and re-authenticate |
| "Gmail API error 403" | Enable Gmail API in Google Cloud Console |
| Email stuck in Approved/ | Ensure Email Approval Watcher is running |

---

*Email Setup Guide - Personal AI Employee*
