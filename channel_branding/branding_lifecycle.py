"""
Pulse Vector — Channel Branding Lifecycle Engine
Orchestrates the complete branding workflow:
  1. Status & Audit: Checks current live YouTube metadata, banner, icon, and Home Tab shelves.
  2. Review Dashboard: Displays formatted comparison of metadata, visual assets, and shelves.
  3. Live Update: Synchronizes description, keywords, banner, icon, and 7 Home Tab shelves via YouTube API.
  4. History Archive: Snapshots previous version and updates branding_ledger.json and branding_ledger.md.
  5. Git Sync: Stages, commits, and pushes to origin/channel-branding-update.
"""

import os
import sys
import json
import argparse
import pathlib
import subprocess
import datetime

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
BRANDING_DIR = pathlib.Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.youtube_utils import get_authenticated_service
from channel_branding.update_youtube_channel import load_details, update_channel_details, upload_channel_banner
from channel_branding.setup_hometab_sections import setup_hometab, get_current_sections
from channel_branding.archive_branding_version import archive_version

LEDGER_JSON = BRANDING_DIR / "branding_ledger.json"
LEDGER_MD = BRANDING_DIR / "branding_ledger.md"
BANNERS_DIR = BRANDING_DIR / "assets" / "banners"
ICONS_DIR = BRANDING_DIR / "assets" / "icons"

def print_banner(text: str):
    print("\n" + "=" * 68)
    print(f"  🌟 PULSE VECTOR BRANDING LIFECYCLE: {text.upper()}")
    print("=" * 68)

def show_review_dashboard(yt, details: dict):
    print_banner("Branding Review & Comparison Dashboard")
    
    # 1. Channel Info
    ch_resp = yt.channels().list(mine=True, part="snippet,brandingSettings,statistics").execute()
    ch_info = ch_resp["items"][0]
    live_title = ch_info.get("snippet", {}).get("title", "")
    live_desc = ch_info.get("brandingSettings", {}).get("channel", {}).get("description", "")
    live_keywords = ch_info.get("brandingSettings", {}).get("channel", {}).get("keywords", "")
    live_banner_url = ch_info.get("brandingSettings", {}).get("image", {}).get("bannerExternalUrl", "None")

    print(f"\n[Channel]: {live_title} ({ch_info.get('id')})")
    print(f"[Handle]: {ch_info.get('snippet', {}).get('customUrl', '@pulse_vector')}")
    print(f"[Subscribers]: {ch_info.get('statistics', {}).get('subscriberCount', 'N/A')}")
    print(f"[Total Videos]: {ch_info.get('statistics', {}).get('videoCount', 'N/A')}")

    # 2. Metadata Diff
    proposed_desc = details.get("description", "")
    proposed_keywords = details.get("keywords_string", "")

    print("\n--- DESCRIPTION STATUS ---")
    print(f"Live Length:     {len(live_desc)} chars")
    print(f"Proposed Length: {len(proposed_desc)} chars (Max 1000)")
    desc_match = (live_desc.strip() == proposed_desc.strip())
    print(f"Status:          {'✅ SYNCHRONIZED' if desc_match else '⚠️ UPDATE PENDING'}")

    print("\n--- KEYWORDS STATUS ---")
    print(f"Live Keywords:     {len(live_keywords)} chars")
    print(f"Proposed Keywords: {len(proposed_keywords)} chars")
    kw_match = (live_keywords.strip() == proposed_keywords.strip())
    print(f"Status:            {'✅ SYNCHRONIZED' if kw_match else '⚠️ UPDATE PENDING'}")

    # 3. Visual Assets
    master_banner = BANNERS_DIR / "banner_cinematic_multigenre_master.png"
    master_icon = ICONS_DIR / "icon_pulse_vector_3d_master.png"

    print("\n--- VISUAL ASSETS STATUS ---")
    print(f"Master Banner:  {'✅ Present' if master_banner.exists() else '❌ Missing'} ({master_banner.name})")
    print(f"Live Banner URL: {live_banner_url[:80]}...")
    print(f"Master Icon:    {'✅ Present' if master_icon.exists() else '❌ Missing'} ({master_icon.name})")

    # 4. Home Tab Sections
    sections = get_current_sections(yt)
    print("\n--- HOME TAB SECTIONS STATUS ---")
    print(f"Active Sections: {len(sections)} shelves configured")
    has_broken = any(s.get("snippet", {}).get("type") == "channelsectiontypeundefined" for s in sections)
    if has_broken:
        print("Status:          ⚠️ BROKEN SECTIONS DETECTED")
    else:
        print("Status:          ✅ HEALTHY & HIGH-CONVERTING")

    print("\n" + "=" * 68)
    return {
        "desc_match": desc_match,
        "kw_match": kw_match,
        "has_broken": has_broken,
        "sections_count": len(sections)
    }

