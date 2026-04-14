---
name: linkedin-poster
description: |
  Post updates to LinkedIn automatically using the official LinkedIn API.
  Creates engaging business posts, schedules them, and tracks engagement.
  Use for generating sales leads, sharing company updates, and building brand presence.
  
  This skill uses LinkedIn's REST API (not browser automation) for reliable posting.
---

# LinkedIn Poster Skill

Automatically post business updates to LinkedIn using the official LinkedIn API.

## 📋 Prerequisites

### Required Python Packages

```bash
pip install requests python-dotenv
```

### LinkedIn API Setup (One-Time)

**Follow the detailed guide:** See `LINKEDIN_API_SETUP_GUIDE.md` in project root.

**Quick Setup:**

1. **Create LinkedIn Developer App**
   - Go to: https://www.linkedin.com/developers/
   - Click "Create app"
   - Fill in app details

2. **Enable "Share on LinkedIn"**
   - In app dashboard → Products tab
   - Enable "Share on LinkedIn"

3. **Generate Access Token**
   - Go to "Auth" tab
   - Generate token with scopes: `w_member_social`, `r_basicprofile`
   - Copy the token immediately

4. **Get Your Person URN**
   ```bash
   # Set token temporarily
   set LINKEDIN_ACCESS_TOKEN=your_token_here
   
   # Get Person URN
   python scripts/linkedin_api_poster.py --get-urn
   ```

5. **Create .env file** in project root:
   ```bash
   LINKEDIN_ACCESS_TOKEN=your_token_here
   LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID
   ```

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# LinkedIn API Credentials
LINKEDIN_ACCESS_TOKEN=AQEDAbcdefgh1234567890...
LINKEDIN_PERSON_URN=urn:li:person:ABC123xyz
```

**⚠️ Security:** Never commit `.env` to version control (already in `.gitignore`)

## 📖 Usage

### Method 1: Direct Command Line

```bash
# Simple text post
python scripts/linkedin_api_poster.py --content "Hello LinkedIn! 🚀"

# Post with hashtags
python scripts/linkedin_api_poster.py \
  --content "Excited to announce our new AI Employee service!" \
  --hashtags "AIEmployee,Automation,Business"

# Specify visibility
python scripts/linkedin_api_poster.py \
  --content "Team update" \
  --visibility "CONNECTIONS"

# From Obsidian vault
python scripts/linkedin_api_poster.py \
  --vault AI_Employee_Vault \
  --content "Business update" \
  --hashtags "Business,Growth"
```

### Method 2: From Action File (HITL Workflow)

```bash
# Process approved LinkedIn post files
python scripts/linkedin_api_poster.py --action-file AI_Employee_Vault/Approved/linkedin_post_*.md
```

### Method 3: Test Connection

```bash
# Test API connection
python scripts/linkedin_api_poster.py --test

# Get your Person URN
python scripts/linkedin_api_poster.py --get-urn

# Show setup instructions
python scripts/linkedin_api_poster.py --setup
```

## 📝 Post Action File Format

For Human-in-the-Loop (HITL) workflow, create action files:

### Pending Approval File

Create in `Needs_Action/` or `Pending_Approval/`:

```markdown
---
type: linkedin_post
created: 2026-02-28T10:00:00Z
status: pending_approval
visibility: PUBLIC
---

# LinkedIn Post Request

## Content
Excited to announce our new AI Employee service! 🚀

Automate your business with AI-powered agents that work 24/7.

## Hashtags
#AIEmployee #Automation #Business #Productivity

## Media (Optional)
- /path/to/image.png

## To Approve
Move this file to /Approved folder to publish.

## To Reject
Move this file to /Rejected folder.
```

### Approved File

After human approval (move to `Approved/`):

```markdown
---
type: linkedin_post
created: 2026-02-28T10:00:00Z
approved: 2026-02-28T10:30:00Z
status: approved
visibility: PUBLIC
---

# LinkedIn Post - READY TO PUBLISH

## Content
Excited to announce our new AI Employee service! 🚀

Automate your business with AI-powered agents that work 24/7.

## Hashtags
#AIEmployee #Automation #Business #Productivity

## Approved By
Human reviewer approved this post at 2026-02-28T10:30:00Z

## Execute
Run: python scripts/linkedin_api_poster.py --action-file this_file.md
```

## ✨ Features

- ✅ **Text posts** with automatic hashtag formatting
- ✅ **Official LinkedIn API** - No browser automation issues
- ✅ **Human-in-the-Loop** approval workflow
- ✅ **Post logging** to JSONL audit trail
- ✅ **Connection testing** and Person URN retrieval
- ✅ **Multiple visibility** options (PUBLIC, CONNECTIONS, ANYONE)
- ✅ **Error handling** with detailed logging
- ✅ **Rate limiting** awareness

## 📊 Post Templates

### Sales/Lead Generation Post

```markdown
🎯 Struggling with [pain point]?

