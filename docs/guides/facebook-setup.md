# Facebook & Instagram Setup Guide

**Facebook Graph API Integration for Social Media Posting**

This guide covers complete Facebook and Instagram Business setup for automated posting.

---

## 📋 What You'll Set Up

- ✅ Facebook Developer App
- ✅ Page Access Token (long-lived)
- ✅ Facebook Page posting
- ✅ Instagram Business posting (optional)

---

## 🚀 Step-by-Step Setup

### Step 1: Create Facebook App

1. **Go to [Facebook Developers](https://developers.facebook.com/)**
2. **Click "My Apps" → "Create App"**
3. **Select use case:** "Other" → "Next"
4. **Select app type:** "Business" → "Next"
5. **Fill in:**
   - App Name: `AI Employee Social Media`
   - App Contact Email: your-email@example.com
6. **Click "Create App"**

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
6. **Click "Generate Token"**
7. **Copy the Access Token**

#### For Production (Long-lived Token):

```bash
# Exchange short-lived for long-lived token
python scripts/facebook_exchange_token.py \
  --app-id YOUR_APP_ID \
  --app-secret YOUR_APP_SECRET \
  --short-token YOUR_SHORT_TOKEN
```

**Long-lived tokens last ~60 days.**

### Step 4: Get Your Page ID

1. **Go to your Facebook Page**
2. **Click "About"**
3. **Find "Facebook Page ID"**

Or use Graph API Explorer:
```
GET /me/accounts
```

### Step 5: Configure .env File

```bash
# Facebook Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your_long_lived_token
FACEBOOK_PAGE_ID=your_page_id
```

### Step 6: Test Connection

```bash
python scripts/facebook_graph_poster.py \
  --test-connection \
  --page-id $FACEBOOK_PAGE_ID
```

**Expected output:**
```
✅ Connected to Facebook Page
   Name: Your Page Name
   Username: @yourpage
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

## 📸 Instagram Business Setup (Optional)

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

## 📝 Usage Examples

### Facebook Text Post

```bash
python scripts/facebook_graph_poster.py \
  --content "Hello from AI Employee! 🤖" \
  --page-id $FACEBOOK_PAGE_ID \
  --hashtags "AI,Automation"
```

### Facebook Photo Post

```bash
python scripts/facebook_graph_poster.py \
  --content "Check out our latest product!" \
  --page-id $FACEBOOK_PAGE_ID \
  --media-path ./photo.jpg \
  --hashtags "Product,Launch"
```

### Scheduled Post

```bash
python scripts/facebook_graph_poster.py \
  --content "Monday motivation!" \
  --page-id $FACEBOOK_PAGE_ID \
  --scheduled-time "2026-03-11T09:00:00Z"
```

---

## 🔐 Security Best Practices

### Token Management

1. **Never commit tokens** to version control
2. **Use environment variables** for all tokens
3. **Rotate tokens regularly** (every 60 days for long-lived)
4. **Monitor token usage** in App Dashboard

### App Review Process

For production use (beyond testing):

1. **Go to App Review in dashboard**
2. **Submit each permission for review:**
   - `pages_manage_posts`
   - `instagram_content_publish`
3. **Provide:**
   - Use case description
   - Screen recording of your app
   - Step-by-step instructions
4. **Wait for approval** (typically 3-7 days)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid access token" | Token expired - generate new long-lived token |
| "Missing permissions" | Re-generate token with all required scopes |
| "Page not found" | Verify Page ID is correct |
| "Instagram account not connected" | Connect Instagram to Facebook Page |
| "Photo upload failed" | Check format (JPG/PNG) and size (< 20MB) |

---

*Facebook & Instagram Setup Guide - Personal AI Employee*
