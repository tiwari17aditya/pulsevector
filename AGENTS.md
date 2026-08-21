# Pulse Vector Agent Routing Table

| File Pattern / Task Scope | Skill Trigger | Skill Path |
| :--- | :--- | :--- |
| `src/*_pipeline.py`, `src/core/genai_utils.py`, `content_parser.py` | Content Gen & AI Prompts | `.agent/skills/content-gen/SKILL.md` |
| `src/core/image_utils.py`, `video_utils.py`, `tts_utils.py` | Media & Video Rendering | `.agent/skills/media-rendering/SKILL.md` |
| `src/core/youtube_utils.py`, `credentials/*` | YouTube API & Uploads | `.agent/skills/youtube-dist/SKILL.md` |
| `src/core/database_utils.py`, `scripts/*supabase*` | Supabase Cloud & DB | `.agent/skills/cloud-db/SKILL.md` |
| `src/pipeline.py`, `src/core/pipeline_engine.py`, `git_backup_utils.py` | Pipeline & Git Automation | `.agent/skills/pipeline-git/SKILL.md` |
| `scripts/test_pipeline.py`, `scripts/monitor_health.py` | Testing & Monitoring | `.agent/workflows/pulse_test.md` |
| `scripts/cleanup_workspace.py`, `scratch/*` | Workspace Storage & Cleanup | `.agent/skills/clean-optimizer/SKILL.md` |

## Skill Invocation Rules
- Load ONLY the skill relevant to the target files or action being performed.
- Do NOT load unrelated skills into agent context.

## Continuous Implementation & Testing Directives
- **Immediate Automated Testing**: As soon as any code change, feature, or refactoring is implemented on tracked files, immediately run `python scripts/test_pipeline.py` (or stage dry-runs). Thoroughly report test outcomes and flag any issues, warnings, or regressions right away.
- **Git Push on Modification**: Whenever modifications to tracked files are completed and verified with tests, automatically stage, commit, and push the changes to remote (`git push origin main`) to keep remote CI / GitHub Actions synchronized.

## Available Slash Workflows
- `/pulse_test`: Run full component test suite & dry-runs (`test_pipeline.py`).
- `/pulse_daily`: Generate Daily Current Affairs & Brain Teasers.
- `/pulse_clean`: Audit & clean workspace artifacts safely.
- `/pulse_monitor`: System health diagnostics (APIs, FFmpeg, Supabase, OAuth).
- `/pulse_structure`: Audit asset hierarchy, fonts, audio libraries & archives.

## Packup Command Sign-Off Checklist
When the user triggers "packup" or "/packup", the agent must execute the following operations before signing off:
- Stage, commit, and push all modifications to the remote repository (`git push origin main`).
- Update all session-related trackers, walkthroughs, and logs (e.g. `Research/developer_token_usage.md` and `walkthrough.md`).
- Document proposed enhancements or next steps for subsequent sessions.
- Review and update the domain skills in `.agent/skills/` if necessary to maintain code standards and optimize token usage.
