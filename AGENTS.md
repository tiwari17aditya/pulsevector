# Pulse Vector Agent Routing Table

| File Pattern / Task Scope | Skill Trigger | Skill Path |
| :--- | :--- | :--- |
| `src/*_pipeline.py`, `src/core/genai_utils.py` | Content Gen & AI Prompts | `.agent/skills/content-gen/SKILL.md` |
| `src/core/image_utils.py`, `video_utils.py`, `tts_utils.py` | Media & Video Rendering | `.agent/skills/media-rendering/SKILL.md` |
| `src/core/youtube_utils.py`, `credentials/*` | YouTube API & Uploads | `.agent/skills/youtube-dist/SKILL.md` |
| `src/core/database_utils.py`, `scripts/*supabase*` | Supabase Cloud & DB | `.agent/skills/cloud-db/SKILL.md` |
| `src/pipeline.py`, `src/core/git_backup_utils.py` | Pipeline & Git Automation | `.agent/skills/pipeline-git/SKILL.md` |

## Skill Invocation Rules
- Load ONLY the skill relevant to the target files or action being performed.
- Do NOT load unrelated skills into agent context.
