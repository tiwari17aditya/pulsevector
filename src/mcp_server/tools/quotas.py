"""
Pulse Vector MCP Server - Cloud Quotas & Health Tool
Monitors YouTube Data API quota units, Gemini token budgets,
Supabase cloud database status, Google Drive, and storage capacity.
"""

import os
import shutil
import pathlib
import datetime
from typing import Dict, Any

from core.config import ARCHIVE_DIR, ENABLE_GDRIVE_UPLOAD, GOOGLE_DRIVE_FOLDER_ID
from core.database_utils import get_supabase_client

def check_api_quotas() -> Dict[str, Any]:
    """
    Checks operational quotas and service health across YouTube, Gemini, Supabase,
    Google Drive, and local archive storage.
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # 1. YouTube Data API v3 Quota estimation
    # Daily ceiling is 10,000 units. Video upload costs 1,600 units; playlist insertion 50; comment 50.
    daily_quota_limit = 10000
    estimated_units = 0
    quota_log_file = pathlib.Path("Research/youtube_quota_usage.md")
    
    if quota_log_file.exists():
        try:
            content = quota_log_file.read_text(encoding="utf-8")
            # Count occurrences of today's uploads or operations
            for line in content.splitlines():
                if today_str in line or now.strftime("%B %d, %Y") in line or now.strftime("%d %B %Y") in line:
                    if "Upload" in line or "upload" in line:
                        estimated_units += 1600
                    elif "Playlist" in line:
                        estimated_units += 50
                    elif "Comment" in line:
                        estimated_units += 50
        except Exception:
            pass

    yt_remaining = max(0, daily_quota_limit - estimated_units)
    yt_status = "HEALTHY"
    if estimated_units >= 8000:
        yt_status = "WARNING"
    if estimated_units >= 10000:
        yt_status = "EXHAUSTED"

    # 2. Gemini API Key Status
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_status = "ACTIVE" if gemini_key else "UNCONFIGURED"

    # 3. Supabase Cloud Database & Storage
    supabase_configured = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
    supabase_connected = False
    db_stats = {}
    
    if supabase_configured:
        try:
            client = get_supabase_client()
            if client:
                # Query row counts from primary tables
                res_v = client.table("video_uploads").select("id", count="exact").limit(1).execute()
                res_s = client.table("daily_summaries").select("id", count="exact").limit(1).execute()
                video_count = getattr(res_v, "count", 0) or 0
                summary_count = getattr(res_s, "count", 0) or 0
                db_stats = {
                    "video_uploads_count": video_count,
                    "daily_summaries_count": summary_count
                }
                supabase_connected = True
        except Exception as err:
            db_stats["error"] = str(err)
            
    # 4. Google Drive Cloud Storage
    gdrive_status = "ENABLED" if ENABLE_GDRIVE_UPLOAD else "DISABLED"

    # 5. Local Storage & Archive Metrics
    archive_size_bytes = 0
    if ARCHIVE_DIR.exists():
        for p in ARCHIVE_DIR.rglob("*"):
            if p.is_file():
                try:
                    archive_size_bytes += p.stat().st_size
                except Exception:
                    pass
    archive_size_mb = round(archive_size_bytes / (1024 * 1024), 2)
    
    # Disk free space
    disk_stat = shutil.disk_usage(str(ARCHIVE_DIR) if ARCHIVE_DIR.exists() else ".")
    free_gb = round(disk_stat.free / (1024 ** 3), 2)
    total_gb = round(disk_stat.total / (1024 ** 3), 2)

    return {
        "timestamp": now.isoformat(),
        "youtube_api": {
            "daily_quota_limit": daily_quota_limit,
            "estimated_consumed_units": estimated_units,
            "remaining_units": yt_remaining,
            "status": yt_status
        },
        "gemini_api": {
            "configured": bool(gemini_key),
            "status": gemini_status
        },
        "supabase_cloud": {
            "configured": supabase_configured,
            "connected": supabase_connected,
            "database_stats": db_stats
        },
        "google_drive_cloud": {
            "enabled": ENABLE_GDRIVE_UPLOAD,
            "canonical_folder_id": GOOGLE_DRIVE_FOLDER_ID,
            "status": gdrive_status
        },
        "storage": {
            "archive_path": str(ARCHIVE_DIR),
            "archive_size_mb": archive_size_mb,
            "disk_free_gb": free_gb,
            "disk_total_gb": total_gb,
            "status": "HEALTHY" if free_gb > 5.0 else "LOW_DISK_SPACE"
        }
    }
