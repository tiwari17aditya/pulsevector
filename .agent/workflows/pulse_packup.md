---
description: Run the unified master packup workflow triggering all skills, diagnostics, test suites, workspace cleanup, and remote git synchronization
---

# Pulse Vector Unified Packup & Sign-Off Workflow

Execute the master sign-off engine that triggers all slash workflows, verifies all domain skills, reclaims disk space, and synchronizes with the remote GitHub repository.

## Step 1: Run Unified Packup Pipeline
// turbo
Run the automated orchestrator covering diagnostics, structure, tests, cleanups, and skills:
```powershell
python scripts/packup_pipeline.py
```

## Step 2: What This Master Slash Command Executes
When triggered via `/packup` or `/pulse_packup`, the engine executes:
1. **`/pulse_monitor`**: Full health diagnostics across Gemini API, Edge-TTS, FFmpeg, YouTube OAuth, Supabase Cloud DB, and archive storage.
2. **`/pulse_structure`**: Asset integrity validation for fonts (`fonts/`), audio library (`samples/Audio/`), and archive hierarchy (`pulse_archive/`).
3. **`/pulse_test`**: Complete 20-point automated test suite covering parsers, slide renderers, karaoke subtitle overlays, multi-track audio, and pipeline dry-runs.
4. **`/pulse_clean`**: Workspace optimizer safely purging intermediate TTS frames, obsolete outro frames, temporary scratch scripts, and Python bytecode caches.
5. **Domain Skills Audit**: Automated integrity verification across all 6 skills in `.agent/skills/`:
   - `content-gen` (Gemini API & Prompts)
   - `media-rendering` (Pillow slides, MoviePy/FFmpeg, Edge-TTS)
   - `youtube-dist` (YouTube Data API v3 & Quota)
   - `cloud-db` (Supabase Cloud PostgreSQL)
   - `pipeline-git` (CLI engine & Git Automation)
   - `clean-optimizer` (Storage & Workspace Cleanup)
6. **Remote Git Push**: Verifies `git status`, auto-stages any pending changes, creates sign-off commit, and pushes to `origin main`.

## Step 3: Verify Sign-Off Scorecard
Ensure the final summary prints:
```text
🎉 ALL WORKFLOWS, SKILLS & TESTS PASSED! Safe to sign off.
```
