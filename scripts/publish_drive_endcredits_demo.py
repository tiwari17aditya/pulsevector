import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = Path(r"E:\hdd-data\pulse-vector")
sys.path.insert(0, str(ROOT_DIR))

from src.core.youtube_utils import (
    get_authenticated_service,
    upload_video_to_youtube,
    sanitize_youtube_tags,
    log_upload_details,
)

def main():
    video_path = ROOT_DIR / "scratch" / "pulse_vector_sample_with_drive_endcredits.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    print("Authenticating with YouTube Data API v3...")
    os.chdir(ROOT_DIR)
    youtube = get_authenticated_service(client_secrets_file='credentials/client_secrets.json')

    title = "Pulse Vector — Daily Intelligence Briefing [Runtime Drive Endcredits & Bell Zoom Demo]"
    description = (
        "⚡ Pulse Vector Daily Intelligence Briefing Demo\n\n"
        "Featuring the new dynamic Google Drive Runtime Endcredits & Progressive Bell Zoom Outro:\n"
        "1. Main news intel presentation\n"
        "2. Seamless main video fade-out to black\n"
        "3. Dynamic animated Endcredits retrieved directly from Google Drive at runtime\n"
        "4. Animated Like, Share & Subscribe state transitions\n"
        "5. Progressive Bell Enlargement (3.2x zoom into center) with glowing aura & radiating shockwaves\n"
        "6. Final smooth fade-out to black\n\n"
        "🔔 Subscribe to Pulse Vector for daily high-yield exam intelligence @ 06:00 AM IST!\n"
        "#PulseVector #CurrentAffairs #Shorts"
    )
    raw_tags = ["Pulse Vector", "Current Affairs", "Daily Intel", "Shorts", "Endcredits", "UPSC", "MPPSC"]
    tags = sanitize_youtube_tags(raw_tags)

    # Privacy status: unlisted so the user can immediately click the URL and review it
    privacy = "unlisted"

    print(f"Uploading video: {video_path.name} ({video_path.stat().st_size // 1024} KB)...")
    print(f"Privacy Status: {privacy.upper()}")

    video_id = upload_video_to_youtube(
        youtube=youtube,
        file_path=str(video_path),
        title=title,
        description=description,
        tags=tags,
        category_id="27",  # Education
        privacy_status=privacy,
    )

    yt_url = f"https://youtu.be/{video_id}"
    print(f"\n=======================================================")
    print(f"  VIDEO SUCCESSFULLY UPLOADED TO YOUTUBE!")
    print(f"  Video ID:  {video_id}")
    print(f"  Watch URL: {yt_url}")
    print(f"=======================================================")

    try:
        log_upload_details(title=title, category_name="Education (27)", video_type="Short (9:16)", video_id=video_id)
    except Exception as e:
        print("Note on upload log:", e)
    return yt_url

if __name__ == "__main__":
    main()
