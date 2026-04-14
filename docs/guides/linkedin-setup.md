# LinkedIn Setup Guide

**LinkedIn API Integration for Auto-Posting**

This guide covers complete LinkedIn API setup for automated business posting.

---

## 📋 What You'll Set Up

- ✅ LinkedIn Developer App
- ✅ Access Token & Person URN
- ✅ Automated posting with approval workflow

---

## 🚀 Step-by-Step Setup

### Step 1: Create LinkedIn Developer App

1. **Go to [LinkedIn Developers](https://www.linkedin.com/developers/)**
2. **Sign in with your LinkedIn account**
3. **Click "Create app"**
4. **Fill in:**
   - App name: `AI Employee Poster`
   - LinkedIn Page: Select or create one
   - App description: `Automated posting for AI Employee`
   - Business email: Your email
5. **Click "Create app"**

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

### Step 6: Test Connection

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

## 📝 Usage Examples

### Simple Text Post

```bash
python scripts/linkedin_api_poster.py --content "Hello LinkedIn!"
```

### Post with Hashtags

```bash
python scripts/linkedin_api_poster.py \
  --content "New product launch" \
  --hashtags "AI,Automation,Tech"
```

### Post from Obsidian Vault

```bash
python scripts/linkedin_api_poster.py \
  --vault AI_Employee_Vault \
  --content "Business update" \
  --hashtags "Business,Growth"
```

---

## 🔧 Configuration

### Token Expiration

LinkedIn tokens expire after **60 days**. Set a reminder:

```
📅 Token Refresh Reminder
Every 50 days:
1. Go to LinkedIn Developer Portal
2. Generate new access token
3. Update .env file
4. Test connection
```

### Company Handbook Rules

Add to `AI_Employee_Vault/Company_Handbook.md`:

```markdown
## LinkedIn Rules
- Post only during business hours (9 AM - 5 PM)
- Use 3-5 hashtags per post
- No political or controversial content
- All posts require approval (HITL)
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "LINKEDIN_ACCESS_TOKEN not found" | Check .env file exists and has correct format |
| "Invalid access token" | Token expired - regenerate in LinkedIn Developer |
| "Missing permissions" | Ensure `w_member_social` scope is selected |
| "Person URN not found" | Run `--get-urn` command |
| "Post button not found" | Try visible mode: `--visible` flag |

---

*LinkedIn Setup Guide - Personal AI Employee*
