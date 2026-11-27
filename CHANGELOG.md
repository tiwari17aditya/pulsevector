# Changelog

All notable changes to the Pulse Vector project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.15.0] - 2026-11-27

### Added
- **YouTube Studio Upgrade Item 1: Dynamic Archetype-Based Shorts Titles**:
  - Eliminated repetitive static title strings (e.g. `🧩 Genius IQ Puzzle: Find the Missing Value!`) cited by YouTube Studio channel audit.
  - Implemented `generate_dynamic_teaser_title()` in `src/core/content_parser.py` mapping all 9 puzzle archetypes (`grid`, `detective`, `formula`, `scale`, `sequence`, `oddone`, `cipher`, `relations`, `riddle`) to high-curiosity, distinct title pools.
  - Added Slot 2 evening variant support (`slot_num=2`) with distinct evening hooks (`🌙`).
  - Enforced strict mobile viewport clamp (`<= 52` chars including `#Shorts`).
  - Integrated dynamic generator directly into `publish_teaser_to_youtube()` in `src/brainteaser_pipeline.py`.
  - Added unit tests in `scripts/test_pipeline.py` verifying archetype variety, evening prefixes, and length limits (all 99 tests PASS).

- **YouTube Studio Upgrade Item 2: Front-Loaded Hooks & Mobile <=52 Character Title Clamp**:
  - Addressed YouTube Studio algorithm audit finding: titles truncating on mobile devices beyond 45–55 characters with hooks buried behind generic prefixes and filler phrases.
  - Upgraded `optimize_youtube_title()` in `src/core/content_parser.py`:
    - Enforced strict mobile viewport clamp (`<= 52` characters total, including `#Shorts`).
    - Stripped generic series labels and filler prefixes (`Daily Current Affairs:`, `Top 15:`, `Daily News:`, `Pulse Vector:`, `& Top News`, dates in parentheses).
    - Front-loaded punchy curiosity news hooks from lead story headlines with an attention emoji prefix (`🔥`).
    - Ensured clean truncation strictly at word boundaries with zero mid-word cuts.
  - Added unit tests in `scripts/test_pipeline.py` under `TestContentParser` and updated `TestBroadcastDeduplicationLedger` (all 100 tests PASS).

- **YouTube Studio Upgrade Item 3: Shorts Stayed-to-Watch Rate Optimization in First 2s**:
  - Addressed YouTube Shorts algorithm priority: raising channel average stayed-to-watch rate from 23.46% toward 35%+ by eliminating intro lag and dead air.
  - Implemented immediate frame-0 countdown tick audio in `generate_countdown_sfx()` (`src/core/video_utils.py`): ticks now begin instantly at `t = 0.0s` with an accentuated opening click, immediately triggering a live game sensation.
  - Upgraded countdown timer visual in `src/brainteaser_pipeline.py`: implemented dynamic urgency color coding (Electric Cyan -> Amber at <=5s -> Alert Red at <=3s).
  - Shortened voiceover retention hooks to punchy 8-9 word ego-challenges delivered in <= 1.5 seconds at +30% speech rate, and reduced karaoke start offset to 0.05s for instant subtitle pop.
  - Added unit tests in `scripts/test_pipeline.py` verifying frame-0 tick audio amplitude and dynamic countdown color stages (all 101 tests PASS).

- **YouTube Studio Upgrade Item 4: High-Contrast Complementary Thumbnail Overlays**:
  - Capitalized on Browse features (5.29% CTR) and Suggested videos (1.85% CTR) as advised by YouTube Studio audit.
  - Eliminated redundant verbatim title repetition on thumbnail cards in favor of 2–3 high-contrast, bold complementary curiosity words.
  - Implemented `extract_thumbnail_power_hook()` in `src/core/video_utils.py`: dynamically maps headlines to high-contrast topical power hooks (e.g. `🚀 SPACE MISSION / HISTORIC ORBIT`, `⚡ POLICY SHIFT / CABINET CLEARS`, `📈 MARKET ALERT / ECONOMIC SURGE`).
  - Redesigned Daily News thumbnail slide layout with high-contrast hero punch text (72pt–80pt bold) and attention badges.
  - Implemented `generate_brainteaser_thumbnail()` in `src/brainteaser_pipeline.py` rendering high-contrast 1080x1920 thumbnail cards tailored to all 9 archetypes (e.g. `WHO IS LYING? / 95% ACCUSE WRONG`).
  - Added `set_video_thumbnail()` in `src/core/youtube_utils.py` and integrated automated custom thumbnail uploads across both Daily News and Brain Teaser publishing pipelines.
  - Added unit tests in `scripts/test_pipeline.py` verifying hook extraction, thumbnail generation, and API setting (all 104 tests PASS).

