# Troubleshooting Guide

**Common Issues and Solutions**

---

## 🔍 Diagnostic Tools

### Verify Installation

```bash
# Bronze Tier
python scripts/verify_bronze_tier.py

# Silver Tier
python scripts/verify_silver_tier.py

# Gold Tier
python scripts/verify_gold_tier.py
```

### Check Logs

```bash
# View recent logs
tail -f AI_Employee_Vault/Logs/*.log

# View today's audit logs
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl

# Search for errors
grep "ERROR" AI_Employee_Vault/Logs/*.log
```

### Test Components

```bash
# Test Gmail Watcher (one-time)
python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json --once

# Test LinkedIn connection
python scripts/linkedin_api_poster.py --test

# Test Facebook connection
python scripts/facebook_graph_poster.py --test-connection --page-id $FACEBOOK_PAGE_ID

# Test Odoo connection
python scripts/odoo_connector.py --test-connection
```

---

## 🐛 Common Issues

### Qwen Code Issues

#### Issue: "Qwen Code not found" or "command not found"

**Symptoms:**
```bash
bash: qwen: command not found
```

**Solutions:**
1. **Verify installation:**
   ```bash
   qwen --version
   ```

2. **Check PATH:**
   ```bash
   # Windows
   echo %PATH%
   
   # Mac/Linux
   echo $PATH
   ```

3. **Reinstall Qwen Code:**
   ```bash
   # Follow installation guide for your system
   # https://github.com/anthropics/qwen-code
   ```

---

#### Issue: Qwen Code exits immediately

**Symptoms:**
- Qwen Code starts but exits without processing
- No output or errors

**Solutions:**
1. **Check vault path:**
   ```bash
   # Ensure vault exists
   ls -la AI_Employee_Vault/
   ```

2. **Check file permissions:**
   ```bash
   # Windows
   icacls AI_Employee_Vault
   
   # Mac/Linux
   ls -la AI_Employee_Vault/
   ```

3. **Run with verbose logging:**
   ```bash
   python scripts/orchestrator.py AI_Employee_Vault --verbose
   ```

---

### Watcher Issues

#### Issue: Watcher not detecting files

**Symptoms:**
- Files dropped in Inbox/ not detected
- No action files created

**Solutions:**
1. **Check folder exists:**
   ```bash
   dir AI_Employee_Vault\Inbox\
   ```

2. **Run watcher in test mode:**
   ```bash
   python scripts/filesystem_watcher.py AI_Employee_Vault --once
   ```

3. **Check logs:**
   ```bash
   cat AI_Employee_Vault\Logs\filesystem_watcher_*.log
   ```

4. **Verify file hash tracking:**
   ```bash
   # Watcher may skip duplicate files
   # Check hash database
   ```

---

#### Issue: Gmail Watcher not detecting emails

**Symptoms:**
- New emails not appearing in Needs_Action/

**Solutions:**
1. **Check credentials:**
   ```bash
   # Ensure credentials.json exists
   dir credentials.json
   ```

2. **Re-authenticate:**
   ```bash
   # Delete old token
   del AI_Employee_Vault\.gmail_token.json
   
   # Re-authenticate
   python scripts/gmail_watcher.py AI_Employee_Vault --auth-only
   ```

3. **Check Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Verify Gmail API is enabled
   - Check OAuth consent screen

4. **Verify query:**
   ```bash
   # Default query: is:unread is:important
   # Try custom query
   python scripts/gmail_watcher.py AI_Employee_Vault \
     --credentials credentials.json \
     --query "is:unread"
   ```

---

#### Issue: WhatsApp Watcher crashes

**Symptoms:**
- Browser crashes
- Session not persisting

**Solutions:**
1. **Clean session:**
   ```bash
   # Delete old session
   rmdir /s /q AI_Employee_Vault\.linkedin_session
   ```

2. **Update Playwright:**
   ```bash
   playwright install chromium
   ```