Our [solution] helps you [benefit].

✅ Feature 1
✅ Feature 2
✅ Feature 3

Ready to transform your business?

DM us or visit [link]

#BusinessGrowth #Automation #AI
```

### Company Milestone Post

```markdown
📈 Company Milestone Alert!

We're thrilled to announce [achievement].

Thank you to our amazing team and clients!

#Milestone #Growth #TeamWork #Success
```

### Product Launch Post

```markdown
🚀 Product Launch: [Product Name]!

After [time period] of development, we're excited to launch...

Key features:
• Feature 1
• Feature 2
• Feature 3

Early bird offer: [details]

#ProductLaunch #Innovation #Tech
```

### Educational/Value Post

```markdown
💡 Tip of the Day: [Topic]

Did you know that [insight]?

Here's how to apply it:
1. Step 1
2. Step 2
3. Step 3

Save this for later!

#Tips #Education #Learning
```

## 🔄 Complete Workflow

```
┌─────────────────┐
│ Qwen Code       │
│ Creates post    │
│ content         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Needs_Action/   │─── Creates linkedin_post_*.md
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Orchestrator    │─── Triggers Qwen to review
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pending_        │
│ Approval/       │─── Awaiting human approval
└────────┬────────┘
         │
         ▼ (Human moves to Approved/)
┌─────────────────┐
│ Approved/       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LinkedIn API    │─── python linkedin_api_poster.py
│ Poster          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Done/           │─── Post published + logged
└─────────────────┘
```

## 📁 File Locations

| File | Purpose | Location |
|------|---------|----------|
| `linkedin_api_poster.py` | Main posting script | `scripts/` |
| `.env` | LinkedIn credentials | Project root |
| `linkedin_api_*.log` | Daily API logs | `AI_Employee_Vault/Logs/` |
| `linkedin_posts.jsonl` | Post audit trail | `AI_Employee_Vault/Logs/` |

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `LINKEDIN_ACCESS_TOKEN not found` | Check `.env` file exists and has correct format |
| `Invalid access token` | Token expired - generate new one from LinkedIn Developer |
| `Insufficient permissions` | Make sure `w_member_social` scope is selected |
| `Person URN not found` | Run `--get-urn` command to retrieve your URN |
| `Post created but not visible` | Check LinkedIn profile → Activity, may be under review |
| `Rate limit exceeded` | Wait 24 hours, max 200 posts per day |

### Debug Commands

```bash
# Test connection
python scripts/linkedin_api_poster.py --test

# Get Person URN
python scripts/linkedin_api_poster.py --get-urn

# Show setup help
python scripts/linkedin_api_poster.py --setup

# Check logs
cat AI_Employee_Vault/Logs/linkedin_api_*.log
```

## ✅ Best Practices

1. **Post Timing**: Post during business hours (9 AM - 5 PM weekdays)
2. **Hashtags**: Use 3-5 relevant hashtags per post
3. **Content Length**: Keep posts under 1,300 characters for optimal engagement
4. **Visuals**: Include images when possible (future enhancement)
5. **Engagement**: Respond to comments within 24 hours
6. **Frequency**: Post 2-3 times per week maximum
7. **Review**: Always use HITL approval for external posts
8. **Monitor**: Check logs after each post

## 🔗 API Reference

### Endpoints

- **Create Post**: `POST https://api.linkedin.com/rest/posts`
- **Get User Info**: `GET https://api.linkedin.com/v2/userinfo`

### Required Headers

```
Authorization: Bearer {ACCESS_TOKEN}
X-Restli-Protocol-Version: 2.0.0
Linkedin-Version: 202502
Content-Type: application/json
```

### Rate Limits

| Limit | Value |
|-------|-------|
| Posts per day | 200 |
| Posts per month | 5,000 |
| Text max length | 3,000 chars |

## 📚 Resources

- [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
- [Posts API Documentation](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Setup Guide](../../LINKEDIN_API_SETUP_GUIDE.md)
- [API Terms of Use](https://www.linkedin.com/legal/api/terms-of-use)

## 🎯 Example Session

```bash
# 1. Setup (first time only)
python scripts/linkedin_api_poster.py --setup

# 2. Test connection
python scripts/linkedin_api_poster.py --test
✅ Connection successful! Person URN: urn:li:person:ABC123

# 3. Create test post
python scripts/linkedin_api_poster.py \
  --content "Testing LinkedIn integration! 🚀" \
  --hashtags "AI,Automation,Testing"

✅ Post published successfully!
Post ID: urn:li:share:123456789
```

---

*LinkedIn Poster Skill v2.0 - Using Official LinkedIn API*