## [2.14.0] - 2026-11-25

### Added
- **Gmail Automated Rules, Hierarchical Labels & 1-Click Filter XML**:
  - Audited mailbox via IMAP across 49 folders; uncovered 16 Pulse Vector automated emails sitting raw in the inbox.
  - Implemented hierarchical Gmail labels under `Pulse Vector`: `Pulse Vector/Weekly Reports`, `Pulse Vector/Monthly Reports`, `Pulse Vector/Alerts`, and `Pulse Vector/GitHub Actions`.
  - Built `scripts/organize_gmail_labels.py` to retroactively organize and label all existing and future emails via IMAP.
  - Enforced inbox hygiene by automatically stripping `\Inbox` (Skip Inbox / Archive it) and `\Important` (Never mark as important) from all Pulse Vector automated emails.
  - Generated standard, validated 1-click import XML file `pulse_vector_gmail_filters.xml` configured with `shouldArchive="true"`, `shouldNeverMarkAsImportant="true"`, and `shouldNeverSpam="true"`.
  - Documented setup instructions and maintenance in `docs/GMAIL_FILTER_SETUP.md`.

### Fixed
- **Redundant Daily Current Affairs Broadcasts on Telegram & Discord**:
  - Diagnosed root cause of duplicate/triplicate daily messages: `pulse_daily.yml` (02:25 UTC) and `pulse_autonomous_orchestrator.yml` (02:30 UTC) firing 5 minutes apart, combined with `AutonomousOrchestrator` calling both `trigger_pipeline_stage("daily")` (which uploads and broadcasts) and `trigger_social_broadcast("daily")` (which broadcasts again).
  - Implemented persistent atomic Broadcast Deduplication Ledger (`pulse_archive/broadcast_ledger.json`) tracking sent content types, dates, and target platforms.
  - Implemented strict deduplication gates in `broadcast_daily_content()` (`src/core/broadcast_utils.py`): checks whether Telegram, Discord, Instagram, and Telegram Quiz polls have already been broadcast for the target date before making network calls. If already sent, logs an info message, skips the network request, and marks platform as skipped unless explicit `force=True` is provided.
  - Added YouTube Upload Deduplication Guard to `stage_youtube_publish()` in `src/core/pipeline_engine.py`: queries recent uploads playlist for matching title; reuses existing video ID and skips redundant re-upload when a video is already live.
  - Propagated `force: bool = False` flag across `src/daily_pipeline.py`, `src/mcp_server/tools/broadcast.py`, and `src/core/autonomous_orchestrator.py`.
  - Added 6 new unit tests in `scripts/test_pipeline.py` under `TestBroadcastDeduplicationLedger`, expanding the test suite to **97 tests** (100% passing).

## [2.13.1] - 2026-11-23

### Fixed
- **LLM Apology Note & Metadata Bleed in Current Affairs Points**:
  - Diagnosed critical defect where sparse RSS context caused Gemini to append an apology note (*"Please Note: Due to the limited verified news context..."*) which bled into the final point text along with `---` separators and `**YouTube Metadata:**` headers.
  - Upgraded `strip_metadata_section` in `src/core/content_parser.py` with multi-marker scanning that terminates cleanly at the earliest occurrence of any metadata header (`YouTube Metadata`, `Title:`, `Description:`), horizontal rules (`---`, `***`, `___`), or conversational disclaimers (`Please Note:`, `Disclaimer:`, `Due to the limited...`, `As an AI...`).
  - Added primary source truncation in `extract_news_points`: text is strictly cut at `source_match.end()` (`[Source: ...]`), guaranteeing zero trailing bleed can ever enter point text.
  - Sanitized and regenerated 15 verified points for `daily-22nov-2026_formatted.txt`.
  - Permanently deleted defective 3-point videos (`-OZHguB2JlU`, `MU2TSmm_Hy0`) from YouTube via YouTube Data API v3 and re-uploaded clean 15-point video (`-_GGbkjjBjk`).

