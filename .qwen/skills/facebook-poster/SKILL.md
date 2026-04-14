# Facebook Poster Skill

**Version:** 1.0.0  
**Type:** Gold Tier  
**Domain:** Social Media Marketing

---

## 📋 Overview

This skill enables the AI Employee to post to Facebook Pages and Instagram Business accounts via the Graph API.

**Capabilities:**
- Post text, photos, and links to Facebook Pages
- Post images to Instagram Business accounts
- Schedule posts for future publishing
- Track engagement and performance
- Cross-post to both platforms

---

## 🎯 Use Cases

### 1. Business Updates
- Product launches
- Company news
- Event announcements
- Promotional content

### 2. Content Marketing
- Blog post shares
- Video content
- Image galleries
- Customer testimonials

### 3. Engagement
- Respond to comments (with approval)
- Share user-generated content
- Community management

---

## 🔧 Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Facebook Configuration
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_PAGE_ACCESS_TOKEN=your_long_lived_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram Configuration (optional)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_business_id
```

### Required Permissions

- `pages_manage_posts`
- `pages_read_engagement`
- `instagram_basic`
- `instagram_content_publish`

---

## 📖 Usage Examples

### Post to Facebook

```markdown
Post this update to our Facebook Page:

"Exciting news! We're launching our new AI-powered service next week. 
Stay tuned for more details! 🚀"

Hashtags: AI, Launch, Innovation
```

**Expected Output:**
```
✅ Facebook post published!
   Post ID: 123456789_987654321
   Permalink: https://www.facebook.com/123456789/posts/987654321
```

---

### Post Photo to Facebook

```markdown
Share this photo to Facebook with the caption:

"Behind the scenes at our office! Our team working hard on the next big thing. 💼"

Photo path: ./office_photo.jpg
Hashtags: TeamWork, BehindTheScenes, CompanyCulture
```

---

### Post to Instagram

```markdown
Post this image to Instagram:

Caption: "Golden hour at the office ✨"
Media path: ./golden_hour.jpg
Hashtags: OfficeLife, GoldenHour, WorkVibes
Share to Facebook feed: Yes
```

**Expected Output:**
```
✅ Instagram post published!
   Post ID: 17841400123456789
   Permalink: https://www.instagram.com/p/ABC123DEF45/
```

---

### Schedule Post

```markdown
Schedule this post for tomorrow at 10 AM:

"Good morning! Start your day with positivity. ☀️"

Scheduled time: 2026-03-03T10:00:00Z
Platform: Facebook
```

---

## 🔄 Workflow Integration

### Standard Posting Workflow

```
1. AI generates post content
2. Checks Company Handbook for rules
3. Creates approval request in /Pending_Approval
4. Human reviews and approves (moves to /Approved)
5. AI posts to Facebook/Instagram
6. Logs action to audit logs
7. Moves to /Done folder
```

### Approval Rules Example

```markdown
## Company Handbook - Social Media Rules

### Auto-Approve (no human review needed)
- Scheduled posts that were previously approved
- Re-posts of company blog articles
- Standard business updates (< $100 ad spend implication)

### Require Approval
- First-time posts to new platforms
- Posts mentioning pricing or promotions
- Responses to customer comments
- Posts with ad spend > $100
- Controversial topics
```

---

## 📁 File Structure

```
AI_Employee_Vault/
├── Pending_Approval/
│   └── FACEBOOK_POST_Launch_2026-03-02.md
├── Approved/
│   └── FACEBOOK_POST_Launch_2026-03-02.md
├── Done/
│   └── FACEBOOK_POST_Launch_2026-03-02.md
└── Logs/
    └── facebook_posts.jsonl
```

---

## 🛡️ Security & Approval

### When to Request Approval

| Scenario | Action |
|----------|--------|
| Regular business update | ✅ Auto-approve |
| First post to Instagram | ✅ Request approval |
| Post with ad spend mention | ✅ Request approval |
| Response to negative comment | ✅ Request approval |
| Promotional/discount post | ✅ Request approval |
| Political/controversial topic | ✅ Request approval |

### Approval File Template

```markdown
---
type: approval_request
action: facebook_post
platform: facebook
content: "Your post content here..."
scheduled_time: 2026-03-05T10:00:00Z
hashtags: "AI,Business,Growth"
created: 2026-03-02T14:30:00Z
expires: 2026-03-03T14:30:00Z
status: pending
---