3. **Check WhatsApp Web:**
   - Open WhatsApp Web in browser
   - Ensure you're logged in
   - Scan QR code if needed

---

### Email Issues

#### Issue: Emails not being sent

**Symptoms:**
- Files stuck in Approved/
- No emails in Gmail Sent folder

**Solutions:**
1. **Check Email Approval Watcher:**
   ```bash
   # Ensure it's running
   python scripts/email_approval_watcher.py AI_Employee_Vault --credentials credentials.json
   ```

2. **Verify Gmail scopes:**
   ```bash
   # Re-authenticate with correct scopes
   del AI_Employee_Vault\.gmail_token.json
   python scripts/gmail_watcher.py AI_Employee_Vault --auth-only
   ```

3. **Check approval file format:**
   ```markdown
   ---
   type: approval_request
   action: email_send
   to: test@example.com
   subject: Test
   ---
   
   Body text
   ```

---

#### Issue: Gmail API 403 Forbidden

**Symptoms:**
```
googleapiclient.errors.HttpError: <HttpError 403 when requesting ...>
```

**Solutions:**
1. **Enable Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Select project
   - APIs & Services → Library
   - Search "Gmail API" → Enable

2. **Verify OAuth consent:**
   - APIs & Services → OAuth consent screen
   - Ensure your email is added as test user

3. **Check credentials:**
   - APIs & Services → Credentials
   - Ensure OAuth client ID is correct

---

### LinkedIn Issues

#### Issue: "Invalid access token"

**Symptoms:**
```
LinkedIn API Error: Invalid access token
```

**Solutions:**
1. **Token expired** (LinkedIn tokens expire after 60 days):
   - Go to LinkedIn Developer Portal
   - Your App → Auth
   - Generate new access token
   - Update `.env` file

2. **Wrong token format:**
   ```bash
   # Check .env file format (no quotes, no spaces)
   LINKEDIN_ACCESS_TOKEN=actual_token_here
   ```

3. **Missing scopes:**
   - Ensure `w_member_social` scope is selected
   - Regenerate token with correct scopes

---

#### Issue: "Person URN not found"

**Symptoms:**
```
Error: Person URN not set
```

**Solutions:**
```bash
# Get your Person URN
python scripts/linkedin_api_poster.py --get-urn

# Should output: urn:li:person:ABC123
# Add to .env file
```

---

#### Issue: Post created but not visible

**Symptoms:**
- API returns success
- Post not appearing on LinkedIn profile

**Solutions:**
1. **Check visibility:**
   - Post may be under review (LinkedIn moderation)
   - Visibility set to "CONNECTIONS" instead of "PUBLIC"

2. **Check your profile:**
   - Go to LinkedIn → Activity
   - Look for post

3. **Review content policies:**
   - Ensure content doesn't violate LinkedIn policies

---

### Facebook Issues

#### Issue: "Invalid access token"

**Symptoms:**
```
Facebook API Error: Invalid OAuth access token
```

**Solutions:**
1. **Token expired:**
   - Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   - Generate new Page Access Token
   - Update `.env` file

2. **Exchange for long-lived token:**
   ```bash
   python scripts/facebook_exchange_token.py \
     --app-id YOUR_APP_ID \
     --app-secret YOUR_APP_SECRET \
     --short-token YOUR_SHORT_TOKEN
   ```

---

#### Issue: "Missing permissions"

**Symptoms:**
```
Facebook API Error: Missing permissions
```

**Solutions:**
1. **Re-generate token with all scopes:**
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
   - `instagram_basic` (for Instagram)

2. **Check App Review:**
   - For production use, submit for App Review
   - Typically 3-7 days for approval

---

#### Issue: Instagram not connected

**Symptoms:**
```
Instagram Business Account ID not set
```

**Solutions:**
1. **Connect Instagram to Facebook Page:**
   - Facebook Page → Settings → Instagram
   - Connect Business Account

2. **Get Instagram Business ID:**
   ```
   GET /{page-id}?fields=instagram_business_account
   ```

