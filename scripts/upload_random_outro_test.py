#!/usr/bin/env python3
"""
Pulse Vector — Random Outro Scene Assembly & Private YouTube Upload
Picks a random end credit scene from the 5 finalists (Vox, MrBeast, Think School, Kurzgesagt, Veritasium),
assembles it dynamically with a sample Daily Briefing video, and uploads to YouTube marked strictly as PRIVATE.
"""

import os
import sys
import random
import logging
import datetime
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.outro_video_engine import OutroVideoEngine, FINALIST_CHANNELS
from core.youtube_utils import (
    get_authenticated_service,
    upload_video_to_youtube,
    sanitize_youtube_tags,
    log_upload_details,
)

logger = logging.getLogger("UploadRandomOutro")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_VIDEO_PATH = ROOT_DIR / "pulse_archive" / "2026" / "October" / "Daily_Videos" / "daily-17oct-2026_formatted.mp4"
BASE_TXT_PATH = ROOT_DIR / "pulse_archive" / "2026" / "October" / "Daily" / "daily-17oct-2026_formatted.txt"
SAMPLES_DIR = ROOT_DIR / "samples" / "End_Credits_Videos"

def prepare_widescreen_base(input_mp4: Path, output_mp4: Path) -> Path:
    """
    Pads a 1080x1920 vertical video into a 1920x1080 widescreen 16:9 container
    with a fast blurred background and sharp centered foreground.
    """
    if output_mp4.exists() and output_mp4.stat().st_size > 100000:
        logger.info(f"Reusing existing prepared widescreen base: {output_mp4.name}")
        return output_mp4

    logger.info(f"Converting base video to 1920x1080 widescreen: {input_mp4.name} -> {output_mp4.name}")
    filter_complex = (
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=10:5,setsar=1[bg];"
        "[0:v]scale=-1:1080,setsar=1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[vout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_mp4),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        str(output_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg widescreen preparation failed: {res.stderr[-300:]}")
    return output_mp4

