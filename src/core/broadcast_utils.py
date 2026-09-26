"""
Pulse Vector - Community Multi-Platform Broadcast Engine
Automates daily distribution of Current Affairs and Brain Teasers to Telegram and Discord.
Supports native .mp4 video broadcasting and rich social media blocks.
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

def truncate_html_caption(text: str, max_length: int = 1024) -> str:
    """
    Safely truncates text formatted in HTML to fit within Telegram's caption limit (<= 1024 chars).
    Ensures that any opened HTML tags (<b>, <a>, <i>, etc.) are properly closed and not cut mid-tag.
    """
    if len(text) <= max_length:
        return text
        
    # Reserve room for ellipsis and closing tags (e.g. </b></i></a>)
    reserve = min(40, max(10, max_length // 4))
    budget = max(10, max_length - reserve)
    truncated = text[:budget]
    
    # Strip any half-opened tag at the cut point (e.g. "<a hr...")
    last_open = truncated.rfind("<")
    last_close = truncated.rfind(">")
    if last_open > last_close:
        truncated = truncated[:last_open]
        
    truncated = truncated.rstrip() + "..."
    
    # Balance opened HTML tags
    open_tags = re.findall(r"<([a-zA-Z0-9_-]+)(?:\s+[^>]*?)?>", truncated)
    close_tags = re.findall(r"</([a-zA-Z0-9_-]+)>", truncated)
    
    for tag in reversed(open_tags):
        if open_tags.count(tag) > close_tags.count(tag):
            closing_tag = f"</{tag}>"
            if len(truncated) + len(closing_tag) <= max_length:
                truncated += closing_tag
                close_tags.append(tag)
            
    # Guarantee strict upper bound
    if len(truncated) > max_length:
        truncated = truncated[:max_length]
        
    return truncated

def broadcast_telegram(
    message: str,
    image_path: Optional[pathlib.Path] = None,
    video_path: Optional[pathlib.Path] = None,
    parse_mode: str = "HTML"
) -> bool:
    """
    Broadcasts video, photo, or text message to a Telegram channel/group via Bot API.
    Prioritizes native .mp4 video upload via sendVideo (supports_streaming=True, max 50 MB).
    Falls back to image upload via sendPhoto, or text via sendMessage.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
    """
    bot_token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.info("[Broadcast] Telegram credentials (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) not configured; skipping.")
        return False
        
    try:
        # 1. Native Video Upload (sendVideo, max 50 MB)
        if video_path and pathlib.Path(video_path).exists():
            v_path = pathlib.Path(video_path)
            file_size_mb = v_path.stat().st_size / (1024 * 1024)
            if file_size_mb <= 50:
                url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
                caption = truncate_html_caption(message, 1024) if parse_mode == "HTML" else message[:1024]
                with open(v_path, "rb") as video_file:
                    payload = {
                        "chat_id": chat_id,
                        "caption": caption,
                        "parse_mode": parse_mode,
                        "supports_streaming": "true"
                    }
                    files = {"video": (v_path.name, video_file, "video/mp4")}
                    resp = requests.post(url, data=payload, files=files, timeout=60)
                if resp.status_code == 200:
                    logger.info("✅ Successfully broadcast native video to Telegram.")
                    return True
                else:
                    logger.warning(f"Telegram sendVideo failed ({resp.status_code}): {resp.text}. Falling back to photo/text.")
            else:
                logger.warning(f"Video file {v_path.name} exceeds Telegram 50MB limit ({file_size_mb:.1f} MB); falling back to photo/text.")

        # 2. Image Upload Fallback (sendPhoto, max 1024 caption)
        if image_path and pathlib.Path(image_path).exists():
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            caption = truncate_html_caption(message, 1024) if parse_mode == "HTML" else message[:1024]
            with open(image_path, "rb") as photo_file:
                payload = {"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode}
                files = {"photo": photo_file}
                resp = requests.post(url, data=payload, files=files, timeout=30)
        else:
            # 3. Text Message Fallback (sendMessage, max 4096)
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
    video_path: Optional[pathlib.Path] = None,
    color: int = 0x38bdf8,
    video_url: Optional[str] = None
) -> bool:
    """
    Broadcasts rich embed to a Discord channel via Webhook.
    Prioritizes native .mp4 video file attachment (max 25 MB).
    Falls back to image attachment or text embed.
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
        # 1. Native Video Attachment (max 25 MB)
        if video_path and pathlib.Path(video_path).exists():
            v_path = pathlib.Path(video_path)
            file_size_mb = v_path.stat().st_size / (1024 * 1024)
            if file_size_mb <= 25:
                with open(v_path, "rb") as vf:
                    files = {"file": (v_path.name, vf, "video/mp4")}
                    resp = requests.post(
                        webhook_url,
                        data={"payload_json": requests.compat.json.dumps(payload)},
                        files=files,
                        timeout=60
                    )
                if resp.status_code in [200, 204]:
                    logger.info("✅ Successfully broadcast native video to Discord.")
                    return True
                else:
                    logger.warning(f"Discord video attachment failed ({resp.status_code}): {resp.text}. Falling back to image/embed.")
            else:
                logger.warning(f"Video file {v_path.name} exceeds Discord 25MB limit ({file_size_mb:.1f} MB); falling back to image/embed.")

        # 2. Image Attachment fallback
        if image_path and pathlib.Path(image_path).exists():
            img_p = pathlib.Path(image_path)
            embed["image"] = {"url": f"attachment://{img_p.name}"}
            with open(img_p, "rb") as f:
                files = {"file": (img_p.name, f, "image/png")}
                resp = requests.post(
                    webhook_url,
                    data={"payload_json": requests.compat.json.dumps(payload)},
                    files=files,
                    timeout=30
                )
        else:
            # 3. Pure JSON embed fallback
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
    video_path: Optional[pathlib.Path] = None,
    video_url: Optional[str] = None
) -> Dict[str, bool]:
    """
    Dispatches automated content to both Telegram and Discord communities.
    Attaches native .mp4 video when available, with rich social footers.
    """
    try:
        from .content_parser import get_social_links_block
    except ImportError:
        from content_parser import get_social_links_block

    date_str = date_obj.strftime("%d %B %Y")
    
    # 1. Format Telegram Message
    tg_lines = [
        f"⚡ <b>PULSE VECTOR | {content_type.upper()}</b>",
        f"📅 <i>{date_str}</i>\n",
        f"<b>{title}</b>\n",
        summary_text
    ]
    if video_url:
        tg_lines.append(f"\n▶️ <b>Watch on YouTube:</b> <a href=\"{video_url}\">{video_url}</a>")
    
    discussion_prompt = "💬 <b>Topic of the Day:</b> Which story will impact the future most? Drop your perspective in the comments!"
    tg_lines.append(f"\n{discussion_prompt}")
    
    social_html = get_social_links_block("html", include_divider=True)
    tg_lines.append(f"\n{social_html}")
    tg_message = "\n".join(tg_lines)
    
    # 2. Format Discord Embed
    dc_title = f"⚡ Pulse Vector | {content_type.upper()}: {date_str}"
    dc_desc = f"**{title}**\n\n{summary_text}"
    if video_url:
        dc_desc += f"\n\n▶️ **[Watch on YouTube]({video_url})**"
        
    dc_desc += "\n\n💬 **Topic of the Day:** Which story will impact the future most? Join the discussion!"
    social_md = get_social_links_block("markdown", include_divider=True)
    dc_desc += f"\n\n{social_md}"
    
    color = 0xf59e0b if "teaser" in content_type.lower() else 0x38bdf8
    
    tg_status = broadcast_telegram(tg_message, image_path=image_path, video_path=video_path)
    dc_status = broadcast_discord(dc_title, dc_desc, image_path=image_path, video_path=video_path, color=color, video_url=video_url)
    
    return {"telegram": tg_status, "discord": dc_status}
