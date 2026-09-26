# Pulse Vector Agent Routing Table

| File Pattern / Task Scope | Skill Trigger | Skill Path |
| :--- | :--- | :--- |
| `src/*_pipeline.py`, `src/core/genai_utils.py`, `content_parser.py` | Content Gen & AI Prompts | `.agent/skills/content-gen/SKILL.md` |
| `src/core/image_utils.py`, `video_utils.py`, `tts_utils.py` | Media & Video Rendering | `.agent/skills/media-rendering/SKILL.md` |
| `src/core/youtube_utils.py`, `credentials/*` | YouTube API & Uploads | `.agent/skills/youtube-dist/SKILL.md` |
| `src/core/database_utils.py`, `scripts/*supabase*` | Supabase Cloud & DB | `.agent/skills/cloud-db/SKILL.md` |
| `src/pipeline.py`, `src/core/pipeline_engine.py`, `git_backup_utils.py` | Pipeline & Git Automation | `.agent/skills/pipeline-git/SKILL.md` |
| `scripts/test_pipeline.py`, `scripts/monitor_health.py` | Testing & Monitoring | `.agent/workflows/pulse_test.md` |
| `scripts/packup_pipeline.py`, `.agent/workflows/pulse_packup.md` | Master Packup & Orchestration | `.agent/workflows/pulse_packup.md` |

## Skill Invocation Rules
- Load ONLY the skill relevant to the target files or action being performed.
- Do NOT load unrelated skills into agent context.

## Branching Strategy & Environment Segregation
- **Production Branch (`main`)**: Exclusively reserved for stable, verified, production-ready code. Scheduled GitHub Actions (daily news generation, brain teaser uploads, weekly/monthly runs, and report crons) execute strictly on `main`.
- **Active Development Branch (`v<version>-dev`)**: All feature development, refactoring, and experimental code must be created and tested on the version-specific development branch (e.g. `v2.4.2-dev`). Never develop directly on `main`.
- **Milestone Promotion to Main**: Merging from the dev branch into `main` occurs only after all tests pass, stage dry-runs succeed, and milestone sign-off is confirmed.

## Continuous Implementation & Testing Directives
- **Immediate Automated Testing**: As soon as any code change, feature, or refactoring is implemented on tracked files, immediately run `python scripts/test_pipeline.py` (or stage dry-runs). Thoroughly report test outcomes and flag any issues, warnings, or regressions right away.
- **Git Push on Modification**: Whenever modifications to tracked files are completed and verified with tests, automatically stage, commit, and push the changes to the active branch (`git push origin <current-branch>`) to maintain remote synchronization safely.

## Available Slash Workflows
- `/packup` (or `/pulse_packup`): **Unified Master Sign-Off Workflow** (Sequentially triggers `/pulse_monitor`, `/pulse_structure`, `/pulse_test`, `/pulse_clean`, all 6 domain skills audits, and remote git push).
- `/pulse_test`: Run full component test suite & dry-runs (`test_pipeline.py`).
- `/pulse_daily`: Generate Daily Current Affairs & Brain Teasers.
- `/pulse_clean`: Audit & clean workspace artifacts safely.
- `/pulse_monitor`: System health diagnostics (APIs, FFmpeg, Supabase, OAuth).
- `/pulse_structure`: Audit asset hierarchy, fonts, audio libraries & archives.

## Packup Command Sign-Off Checklist
When the user triggers "packup", "/packup", or "/pulse_packup", the agent executes the unified master pipeline `python scripts/packup_pipeline.py` which automatically runs all workflows and verifies all skills:
1. **System Health Diagnostics (`/pulse_monitor`)**: Validates APIs, FFmpeg, OAuth, Supabase, TTS, and storage.
2. **Structure & Asset Hierarchy (`/pulse_structure`)**: Audits fonts, audio library, and archive integrity.
3. **Automated Test Suite (`/pulse_test`)**: Executes all 20 unit tests and pipeline stage dry-runs.
4. **Workspace Storage Cleanup (`/pulse_clean`)**: Safely purges temporary frames, intermediate TTS clips, and cache.
5. **Domain Skills Audit**: Verifies all 6 skills in `.agent/skills/` (`content-gen`, `media-rendering`, `youtube-dist`, `cloud-db`, `pipeline-git`, `clean-optimizer`).
6. **Git Remote Synchronization**: Automatically stages all changes, creates a sign-off commit, and pushes to remote (`git push origin main`).
7. **Session Tracker Log**: Verifies `Research/developer_token_usage.md`, `walkthrough.md`, and prepares sign-off scorecard.