## Post Details
- Platform: Facebook Page
- Content: "Your post content here..."
- Hashtags: #AI #Business #Growth
- Scheduled: March 5, 2026 at 10:00 AM

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder with reason.
```

---

## 📊 Logging & Analytics

### Log Entry Format

```json
{
  "timestamp": "2026-03-02T14:30:00Z",
  "log_id": "fb_20260302143000",
  "action_type": "facebook_post",
  "actor": "ai_employee",
  "parameters": {
    "message": "Post content here...",
    "platform": "facebook",
    "hashtags": ["AI", "Business"]
  },
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success",
  "post_id": "123456789_987654321"
}
```

### Performance Tracking

The AI Employee can track:
- Post engagement (likes, comments, shares)
- Reach and impressions
- Best posting times
- Content performance trends

---

## 🐛 Troubleshooting

### Token Expired

```
❌ Facebook API Error: Invalid OAuth access token
```

**Solution:**
1. Generate new long-lived token
2. Update `.env` file
3. Test connection: `python scripts/facebook_graph_poster.py --test-connection`

---

### Missing Permissions

```
❌ Facebook API Error: Missing permissions
```

**Solution:**
1. Check token has required permissions
2. Re-authorize with all permissions
3. For production, submit for App Review

---

### Instagram Not Connected

```
❌ Instagram Business Account ID not set
```

**Solution:**
1. Connect Instagram to Facebook Page
2. Get Instagram Business Account ID
3. Add to `.env` file

---

## 📈 Best Practices

### Content Guidelines

1. **Keep it professional** - Represent your brand well
2. **Use visuals** - Posts with images get 2.3x more engagement
3. **Optimal length** - 40-80 characters for Facebook
4. **Hashtag strategy** - 3-5 relevant hashtags
5. **Posting frequency** - 1-2 times per day maximum

### Timing

- **Facebook:** Best times are Wed-Fri, 9 AM - 1 PM
- **Instagram:** Best times are Mon-Fri, 11 AM - 2 PM
- Use insights to find your audience's active hours

### Engagement

- Respond to comments within 24 hours
- Like and reply to meaningful comments
- Share user-generated content (with permission)
- Monitor sentiment and adjust strategy

---

## 🧪 Testing

### Test Connection

```bash
python scripts/facebook_graph_poster.py --test-connection --page-id $FACEBOOK_PAGE_ID
```

### Test Post (Dry Run)

```bash
python scripts/facebook_graph_poster.py \
  --content "Test post from AI Employee" \
  --page-id $FACEBOOK_PAGE_ID \
  --dry-run
```

### Test Instagram

```bash
python scripts/facebook_graph_poster.py \
  --content "Instagram test" \
  --instagram \
  --media-path ./test.jpg \
  --dry-run
```

---

## 📚 API Reference

### Facebook Graph API Endpoints

```
POST /{page-id}/feed - Create text/link post
POST /{page-id}/photos - Create photo post
GET  /{page-id}/posts - Get page posts
GET  /{post-id} - Get post details
GET  /{page-id}/insights - Get page analytics
```

### Instagram Graph API Endpoints

```
POST /{ig-account-id}/media - Create media container
POST /{ig-account-id}/media_publish - Publish media
GET  /{ig-account-id}/media - Get media items
GET  /{media-id} - Get media details
```

---

## 🎯 Integration Examples

### With CEO Briefing

```markdown
## Weekly Social Media Report

### Facebook Performance
- Posts this week: 5
- Total reach: 12,450
- Engagement rate: 3.2%
- Top post: "Product Launch" (520 likes)

### Instagram Performance
- Posts this week: 3
- New followers: +45
- Average likes: 234
- Best performing hashtag: #AI

### Recommendations
- Post more video content (2x engagement)
- Best time to post: Tuesday 11 AM
- Consider Instagram Stories for behind-the-scenes
```

### With LinkedIn Integration

Cross-post strategy:
- LinkedIn: Professional, long-form content
- Facebook: Community updates, events
- Instagram: Visual, behind-the-scenes

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial Gold Tier implementation |

---

*Facebook Poster Skill - Part of AI Employee Gold Tier*
