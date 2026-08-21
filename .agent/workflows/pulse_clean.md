---
description: Scan workspace for junk/temporary artifacts, review suggestions, and clean disk space safely
---

# Pulse Vector Workspace Cleanup & Optimizer

Audit the workspace for obsolete files, temporary render frames, old logs, and scratch scripts, and reclaim disk space.

## Step 1: Scan Workspace for Cleanup Candidates (Read-Only)
// turbo
Run the scanner to identify disposable items and review reclaimed space estimates:
```powershell
python scripts/cleanup_workspace.py --scan
```

## Step 2: Execute Workspace Cleanup
// turbo
Safely delete temporary artifacts, intermediate TTS frames, old logs, and scratch folders:
```powershell
python scripts/cleanup_workspace.py --clean
```

## Step 3: Check Current Project Footprint
Verify the total remaining workspace size:
```powershell
python -c "import pathlib; root = pathlib.Path('.'); total = sum(f.stat().st_size for f in root.glob('**/*') if f.is_file() and '.venv' not in f.parts); print(f'Active Workspace Size (excl .venv): {total / (1024*1024):.2f} MB')"
```
