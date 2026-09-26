# Pulse Vector Automation Pipeline: Enhancements Roadmap

This document outlines the versioned progression of the automated content creation, rendering, and distribution pipeline for **Pulse Vector**.

---

## 📌 Release Timeline & Features

### 🟢 v1.0.0 - Core Automation Engine (Completed)
* **AI Content Generation**: Dynamic current affairs headlines via Google Search and Gemini API integration (`gemini-2.5-flash`).
* **Slide Generation**: Automatic rendering of glassmorphic mobile slides (`1080x1920` vertical aspect ratio) with custom typography caches.
* **Archiving Database**: Year/Month-partitioned directory sorting for plain texts and image assets.
* **Automation Scheduled Task**: Automated runs via Windows Task Scheduler.

### 🟢 v1.1.0 - YouTube Direct Upload & Audio Overlay (Completed)
* **Slide Compilation**: Dynamic stitch of daily PNG slide images into an MPEG-4 `.mp4` video (each slide displaying for 3 seconds).
* **Automated Audio Library**: Automatic retrieval and storage of 15 open-source background music tracks in `samples/Audio/`.
* **Random Audio Selection**: Picks a random music track daily to add variety to the videos.
* **Audio Muxing**: Combines video and audio streams, reduces music volume to 35%, and adds a smooth 1-second audio fade-out at the end.
* **Video Directory Sorting**: Daily videos are saved under matching month folder under `Daily_Videos` matching the slides hierarchy.
* **OAuth Credentials Caching**: Auto-saved local credentials `token.json` for headless, login-free execution.
* **Strict Verification**: Checks input validity, file sizes, and handles errors cleanly by aborting uploads on failure.

### 🟢 v1.2.0 - Weekly/Monthly Content & Playlist Integration (Completed)
* **Weekly and Monthly Current Affairs Automation**: Extended content generation, slide rendering (Daily: 15 points/3 slides, Weekly: 30 points/6 slides, Monthly: 50 points/10 slides), and video compilation to support Weekly and Monthly current affairs.
* **Dedicated YouTube Playlists**: Automatically creates and manages category-specific YouTube Playlists:
  * Daily -> Quarterly playlists (e.g. `Daily Current Affairs - ( Apr to June )- 2026`).
  * Weekly -> Annual playlists (`Weekly Current Affairs - {Year}`).
  * Monthly -> Annual playlists (`Monthly Current Affairs - {Year}`).
* **Category-Specific Dynamic Covers**: Automatically generates dynamic covers/thumbnails with matching subtitles (`DAILY`, `WEEKLY`, `MONTHLY`) and custom date formatting (date range for weekly, month name/year for monthly).
* **Animated Subscription End Slide**: Automatically generates and appends a 3-second animated slide featuring a shaking/ringing bell vector icon and text fade-in transitions.
* **Logs Optimization**: Deduped and cleaned up legacy root log files.

### 🟢 v1.3.0 - Verified News Sources Integration (Completed)
* **Source Extraction**: Modified the Gemini API prompts to extract and return reputable news citations (e.g. BBC, Reuters, Bloomberg) for each generated point using page URLs from context.
* **Slide Attribution**: Displays a clean "Source: [Publisher]" label at the bottom of each slide/point.
* **Description Attributions**: Automatically structures a list of reference URLs in the YouTube video description matching the headlines.

### 🟢 v1.3.1 - Pipeline Robustness & Bug Fixes (Completed — 2 July 2026)
* **Metadata Bleed Fix**: All three pipelines now strip `YouTube Metadata:` / `Title:` / `Reel Description:` / `Hashtags:` / `Source URLs:` from the file content before running the numbered-point regex. Prevents trailing metadata from bleeding into the last news point's slide text.
* **Google Search Grounding Fallback**: When `googlesearch-python` returns empty results (rate-limited), `generate_content()` now automatically retries using **Gemini's native Google Search grounding tool** (`google_search`). Ensures the LLM always has live web access and generates the full 15 points reliably.
* **YouTube Description Length Cap**: Description parsing now stops at section markers (`Hashtags:`, `Source URLs:`) and is hard-capped at 4950 chars to stay under YouTube's 5000-char API limit — prevents `invalidDescription` upload errors caused by grounding redirect URLs inflating the description.
* **`googlesearch-python` Empty Result Handling**: Pipeline no longer fails silently with 12 points — it falls through to grounding and always produces the correct 15/30/50 points.
* **Per-File Exception Isolation**: All pipeline loops already use `try/except` per file — a single broken historical file (e.g. `daily-28jan-2026_formatted.txt`) no longer raises `ValueError` and aborts the entire slide run; it logs and continues.