### Added
- **Mandatory Pre-Upload Quality & Validation Gate (`validate_content_payload`)**:
  - Implemented strict quality validation in `src/core/content_parser.py` and `src/core/pipeline_engine.py`.
  - Enforced minimum point counts: Daily (>= 15 points), Weekly (>= 15 points), Monthly (>= 50 points).
  - Enforced zero-tolerance scan for conversational phrases (`FORBIDDEN_CONTENT_PHRASES`), forbidding `please note`, `due to the limited`, `cannot generate`, `as an ai`, `i apologize`, etc.
  - Implemented strict gate in `stage_youtube_publish`: if validation fails, the pipeline immediately logs a critical error, raises `ContentValidationError`, and **STRICTLY ABORTS THE UPLOAD**, ensuring defective content can NEVER be published to YouTube.
  - Implemented self-healing retry loop in `stage_generate_text("daily", ...)` that retries with Google Search Grounding if fewer than 15 points are produced.
  - Added 6 new unit tests in `scripts/test_pipeline.py` under `TestQualityGateAndParserBleedPrevention`, expanding test suite to **91 tests** (100% passing).

## [2.13.0] - 2026-11-21

### Added
- **Telegram Native Interactive Quiz Polls (`sendPoll`)**:
  - Implemented `broadcast_telegram_quiz` in `src/core/broadcast_utils.py` utilizing Telegram Bot API `sendPoll` with `type="quiz"`.
  - Configured anonymous voting, instant celebratory confetti animations, real-time answer verification, and educational step-by-step logic hints (`explanation`).
  - Integrated into `src/brainteaser_pipeline.py` inside `publish_teaser_to_youtube`, automatically constructing clean quiz options and correct option indices for every daily brain teaser run.
- **YouTube High-CTR Interactive Challenge Pinned Comments**:
  - Upgraded `format_teaser_challenge_comment` in `src/core/content_parser.py` to automatically include multiple-choice voting options (`[A]`, `[B]`, `[C]`, `[D]`) and explicit community participation calls-to-action.
  - Automatically pinned to every uploaded YouTube Short via `add_video_comment` to drive comment velocity and boost YouTube recommendation rank.
- **Meta Developer Platform & Instagram Graph API Integration**:
  - Implemented modular Meta Graph API client (`src/core/meta_utils.py`) supporting Instagram Reels publishing, single photo publishing, Facebook Page video/photo publishing, 60-day long-lived token exchange (`oauth/access_token`), and auto-discovery of linked Instagram Business Accounts and Page IDs from Facebook Pages (`/me/accounts`).
  - Added interactive developer configuration CLI (`scripts/setup_meta_auth.py`) providing guided token exchange, auto-detection of `INSTAGRAM_ACCOUNT_ID` and `FACEBOOK_PAGE_ID`, connection health testing, and safe `.env` persistence.
  - Upgraded multi-platform community broadcast engine (`src/core/broadcast_utils.py`) with `broadcast_instagram()`, enabling automated distribution of 9:16 Shorts to Instagram Reels alongside Telegram, Discord, and YouTube with fail-open safety.
  - Authored comprehensive documentation in `docs/META_DEVELOPER_SETUP.md` with step-by-step setup walkthrough for developers.facebook.com, permission scopes (`instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`), and troubleshooting tips.
  - Added `.env.example` documenting all configuration keys.
  - Expanded automated test suite in `scripts/test_pipeline.py` to **83 unit tests** (all passing).

## [2.12.1] - 2026-11-12

