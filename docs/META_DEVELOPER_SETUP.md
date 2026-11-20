# Meta Developer & Instagram Graph API Setup Guide

This guide details how to configure the **Meta Developer Platform** and **Instagram Graph API** to enable automated publishing of Pulse Vector Daily Current Affairs and Brain Teaser vertical videos (`.mp4`) as **Instagram Reels**, as well as daily slide cards as **Instagram Feed Posts**.

---

## 1. Overview & Architecture

Pulse Vector's multi-platform distribution engine broadcasts generated content across YouTube, Telegram, Discord, and now **Instagram Reels / Meta Graph API**.

```mermaid
flowchart TD
    A[Rendered 9:16 Short Video] --> B[Supabase Cloud Storage]
    B -->|Generates Public HTTPS URL| C[Public Media URL]
    C --> D[Meta Graph API Engine src/core/meta_utils.py]
    D -->|Step 1: POST /{ig-user-id}/media| E[Create Media Container]
    E -->|Step 2: GET /{container-id}?fields=status_code| F{Status == FINISHED?}
    F -->|Poll every 5s| F
    F -->|Finished| G[Step 3: POST /{ig-user-id}/media_publish]
    G --> H[Live Instagram Reel Published! 🚀]
```

### Video Requirements for Instagram Reels
- **Aspect Ratio**: `9:16` vertical (`1080x1920` px) — *Native to Pulse Vector*
- **Format**: MP4 container with H.264 video codec + AAC audio codec — *Native to Pulse Vector*
- **Duration**: 3 seconds to 15 minutes (Daily Shorts: ~58s, Brain Teasers: ~25s) — *100% compliant*
- **Hosting**: Accessible via a public HTTPS URL without basic authentication — *Supabase Storage provides permanent public URLs*

---

## 2. Prerequisites

Before interacting with the Meta Graph API, ensure you have:
1. **Instagram Professional Account**:
   - The Instagram account must be switched to **Business** or **Creator** (Personal accounts cannot use the Graph API).
   - Go to Instagram App > Settings & privacy > Account type and tools > Switch to professional account.
2. **Connected Facebook Page**:
   - Meta requires all Instagram Professional accounts to be linked to a Facebook Page.
   - Go to Facebook > Pages > Create or select your Page > Settings > Linked Accounts > Connect Instagram.

---

## 3. Meta Developer Portal Setup (Step-by-Step)

### Step 1: Create a Meta for Developers Account
1. Visit [Meta for Developers](https://developers.facebook.com/).
2. Log in with your Facebook account associated with the connected Facebook Page.
3. Click **Get Started** or **My Apps** > **Create App**.

### Step 2: Configure Your Meta App
1. When prompted for **Use Case**, select **"Other"** (or "Business").
2. Select App Type: **"Business"** (provides access to Instagram Graph API and Pages API).
3. Set your App Display Name: `Pulse Vector Auto-Broadcast`.
4. Enter your contact email and click **Create app**.

### Step 3: Add the Instagram Graph API Product
1. In the App Dashboard, scroll to **Add Products to Your App**.
2. Locate **Instagram Graph API** and click **Set Up**.
3. (Optional) Also add **Facebook Login for Business**.

### Step 4: Generate Access Token in Graph API Explorer
1. Navigate to **Tools** > [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. In the top-right:
   - **Meta App**: Select your newly created app (`Pulse Vector Auto-Broadcast`).
   - **User or Page**: Select `User Token`.
3. In the **Permissions** panel, add the following 4 scopes:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
4. Click **Generate Access Token** and approve the Facebook login dialog.
5. Copy the generated **Short-Lived Access Token**.

### Step 5: Retrieve App ID & App Secret
1. In the left sidebar of the Meta Developer Dashboard, click **App settings** > **Basic**.
2. Note your **App ID**.
3. Click **Show** next to **App secret** and note your **App Secret**.

---

## 4. Automated 60-Day Token Exchange & Verification

Short-lived tokens from Graph API Explorer expire in 1-2 hours. Pulse Vector provides an automated configuration CLI that converts this into a **60-day Long-Lived Token** and auto-detects your **Instagram Account ID**:

```bash
python scripts/setup_meta_auth.py
```

The script will prompt for:
- Meta App ID
- Meta App Secret
- Short-Lived Access Token

It automatically:
1. Exchanges the token for a 60-day Long-Lived Access Token.
2. Queries Meta Graph API `/me/accounts` to find the Facebook Page and its linked `instagram_business_account.id`.
3. Verifies container creation capabilities.
4. Updates your local `.env` file safely with:
   - `META_APP_ID`
   - `META_APP_SECRET`
   - `META_ACCESS_TOKEN`
   - `INSTAGRAM_ACCOUNT_ID`

---

## 5. Environment Variables Specification

Ensure your `.env` contains the following keys:

```ini
# Meta / Instagram Graph API Configuration
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_60_day_long_lived_access_token
INSTAGRAM_ACCOUNT_ID=your_numeric_instagram_business_account_id

# Public Handle / Profile URL (used in description footers)
PULSE_INSTAGRAM_URL=https://www.instagram.com/pulse_vector
```

---

## 6. Token Longevity & Auto-Refresh

- Long-lived tokens last **60 days**.
- To prevent expiration, tokens can be programmatically refreshed before the 60 days elapse using Meta's token refresh endpoint:
  ```
  GET https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={LONG_LIVED_TOKEN}
  ```
- Pulse Vector's `src/core/meta_utils.py` contains built-in token health auditing and refresh routines.

---

## 7. Troubleshooting & Common Pitfalls

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `(#10) Application does not have permission for this action` | Missing permissions on access token | Re-generate token in Graph API Explorer with `instagram_content_publish` and `instagram_basic`. |
| `No Instagram Business Account linked to Page` | Instagram account is Personal or not connected to FB Page | Switch Instagram account to Professional/Business and link it in Facebook Page Settings > Linked Accounts. |
| `Media URL could not be downloaded` | Video URL is not publicly accessible via HTTPS | Verify Supabase Storage bucket is marked Public or use a public CDN URL. |
| `The media is not ready for publishing` | Polling container was published before status `FINISHED` | `meta_utils.py` handles exponential backoff and status polling automatically. |
| `OAuthException: Error validating access token: Session has expired` | 60-day token expired | Re-run `python scripts/setup_meta_auth.py` with a fresh token. |
