---
description: Handover full channel execution and maintenance to the Autonomous AI Orchestrator
---

# Pulse Vector Autonomous AI Handover Workflow

This workflow transfers active control of the Pulse Vector production pipeline to the AI agent and autonomous MCP server.

## Step 1: Pre-flight Status & Environment Diagnostics
// turbo
Check system health, API quotas, and execute self-healing:
```powershell
python scripts/run_autonomous_daemon.py --status
```

## Step 2: Validate Autonomous Pipeline (Dry-Run Simulation)
// turbo
Verify all pipeline paths, dependencies, slide templates, and broadcast connections without writing files or spending YouTube API quota:
```powershell
python scripts/run_autonomous_daemon.py --dry-run
```

## Step 3: Run Full Autonomous Production Cycle (Optional / On-Demand)
Execute live daily news generation, brain teaser rendering, video compilation, YouTube upload, social broadcast, and git sync:
```powershell
python scripts/run_autonomous_daemon.py --run-now
```

## Step 4: Schedule Daily Autonomous Run
To run autonomously in the background daily at 08:00 AM IST:
- **Cloud (GitHub Actions)**: Handled by `.github/workflows/pulse_autonomous_orchestrator.yml` (Runs daily at 02:30 UTC / 08:00 AM IST).
- **Local (Windows Task Scheduler)**: Run `scripts\run_autonomous.bat` at 08:00 AM daily.
- **Antigravity Timer**: Use `/schedule` or the agent schedule tool to trigger `/pulse_autonomous` daily.

