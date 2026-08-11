---
name: pipeline-git
description: Domain skill for pipeline orchestration CLI, date-based archive sorting, Git automation, and token usage logging.
---

# Pipeline Orchestration & Git Automation Domain Skill

## Scope & Target Files
- `src/pipeline.py`
- `src/core/git_backup_utils.py`
- `scripts/clean_local_archive.py`
- `scripts/reauthenticate.py`
- `scripts/run_daily.bat`
- `Research/developer_token_usage.md`
- `pulse_archive/`

## Instructions & Core Operations
1. **CLI Pipeline Orchestration**:
   - `python src/pipeline.py --all`: Execute full pipeline flow.
   - `python src/pipeline.py --generate`: Content generation stage only.
   - `python src/pipeline.py --archive`: Move raw `incoming_data/` files into date hierarchy (`pulse_archive/[Year]/[Month]/[Category]/`).
   - `python src/pipeline.py --git`: Run Git status, commit, and push automatically.
   - `python src/pipeline.py --backup`: Sync archive to backup location.
2. **Developer Token Usage Tracking**:
   - In every turn, estimate token consumption (~4 chars per token).
   - Append log entry to `Research/developer_token_usage.md` with turn timestamp and estimated token usage.
3. **Structured Archive Organization**:
   - Enforce date-based hierarchy: `pulse_archive/[Year]/[Month Name]/Daily/` (or `Weekly/`, `Monthly/`, `Brain_Teasers/`).

## Domain Constraints
- Commit tracked metadata files cleanly after every render/compile run.
- Do not commit secure credential files (`credentials/*.json`) or `.env`.

## Verification Checklist
- [ ] Test CLI flags (`--help`, `--list-models`).
- [ ] Verify `pulse_archive/` file path structure matching target date.
- [ ] Check token usage log formatting in `Research/developer_token_usage.md`.
