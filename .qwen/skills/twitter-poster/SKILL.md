---
name: twitter-poster
description: |
  Post updates to Twitter/X via API v2.
  Supports tweeting with hashtags, scheduling, and weekly summary generation.
  Integrates with the AI Employee system for automated social media posting.
---

# Twitter/X Poster Skill

Post to Twitter/X and generate weekly activity summaries.

## Purpose

Automate Twitter/X posting for the AI Employee system:
- Post tweets with hashtags via API v2
- Generate weekly Twitter summaries
- Audit logging for all tweets
- Dry-run mode for testing

## Setup

### 1. Create Twitter Developer Account

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a Project and App
3. Enable OAuth 2.0
4. Get your credentials

### 2. Configure .env

```bash
# Twitter API v2 Credentials
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

### 3. Test Connection

```bash
py scripts/twitter_poster.py --test-connection
```

## Usage

### Post a Tweet

```bash
# Basic tweet
py scripts/twitter_poster.py --content "Hello Twitter!"

# With hashtags
py scripts/twitter_poster.py --content "Check out my AI Employee" --hashtags "AI,Automation"

# Dry run (test without posting)
py scripts/twitter_poster.py --dry-run --content "Test tweet" --hashtags "Test"
```

### Generate Weekly Summary

```bash
# Generate summary for last 7 days
py scripts/twitter_poster.py --generate-summary --days 7

# Save summary to file
py scripts/twitter_poster.py --generate-summary --days 7 > twitter_summary.md
```

### List Recent Tweets

```bash
# List tweets from last 7 days
py scripts/twitter_poster.py --list-tweets --days 7

# List last 30 days
py scripts/twitter_poster.py --list-tweets --days 30
```

### Process Action File

```bash
# Process tweet from action file
py scripts/twitter_poster.py --action-file path/to/action.md
```

## Integration with AI Employee

The Twitter poster integrates with the AI Employee system via:

1. **Action Files**: Create `.md` files in `Needs_Action/` with tweet content
2. **Audit Logging**: All tweets logged to `Logs/twitter_posts.jsonl`
3. **Weekly Summaries**: Generated alongside other social media summaries
4. **CEO Briefing**: Twitter metrics included in weekly CEO briefings

### Example Action File

```markdown
---
type: twitter_post
created: 2026-04-14T10:00:00Z
status: pending
---

## Tweet Content
content: Excited to share our AI Employee project!

## Hashtags
hashtags: AI,Automation,OpenSource
```

## API Rate Limits

| Action | Limit |
|--------|-------|
| Tweets per day | 300 |
| Tweets per 3-hour window | 300 |
| Characters per tweet | 280 |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No bearer token configured | Add TWITTER_BEARER_TOKEN to .env |
| HTTP 401 | Check token validity, regenerate if needed |
| HTTP 403 | Verify app has write permissions |
| Tweet too long | Content auto-truncated to 280 chars |

## Examples

### Automated Business Update

```bash
py scripts/twitter_poster.py \
  --content "This week our AI Employee processed 21 tasks, posted 5 social updates, and generated 3 CEO briefings. Autonomous business management is here!" \
  --hashtags "AI,Automation,BusinessIntelligence"
```

### Weekly Summary Report

```
# 🐦 Twitter/X Weekly Summary

**Period:** Last 7 days

## 📊 Key Metrics
| Metric | Value |
|--------|-------|
| **Total Tweets** | 5 |
| **Successful** | 5 ✅ |
| **Failed** | 0 |
| **Success Rate** | 100.0% |
| **Tweets/Day** | 0.7 |
```

---

*Twitter/X Poster Skill - AI Employee v1.0.0 (Gold Tier)*
*"Automate your Twitter/X presence"*
