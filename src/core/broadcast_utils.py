"""
Pulse Vector - Community Multi-Platform Broadcast Engine
Automates daily distribution of Current Affairs and Brain Teasers to Telegram and Discord.
"""

import os
import re
import datetime
import pathlib
import logging
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves environment variable with fallback from os.environ or .env file."""
    val = os.getenv(key)
    if val:
        return val
        
    env_file = pathlib.Path(".env")
    if env_file.exists():
        try:
            content = env_file.read_text(encoding="utf-8")
            match = re.search(rf"^\s*{re.escape(key)}\s*=\s*['\"]?(.*?)['\"]?\s*$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
    return default

def broadcast_telegram(
    message: str,
    image_path: Optional[pathlib.Path] = None,
    parse_mode: str = "HTML"
) -> bool:
    """
    Broadcasts message or photo to a Telegram channel/group via Bot API.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
    """
    bot_token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.info("[Broadcast] Telegram credentials (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) not configured; skipping.")
        return False
        
    try:
        if image_path and pathlib.Path(image_path).exists():
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            caption = message[:1024]  # Telegram photo caption limit
            with open(image_path, "rb") as photo_file:
                payload = {"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode}
                files = {"photo": photo_file}
                resp = requests.post(url, data=payload, files=files, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message[:4096], "parse_mode": parse_mode, "disable_web_page_preview": False}
            resp = requests.post(url, json=payload, timeout=15)
            
        if resp.status_code == 200:
            logger.info("✅ Successfully broadcast to Telegram.")
            return True
        else:
            logger.warning(f"Telegram broadcast failed ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        logger.warning(f"Error broadcasting to Telegram: {e}")
        return False

def broadcast_discord(
    title: str,
    description: str,
    fields: Optional[List[Dict[str, Any]]] = None,
    image_path: Optional[pathlib.Path] = None,
    color: int = 0x38bdf8,
    video_url: Optional[str] = None
) -> bool:
    """
    Broadcasts rich embed to a Discord channel via Webhook.
    Requires DISCORD_WEBHOOK_URL.
    """
    webhook_url = get_env_var("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.info("[Broadcast] Discord webhook (DISCORD_WEBHOOK_URL) not configured; skipping.")
        return False
        
    embed = {
        "title": title[:256],
        "description": description[:4096],
        "color": color,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "footer": {
            "text": "Pulse Vector • Knowledge in Motion",
            "icon_url": "https://img.youtube.com/vi/NuOwtBvT8Ew/hqdefault.jpg"
        }
    }
    
    if video_url:
        embed["url"] = video_url
        
    if fields:
        embed["fields"] = fields[:25]
        
    payload = {"embeds": [embed]}
    
    try:
        if image_path and pathlib.Path(image_path).exists():
            embed["image"] = {"url": f"attachment://{pathlib.Path(image_path).name}"}
            with open(image_path, "rb") as f:
                files = {"file": (pathlib.Path(image_path).name, f, "image/png")}
                resp = requests.post(webhook_url, data={"payload_json": requests.compat.json.dumps(payload)}, files=files, timeout=15)
        else:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            
        if resp.status_code in [200, 204]:
            logger.info("✅ Successfully broadcast to Discord.")
            return True
        else:
            logger.warning(f"Discord broadcast failed ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        logger.warning(f"Error broadcasting to Discord: {e}")
        return False

def broadcast_daily_content(
    content_type: str,
    date_obj: datetime.date,
    title: str,
    summary_text: str,
    image_path: Optional[pathlib.Path] = None,
    video_url: Optional[str] = None
) -> Dict[str, bool]:
    """
    Dispatches automated content to both Telegram and Discord communities.
    """
    date_str = date_obj.strftime("%d %B %Y")
    
    # 1. Format Telegram Message
    tg_lines = [
        f"⚡ <b>PULSE VECTOR | {content_type.upper()}</b>",
        f"📅 <i>{date_str}</i>\n",
        f"<b>{title}</b>\n",
        summary_text
    ]
    if video_url:
        tg_lines.append(f"\n▶️ <b>Watch 60s Video Short:</b> <a href=\"{video_url}\">{video_url}</a>")
    tg_message = "\n".join(tg_lines)
    
    # 2. Format Discord Embed
    dc_title = f"⚡ Pulse Vector | {content_type.upper()}: {date_str}"
    dc_desc = f"**{title}**\n\n{summary_text}"
    if video_url:
        dc_desc += f"\n\n▶️ **[Watch Full Short on YouTube]({video_url})**"
        
    color = 0xf59e0b if "teaser" in content_type.lower() else 0x38bdf8
    
    tg_status = broadcast_telegram(tg_message, image_path=image_path)
    dc_status = broadcast_discord(dc_title, dc_desc, image_path=image_path, color=color, video_url=video_url)
    
    return {"telegram": tg_status, "discord": dc_status}