### Added
- **Multi-Slot Daily Brain Teaser Architecture & Same-Day Question Deduplication**:
  - Engineered dual-slot execution (`slot=1` Morning Edition, `slot=2` Evening Edition) across `src/brainteaser_pipeline.py` and `src/core/genai_utils.py` so each daily trigger circulates a completely unique question.
  - Implemented negative-constraint prompt engineering in `build_brainteaser_prompt` (Rule 9) when generating Slot 2, forbidding repetition of the Slot 1 puzzle statement and enforcing category divergence across the 13 teaser archetypes.
  - Added dedicated asset segregation for Slot 2: `brainteaser-{date}_2.txt`, `poll-{date}_2.txt`, `brainteaser-{date}_2_styled.png`, and `brainteaser-{date}_2.mp4` with distinct curiosity titles (Part 2 / Evening Edition) and retention audio hooks.
  - Added YouTube Upload Deduplication Guard in `publish_teaser_to_youtube` checking recent uploads to eliminate redundant duplicate postings of the same puzzle.
  - Updated `.github/workflows/pulse_brainteaser.yml` with workflow dispatch inputs and slot-aware morning/evening execution flags.
  - Added automated unit tests `test_build_brainteaser_prompt_slot_uniqueness` and `test_brainteaser_slot2_path_and_deduplication` in `scripts/test_pipeline.py`, expanding test suite to 71 tests (all passing).

### Fixed
- **Brain Teaser Card Overflow & Options Clipping**:
  - Diagnosed root cause of clipped options in YouTube Short `_Oeqawy6ILM`: verbose 183-character riddle rendered with static 38pt font wrapped to 8 lines, causing the series box to end at Y=547 and forcing options to Y=642–702 (completely off-canvas on a 656px card).
  - Implemented `compute_adaptive_series_layout` in `src/brainteaser_pipeline.py` to dynamically scale font size (from 38pt down to 18pt) and line spacing, ensuring the series box strictly stays within the safe 210px vertical budget.
  - Implemented hard vertical bounds clamping (`max_allowed_y = 585px`) across `draw_options_standard`, `draw_options_capsule`, and `draw_options_cropped` for both 2x2 grid and vertical list layouts, leaving >= 35px clearance above the watermark.
  - Upgraded all 10 visual layout renderers (`draw_layout_1` through `draw_layout_10`) and fallback plain-path to use adaptive typography.
  - Eradicated `.notdef` emoji glyph tofu (`[X]` box artifacts) from top retention hook badges.
  - Added Rule 8 brevity constraints (<= 120 chars) in `src/core/genai_utils.py`, `.agent/pulse_prompts.md`, and `.agent/workflows/pulse_prompts.md`.
  - Added automated regression test `test_brainteaser_long_series_adaptive_layout_and_bounds` in `scripts/test_pipeline.py`, bringing test suite to 69 tests (all passing).

## [2.12.0] - 2026-11-10

### Added
- **Full Autonomous AI Handover Architecture & Orchestrator Control Plane**:
  - Implemented `AutonomousOrchestrator` (`src/core/autonomous_orchestrator.py`) unifying the 6-phase autonomous cycle:
    1. Operational pre-flight diagnostics and environment auto-healing.
    2. 90-day archive similarity & deduplication screening.
    3. Multi-stage execution (Daily Current Affairs, Brain Teasers, Weekly/Monthly Masterclasses).
    4. Compliance verification (slide asset generation, audio alignment, 60s Shorts limit).
    5. YouTube Data API publishing, pinned comment engagement, and multi-platform broadcasting (Telegram, Discord).
    6. Supabase DB/Storage cloud backup, Google Drive sync, and master packup git remote synchronization.
  - Built `scripts/run_autonomous_daemon.py` and `scripts/run_autonomous.bat` supporting `--run-now`, `--dry-run`, `--status`, and `--cron` operational modes.
  - Added GitHub Actions autonomous cloud workflow `.github/workflows/pulse_autonomous_orchestrator.yml` (scheduled daily at 08:00 AM IST / 02:30 UTC).
