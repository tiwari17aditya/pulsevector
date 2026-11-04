"""
Pulse Vector — YouTube Channel Details & Banner Synchronizer
Directly updates YouTube Channel Description, Keywords, and Banners via YouTube Data API v3.
Runs strictly from the dedicated channel_branding module.
"""

import os
import sys
import json
import argparse
import pathlib

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
BRANDING_DIR = pathlib.Path(__file__).resolve().parent
DETAILS_JSON = BRANDING_DIR / "channel_details.json"
BANNERS_DIR = BRANDING_DIR / "assets" / "banners"

# Add src/ to path to use existing OAuth authentication
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.youtube_utils import get_authenticated_service
from googleapiclient.http import MediaFileUpload

def load_details() -> dict:
    if not DETAILS_JSON.exists():
        raise FileNotFoundError(f"Missing channel details: {DETAILS_JSON}")
    with open(DETAILS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def get_current_channel_info(yt, channel_id: str = None) -> dict:
    resp = yt.channels().list(mine=True, part="snippet,brandingSettings,statistics").execute()
    items = resp.get("items", [])
    if not items:
        raise RuntimeError("No authenticated channel found.")
    return items[0]

def update_channel_details(yt, details: dict, apply: bool = False) -> bool:
    print("\n" + "=" * 62)
    print("  📋 PULSE VECTOR — YOUTUBE CHANNEL METADATA UPDATE")
    print("=" * 62)

    ch_info = get_current_channel_info(yt)
    ch_id = ch_info["id"]
    current_title = ch_info.get("snippet", {}).get("title", "")
    current_desc = ch_info.get("brandingSettings", {}).get("channel", {}).get("description", "")
    current_keywords = ch_info.get("brandingSettings", {}).get("channel", {}).get("keywords", "")

    new_desc = details["description"]
    new_keywords = details["keywords_string"]

    print(f"\n[Channel Target]: {current_title} ({ch_id})")
    print(f"[Handle]: {ch_info.get('snippet', {}).get('customUrl', '@pulse_vector')}")

    print("\n--- CURRENT DESCRIPTION ---")
    print(current_desc[:300] + ("..." if len(current_desc) > 300 else ""))

    print("\n--- NEW PROPOSED DESCRIPTION (Length: {} chars / Max 1000) ---".format(len(new_desc)))
    print(new_desc)

    print("\n--- NEW KEYWORDS (Length: {} chars) ---".format(len(new_keywords)))
    print(new_keywords)

    if not apply:
        print("\n🔍 DRY RUN COMPLETE: No live changes made to YouTube channel.")
        print("💡 Pass '--apply' to update channel description and keywords on YouTube.")
        return True

    print("\n🚀 Applying update via YouTube Data API v3 (channels().update)...")
    body = {
        "id": ch_id,
        "brandingSettings": {
            "channel": {
                "description": new_desc,
                "keywords": new_keywords
            }
        }
    }

    try:
        update_resp = yt.channels().update(part="brandingSettings", body=body).execute()
        print("✅ Channel details successfully updated on YouTube!")
        updated_settings = update_resp.get("brandingSettings", {}).get("channel", {})
        print("   • New Description Length:", len(updated_settings.get("description", "")))
        print("   • New Keywords Length:", len(updated_settings.get("keywords", "")))
        return True
    except Exception as e:
        print(f"❌ Failed to update channel details: {e}")
        return False

def upload_channel_banner(yt, banner_path: pathlib.Path, apply: bool = False) -> bool:
    print("\n" + "=" * 62)
    print("  🖼️ PULSE VECTOR — YOUTUBE CHANNEL BANNER UPLOAD")
    print("=" * 62)

    if not banner_path.exists():
        print(f"❌ Banner file not found: {banner_path}")
        return False

    size_kb = banner_path.stat().st_size // 1024
    print(f"Target Banner: {banner_path.name} ({size_kb} KB)")

    ch_info = get_current_channel_info(yt)
    ch_id = ch_info["id"]

    if not apply:
        print("🔍 DRY RUN: Banner verified. Pass '--apply' to upload banner to YouTube.")
        return True

    print("🚀 Uploading 2560x1440 banner via yt.channelBanners().insert()...")
    media = MediaFileUpload(str(banner_path), mimetype="image/png", resumable=True)

    try:
        banner_resp = yt.channelBanners().insert(channelId=ch_id, media_body=media).execute()
        banner_url = banner_resp.get("url")
        print(f"✅ Banner uploaded to YouTube CDN: {banner_url}")

        print("Updating channel brandingSettings.image.bannerExternalUrl...")
        branding_settings = ch_info.get("brandingSettings", {})
        if "image" not in branding_settings:
            branding_settings["image"] = {}
        branding_settings["image"]["bannerExternalUrl"] = banner_url

        body = {
            "id": ch_id,
            "brandingSettings": branding_settings
        }
        yt.channels().update(part="brandingSettings", body=body).execute()
        print("✅ Channel Banner successfully updated and published on YouTube!")
        return True
    except Exception as e:
        print(f"❌ Failed to upload channel banner: {e}")
        print("💡 Note: YouTube requires the banner image to be at least 2048x1152 and under 6MB.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector YouTube Channel Details & Banner Synchronizer")
    parser.add_argument("--apply", action="store_true", help="Apply live changes to YouTube (default is dry-run)")
    parser.add_argument("--upload-banner", action="store_true", help="Upload and apply the 2560x1440 master banner")
    parser.add_argument("--banner-type", choices=["multigenre", "prestige", "tactical"], default="multigenre",
                        help="Which generated banner to upload (default: multigenre)")
    args = parser.parse_args()

    details = load_details()
    yt = get_authenticated_service()
    if not yt:
        print("❌ Could not authenticate with YouTube API. Check credentials/token.json.")
        sys.exit(1)

    # 1. Update Channel Details (Description & Keywords)
    success = update_channel_details(yt, details, apply=args.apply)

    # 2. Upload Banner if requested
    if args.upload_banner:
        banner_map = {
            "multigenre": BANNERS_DIR / "banner_cinematic_multigenre_master.png",
            "editorial": BANNERS_DIR / "banner_cinematic_editorial_master.png"
        }
        b_path = banner_map.get(args.banner_type, BANNERS_DIR / "banner_cinematic_multigenre_master.png")
        b_success = upload_channel_banner(yt, b_path, apply=args.apply)
        success = success and b_success

    if args.apply and success:
        print("\n🎉 ALL REQUESTED CHANNEL BRANDING UPDATES APPLIED TO YOUTUBE!")
        print("🔗 View Channel: https://youtube.com/@pulse_vector")
        print("⚙️ YouTube Studio Customization: https://studio.youtube.com/channel/UCt154eXNnEfKtRNBrAnay7A/editing/profile")

if __name__ == "__main__":
    main()
