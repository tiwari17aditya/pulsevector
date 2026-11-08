# Changelog

All notable changes to the Pulse Vector project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

