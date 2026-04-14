# Getting Started Guide

**Your Personal AI Employee in 15 Minutes**

This guide walks you through setting up the foundation (Bronze Tier) of your AI Employee. By the end, you'll have a working system that monitors files and processes them with Qwen Code.

---

## 📋 What You'll Build

```
Drop File → Watcher Detects → Qwen Processes → Task Complete
```

---

## 🎯 Prerequisites

### Required Software (15 minutes to install)

| Software | Version | Install Link | Purpose |
|----------|---------|--------------|---------|
| **Python** | 3.13+ | [Download](https://www.python.org/downloads/) | Runs watcher scripts |
| **Qwen Code** | Latest | [Install Guide](https://github.com/anthropics/qwen-code) | AI reasoning engine |
| **Obsidian** | v1.10.6+ | [Download](https://obsidian.md/download) | Knowledge base & dashboard |

### Verify Installation

```bash
# Check Python (should be 3.13 or higher)
python --version

# Check Qwen Code
qwen --version

# If Qwen Code is not installed, follow the installation guide for your system
```

---

## 🚀 Step-by-Step Setup

### Step 1: Clone or Download the Project

```bash
# If using Git
git clone <your-repo-url>
cd Personal-AI-Employe-Hackathon-0-FTE

# Or download and extract the ZIP file
# Then open Terminal/PowerShell in the project folder
```

### Step 2: Open the Obsidian Vault

The vault is your AI Employee's memory and dashboard.

1. **Open Obsidian**
2. **Click "Open folder as vault"**
3. **Navigate to:** `AI_Employee_Vault/` in the project folder
4. **Click "Open"**

**You should see:**
- Dashboard.md (main status screen)
- Company_Handbook.md (rules for AI)
- Business_Goals.md (your objectives)
- Folders: Inbox, Needs_Action, Done, etc.

### Step 3: Review the Company Handbook

Open `Company_Handbook.md` in Obsidian. This contains the rules your AI follows.

**Example rules:**
```markdown
## Rules of Engagement

1. Always be polite in communications
2. Flag any payment over $500 for approval
3. No auto-payments to new recipients
4. Response time target: < 24 hours for client messages
```

**Customize these rules** to match your preferences.

### Step 4: Review Business Goals

Open `Business_Goals.md` in Obsidian. This tracks your objectives.

**Example:**
```markdown
## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $4,500

### Key Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
```

### Step 5: Start the File System Watcher

The watcher monitors the `Inbox/` folder for new files.

```bash
# Open Terminal/PowerShell in project folder
python scripts/filesystem_watcher.py AI_Employee_Vault
```

**What you'll see:**
```
2026-03-07 10:00:00 - INFO - Starting FilesystemWatcher
2026-03-07 10:00:00 - INFO - Monitoring: AI_Employee_Vault/Inbox
2026-03-07 10:00:00 - INFO - Watcher running (check interval: 30s)
```

**Leave this terminal running** - it monitors continuously.

### Step 6: Start the Orchestrator

The orchestrator triggers Qwen Code when files are detected.

```bash
# Open a NEW terminal window
python scripts/orchestrator.py AI_Employee_Vault
```

**What you'll see:**
```
2026-03-07 10:01:00 - INFO - Starting Orchestrator
2026-03-07 10:01:00 - INFO - Vault: AI_Employee_Vault
2026-03-07 10:01:00 - INFO - Monitoring Needs_Action folder
2026-03-07 10:01:00 - INFO - Orchestrator running
```

**Leave this terminal running too.**

---

## 🧪 Test the System

### Test 1: Drop a File

1. **Create a test file:**
   ```bash
   # Create a simple text file
   echo "Hello AI Employee! Please summarize this document." > test_document.txt
   
   # Copy to Inbox folder
   cp test_document.txt AI_Employee_Vault/Inbox/
   ```

2. **Watch the magic happen:**
   - File System Watcher detects the new file (within 30 seconds)
   - Creates action file in `Needs_Action/`
   - Orchestrator triggers Qwen Code
   - Qwen processes the file
   - File moves to `Done/`

3. **Check the results:**
   ```bash
   # Check Needs_Action folder
   dir AI_Employee_Vault\Needs_Action\
   
   # Check Done folder
   dir AI_Employee_Vault\Done\
   
   # Check Dashboard
   cat AI_Employee_Vault\Dashboard.md
   ```

### Test 2: Create a Manual Task

1. **Create a task file** in `Needs_Action/`:

```markdown
---
type: manual_task
created: 2026-03-07T10:30:00Z
priority: normal
status: pending
---

# Task: Update Dashboard

Please review the Business_Goals.md and update the Dashboard 
with current status.

## Suggested Actions
- [ ] Check all metrics
- [ ] Flag any alerts
- [ ] Update summary
```

2. **Wait for processing** (within 60 seconds)

3. **Check Dashboard.md** for updates

---

## 📖 Understanding the Workflow

### The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. You drop a file in Inbox/                              │
│     Example: invoice.pdf, contract.txt, notes.md           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. File System Watcher detects (every 30 seconds)         │
│     - Checks for new files                                  │
│     - Creates action file in Needs_Action/                  │
│     - Tracks file hash (no duplicates)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Orchestrator detects action file                       │
│     - Monitors Needs_Action/ folder                         │
│     - Triggers Qwen Code with context                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Qwen Code processes                                     │
│     - Reads action file                                     │
│     - Consults Company_Handbook.md for rules                │
│     - Takes appropriate action                              │
│     - Updates Dashboard.md                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Task complete                                           │
│     - File moved to Done/                                   │
│     - Action logged in Logs/                                │
│     - Dashboard updated                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Options

### Watcher Settings

```bash
# Custom check interval (default: 30 seconds)
python scripts/filesystem_watcher.py AI_Employee_Vault --interval 60

# Test mode (run once and exit)
python scripts/filesystem_watcher.py AI_Employee_Vault --once

# Verbose logging
python scripts/filesystem_watcher.py AI_Employee_Vault --verbose
```

### Orchestrator Settings

```bash
# Dry run mode (log without executing)
python scripts/orchestrator.py AI_Employee_Vault --dry-run

# Test mode (run once and exit)
python scripts/orchestrator.py AI_Employee_Vault --once

# Custom vault path
python scripts/orchestrator.py /path/to/your/vault
```

---

## 📊 What's Next?

### Upgrade to Silver Tier

Add communication automation:

- 📧 **Gmail Watcher** - Monitor emails automatically
- 💬 **WhatsApp Watcher** - Track urgent messages
- 📱 **LinkedIn Poster** - Auto-post business updates
- ✅ **Email Approval** - Send emails with HITL

[→ Silver Tier Setup Guide](./silver-tier-setup.md)

### Customize Your System

1. **Edit Company Handbook** - Add your rules
2. **Update Business Goals** - Set your targets
3. **Create Templates** - For common tasks
4. **Configure Scheduling** - Run at specific times

---

## 🐛 Troubleshooting

### Issue: Watcher not detecting files

**Check:**
```bash
# Verify Inbox folder exists
dir AI_Employee_Vault\Inbox\

# Run watcher in test mode
python scripts/filesystem_watcher.py AI_Employee_Vault --once

# Check logs
cat AI_Employee_Vault\Logs\*.log
```

### Issue: Orchestrator not processing

**Check:**
```bash
# Verify Needs_Action folder exists
dir AI_Employee_Vault\Needs_Action\

# Run orchestrator in test mode
python scripts/orchestrator.py AI_Employee_Vault --once --dry-run

# Check logs
cat AI_Employee_Vault\Logs\orchestrator_*.log
```

### Issue: Qwen Code not found

```bash
# Verify installation
qwen --version

# Reinstall if needed
# Follow: https://github.com/anthropics/qwen-code
```

### Issue: Python module not found

```bash
# Ensure Python 3.13+ is installed
python --version

# Install required packages (if any)
pip install -r requirements.txt
```

---

## 📝 Example Use Cases

### Use Case 1: Document Summarization

```bash
# Drop a long document
cp contract.pdf AI_Employee_Vault/Inbox/

# Qwen will:
# 1. Read the document
# 2. Create summary
# 3. Save to Done/ with summary
```

### Use Case 2: Task Management

```markdown
# Create task file in Needs_Action/:

---
type: manual_task
priority: high
---

# Task: Review Weekly Metrics

Check business metrics and flag any concerns.
```

### Use Case 3: File Organization

```bash
# Drop multiple files
cp *.txt AI_Employee_Vault/Inbox/

# Qwen will:
# 1. Process each file
# 2. Categorize content
# 3. Organize into folders
```

---

## 🔐 Best Practices

### 1. Start Small
- Begin with file monitoring only
- Add features gradually
- Test each component

### 2. Review Logs
```bash
# Check daily logs
cat AI_Employee_Vault\Logs\*.log

# Look for patterns
# - What's working well?
# - What needs adjustment?
```

### 3. Update Handbook
- Review Company_Handbook.md monthly
- Add rules as you discover edge cases
- Remove outdated rules

### 4. Backup Vault
```bash
# Backup your vault regularly
robocopy AI_Employee_Vault D:\Backups\AI_Vault /MIR
```

---

## 📚 Resources

- [Main README](../README.md) - Project overview
- [QWEN.md](../QWEN.md) - Full architecture
- [Company Handbook Template](../AI_Employee_Vault/Company_Handbook.md)
- [Business Goals Template](../AI_Employee_Vault/Business_Goals.md)

---

## ✅ Bronze Tier Checklist

- [ ] Python 3.13+ installed
- [ ] Qwen Code installed
- [ ] Obsidian vault opened
- [ ] Company_Handbook.md reviewed
- [ ] Business_Goals.md reviewed
- [ ] File System Watcher running
- [ ] Orchestrator running
- [ ] Test file processed successfully
- [ ] Dashboard updated

**Congratulations! 🎉 Your AI Employee foundation is complete!**

---

*Getting Started Guide - Bronze Tier*
*Personal AI Employee v1.0.0*