### 🟢 v1.4.0 - Automated Brain Teaser Publishing (Completed — 3 July 2026)
* **Goal**: Convert daily brain teaser images into automated videos and publish directly to YouTube.
* **Implementation**:
  * **Video Compilation**: Automated compilation of vertical 1080x1920 H.264 compatible videos with dynamic background animations, custom audio track overlays, and animated progress ring countdowns.
  * **Playlist Integration**: Automated publishing to YouTube with tags, descriptions, and automatic organization inside annual playlists (`Daily Brain Teasers - 2026`).
  * **Dual Scheduling Task**: Structured scheduling via GitHub Actions running twice a day with AM/PM target dates.

### 🟢 v1.5.0 - Dynamic Video Transitions Engine (Completed — 19 July 2026)
* **Goal**: Introduce smooth visual slide transitions (slide_left, zoom_fade, crossfade) between 9:16 vertical glassmorphism cards.
* **Implementation & Validation**:
  * **Transition Engine**: Implemented `create_transition_frames()` and `compile_images_with_transitions()` in `src/core/video_utils.py` supporting high frame-rate 30 FPS dynamic slide motion.
  * **3-Pipeline Integration**: Fully integrated and verified across **Daily**, **Weekly**, and **Monthly** video compilation pipelines (`daily_pipeline.py`, `weekly_pipeline.py`, `monthly_pipeline.py`).
  * **Validated POC**: `scratch/poc_video_transitions.py` & `scratch/test_all_3_pipelines.py` verified outputs.
  * **Private YouTube Test Upload**: Uploaded as private test video (`FAt2h_jFBr0`) without playlist additions and tracked in `youtube_upload_details.md`.

---

### 🟢 v2.0.0 - AI Voiceover / Text-to-Speech & Audio Sync (Completed — 20 July 2026)
* **Goal**: Automated professional neural AI voiceovers reading current affairs summaries, with slide display durations dynamically synced to speech lengths.
* **Implementation & Validation**:
  * **TTS Module (`src/core/tts_utils.py`)**: Synthesizes high-quality neural voiceover (`en-US-ChristopherNeural`) for intro, per-page slides, and outro using `edge-tts` and measures exact per-slide durations via `mutagen`.
  * **3-Pipeline Integration**: Fully integrated into **Daily**, **Weekly**, and **Monthly** video compilation pipelines (`daily_pipeline.py`, `weekly_pipeline.py`, `monthly_pipeline.py`).
  * **Dynamic Slide Sync**: Slide display durations automatically adjust frame-by-frame to match spoken audio length with smooth 30 FPS transitions (`compile_images_with_transitions()`).
  * **Audio Ducking**: Combines foreground voiceover with background music ducked to 10% volume (`merge_audio_video()`).
  * **Shorts Compliance (< 60s)**: Tuned TTS speech rate (`+35%` / `+48%`) for Daily Shorts to ensure full 15-headline coverage stays under 60 seconds (verified 58.30s sample: `samples/Videos/test_synced_short_58s.mp4`).
  * **CLI & Fallback**: Added `--no-tts` flag to `pipeline.py` for silent/backwards-compatible execution.

### 🟢 v2.1.0 - Dynamic Animated "Karaoke" Subtitles (Completed — 4 September 2026)
* **Word Timing Engine**: `compute_word_timings()` extracts word-level speech duration metadata aligned with neural audio pronunciation.
* **Animated Highlight Renderer**: `render_karaoke_subtitle_overlay()` groups words into readable capsules, rendering active words in electric neon yellow/gold with subtle breathing border pulses.

