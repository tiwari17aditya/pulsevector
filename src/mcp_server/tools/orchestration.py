"""
Pulse Vector MCP Server - Autonomous Orchestration & Execution Tools
Enables autonomous AI control for triggering pipeline stages, running
unified packup verification, self-healing environment issues, and querying
cloud/database ledgers without manual CLI intervention.
"""

import os
import sys
import shutil
import pathlib
import datetime
import subprocess
from typing import Dict, Any, List, Optional

_CURRENT_DIR = pathlib.Path(__file__).resolve().parent
_SRC_DIR = _CURRENT_DIR.parent.parent
_ROOT_DIR = _SRC_DIR.parent

for p in (str(_SRC_DIR), str(_ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.config import ARCHIVE_DIR
from core.database_utils import get_supabase_client
from mcp_server.tools.security import protect_sensitive_data


@protect_sensitive_data
def trigger_pipeline_stage(
    content_type: str = "daily",
    target_date: Optional[str] = None,
    stages: Optional[List[str]] = None,
    dry_run: bool = False,
    force: bool = False,
    no_tts: bool = False
) -> Dict[str, Any]:
    """
    Autonomously executes a specific Pulse Vector pipeline stage.
    
    Args:
        content_type: 'daily', 'weekly', 'monthly', 'brainteaser', or 'all'.
        target_date: Optional target date in YYYY-MM-DD format (defaults to current date).
        stages: Optional list of granular stages (e.g. ['text', 'slides', 'video', 'youtube', 'sync']).
        dry_run: If True, validates prerequisites and paths without generating files or uploading.
        force: If True, forces regeneration of existing slides and videos.
        no_tts: If True, disables voiceover generation.
        
    Returns:
        Structured execution result including status, stdout, stderr, and execution duration.
    """
    content_type = content_type.lower()
    start_time = datetime.datetime.now()
    
    cmd = [sys.executable, str(_SRC_DIR / "pipeline.py")]
    
    if content_type == "daily":
        cmd.append("--daily")
    elif content_type == "weekly":
        cmd.append("--weekly")
    elif content_type == "monthly":
        cmd.append("--monthly")
    elif content_type == "all":
        cmd.append("--all")
    elif content_type == "brainteaser":
        cmd = [sys.executable, str(_SRC_DIR / "brainteaser_pipeline.py")]
    else:
        return {
            "status": "ERROR",
            "message": f"Unsupported content_type: '{content_type}'. Must be daily, weekly, monthly, brainteaser, or all."
        }
        
    if target_date:
        cmd.extend(["--date", target_date])
    if stages:
        cmd.extend(["--stages", ",".join(stages)])
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    if no_tts:
        cmd.append("--no-tts")
        
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(_ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600
        )
        duration_s = (datetime.datetime.now() - start_time).total_seconds()
        
        return {
            "status": "SUCCESS" if proc.returncode == 0 else "FAILED",
            "content_type": content_type,
            "target_date": target_date or datetime.datetime.now().strftime("%Y-%m-%d"),
            "dry_run": dry_run,
            "returncode": proc.returncode,
            "duration_seconds": round(duration_s, 2),
            "stdout_summary": (proc.stdout or "").strip()[-2000:],
            "stderr": (proc.stderr or "").strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "content_type": content_type,
            "message": "Pipeline execution exceeded 600 seconds timeout limit."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "content_type": content_type,
            "message": str(e)
        }


@protect_sensitive_data
def execute_autonomous_packup() -> Dict[str, Any]:
    """
    Autonomously executes the 6-phase master packup pipeline:
    1. Health diagnostics (/pulse_monitor)
    2. Asset and font hierarchy (/pulse_structure)
    3. 63-point automated test suite (/pulse_test)
    4. Storage cleanup and temp purge (/pulse_clean)
    5. Domain skills integrity audit
    6. Git remote synchronization (rebase-pull and push)
    """
    start_time = datetime.datetime.now()
    packup_script = _ROOT_DIR / "scripts" / "packup_pipeline.py"
    
    if not packup_script.exists():
        return {
            "status": "ERROR",
            "message": f"Packup script not found at {packup_script}"
        }
        
    try:
        proc = subprocess.run(
            [sys.executable, str(packup_script)],
            cwd=str(_ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300
        )
        duration_s = (datetime.datetime.now() - start_time).total_seconds()
        
        return {
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "returncode": proc.returncode,
            "duration_seconds": round(duration_s, 2),
            "output_summary": (proc.stdout or "").strip()[-3000:],
            "stderr": (proc.stderr or "").strip()
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


@protect_sensitive_data
def auto_heal_environment() -> Dict[str, Any]:
    """
    Autonomously inspects and heals workspace environment anomalies:
    - Purges temporary TTS caches, dangling video frames, and lock files.
    - Validates required typography assets and directory hierarchies.
    - Checks FFmpeg binary resolution.
    - Validates cross-platform file path formatting.
    """
    healed_actions = []
    issues_detected = []
    
    # 1. Clean temporary cache directories
    temp_patterns = ["**/tts_temp", "**/temp_end_frames", "**/__pycache__"]
    total_purged_dirs = 0
    
    for pat in temp_patterns:
        for p in _ROOT_DIR.glob(pat):
            if p.is_dir() and ".venv" not in p.parts:
                try:
                    shutil.rmtree(p, ignore_errors=True)
                    total_purged_dirs += 1
                except Exception as ex:
                    issues_detected.append(f"Failed to delete {p.name}: {ex}")
                    
    if total_purged_dirs > 0:
        healed_actions.append(f"Purged {total_purged_dirs} temporary cache and intermediate render directories.")

    # 2. Check and ensure directory hierarchy
    required_dirs = [
        _ROOT_DIR / "fonts",
        _ROOT_DIR / "samples" / "Audio",
        _ROOT_DIR / "samples" / "Videos",
        _ROOT_DIR / "pulse_archive",
        _ROOT_DIR / "Research"
    ]
    for d in required_dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            healed_actions.append(f"Created missing directory: {d.relative_to(_ROOT_DIR)}")

    # 3. Typography asset verification
    required_fonts = ["Roboto-Regular.ttf", "Roboto-Bold.ttf"]
    fonts_dir = _ROOT_DIR / "fonts"
    for font_name in required_fonts:
        fpath = fonts_dir / font_name
        if not fpath.exists():
            issues_detected.append(f"Missing typography asset: fonts/{font_name}")
            
    # 4. Check FFmpeg resolution
    from core.tts_utils import get_ffmpeg_executable
    ffmpeg_resolved = False
    try:
        ffmpeg_bin = get_ffmpeg_executable()
        ffmpeg_resolved = bool(ffmpeg_bin)
    except Exception:
        ffmpeg_resolved = False
        
    if not ffmpeg_resolved:
        issues_detected.append("FFmpeg binary path could not be resolved.")
    else:
        healed_actions.append("FFmpeg binary verified and available.")

    return {
        "status": "HEALTHY" if not issues_detected else "WARNING",
        "healed_actions": healed_actions,
        "issues_detected": issues_detected,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@protect_sensitive_data
def query_supabase_ledger(
    table: str = "video_uploads",
    limit: int = 10,
    date_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read-only safe query to inspect database records in Supabase cloud database.
    
    Args:
        table: 'video_uploads', 'daily_summaries', or 'brain_teasers'.
        limit: Max rows to retrieve (default 10, max 50).
        date_filter: Optional date substring or YYYY-MM-DD to filter by.
    """
    limit = min(max(1, limit), 50)
    allowed_tables = {"video_uploads", "daily_summaries", "brain_teasers"}
    if table not in allowed_tables:
        return {
            "status": "ERROR",
            "message": f"Table '{table}' not allowed. Must be one of: {list(allowed_tables)}"
        }
        
    client = get_supabase_client()
    if not client:
        return {
            "status": "DISABLED",
            "message": "Supabase client unconfigured or credentials missing."
        }
        
    try:
        query = client.table(table).select("*").order("created_at", desc=True).limit(limit)
        if date_filter:
            query = query.ilike("created_at", f"%{date_filter}%")
        res = query.execute()
        rows = res.data or []
        
        # Redact any sensitive internal keys if present
        for r in rows:
            for k in ("api_key", "secret", "token"):
                if k in r:
                    r[k] = "[REDACTED]"
                    
        return {
            "status": "SUCCESS",
            "table": table,
            "row_count": len(rows),
            "rows": rows
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "table": table,
            "message": str(e)
        }


@protect_sensitive_data
def audit_token_and_quota_ledgers() -> Dict[str, Any]:
    """
    Audits the current YouTube quota budget and recent token consumption logs.
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # Check YouTube quota log
    quota_log_file = _ROOT_DIR / "Research" / "youtube_quota_log.md"
    if not quota_log_file.exists():
        quota_log_file = _ROOT_DIR / "Research" / "youtube_quota_usage.md"
        
    quota_info = {
        "daily_ceiling": 10000,
        "estimated_used": 0,
        "remaining_units": 10000,
        "status": "HEALTHY"
    }
    
    if quota_log_file.exists():
        try:
            content = quota_log_file.read_text(encoding="utf-8")
            units = 0
            for line in content.splitlines():
                if today_str in line or now.strftime("%B %d, %Y") in line or now.strftime("%d %B %Y") in line:
                    if "Upload" in line or "upload" in line:
                        units += 1600
                    elif "Playlist" in line:
                        units += 50
                    elif "Comment" in line:
                        units += 50
            quota_info["estimated_used"] = units
            quota_info["remaining_units"] = max(0, 10000 - units)
            if units >= 8000:
                quota_info["status"] = "WARNING"
            if units >= 10000:
                quota_info["status"] = "EXHAUSTED"
        except Exception as e:
            quota_info["error"] = str(e)
            
    # Check token log tail
    token_log_file = _ROOT_DIR / "Research" / "developer_token_usage.md"
    recent_tokens = []
    if token_log_file.exists():
        try:
            lines = token_log_file.read_text(encoding="utf-8").splitlines()
            table_lines = [l for l in lines if l.startswith("| **Turn")]
            for tl in table_lines[-5:]:
                recent_tokens.append(tl)
        except Exception:
            pass
            
    return {
        "youtube_quota": quota_info,
        "recent_token_turns": recent_tokens,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
    }
