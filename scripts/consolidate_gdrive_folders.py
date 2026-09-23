"""
Pulse Vector - Google Drive Folder Consolidation & Deduplication Script
Safely merges files from duplicate folders ('antigravity-projects-storage (1)' and subdirectories with '(1)', '(2)')
into the primary canonical folder ('antigravity-projects-storage/pulse-vector').
Supports --dry-run (preview only) and --execute (live safe consolidation).
"""

import os
import sys
import re
import shutil
import pathlib
import argparse
import logging

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.gdrive_utils import get_gdrive_service

PRIMARY_ROOT = pathlib.Path(r"G:\My Drive\antigravity-projects-storage\pulse-vector")
DUPLICATE_ROOT = pathlib.Path(r"G:\My Drive\antigravity-projects-storage (1)\pulse-vector")
API_DUPLICATE_FOLDER_ID = "1nXOpMPCQdmJ7DnGjsnGcCf17FYKOSSCu"  # Folder ID of the API-created antigravity-projects-storage


def normalize_rel_path(rel_path_str: str) -> str:
    """
    Removes Windows collision suffixes like ' (1)', ' (2)' from directory and file names.
    e.g. '2026/August (1)/video.mp4' -> '2026/August/video.mp4'
         'temp_end_frames (2)/frame_001.png' -> 'temp_end_frames/frame_001.png'
    """
    parts = pathlib.Path(rel_path_str).parts
    clean_parts = []
    for part in parts:
        clean_part = re.sub(r"\s+\(\d+\)", "", part)
        clean_parts.append(clean_part)
    return str(pathlib.Path(*clean_parts))


def scan_and_plan():
    if not DUPLICATE_ROOT.exists():
        print(f"✅ Duplicate folder '{DUPLICATE_ROOT}' does not exist. Nothing to consolidate.")
        return [], []

    files_to_copy = []
    files_already_present = []

    for root, dirs, files in os.walk(DUPLICATE_ROOT):
        for f in files:
            source_file = pathlib.Path(root) / f
            try:
                rel_from_dup = source_file.relative_to(DUPLICATE_ROOT)
                clean_rel = normalize_rel_path(str(rel_from_dup))
                dest_file = PRIMARY_ROOT / clean_rel

                source_size = source_file.stat().st_size
                if dest_file.exists():
                    dest_size = dest_file.stat().st_size
                    if dest_size == source_size:
                        files_already_present.append((source_file, dest_file, source_size))
                    else:
                        files_to_copy.append((source_file, dest_file, source_size, True)) # overwrite/update
                else:
                    files_to_copy.append((source_file, dest_file, source_size, False)) # new file
            except Exception as e:
                print(f"⚠️ Error scanning {source_file}: {e}")

    return files_to_copy, files_already_present


def main():
    parser = argparse.ArgumentParser(description="Consolidate duplicate Google Drive folders into a single unified directory.")
    parser.add_argument("--execute", action="store_true", help="Perform live merge and trash duplicate cloud folder.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview actions without modifying files.")
    args = parser.parse_args()

    execute_mode = args.execute

    print("=" * 65)
    print("📁 Pulse Vector - Google Drive Consolidation & Deduplication")
    print(f"Primary Canonical Folder:   {PRIMARY_ROOT}")
    print(f"Duplicate Folder to Merge:  {DUPLICATE_ROOT}")
    print(f"Mode:                       {'🔴 LIVE EXECUTION' if execute_mode else '🟢 DRY-RUN PREVIEW'}")
    print("=" * 65)

    if not PRIMARY_ROOT.exists():
        print(f"❌ Primary root '{PRIMARY_ROOT}' does not exist! Please verify path.")
        sys.exit(1)

    files_to_copy, files_already_present = scan_and_plan()

    print(f"\n📊 Scan Results:")
    print(f"  - Files already present in primary (exact duplicates): {len(files_already_present)}")
    print(f"  - Files needing merge/copy into primary:              {len(files_to_copy)}")

    if files_to_copy:
        print("\n📥 Sample of files to be merged into primary:")
        for src, dst, sz, is_update in files_to_copy[:10]:
            print(f"  {'[UPDATE]' if is_update else '[NEW]'} {dst.relative_to(PRIMARY_ROOT)} ({sz / 1024:.1f} KB)")
        if len(files_to_copy) > 10:
            print(f"  ... and {len(files_to_copy) - 10} more files")

    if not execute_mode:
        print("\n" + "=" * 65)
        print("💡 Dry-run complete. No files were moved or deleted.")
        print("Run with '--execute' to perform the consolidation and trash the duplicate folder.")
        print("=" * 65)
        return

    # LIVE EXECUTION
    print("\n🚀 Executing consolidation...")
    copied_count = 0
    for src, dst, sz, is_update in files_to_copy:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied_count += 1
        except Exception as e:
            print(f"❌ Failed to copy {src} to {dst}: {e}")

    print(f"✅ Successfully copied/merged {copied_count} files into '{PRIMARY_ROOT}'.")

    # Trash duplicate folder via Google Drive API
    print("\n🗑️ Trashing duplicate cloud folder in Google Drive...")
    service = get_gdrive_service()
    if service:
        try:
            # Check duplicate root folder
            res = service.files().get(fileId=API_DUPLICATE_FOLDER_ID, fields="id, name, trashed").execute()
            if res and not res.get("trashed"):
                service.files().update(fileId=API_DUPLICATE_FOLDER_ID, body={"trashed": True}).execute()
                print(f"✅ Moved duplicate cloud folder '{res.get('name')}' (ID: {API_DUPLICATE_FOLDER_ID}) to Google Drive Trash.")
            else:
                print("ℹ️ Duplicate folder was already trashed or not found.")
        except Exception as e:
            print(f"⚠️ Cloud trash note: {e}")
            print("You can also manually delete 'antigravity-projects-storage (1)' from Google Drive Web.")
    else:
        print("ℹ️ Google Drive API service unavailable; please remove 'antigravity-projects-storage (1)' from Google Drive Web.")

    print("\n" + "=" * 65)
    print("🎉 Consolidation finished! Google Drive for Desktop will synchronize")
    print("and remove 'antigravity-projects-storage (1)', leaving only one folder.")
    print("=" * 65)


if __name__ == "__main__":
    main()
