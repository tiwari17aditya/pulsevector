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

## Packup Command Sign-Off Checklist
When the user triggers "packup" or "/packup", the agent must execute the following operations before signing off:
- Stage, commit, and push all modifications to the remote repository (`git push origin main`).
- Update all session-related trackers, walkthroughs, and logs (e.g. `Research/developer_token_usage.md` and `walkthrough.md`).
- Document proposed enhancements or next steps for subsequent sessions.
- Review and update the domain skills in `.agent/skills/` if necessary to maintain code standards and optimize token usage.
