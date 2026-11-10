---
name: autonomous-orchestrator
description: Domain skill for fully autonomous AI channel operations, self-healing diagnostics, quota budgeting, MCP-driven execution, and scheduled cycle handover.
---

# Autonomous AI Orchestrator Domain Skill

## Scope & Target Files
- `src/core/autonomous_orchestrator.py`
- `scripts/run_autonomous_daemon.py`
- `scripts/run_autonomous.bat`
- `.github/workflows/pulse_autonomous_orchestrator.yml`
- `src/mcp_server/server.py`
- `src/mcp_server/tools/orchestration.py`
- `.agent/mcp/pulse-ops/`

## Autonomous Handover Architecture
This skill enables the AI Agent to autonomously manage Pulse Vector without requiring manual user prompting for daily routines:
1. **Operational Pre-flight**:
   - Call `check_quotas_and_health` and `auto_heal_environment`.
   - Verify that YouTube upload quota has >1,600 units available. If exhausted, degrade gracefully to draft/social broadcast mode without failing the pipeline.
2. **Content Deduplication**:
   - Call `check_content_deduplication` before generating news or puzzles.
   - Enforce 90-day topic and formula separation.
3. **Multi-Stage Execution**:
   - Trigger `trigger_pipeline_stage` for Daily Current Affairs, Brain Teasers, Weekly (Sundays), and Monthly (Month-End).
4. **Compliance & Diagnostics**:
   - Validate slide assets, audio track synchronization, and 60-second YouTube Shorts limits via `get_render_diagnostics`.
5. **Distribution & Broadcasting**:
   - Trigger `dispatch_social_broadcast` for Telegram (@pulsevector_daily) and Discord community.
   - Post interactive pinned engagement comments on YouTube.
   - Backup videos and metadata to Supabase DB/Storage and Google Drive.
6. **Master Packup & Ledger Sync**:
   - Execute `execute_autonomous_packup` to run the 63-point test suite, purge scratch files, audit domain skills, and sync Git to remote.

## Autonomous Commands
- Check real-time operational status:
  ```powershell
  python scripts/run_autonomous_daemon.py --status
  ```
- Run dry-run autonomous simulation:
  ```powershell
  python scripts/run_autonomous_daemon.py --dry-run
  ```
- Trigger immediate live autonomous cycle:
  ```powershell
  python scripts/run_autonomous_daemon.py --run-now
  ```

## Domain Constraints & Directives
- **Zero Accidental Overwrite**: Never overwrite archived content without explicit `--force`.
- **DLP Protection**: Ensure all external payloads pass through `sanitize_and_redact_sensitive_data`.
- **Continuous Remote Sync**: Always push verified changes to the remote branch (`git push origin <current-branch>`).

