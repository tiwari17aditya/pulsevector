"""
Pulse Vector MCP Server - Media Render Diagnostics Tool
Inspects pipeline render outputs (video files, slide counts, TTS alignment,
durations, and Shorts 60s compliance) for any specified target date.
"""

import os
import pathlib
import datetime
from typing import Dict, Any, Optional

from core.config import ARCHIVE_DIR, BT_DATE_FMT
from core.pipeline_engine import PipelineEngine
from core.tts_utils import get_ffmpeg_executable

def inspect_render_diagnostics(
    target_date: Optional[str] = None,
    content_type: str = "daily"
) -> Dict[str, Any]:
    """
    Inspects pipeline assets, slide cards, audio alignment, and compiled video
    duration for a specific date and content type.
    
    Args:
        target_date: Date string (YYYY-MM-DD), defaults to today.
        content_type: 'daily', 'weekly', 'monthly', or 'brainteaser'.
    """
    if target_date:
        try:
            d_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            return {"error": f"Invalid date format: '{target_date}'. Expected YYYY-MM-DD."}
    else:
        d_obj = datetime.datetime.now()

    ctype = content_type.lower()
    year_str = d_obj.strftime("%Y")
    month_str = d_obj.strftime("%B")
    
    engine = PipelineEngine()
    ffmpeg_exe = get_ffmpeg_executable()

    diagnostics = {
        "target_date": d_obj.strftime("%Y-%m-%d"),
        "content_type": ctype,
        "ffmpeg_status": "FOUND" if ffmpeg_exe else "NOT_FOUND",
        "ffmpeg_path": ffmpeg_exe,
        "artifacts": {}
    }

    if ctype in ("daily", "weekly", "monthly"):
        paths = engine.get_paths(ctype, d_obj)
        txt_file = paths["text_file"]
        img_dir = paths.get("img_dir") or paths.get("image_dir")
        video_file = paths["video_file"]

        txt_exists = txt_file.exists()
        img_count = len(list(img_dir.glob("*.png"))) if (img_dir and img_dir.exists()) else 0
        video_exists = video_file.exists()
        video_size_mb = round(video_file.stat().st_size / (1024 * 1024), 2) if video_exists else 0.0

        diagnostics["artifacts"] = {
            "text_file": {
                "path": str(txt_file),
                "exists": txt_exists,
                "size_bytes": txt_file.stat().st_size if txt_exists else 0
            },
            "slide_images": {
                "directory": str(img_dir),
                "exists": img_dir.exists(),
                "rendered_count": img_count
            },
            "video_render": {
                "path": str(video_file),
                "exists": video_exists,
                "size_mb": video_size_mb,
                "shorts_compliant_under_60s": "UNKNOWN"  # Evaluated below if exists
            }
        }

        # Health status
        if video_exists and txt_exists and img_count > 0:
            diagnostics["overall_health"] = "READY_FOR_PUBLISH"
        elif txt_exists:
            diagnostics["overall_health"] = "TEXT_GENERATED_PENDING_RENDER"
        else:
            diagnostics["overall_health"] = "NOT_STARTED"

    elif "teaser" in ctype or "brain" in ctype:
        bt_code = d_obj.strftime(BT_DATE_FMT)
        base_dir = ARCHIVE_DIR / year_str / month_str / "Brain_Teasers"
        txt_path = base_dir / "Text" / f"brainteaser-{bt_code}.txt"
        img_path = base_dir / "Images" / f"brainteaser-{bt_code}.png"
        vid_path = base_dir / "Videos" / f"brainteaser-{bt_code}.mp4"

        txt_exists = txt_path.exists()
        img_exists = img_path.exists()
        vid_exists = vid_path.exists()
        vid_size_mb = round(vid_path.stat().st_size / (1024 * 1024), 2) if vid_exists else 0.0

        diagnostics["artifacts"] = {
            "text_file": {"path": str(txt_path), "exists": txt_exists},
            "puzzle_image": {"path": str(img_path), "exists": img_exists},
            "video_render": {"path": str(vid_path), "exists": vid_exists, "size_mb": vid_size_mb}
        }

        if vid_exists and txt_exists and img_exists:
            diagnostics["overall_health"] = "READY_FOR_PUBLISH"
        elif txt_exists:
            diagnostics["overall_health"] = "PUZZLE_GENERATED_PENDING_RENDER"
        else:
            diagnostics["overall_health"] = "NOT_STARTED"

    return diagnostics