- **Expanded Operational MCP Server (`pulse-ops-mcp` v3.0.0)**:
  - Added `trigger_pipeline_stage`: Autonomously execute daily, weekly, monthly, or brainteaser runs with granular stage controls.
  - Added `execute_autonomous_packup`: Automated execution of the 6-phase master packup and remote Git sync.
  - Added `auto_heal_environment`: Self-healing workspace cleaner (purges temp render frames, checks fonts and FFmpeg binaries).
  - Added `query_supabase_ledger`: Read-only safe inspection of Supabase video, summary, and teaser tables.
  - Added `audit_token_and_quota_ledgers`: Real-time YouTube quota ceiling (10,000 units) and developer token consumption auditing.
  - Registered all new tools with standard JSON schemas in `.agent/mcp/pulse-ops/`.
- **Domain Skills & Workflow Integration**:
  - Added `autonomous-orchestrator` domain skill (`.agent/skills/autonomous-orchestrator/SKILL.md`).
  - Added `/pulse_autonomous` slash workflow (`.agent/workflows/pulse_autonomous.md`).
  - Updated `AGENTS.md` and `scripts/packup_pipeline.py` to audit all 7 domain skills.

## [2.11.0] - 2026-11-09

### Added
- **Multi-Archetype Brain Teaser Formatting & Rendering Engine**:
  - Dynamically classifies brain teaser content into 9 specialized archetypes (`grid`, `detective`, `sequence`, `formula`, `scale`, `cipher`, `relations`, `oddone`, `riddle`).
  - Hero visual component rendering:
    - `grid`: 3x3 graphic layout with cell borders, center accent highlights, and monospace digit rendering.
    - `detective`: Dossier-style suspect cards with avatar badges and formatted witness statement bubbles.
    - `sequence`: Number/node flow progression with custom vector transition arrows.
    - `formula`: High-contrast algebraic badge cards with highlighted operator tokens.
  - Category-aware LLM prompt architecture (`build_brainteaser_prompt`) tailored for 5 core genres (Mathematical, Spatial/Grid, Logic/Alibi, Word/Cipher, Pattern/Sequence).
  - Circular letter badge option buttons (`A`, `B`, `C`, `D`) replacing bracketed text across both 2x2 grid and 1-column layouts.
  - Safe margin enforcement ($Y \le 585$px) ensuring 100% zero collision with lower third and options.
  - Master Showcase Video compiling 20 standardized format templates across 5 genres uploaded to YouTube private playlist (`Pulse Vector - Brain Teaser Format Showcase`).
  - Comprehensive Step-by-Step Solution Guide for all prior week brain teasers (Nov 1–9, 2026) archived in `reports/last_week_brain_teaser_solutions.md`.

### Fixed
- **Font Glyph Tofu & Missing Symbol Rendering**:
  - Completely eradicated `.notdef` missing glyph ("box with an X") rendering by eliminating raw Unicode emoji and arrow characters from slide text.
  - Implemented mathematical `draw_vector_arrow()` via PIL polygon graphics for clean, anti-aliased sequence indicators.
  - Stripped square bracket noise `[` `]` from options for a modern, sleek mobile UX.
- **Teaser Parser Option Extraction**:
  - Hardened option regex (`classify_teaser_archetype`, `parse_teaser_content`) to prevent false positives from hashtags or inline text containing bare letters.
  - Added structured parser extraction for suspects, 3x3 grids, and sequence nodes.

## [2.10.0] - 2026-11-08

### Added
- **Dynamic Daily Layout Rotation & Visual Presentation Engine**:
  - Deterministic date-seeded rotation between 4 layouts: `spotlight`, `minimalist`, `inline_tag`, and `split_pane`.
  - Thematic 4K Editorial Backgrounds for all 8 categories (`GEOPOLITICS`, `DEFENCE`, `ECONOMY`, `SCIENCE_TECH`, `CLIMATE_ENERGY`, `NATIONAL`, `SPORTS`, `GLOBAL`), strictly locked to the top headline on each slide.
  - S-curve fluid spotlight glide transition animation for `spotlight` layout.
  - Adda247 educational split-pane layout with framed lead visual box and glassmorphic exam point capsule.
  - Centered single-digit number badges (`1`, `2`, `3`...) vertically aligned with point text.
  - Clean slide cards with complete category pill clutter removal.
  - Minimalist header and footer (`Page X of Y`), with all approach labels removed.
  - Relocated source citations cleanly into YouTube description under `🔗 VERIFIED SOURCES & COVERAGE:`.
  - Applicable across all current affairs video pipelines: **Daily Shorts**, **Weekly Masterclasses**, and **Monthly Editions**.