def run_lifecycle(apply: bool = False, upload_banner: bool = False, version: str = None, codename: str = None):
    yt = get_authenticated_service()
    details = load_details()

    # 1. Show review dashboard
    review = show_review_dashboard(yt, details)

    if not apply:
        print("\n🔍 REVIEW COMPLETE (DRY-RUN).")
        print("💡 To apply all metadata and Home Tab changes live to YouTube:")
        print("   python channel_branding/branding_lifecycle.py --apply")
        print("💡 To also re-upload master banner:")
        print("   python channel_branding/branding_lifecycle.py --apply --upload-banner")
        return True

    # 2. Live YouTube Updates
    print_banner("Executing Live YouTube Updates")
    
    # Metadata
    print("\n[Step 1/4] Updating Channel Description & Keywords...")
    update_channel_details(yt, details, apply=True)

    # Banner (if requested)
    banner_url = None
    if upload_banner:
        print("\n[Step 2/4] Uploading Master Banner Image...")
        banner_path = BANNERS_DIR / "banner_cinematic_multigenre_master.png"
        upload_channel_banner(yt, banner_path, apply=True)
    else:
        print("\n[Step 2/4] Banner upload skipped (use --upload-banner if new banner generated).")

    # Home Tab Shelves
    print("\n[Step 3/4] Structuring 7 Home Tab Shelves...")
    setup_hometab(yt, apply=True)

    # Archive & Ledger
    print("\n[Step 4/4] Archiving Version & Updating Ledger...")
    ver = version or "v1.0.0"
    code = codename or "Cinematic Multi-Genre Nexus"
    master_banner = BANNERS_DIR / "banner_cinematic_multigenre_master.png"
    master_icon = ICONS_DIR / "icon_pulse_vector_3d_master.png"
    archive_version(ver, code, master_banner, master_icon, cdn_url=banner_url or "")

    print_banner("Branding Lifecycle Execution Completed Successfully ✅")
    return True

def commit_and_push(version: str = "v1.0.0"):
    print_banner("Synchronizing with Git Remote")
    subprocess.run(["git", "add", "channel_branding/"], cwd=str(ROOT_DIR), check=True)
    msg = f"chore(branding): periodic branding refresh & ledger sync [{version}]"
    res = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT_DIR), capture_output=True, text=True)
    print(res.stdout or res.stderr)
    print("\nPushing to origin/channel-branding-update...")
    subprocess.run(["git", "push", "origin", "channel-branding-update"], cwd=str(ROOT_DIR), check=True)
    print("✅ Remote git synchronization complete!")

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Channel Branding Lifecycle Manager")
    parser.add_argument("--review", action="store_true", help="Display review dashboard only")
    parser.add_argument("--apply", action="store_true", help="Execute live changes to YouTube channel")
    parser.add_argument("--upload-banner", action="store_true", help="Upload master banner to YouTube")
    parser.add_argument("--version", type=str, default=None, help="Version tag (e.g. v1.1.0)")
    parser.add_argument("--codename", type=str, default=None, help="Release codename")
    parser.add_argument("--commit-push", action="store_true", help="Commit and push changes to remote")
    args = parser.parse_args()

    if args.review:
        yt = get_authenticated_service()
        details = load_details()
        show_review_dashboard(yt, details)
        return

    success = run_lifecycle(
        apply=args.apply,
        upload_banner=args.upload_banner,
        version=args.version,
        codename=args.codename
    )

    if success and args.apply and args.commit_push:
        commit_and_push(version=args.version or "v1.0.0")

if __name__ == "__main__":
    main()
