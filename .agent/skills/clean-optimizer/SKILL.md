---
name: clean-optimizer
description: Domain skill for workspace storage monitoring, disk cleanup auditing, and removing obsolete artifacts.
---

# Clean Optimizer Skill

This skill governs workspace hygiene, identifying disposable build outputs, temporary TTS/FFmpeg frames, orphan test scripts, and historical logs.

## When to Invoke
- Whenever the user asks to clean up files, optimize disk space, or inspect workspace size.
- At the end of major rendering runs or pipeline debugging sessions.
- Before committing to Git to ensure local scratch/temporary artifacts are not committed.

## Key Actions & Commands
1. **Audit Workspace Storage (Read-Only Scan)**:
   ```powershell
   python scripts/cleanup_workspace.py --scan
   ```
2. **Execute Full Safe Cleanup**:
   ```powershell
   python scripts/cleanup_workspace.py --clean
   ```

## Retained vs Disposable Artifacts Policy
- **Safe to Clean**:
  - `scratch/` (One-off rendering tests and debug experiments)
  - `pulse_archive/**/temp_end_frames/` (Auto-generated animation frames)
  - `pulse_archive/**/tts_temp/` (Intermediate voiceover MP3 slices)
  - `logs/*.log` (Older than 7 days)
  - `**/__pycache__/`
- **Never Delete**:
  - `src/` (Core engine & pipelines)
  - `fonts/` (Font assets)
  - `samples/Audio/` (Background music tracks)
  - `pulse_archive/2026/` (Production archive of formatted text, slides, and final MP4s)
  - `.env` and `credentials/` (Secrets and OAuth credentials)
