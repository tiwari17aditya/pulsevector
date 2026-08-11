---
name: youtube-dist
description: Domain skill for YouTube Data API v3 uploads, OAuth authentication, video metadata, and API quota management.
---

# YouTube API & Distribution Domain Skill

## Scope & Target Files
- `src/core/youtube_utils.py`
- `POC/youtube_upload_poc.py`
- `credentials/*`
- `Research/youtube_quota_log.md`
- `Research/youtube_upload_details.md`

## Instructions & Core Operations
1. **Video Upload Metadata**:
   - YouTube Category: `27` (Education).
   - Related Video linkage: Link Daily Shorts to the latest Weekly Masterclass or previous Daily episode.
   - Pinned Comment: Post standard engagement pinned comment immediately following successful upload.
2. **Quota & Usage Management**:
   - Daily Query Quota: 10,000 units max.
   - Daily Upload Limit: 100 videos max.
   - Log daily usage and remaining units after every upload turn in `Research/youtube_quota_log.md`.
3. **Upload Log Tracking**:
   - Record video ID, title, URL, upload timestamp, category ID, and pinned comment status in `Research/youtube_upload_details.md`.

## Domain Constraints
- Never expose OAuth client secret or user refresh tokens in git-tracked code files.
- Halt upload attempts immediately if daily YouTube quota is exhausted.

## Verification Checklist
- [ ] Verify `credentials/client_secrets.json` and `credentials/token.json` exist.
- [ ] Confirm remaining YouTube API quota in `Research/youtube_quota_log.md` before initiating uploads.
- [ ] Verify upload log entry appended to `Research/youtube_upload_details.md` after upload.
