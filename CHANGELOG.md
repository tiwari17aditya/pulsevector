# Changelog

All notable changes to the Pulse Vector project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