### 🟢 v2.2.0 - Telegram & Discord Community Auto-Broadcast (Completed — 4 September 2026)
* **Multi-Platform Engine**: `broadcast_utils.py` automates daily broadcast of Current Affairs headlines, puzzle cards, and YouTube links.
* **Safe Fallbacks**: Reads `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `DISCORD_WEBHOOK_URL` from `.env`, gracefully skipping when unconfigured.

### 🟢 v2.3.0 - Category Badges & Thematic Styling for Current Affairs (Completed — 4 September 2026)
* **Smart Classifier**: `classify_news_category()` assigns headlines to `DEFENCE` 🛡️, `ECONOMY` 📈, `TECH & AI` 🚀, `GEOPOLITICS` 🌐, `ENVIRONMENT` 🌱, `NATIONAL` 🏛️, or `GLOBAL` 🌍.
* **Editorial Slide Pills**: Renders glowing category micro-pills with domain-specific accent palettes on news slides.

### 🟢 v2.4.1 - Google Drive Storage Consolidation & Thread-Safe Cloud Sync (Completed — September 2026)
* **Single Cloud Directory**: Unified Google Drive storage under canonical folder (`antigravity-projects-storage/pulse-vector`), eliminating duplicate cloud folder collisions (`(1)`).
* **Concurrency Lock**: Added `threading.Lock()` to `find_or_create_folder()` in `gdrive_utils.py` to prevent multi-threaded race conditions during batch uploads.
* **Dual-Sync Prevention**: Serialized cloud sync to prioritize API uploads and eliminate simultaneous disk copy races.

### 🟢 v2.4.2 - Native Video Broadcasting & Universal Social Media Footers (Completed — September 2026)
* **Native Video Uploads to Telegram**: Upgraded `broadcast_telegram()` to stream actual `.mp4` video files via Telegram Bot API `sendVideo` (`supports_streaming=True`, max 50 MB) with safe HTML tag balancing and caption truncation (`truncate_html_caption`).
* **Native Video Attachments to Discord**: Upgraded `broadcast_discord()` to upload `.mp4` video files directly as multipart webhook attachments (max 25 MB) alongside rich embeds.
* **Universal Social Media Block**: Implemented `get_social_links_block()` across YouTube descriptions (plain text), Telegram captions (HTML), and Discord embeds (Markdown). Includes YouTube channel, Telegram community, and Discord server, strictly excluding bot handles and interactive play links.
* **Pipeline Integration**: Connected compiled `video_path` in `stage_youtube_publish` (`pipeline_engine.py`) and `publish_teaser_to_youtube` (`brainteaser_pipeline.py`). Verified with 43/43 automated unit tests.

---

## 🚀 Future Roadmap & Proposals

### 🕒 v2.5.0 - Pulse Vector Operational MCP Server (Direct Next Enhancement)
* **Goal**: Provide an interactive operational control plane for the AI agent in Antigravity IDE using the Model Context Protocol (MCP).
* **Architecture**: Standalone stdio/JSON-RPC MCP server (`pulse-ops-mcp`) exposing dedicated operational tools for the AI assistant:
  * `check_api_quotas`: Live tracking of YouTube Data API quota units consumed (against daily 10,000 limit), Gemini API tokens, and Supabase storage.
  * `query_content_deduplication`: Query Supabase/DuckDB archive to ensure news topics or brain teaser formulas have not been used in the past 90 days.
  * `inspect_render_diagnostics`: Inspect audio-video alignment, karaoke syllable timing ledgers, and FFmpeg output health for any historical date.
  * `trigger_social_broadcast`: On-demand manual broadcast dispatch to Telegram and Discord channels directly from chat.
* **Scope Isolation**: Keeps headless production pipelines (`pipeline.py`, GitHub Actions CI) purely native Python, while empowering the IDE agent with deep tool execution.

### 🕒 v2.6.0 - Generative AI Visual Assets per Headline
* **Goal**: Replace generic background slides with topic-specific AI illustrations.
* **Implementation Plan**:
  * Query Google Imagen or DALL-E 3 API with condensed headline keywords to produce unique per-point backgrounds.

### 🕒 v2.7.0 - Dynamic Analytics Feedback Loop
* **Goal**: Optimize content topics based on historical view/engagement metrics.
* **Implementation Plan**:
  * Fetch analytics (views, watch retention) daily via YouTube Reporting API.
  * Feed historical engagement data back into the Gemini prompt context to prioritize high-performing categories.

### 🕒 v2.8.0 - Interactive Channel Membership Dashboard
* **Goal**: Web portal providing exclusive PDF downloads of current affairs for channel members.
* **Implementation Plan**:
  * Build a React/Next.js frontend authenticated via YouTube Memberships API.
  * Export clean PDF versions of Monthly/Weekly current affairs for members.
