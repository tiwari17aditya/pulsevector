"""
Pulse Vector - Community Multi-Platform Broadcast Engine
Automates daily distribution of Current Affairs and Brain Teasers to Telegram and Discord.
Supports native .mp4 video broadcasting and rich social media blocks.
"""

import os
import re
import json
import datetime
import pathlib
import logging
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# BROADCAST DEDUPLICATION LEDGER (Idempotency Engine)
# -------------------------------------------------------------
def get_broadcast_ledger_path(archive_dir: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Returns the persistent broadcast ledger file path within the archive."""
    if archive_dir:
        return pathlib.Path(archive_dir) / "broadcast_ledger.json"
    try:
        from .config import ARCHIVE_DIR
    except ImportError:
        try:
            from core.config import ARCHIVE_DIR
        except ImportError:
            ARCHIVE_DIR = pathlib.Path("pulse_archive")
    return ARCHIVE_DIR / "broadcast_ledger.json"

def normalize_broadcast_key(content_type: str, slot: Optional[int] = None) -> str:
    """
    Normalizes content_type to a canonical key for ledger tracking.
    'daily' (or 'daily current affairs') -> 'daily'
    'weekly' -> 'weekly'
    'monthly' -> 'monthly'
    'brainteaser' -> 'brainteaser' (or 'brainteaser_slot2' if slot == 2)
    """
    ct = (content_type or "").lower().strip()
    if "teaser" in ct or "brain" in ct:
        if slot and int(slot) == 2:
            return "brainteaser_slot2"
        return "brainteaser"
    elif "weekly" in ct:
        return "weekly"
    elif "monthly" in ct:
        return "monthly"
    elif "daily" in ct or "current" in ct or "news" in ct:
        return "daily"
    return ct or "daily"

def load_broadcast_ledger(ledger_path: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Loads the broadcast deduplication ledger safely."""
    path = ledger_path or get_broadcast_ledger_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[Broadcast Dedup] Could not parse broadcast ledger: {e}")
    return {}

def save_broadcast_ledger(data: Dict[str, Any], ledger_path: Optional[pathlib.Path] = None) -> bool:
    """Saves the broadcast deduplication ledger atomically."""
    path = ledger_path or get_broadcast_ledger_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(path)
        return True
    except Exception as e:
        logger.warning(f"[Broadcast Dedup] Could not write broadcast ledger: {e}")
        return False

def is_already_broadcast(
    content_type: str,
    date_obj: Any,
    platform: str,
    slot: Optional[int] = None,
    ledger_path: Optional[pathlib.Path] = None
) -> bool:
    """
    Checks if a given content type for a specific date has already been broadcast
    to the target platform ('telegram', 'discord', 'instagram').
    Strictly prevents duplicate/redundant daily posts.
    """
    date_str = date_obj.strftime("%Y-%m-%d") if hasattr(date_obj, "strftime") else str(date_obj)[:10]
    c_key = normalize_broadcast_key(content_type, slot=slot)
    p_key = platform.lower().strip()
    
    ledger = load_broadcast_ledger(ledger_path)
    day_record = ledger.get(date_str, {})
    content_record = day_record.get(c_key, {})
    plat_record = content_record.get(p_key, {})
    
    return plat_record.get("status") == "SENT"

def record_broadcast_event(
    content_type: str,
    date_obj: Any,
    platform: str,
    status: str = "SENT",
    title: str = "",
    video_url: Optional[str] = None,
    slot: Optional[int] = None,
    ledger_path: Optional[pathlib.Path] = None
) -> None:
    """
    Records a completed broadcast event to the persistent ledger.
    """
    date_str = date_obj.strftime("%Y-%m-%d") if hasattr(date_obj, "strftime") else str(date_obj)[:10]
    c_key = normalize_broadcast_key(content_type, slot=slot)
    p_key = platform.lower().strip()
    
    ledger = load_broadcast_ledger(ledger_path)
    if date_str not in ledger:
        ledger[date_str] = {}
    if c_key not in ledger[date_str]:
        ledger[date_str][c_key] = {}
        
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ledger[date_str][c_key][p_key] = {
        "status": status,
        "timestamp": now_iso,
        "title": title[:200] if title else "",
        "video_url": video_url or ""
    }
    save_broadcast_ledger(ledger, ledger_path)

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

def broadcast_telegram_quiz(
    question: str,
    options: List[str],
    correct_option_id: int,
    explanation: Optional[str] = None
) -> bool:
    """
    Broadcasts an interactive Quiz poll to a Telegram channel/group via Bot API sendPoll.
    Features native celebratory confetti animations, instant validation, and explanation hints.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
    """
    bot_token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.info("[Broadcast] Telegram credentials not configured; skipping quiz poll.")
        return False

    clean_options = [opt.strip()[:100] for opt in options if opt.strip()][:10]
    if len(clean_options) < 2:
        logger.warning("[Broadcast] Need at least 2 options for a Telegram quiz poll.")
        return False

    clean_question = question.strip()[:300]
    safe_correct_id = max(0, min(correct_option_id, len(clean_options) - 1))

    url = f"https://api.telegram.org/bot{bot_token}/sendPoll"
    payload = {
        "chat_id": chat_id,
        "question": clean_question,
        "options": requests.compat.json.dumps(clean_options),
        "is_anonymous": True,
        "type": "quiz",
        "correct_option_id": safe_correct_id,
    }
    if explanation:
        payload["explanation"] = explanation.strip()[:200]
        payload["explanation_parse_mode"] = "HTML"

    try:
        resp = requests.post(url, data=payload, timeout=15)
        if resp.status_code == 200:
            logger.info("✅ Successfully broadcast interactive Quiz poll to Telegram.")
            return True
        else:
            logger.warning(f"Telegram sendPoll failed ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        logger.warning(f"Error broadcasting Telegram quiz poll: {e}")
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

def broadcast_instagram(
    caption: str,
    video_url: Optional[str] = None,
    image_url: Optional[str] = None
) -> bool:
    """
    Broadcasts video (as Reel) or image (as Post) to Instagram via Meta Graph API v21.0.
    Requires public HTTPS URL (e.g. from Supabase Storage).
    Gracefully skips if META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID is not configured.
    """
    try:
        from .meta_utils import publish_instagram_reel, publish_instagram_photo, get_meta_credentials
    except ImportError:
        from meta_utils import publish_instagram_reel, publish_instagram_photo, get_meta_credentials

    creds = get_meta_credentials()
    if not creds.get("access_token") or not creds.get("account_id"):
        logger.info("[Broadcast] Meta/Instagram credentials not configured; skipping Instagram broadcast.")
        return False

    try:
        if video_url:
            media_id = publish_instagram_reel(video_url=video_url, caption=caption)
            return media_id is not None
        elif image_url:
            media_id = publish_instagram_photo(image_url=image_url, caption=caption)
            return media_id is not None
        return False
    except Exception as e:
        logger.warning(f"[Broadcast] Error broadcasting to Instagram: {e}")
        return False

def broadcast_daily_content(
    content_type: str,
    date_obj: datetime.date,
    title: str,
    summary_text: str,
    image_path: Optional[pathlib.Path] = None,
    video_path: Optional[pathlib.Path] = None,
    video_url: Optional[str] = None,
    public_media_url: Optional[str] = None,
    quiz_data: Optional[Dict[str, Any]] = None,
    force: bool = False,
    slot: Optional[int] = None,
    ledger_path: Optional[pathlib.Path] = None
) -> Dict[str, Any]:
    """
    Dispatches automated content to Telegram, Discord, and Instagram communities.
    Attaches native .mp4 video when available, with rich social footers.
    If quiz_data is provided (e.g. for Brain Teasers), dispatches an interactive Telegram Quiz poll.
    Enforces strict once-a-day deduplication across Telegram and Discord unless force=True.
    """
    try:
        from .content_parser import get_social_links_block
    except ImportError:
        from content_parser import get_social_links_block

    date_str = date_obj.strftime("%d %B %Y")
    c_key = normalize_broadcast_key(content_type, slot=slot)
    
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
    
    # -------------------------------------------------------------
    # DEDUPLICATION GATES (Strict Once-A-Day Enforcement)
    # -------------------------------------------------------------
    # Telegram Deduplication Gate
    tg_already = not force and is_already_broadcast(c_key, date_obj, "telegram", slot=slot, ledger_path=ledger_path)
    if tg_already:
        logger.info(f"ℹ️ [Broadcast Dedup] '{c_key.upper()}' for {date_str} already broadcast to Telegram today. Skipping redundant post.")
        print(f"ℹ️ [Broadcast Dedup] '{c_key.upper()}' for {date_str} already broadcast to Telegram today. Skipping redundant post.")
        tg_status = True
        tg_skipped = True
    else:
        tg_status = broadcast_telegram(tg_message, image_path=image_path, video_path=video_path)
        tg_skipped = False
        if tg_status:
            record_broadcast_event(c_key, date_obj, "telegram", status="SENT", title=title, video_url=video_url, slot=slot, ledger_path=ledger_path)
            
    # Discord Deduplication Gate
    dc_already = not force and is_already_broadcast(c_key, date_obj, "discord", slot=slot, ledger_path=ledger_path)
    if dc_already:
        logger.info(f"ℹ️ [Broadcast Dedup] '{c_key.upper()}' for {date_str} already broadcast to Discord today. Skipping redundant post.")
        print(f"ℹ️ [Broadcast Dedup] '{c_key.upper()}' for {date_str} already broadcast to Discord today. Skipping redundant post.")
        dc_status = True
        dc_skipped = True
    else:
        dc_status = broadcast_discord(dc_title, dc_desc, image_path=image_path, video_path=video_path, color=color, video_url=video_url)
        dc_skipped = False
        if dc_status:
            record_broadcast_event(c_key, date_obj, "discord", status="SENT", title=title, video_url=video_url, slot=slot, ledger_path=ledger_path)
    
    # 3. Instagram Reels / Post Broadcast
    ig_already = not force and is_already_broadcast(c_key, date_obj, "instagram", slot=slot, ledger_path=ledger_path)
    if ig_already:
        logger.info(f"ℹ️ [Broadcast Dedup] '{c_key.upper()}' for {date_str} already broadcast to Instagram today. Skipping redundant post.")
        ig_status = True
        ig_skipped = True
    else:
        ig_caption = f"⚡ Pulse Vector | {content_type.upper()}: {date_str}\n\n{title}\n\n{summary_text}\n\n#pulsevector #currentaffairs #dailyupdate #shorts"
        ig_status = broadcast_instagram(caption=ig_caption, video_url=public_media_url if public_media_url and public_media_url.endswith('.mp4') else None, image_url=public_media_url if public_media_url and not public_media_url.endswith('.mp4') else None)
        ig_skipped = False
        if ig_status:
            record_broadcast_event(c_key, date_obj, "instagram", status="SENT", title=title, video_url=video_url, slot=slot, ledger_path=ledger_path)
    
    # 4. Telegram Interactive Quiz Poll (if quiz_data provided)
    tg_quiz_status = False
    tg_quiz_skipped = False
    if quiz_data and "options" in quiz_data and len(quiz_data["options"]) >= 2:
        quiz_already = not force and is_already_broadcast(c_key, date_obj, "telegram_quiz", slot=slot, ledger_path=ledger_path)
        if quiz_already:
            logger.info(f"ℹ️ [Broadcast Dedup] Quiz poll for {date_str} already broadcast to Telegram today. Skipping redundant poll.")
            tg_quiz_status = True
            tg_quiz_skipped = True
        else:
            q_text = quiz_data.get("question", title)
            q_opts = quiz_data.get("options", [])
            q_correct = quiz_data.get("correct_option_id", 0)
            q_exp = quiz_data.get("explanation")
            tg_quiz_status = broadcast_telegram_quiz(
                question=q_text,
                options=q_opts,
                correct_option_id=q_correct,
                explanation=q_exp
            )
            if tg_quiz_status:
                record_broadcast_event(c_key, date_obj, "telegram_quiz", status="SENT", title=title, slot=slot, ledger_path=ledger_path)

    res = {
        "telegram": tg_status,
        "discord": dc_status,
        "instagram": ig_status,
        "telegram_skipped": tg_skipped,
        "discord_skipped": dc_skipped
    }
    if quiz_data:
        res["telegram_quiz"] = tg_quiz_status
        res["telegram_quiz_skipped"] = tg_quiz_skipped
    return res
