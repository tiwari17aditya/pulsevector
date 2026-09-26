"""
Pulse Vector MCP Server - Social Broadcast Dispatcher Tool
Provides manual or scheduled dispatch of Current Affairs and Brain Teaser
broadcasts to Telegram and Discord with native .mp4 video attachments.
"""

import os
import pathlib
import datetime
from typing import Dict, Any, Optional

from core.config import ARCHIVE_DIR, BT_DATE_FMT
from core.content_parser import parse_news_content, parse_teaser_content, get_social_links_block
from core.broadcast_utils import broadcast_daily_content, truncate_html_caption
from core.pipeline_engine import PipelineEngine

def trigger_social_broadcast(
    target_date: Optional[str] = None,
    content_type: str = "daily",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Triggers or previews a multi-platform broadcast (Telegram & Discord) for a given date.
    
    Args:
        target_date: Date string (YYYY-MM-DD), defaults to today.
        content_type: 'daily', 'weekly', 'monthly', or 'brainteaser'.
        dry_run: If True, previews captions & payloads without dispatching API calls.
    """
    if target_date:
        try:
            d_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            return {"error": f"Invalid date format: '{target_date}'. Expected YYYY-MM-DD."}
    else:
        d_obj = datetime.datetime.now()

    ctype = content_type.lower()
    date_display = d_obj.strftime("%d %B %Y")
    
    # Locate assets
    video_path = None
    image_path = None
    title = ""
    summary_text = ""
    
    if ctype in ("daily", "weekly", "monthly"):
        engine = PipelineEngine()
        paths = engine.get_paths(ctype, d_obj)
        txt_file = paths["text_file"]
        
        if not txt_file.exists():
            return {"error": f"Archive text file not found at: {txt_file}"}
            
        content = txt_file.read_text(encoding="utf-8", errors="ignore")
        payload = parse_news_content(content, ctype, d_obj, txt_file)
        
        title = payload.title
        summary_text = "\n".join([f"• {p[1]}" for p in payload.points[:5]])
        
        img_directory = paths.get("img_dir") or paths.get("image_dir")
        thumb_candidate = img_directory / "thumbnail.png" if img_directory else None
        if thumb_candidate and thumb_candidate.exists():
            image_path = thumb_candidate
        if paths["video_file"].exists():
            video_path = paths["video_file"]
            
    elif "teaser" in ctype or "brain" in ctype:
        bt_code = d_obj.strftime(BT_DATE_FMT)
        base_dir = ARCHIVE_DIR / d_obj.strftime("%Y") / d_obj.strftime("%B") / "Brain_Teasers"
        txt_path = base_dir / "Text" / f"brainteaser-{bt_code}.txt"
        
        if not txt_path.exists():
            return {"error": f"Brain teaser file not found at: {txt_path}"}
            
        content = txt_path.read_text(encoding="utf-8", errors="ignore")
        data = parse_teaser_content(content, target_date=d_obj)
        
        title = f"Daily Brain Teaser: {date_display} 🧠"
        summary_text = (
            f"{data.get('question_header', '')}\n{data.get('series', '')}\n\n"
            f"Options:\n" + "\n".join([f"• {opt}" for opt in data.get('options', [])]) +
            f"\n\n🧠 Drop your answer in the comments! Solution revealed in 24 hours."
        )
        
        img_candidate = base_dir / "Images" / f"brainteaser-{bt_code}.png"
        if img_candidate.exists():
            image_path = img_candidate
        vid_candidate = base_dir / "Videos" / f"brainteaser-{bt_code}.mp4"
        if vid_candidate.exists():
            video_path = vid_candidate

    # Construct preview payloads
    social_html = get_social_links_block("html")
    tg_lines = [
        f"⚡ <b>PULSE VECTOR | {ctype.upper()}</b>",
        f"📅 <i>{date_display}</i>\n",
        f"<b>{title}</b>\n",
        summary_text,
        f"\n{social_html}"
    ]
    raw_tg = "\n".join(tg_lines)
    tg_caption = truncate_html_caption(raw_tg, 1024)
    
    social_md = get_social_links_block("markdown")
    dc_desc = f"**{title}**\n\n{summary_text}\n\n{social_md}"

    result = {
        "target_date": d_obj.strftime("%Y-%m-%d"),
        "content_type": ctype,
        "dry_run": dry_run,
        "video_attached": bool(video_path and video_path.exists()),
        "video_path": str(video_path) if video_path else None,
        "image_attached": bool(image_path and image_path.exists()),
        "image_path": str(image_path) if image_path else None,
        "previews": {
            "telegram_caption_html": tg_caption,
            "discord_description_md": dc_desc
        }
    }

    if not dry_run:
        dispatch_status = broadcast_daily_content(
            content_type=ctype,
            date_obj=d_obj.date(),
            title=title,
            summary_text=summary_text,
            image_path=image_path,
            video_path=video_path
        )
        result["dispatch_result"] = dispatch_status
    else:
        result["dispatch_result"] = {"telegram": "DRY_RUN", "discord": "DRY_RUN"}

    return result