3. **Add to `.env`:**
   ```bash
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_id
   ```

---

### Odoo Issues

#### Issue: "Connection refused"

**Symptoms:**
```
Connection refused to http://localhost:8069
```

**Solutions:**
1. **Check Docker containers:**
   ```bash
   docker-compose ps
   ```

2. **Start Odoo:**
   ```bash
   docker-compose up -d odoo db
   ```

3. **Check logs:**
   ```bash
   docker-compose logs odoo
   ```

4. **Verify port:**
   ```bash
   netstat -ano | findstr :8069
   ```

---

#### Issue: "Database not found"

**Symptoms:**
```
Odoo error: database does not exist
```

**Solutions:**
1. **Create database:**
   - Go to http://localhost:8069
   - Click "Create Database"
   - Fill in details

2. **Verify database name:**
   ```bash
   # Check .env file
   ODOO_DB=ai_employee
   ```

---

#### Issue: "Authentication failed"

**Symptoms:**
```
Odoo error: authentication failed
```

**Solutions:**
1. **Verify API user:**
   - Odoo → Settings → Users
   - Ensure user exists
   - Check password

2. **Generate API key:**
   - Click profile → Preferences
   - Generate API Key
   - Update `.env` file

---

### Ralph Wiggum Issues

#### Issue: Loop runs max iterations

**Symptoms:**
- Always hits max iterations without completing

**Solutions:**
1. **Increase max_iterations:**
   ```bash
   python scripts/ralph_wiggum.py "Task" --max-iterations 20
   ```

2. **Check if files are being moved:**
   ```bash
   ls -la AI_Employee_Vault/Needs_Action/
   ls -la AI_Employee_Vault/Done/
   ```

3. **Check Qwen output:**
   ```bash
   cat Logs/ralph_wiggum_*.log | grep -A 5 "Qwen Code"
   ```

---

#### Issue: Loop exits immediately

**Symptoms:**
- Exits after 1-2 iterations

**Solutions:**
1. **Use more specific completion promise:**
   ```bash
   python scripts/ralph_wiggum.py "Task" \
     --completion-promise "INVOICES_GENERATED_2026"
   ```

2. **Check if promise appears in normal output:**
   ```bash
   cat Logs/ralph_wiggum_*.log | grep "Completion"
   ```

---

## 📊 Performance Issues

### Slow Processing

**Symptoms:**
- Tasks taking longer than expected
- Watchers lagging

**Solutions:**
1. **Reduce check interval:**
   ```bash
   python scripts/filesystem_watcher.py AI_Employee_Vault --interval 60
   ```

2. **Check system resources:**
   ```bash
   # Windows Task Manager
   # Mac Activity Monitor
   ```

3. **Close unnecessary applications**

---

### High Memory Usage

**Symptoms:**
- System running out of memory
- Slowdowns

**Solutions:**
1. **Restart watchers:**
   ```bash
   # Stop and restart each watcher
   ```

2. **Clear session data:**
   ```bash
   # Delete old browser sessions
   rmdir /s /q AI_Employee_Vault\.linkedin_session
   ```

3. **Reduce concurrent watchers**

---

## 🛡️ Security Issues

### Credential Leaks

**If credentials are accidentally committed:**

1. **Rotate immediately:**
   - Gmail API: Regenerate credentials
   - LinkedIn: Generate new token
   - Facebook: Generate new token
   - Odoo: Change password

2. **Remove from git history:**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   ```

3. **Update .gitignore:**
   ```bash
   .env
   credentials.json
   *.token.json
   ```

---

## 📚 Additional Resources

- [Main README](../README.md)
- [Architecture Overview](./architecture/overview.md)
- [Agent Skills Reference](./reference/agent-skills.md)
- [Qwen Code Documentation](https://github.com/anthropics/qwen-code)
- [Obsidian Documentation](https://help.obsidian.md/)

---

*Troubleshooting Guide - Personal AI Employee*
