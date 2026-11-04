"""
Pulse Vector — Channel Branding Version Archiver
Automates snapshotting the active branding into channel_branding/history/
and updating branding_ledger.json and branding_ledger.md.
"""

import os
import sys
import json
import shutil
import argparse
import datetime
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
BRANDING_DIR = pathlib.Path(__file__).resolve().parent
HISTORY_DIR = BRANDING_DIR / "history"
LEDGER_JSON = BRANDING_DIR / "branding_ledger.json"
LEDGER_MD = BRANDING_DIR / "branding_ledger.md"
DETAILS_JSON = BRANDING_DIR / "channel_details.json"

def archive_version(version: str, codename: str, banner_path: pathlib.Path, icon_path: pathlib.Path, cdn_url: str = ""):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    clean_codename = codename.lower().replace(" ", "_")
    target_dir = HISTORY_DIR / f"{version}_{today_str}_{clean_codename}"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Archiving branding version {version} ({codename}) to: {target_dir}...")

    # Copy banner & icon
    if banner_path.exists():
        shutil.copy2(banner_path, target_dir / "banner.png")
    if icon_path.exists():
        shutil.copy2(icon_path, target_dir / "icon_master.png")

    # Load details
    with open(DETAILS_JSON, "r", encoding="utf-8") as f:
        details = json.load(f)

    snapshot = {
        "version": version,
        "codename": codename,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "ARCHIVED",
        "youtube_banner_cdn_url": cdn_url,
        "banner_file": str(banner_path.relative_to(BRANDING_DIR)),
        "icon_file": str(icon_path.relative_to(BRANDING_DIR)),
        "channel_title": details.get("title"),
        "channel_handle": details.get("custom_url"),
        "description": details.get("description"),
        "keywords_string": details.get("keywords_string")
    }

    with open(target_dir / "metadata_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    # Update ledger
    if LEDGER_JSON.exists():
        with open(LEDGER_JSON, "r", encoding="utf-8") as f:
            ledger = json.load(f)
        ledger["versions"].append(snapshot)
        with open(LEDGER_JSON, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)

    print(f"✅ Version {version} successfully archived.")

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Branding Version Archiver")
    parser.add_argument("--version", required=True, help="Semantic version (e.g. v1.1.0)")
    parser.add_argument("--codename", required=True, help="Codename for this branding iteration")
    parser.add_argument("--banner", default=str(BRANDING_DIR / "assets" / "banners" / "banner_cinematic_multigenre_master.png"))
    parser.add_argument("--icon", default=str(BRANDING_DIR / "assets" / "icons" / "icon_pulse_vector_3d_master.png"))
    parser.add_argument("--cdn-url", default="", help="YouTube CDN URL returned after upload")
    args = parser.parse_args()

    archive_version(args.version, args.codename, pathlib.Path(args.banner), pathlib.Path(args.icon), args.cdn_url)

if __name__ == "__main__":
    main()
