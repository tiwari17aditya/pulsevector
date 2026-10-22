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
4. **Playlist Creation & Description Standard**:
   - Never use placeholder or barebones descriptions (e.g., `Collection of...` or `Automated playlist for...`).
   - All current and future playlists (Daily Current Affairs, Weekly Masterclasses, Monthly Roundups, Brain Teasers, and exam collections) must follow the rich, structured format implemented via `generate_playlist_description(title)` in `src/core/youtube_utils.py`:
     - **Daily Current Affairs**: High-yield 60s capsules, multi-domain breakdown (Economy, Defense, Polity, Tech), rapid revision focus for UPSC/SSC/Banking, `@Pulse_vector` channel links, and clean hashtags (`#CurrentAffairs #DailyCurrentAffairs #UPSC #SSCCGL`).
     - **Weekly Masterclasses**: Sunday 7-day analytical masterclass summary, category breakdown, exam depth, and `#WeeklyCurrentAffairs`.
     - **Monthly Masterclasses**: 360° exhaustive monthly roundups, visual infographic synthesis, pre-exam power revision, and `#MonthlyCurrentAffairs`.
     - **Daily Brain Teasers**: Fast-paced logic shorts, CSAT/SSC aptitude practice, step-by-step reasoning, community discussion loop invitation, and `#BrainTeasers #Puzzles`.
   - Every playlist description must include the official channel URL: `https://www.youtube.com/@Pulse_vector` and subscribe CTA.

## Domain Constraints
- Never expose OAuth client secret or user refresh tokens in git-tracked code files.
- Halt upload attempts immediately if daily YouTube quota is exhausted.
- Never create a YouTube playlist with an empty or generic description; always apply the structured description standard.

## Verification Checklist
- [ ] Verify `credentials/client_secrets.json` and `credentials/token.json` exist.
- [ ] Confirm remaining YouTube API quota in `Research/youtube_quota_log.md` before initiating uploads.
- [ ] Verify upload log entry appended to `Research/youtube_upload_details.md` after upload.
- [ ] Verify newly created playlists have rich, structured descriptions containing channel URL, exam targets, and domain hashtags.