### Fixed
- **Daily CI Pipeline Timeout & Crash Resolution**:
  - Eliminated unbounded $O(N)$ archive traversal in `stage_generate_teasers()` and `generate_daily_slides()`. Added fast paths targeting the specific active date.
  - Resolved synthetic audio bottleneck in `download_audio_library()`: tracked 3 baseline tracks in `samples/Audio/` and streamlined synthesis fallback to 3 60-second tracks ($< 2$s).
  - Hardened `resolve_gdrive_endcredits_dir()` and `BACKUP_DIR` for POSIX/Linux runners, preventing invalid Windows drive letter leakage (`G:\`) into Linux CI runs.
  - Added `.gitignore` safety guards against literal Windows drive path tracking.
  - Implemented fail-open video compilation fallback in `stage_compile_video()`: if outro attachment encounters an issue, the pipeline falls back to the main video rather than crashing.
- **Test Suite Overhaul (`scripts/test_pipeline.py`)**:
  - Expanded automated test suite from 57 to 63 tests (100% pass rate).
  - Replaced dry-run stubs with real-execution integration tests: actual PIL slide rendering $(1080 \times 1920)$, fast-path timing assertion ($< 1.5$s), instant audio resolution, cross-platform path safety, and compilation fallback verification.

## [2.9.0] - 2026-11-01

### Added
- **Finalized 5 Outro Archetypes (`OutroVideoEngine`)**:
  - `vox`: Kinetic split layout with sliding interactive containers ("Watch Next" & "Series Playlist") and animated triad dock.
  - `mrbeast`: High-energy studio with oversized golden bell tower and radial soundwave shockwaves.
  - `thinkschool`: Academic study capsule resource dock and verified community count.
  - `kurzgesagt`: Cosmic flat-art starfield with wobbling ringed planet and candy buttons.
  - `veritasium`: Algorithmic retention question loop with pinned comment challenge.
- **Full Animated Like, Share & Subscribe Triad**:
  - Implemented button physics using LastDayOnEarth mathematical easing (`scale = 1.0 + 0.16 * sin(...)`).
  - Animated cursor and cartoon pointer glove motion paths.
  - State transformations (`SMASH LIKE!` -> `LIKED!`, `SHARE` -> `SHARED!`, `SUBSCRIBE` -> `SUBSCRIBED!`).
  - Synchronized high-pitch 1760Hz bell chime SFX mixed over background music.
- **Dynamic Context Parameter Injection**:
  - Conditional handling for `next_video_title`, `playlist_title`, `telegram_handle`, and `question_text`.
  - Automated string truncation and graceful fallback defaults.
- **Random Outro Rotation Dispatcher**:
  - `OutroVideoEngine.get_random_outro_channel()` and `render_dynamic_outro()` to prevent audience visual fatigue and perform continuous algorithmic A/B testing.
- **Widescreen 16:9 Video Concatenation & YouTube Upload Tool**:
  - `scripts/upload_random_outro_test.py`: Automatically converts vertical briefings to 16:9 with ambient blurred background, stitches random outro, and uploads to YouTube marked strictly as `private`.
  - Successfully verified live test upload: Video ID `AseNycCHV-k` (`privacyStatus="private"`).
- **Interactive Theater HTML**:
  - `scripts/build_video_theater.py`: Generates responsive video theater player featuring the 5 finalists with embedded base64 videos and posters.

### Changed
- Pruned non-selected outro archetypes (`mkbhd`, `aliabdaal`, `oversimplified`, `caspian`, `lemmino`) across scripts, engine, tests, posters, and UI artifacts.
- Synchronized YouTube upload details log (`Research/youtube_upload_details.md`) and quota usage log (`Research/youtube_quota_log.md`).

## [2.8.0] - 2026-10-31
- Initial exploration of 10 YouTube outro scenes.

## [2.7.0] - 2026-10-23
- Automated daily/weekly/monthly pipeline stabilization and GitHub Secrets synchronization.