def concatenate_videos(video1: Path, video2: Path, output_mp4: Path) -> Path:
    """Concatenates two 1080p 30fps videos cleanly via FFmpeg concat filter enforcing matching SAR and pix_fmt."""
    logger.info(f"Concatenating {video1.name} + {video2.name} -> {output_mp4.name}")
    filter_complex = (
        "[0:v]setsar=1,format=yuv420p[v0];"
        "[1:v]setsar=1,format=yuv420p[v1];"
        "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video1),
        "-i", str(video2),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-movflags", "+faststart",
        str(output_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {res.stderr[-300:]}")
    return output_mp4

def update_quota_log(video_id: str, channel_key: str):
    """Logs the upload turn in Research/youtube_quota_log.md as per youtube-dist skill."""
    quota_file = ROOT_DIR / "Research" / "youtube_quota_log.md"
    if not quota_file.exists():
        return
    date_str = datetime.datetime.now().strftime("%d %b %Y")
    entry = f"\n| **{date_str}** | Private Test ({channel_key.title()} Outro) | `{video_id}` | Uploaded (Private) | 1 video | 99 left | ~1600 units | 8400 units |\n"
    content = quota_file.read_text(encoding="utf-8")
    content += entry
    quota_file.write_text(content, encoding="utf-8")
    logger.info(f"Updated YouTube quota log in {quota_file.name}")

def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = SAMPLES_DIR / "temp_upload"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print("  PULSE VECTOR -- RANDOM OUTRO ASSEMBLY & PRIVATE YOUTUBE UPLOAD  ")
    print("==================================================================")

    # 1. Randomly pick an outro archetype from the 5 finalists
    engine = OutroVideoEngine(output_dir=SAMPLES_DIR)
    chosen_channel = engine.get_random_outro_channel()
    print(f"\n[*] [DICE] Random Outro Archetype Selected: [{chosen_channel.upper()}] (from 5 Finalists)")

    # 2. Dynamic Context parameters
    context = {
        "next_video_title": "India Manufacturing & Economic Policy 2026",
        "playlist_title": "Daily Current Affairs Archive October 2026",
        "telegram_handle": "@pulsevector_official",
        "question_text": "Which of today's events will have the greatest impact?",
    }

    # 3. Render the chosen outro
    print(f"[*] Rendering dynamic outro scene for {chosen_channel}...")
    outro_path = temp_dir / f"dynamic_outro_{chosen_channel}.mp4"
    engine.generate_single_outro_video(chosen_channel, output_path=outro_path, context=context)
    print(f"    [OK] Generated outro: {outro_path.name} ({outro_path.stat().st_size // 1024} KB)")

    # 4. Prepare widescreen 16:9 base video
    prepared_base = temp_dir / "base_widescreen.mp4"
    prepare_widescreen_base(BASE_VIDEO_PATH, prepared_base)
    print(f"    [OK] Prepared 16:9 base video: {prepared_base.name} ({prepared_base.stat().st_size // 1024} KB)")

    # 5. Concatenate base video + dynamic outro
    composite_video = SAMPLES_DIR / f"pulse_vector_test_{chosen_channel}_outro.mp4"
    concatenate_videos(prepared_base, outro_path, composite_video)
    file_size_mb = composite_video.stat().st_size / (1024 * 1024)
    print(f"    [OK] Created Composite Video: {composite_video.name} ({file_size_mb:.2f} MB)")

    # 6. YouTube Upload Preparation (Strictly PRIVATE)
    title = f"Global Treaty & Top News (17 Oct 2026) [Private Outro Test: {chosen_channel.title()}]"
    description = (
        f"Pulse Vector Daily Intel Briefing (17 October 2026)\n"
        f"Featuring randomized animated end-credit scene: {chosen_channel.upper()} Archetype.\n\n"
        f"Key Highlights:\n"
        f"- Global climate summit concludes with landmark treaty.\n"
        f"- India launches new economic policy for manufacturing.\n"
        f"- Supreme Court rules on digital privacy legislation.\n\n"
        f"Animated Outro Dock: Like, Share, and Subscribe Triad Animation ({chosen_channel.title()})\n"
        f"Official Channel: https://www.youtube.com/@Pulse_vector\n"
        f"Telegram Community: https://t.me/pulsevector_official\n\n"
        f"#CurrentAffairs #DailyCurrentAffairs #UPSC #SSCCGL #PulseVector"
    )
    raw_tags = [
        "DailyCurrentAffairs", "CurrentAffairs", "GK", "GeneralKnowledge",
        "UPSC", "SSC", "Banking", "Railways", "ExamPrep", "PulseVector",
        f"Outro{chosen_channel.title()}", "AnimatedEndScreen"
    ]
    safe_tags = sanitize_youtube_tags(raw_tags)

    print("\n[*] Authenticating with YouTube Data API...")
    youtube = get_authenticated_service()

    print(f"[*] Uploading to YouTube as PRIVATE video...")
    print(f"    Title: {title}")
    print(f"    Privacy Status: private")
    print(f"    Category: 27 (Education)")

    video_id = upload_video_to_youtube(
        youtube=youtube,
        file_path=str(composite_video),
        title=title,
        description=description,
        tags=safe_tags,
        category_id="27",
        privacy_status="private",  # Strictly PRIVATE as requested
    )

    watch_url = f"https://youtu.be/{video_id}"
    studio_url = f"https://studio.youtube.com/video/{video_id}/edit"
    print("\n==================================================================")
    print("  [SUCCESS] VIDEO SUCCESSFULLY UPLOADED TO YOUTUBE!")
    print(f"  * Video ID:       {video_id}")
    print(f"  * Privacy Status: PRIVATE")
    print(f"  * Outro Archetype:{chosen_channel.upper()}")
    print(f"  * Watch URL:      {watch_url}")
    print(f"  * YouTube Studio: {studio_url}")
    print("==================================================================\n")

    # 7. Update logs
    log_upload_details(
        title=title,
        category_name="Education (27)",
        video_type="Widescreen 16:9 + Outro",
        related_video_setting="Private Test Upload",
        pinned_comment_status="N/A (Private)",
        video_id=video_id,
    )
    update_quota_log(video_id=video_id, channel_key=chosen_channel)

    # Clean up temp files
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return video_id, watch_url, chosen_channel

if __name__ == "__main__":
    main()
