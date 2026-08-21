"""
Pulse Vector - Workspace Cleaner & Storage Optimizer
Scans workspace for temporary artifacts, old logs, orphan renders, and scratch files,
providing actionable disk cleanup recommendations and one-command pruning.
"""

import os
import sys
import shutil
import argparse
import datetime
import pathlib
from typing import List, Dict, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def get_dir_size(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

def scan_workspace(root_dir: pathlib.Path = pathlib.Path(".")) -> Dict[str, List[Tuple[pathlib.Path, int, str]]]:
    """Scans for temporary or obsolete files and folders."""
    candidates = {
        "scratch": [],
        "temp_frames": [],
        "old_logs": [],
        "orphan_samples": [],
        "cache": []
    }
    
    # 1. Scratch directories
    scratch_dir = root_dir / "scratch"
    if scratch_dir.exists():
        size = get_dir_size(scratch_dir)
        candidates["scratch"].append((scratch_dir, size, "Temporary test outputs & scratch scripts"))
        
    # 2. Residual temp frames & TTS artifacts
    for temp_dir in root_dir.glob("**/temp_end_frames"):
        if temp_dir.exists():
            size = get_dir_size(temp_dir)
            candidates["temp_frames"].append((temp_dir, size, "Auto-regenerated video outro animation frames"))
            
    for tts_dir in root_dir.glob("**/tts_temp"):
        if tts_dir.exists():
            size = get_dir_size(tts_dir)
            candidates["temp_frames"].append((tts_dir, size, "Intermediate TTS voiceover segment WAV/MP3 files"))
            
    # 3. Old logs (> 7 days)
    logs_dir = root_dir / "logs"
    if logs_dir.exists():
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
        for log_f in logs_dir.glob("*.log"):
            try:
                mtime = datetime.datetime.fromtimestamp(log_f.stat().st_mtime)
                if mtime < cutoff_date or log_f.name == "old.log":
                    candidates["old_logs"].append((log_f, log_f.stat().st_size, f"Log from {mtime.strftime('%Y-%m-%d')}"))
            except Exception:
                pass
                
    # 4. Pycache directories
    for pycache in root_dir.glob("**/__pycache__"):
        if pycache.exists() and ".venv" not in pycache.parts:
            size = get_dir_size(pycache)
            candidates["cache"].append((pycache, size, "Python bytecode cache"))
            
    # 5. Obsolete sample test video renders
    sample_videos = root_dir / "samples" / "Videos"
    if sample_videos.exists():
        size = get_dir_size(sample_videos)
        candidates["orphan_samples"].append((sample_videos, size, "Historical POC video test exports"))
        
    return candidates

def clean_candidates(candidates: Dict[str, List[Tuple[pathlib.Path, int, str]]]) -> int:
    total_reclaimed = 0
    for category, items in candidates.items():
        for path, size, desc in items:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                total_reclaimed += size
                print(f"🗑️ Deleted [{category}]: {path} ({size / 1024:.1f} KB)")
            except Exception as e:
                print(f"⚠️ Failed to remove {path}: {e}")
    return total_reclaimed

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Workspace Storage Optimizer")
    parser.add_argument("--clean", action="store_true", help="Execute cleanup and delete identified junk items")
    parser.add_argument("--scan", action="store_true", help="Only scan and display suggestions without deleting")
    args = parser.parse_args()
    
    print("==========================================================")
    print("  🧹 PULSE VECTOR WORKSPACE STORAGE & CLEANUP MONITOR    ")
    print("==========================================================")
    
    candidates = scan_workspace()
    total_junk_bytes = sum(sum(item[1] for item in items) for items in candidates.values())
    
    item_count = sum(len(items) for items in candidates.values())
    
    if item_count == 0:
        print("✨ Workspace is clean! No obsolete or temporary junk files found.")
        print("==========================================================")
        return
        
    print(f"Found {item_count} disposable items totaling {total_junk_bytes / (1024*1024):.2f} MB:\n")
    for category, items in candidates.items():
        if not items:
            continue
        cat_size = sum(i[1] for i in items)
        print(f"📂 {category.upper()} ({cat_size / (1024*1024):.2f} MB):")
        for path, size, desc in items:
            print(f"   • {path} ({size / (1024*1024):.2f} MB) — {desc}")
        print()
        
    if args.clean:
        print("🚀 Executing cleanup...")
        reclaimed = clean_candidates(candidates)
        print("==========================================================")
        print(f"🎉 Cleanup complete! Reclaimed {reclaimed / (1024*1024):.2f} MB.")
        print("==========================================================")
    else:
        print("💡 Suggestion: Run 'python scripts/cleanup_workspace.py --clean' or trigger '/pulse_clean' to reclaim this space.")
        print("==========================================================")

if __name__ == "__main__":
    main()
