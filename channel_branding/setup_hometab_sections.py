"""
Pulse Vector — YouTube Channel Home Tab Sections Architect & Automation
Configures the YouTube Channel Home Tab shelves/sections via YouTube Data API v3 (channelSections).
Provides a high-retention, high-converting showcase across all genres:
  1. Daily Current Affairs (Oct-Dec 2026) [Active flagship daily series]
  2. Last Day on Earth: Survival [105-episode epic gaming playthrough]
  3. Daily Brain Teasers - 2026 [High-engagement puzzle shorts]
  4. Mahabharat: The Epic Battle of Dharma [70-episode animated series]
  5. Weekly Current Affairs Masterclasses [Deep dive analytical series]
  6. Recent Uploads [Fresh content across all categories]
  7. Channel Playlists Directory [Complete archive exploration]
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
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.youtube_utils import get_authenticated_service

TARGET_SHELVES = [
    {
        "title": "Daily Current Affairs (Oct - Dec 2026)",
        "type": "singleplaylist",
        "playlist_id": "PLKaPhI3LucGw",
        "description": "Daily UPSC/competitive exam intelligence briefs"
    },
    {
        "title": "Last Day on Earth: Survival — Official Gameplay Series",
        "type": "singleplaylist",
        "playlist_id": "PLJPzVNVZwaGY",
        "description": "Complete survival bunker raids, sector 7 & boss fights"
    },
    {
        "title": "Daily Brain Teasers — 2026",
        "type": "singleplaylist",
        "playlist_id": "PLENP5DyB-lS4",
        "description": "Daily IQ challenges, logic puzzles & brain workouts"
    },
    {
        "title": "Mahabharat: The Epic Battle of Dharma (Animated)",
        "type": "singleplaylist",
        "playlist_id": "PLTdRkcKiCRVA",
        "description": "Complete cinematic animated epic series"
    },
    {
        "title": "Weekly Current Affairs Masterclasses",
        "type": "singleplaylist",
        "playlist_id": "PL4PQLXRi54n0f5deGjKOCuz3VbMOMzmxO",
        "description": "Deep-dive analytical retrospectives & geopolitical summaries"
    },
    {
        "title": "Latest Uploads",
        "type": "recentuploads",
        "playlist_id": None,
        "description": "Most recent drops across all channels & pipelines"
    },
    {
        "title": "All Playlists Directory",
        "type": "allplaylists",
        "playlist_id": None,
        "description": "Explore the full Pulse Vector catalog"
    }
]

def get_current_sections(yt):
    resp = yt.channelSections().list(
        part="id,snippet,contentDetails",
        mine=True
    ).execute()
    return resp.get("items", [])

def print_sections(sections, header="Current Home Tab Sections"):
    print("\n" + "=" * 68)
    print(f"  📺 PULSE VECTOR — {header.upper()}")
    print("=" * 68)
    if not sections:
        print("  (No sections configured on this channel)")
        return

    for idx, s in enumerate(sections):
        s_id = s.get("id", "Unknown")
        snippet = s.get("snippet", {})
        s_type = snippet.get("type", "unknown")
        pos = snippet.get("position", idx)
        playlists = s.get("contentDetails", {}).get("playlists", [])
        pl_str = f"-> Playlist: {playlists[0]}" if playlists else ""
        print(f"  [{pos}] ID: {s_id}")
        print(f"      Type: {s_type} {pl_str}")
    print("=" * 68)

def clean_all_sections(yt, apply=False):
    sections = get_current_sections(yt)
    print(f"\nFound {len(sections)} existing channel sections to clear.")
    for s in sections:
        s_id = s.get("id")
        s_type = s.get("snippet", {}).get("type")
        if not apply:
            print(f"  [DRY RUN] Would delete section: {s_id} ({s_type})")
        else:
            try:
                print(f"  🗑️ Deleting section: {s_id} ({s_type})...", end="", flush=True)
                yt.channelSections().delete(id=s_id).execute()
                print(" DONE ✅")
            except Exception as e:
                print(f" FAILED: {e}")

def setup_hometab(yt, apply=False):
    print("\n" + "=" * 68)
    print("  🚀 CONFIGURING PULSE VECTOR OPTIMIZED HOME TAB LAYOUT")
    print("=" * 68)

    print(f"Target Shelves Count: {len(TARGET_SHELVES)}")
    for i, shelf in enumerate(TARGET_SHELVES):
        print(f"  Shelf {i+1}: {shelf['title']} ({shelf['type']})")
        print(f"           {shelf['description']}")

    if not apply:
        print("\n🔍 DRY RUN: No sections were deleted or created.")
        print("💡 Pass '--apply' to wipe old/broken sections and apply this layout live.")
        return True

    # 1. Clear existing sections so we have a clean slate in the exact desired order
    print("\n--- STEP 1: Purging Old & Broken Shelves ---")
    clean_all_sections(yt, apply=True)

    # 2. Sequentially insert target shelves
    print("\n--- STEP 2: Building High-Converting Shelves ---")
    success_count = 0
    for pos, shelf in enumerate(TARGET_SHELVES):
        body = {
            "snippet": {
                "type": shelf["type"],
                "position": pos
            }
        }
        if shelf["playlist_id"]:
            body["contentDetails"] = {
                "playlists": [shelf["playlist_id"]]
            }

        try:
            print(f"  ➕ Adding Shelf {pos+1}/{len(TARGET_SHELVES)}: {shelf['title']}...", end="", flush=True)
            res = yt.channelSections().insert(
                part="snippet,contentDetails",
                body=body
            ).execute()
            new_id = res.get("id", "OK")
            print(f" SUCCESS ✅ (ID: {new_id})")
            success_count += 1
        except Exception as e:
            print(f" FAILED ❌: {e}")

    print(f"\nSuccessfully created {success_count}/{len(TARGET_SHELVES)} sections!")
    
    # 3. Verify
    print("\n--- STEP 3: Verifying Final Live Channel Sections ---")
    final_sections = get_current_sections(yt)
    print_sections(final_sections, "Final Live Home Tab Configuration")
    return success_count == len(TARGET_SHELVES)

def main():
    parser = argparse.ArgumentParser(description="YouTube Home Tab Shelf Manager")
    parser.add_argument("--list", action="store_true", help="List current sections on channel")
    parser.add_argument("--apply", action="store_true", help="Execute live changes to channel")
    parser.add_argument("--clean-only", action="store_true", help="Delete all sections only")
    args = parser.parse_args()

    yt = get_authenticated_service()

    if args.list:
        sections = get_current_sections(yt)
        print_sections(sections)
        return

    if args.clean_only:
        clean_all_sections(yt, apply=args.apply)
        return

    setup_hometab(yt, apply=args.apply)

if __name__ == "__main__":
    main()
