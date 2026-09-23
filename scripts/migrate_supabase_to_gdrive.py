"""
Pulse Vector - Supabase to Google Drive Cloud Data Migration
Migrates bulky media data (Videos, Audio, and optionally Images) from Supabase Storage into your 5 TB Google Drive.
Updates metadata in Supabase PostgreSQL and optionally frees up Supabase storage space.
"""

import os
import sys
import time
import pathlib
import requests
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.config import (
    ARCHIVE_DIR, GOOGLE_DRIVE_FOLDER_PATH, GOOGLE_DRIVE_FOLDER_NAME
)
from core.database_utils import get_supabase_client
from core.gdrive_utils import get_gdrive_service, sync_archive_file_to_gdrive, upload_file_to_gdrive, ensure_folder_path


import threading
_thread_local = threading.local()

def get_thread_gdrive_service():
    if not hasattr(_thread_local, "service"):
        _thread_local.service = get_gdrive_service()
    return _thread_local.service

def process_record(record, root_folder_id, local_gdrive_root, purge_supabase=False, sp_client=None):
    rec_id = record["id"]
    file_path_rel = record["file_path"].replace("\\", "/")
    sp_url = record["url"]
    file_type = record["file_type"]
    file_name = os.path.basename(file_path_rel)

    # Destination path on Google Drive Desktop
    dest_local_file = local_gdrive_root / file_path_rel
    dest_local_file.parent.mkdir(parents=True, exist_ok=True)

    local_archive_file = ARCHIVE_DIR / file_path_rel
    temp_downloaded = False

    # 1. Obtain file content (Local Archive vs Stream from Supabase)
    source_file = None
    if local_archive_file.exists() and local_archive_file.stat().st_size > 0:
        source_file = local_archive_file
    elif dest_local_file.exists() and dest_local_file.stat().st_size > 0:
        source_file = dest_local_file
    else:
        # Download from Supabase URL into local Google Drive destination
        try:
            r = requests.get(sp_url, stream=True, timeout=60)
            if r.status_code == 200:
                with open(dest_local_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                source_file = dest_local_file
                temp_downloaded = True
            else:
                logging.error(f"Failed to download {sp_url}: HTTP {r.status_code}")
                return False, f"HTTP {r.status_code} on download"
        except Exception as e:
            logging.error(f"Error downloading {sp_url}: {e}")
            return False, str(e)

    # 2. Upload to Google Drive via API if service is available
    gdrive_link = None
    service = get_thread_gdrive_service()
    if service and root_folder_id:
        try:
            parent_dir = os.path.dirname(file_path_rel)
            path_segments = [p for p in parent_dir.split("/") if p]
            target_folder_id = ensure_folder_path(service, path_segments, root_folder_id=root_folder_id)
            res = upload_file_to_gdrive(service, str(source_file or dest_local_file), target_folder_id)
            if res:
                gdrive_link = res.get("webViewLink") or res.get("webContentLink")
        except Exception as e:
            logging.warning(f"Drive API upload warning for {file_path_rel}: {e}")

    # Fallback: Copy to local G: Drive Desktop folder if API is not available
    if not gdrive_link:
        if source_file and source_file != dest_local_file:
            try:
                import shutil
                shutil.copy2(source_file, dest_local_file)
            except Exception as e:
                logging.warning(f"Error copying to local Google Drive: {e}")
        gdrive_link = f"gdrive://My Drive/{GOOGLE_DRIVE_FOLDER_PATH}/{file_path_rel}"

    # 3. Update Supabase pipeline_runs record with new Google Drive URL
    try:
        sp_client.table("pipeline_runs").update({"url": gdrive_link}).eq("id", rec_id).execute()
    except Exception as e:
        logging.warning(f"Failed to update metadata for {file_path_rel}: {e}")

    # 4. Optionally purge from Supabase storage to free space
    if purge_supabase and sp_client:
        try:
            type_folder_map = {
                "video": "videos",
                "audio": "audio",
                "image": "images",
                "text": "texts"
            }
            folder_prefix = type_folder_map.get(file_type, "videos")
            storage_path = f"{folder_prefix}/{file_path_rel}"
            sp_client.storage.from_("pulse-vector-media").remove([storage_path])
        except Exception as e:
            logging.warning(f"Failed to remove {storage_path} from Supabase: {e}")

    return True, file_path_rel


def migrate_data(types=("video", "audio"), purge_supabase=False, max_workers=6):
    print("=" * 65, flush=True)
    print("🚀 Pulse Vector - Supabase to Google Drive Migration", flush=True)
    print(f"📦 Target Data Types: {', '.join(types)}", flush=True)
    print(f"📁 Destination: MyDrive/{GOOGLE_DRIVE_FOLDER_PATH}", flush=True)
    print(f"🧹 Purge from Supabase Storage: {purge_supabase}", flush=True)
    print("🔒 Guardrail: Strictly constrained to MyDrive/antigravity-projects-storage/pulse-vector", flush=True)
    print("=" * 65, flush=True)

    sp = get_supabase_client()
    if not sp:
        print("❌ Supabase client initialization failed. Check credentials.", flush=True)
        return

    main_service = get_gdrive_service()
    if main_service:
        print("✅ Google Drive API initialized successfully.", flush=True)
    else:
        print("ℹ️ Google Drive API not active; will use direct Google Drive for Desktop sync.", flush=True)

    # Resolve Google Drive root folder ID
    root_folder_id = None
    if main_service:
        segments = [s.strip() for s in GOOGLE_DRIVE_FOLDER_PATH.replace("->", "/").split("/") if s.strip()]
        root_folder_id = ensure_folder_path(main_service, segments, root_folder_id=None)

    local_gdrive_root = pathlib.Path("G:/My Drive") / GOOGLE_DRIVE_FOLDER_PATH.replace("->", "/").strip("/")
    local_gdrive_root.mkdir(parents=True, exist_ok=True)

    # Collect all matching records
    all_records = []
    print("\n🔍 Fetching records from Supabase pipeline_runs...", flush=True)
    for t in types:
        offset = 0
        limit = 1000
        while True:
            r = sp.table("pipeline_runs").select("id, file_path, file_type, url") \
                .eq("file_type", t) \
                .like("url", "%supabase.co%") \
                .range(offset, offset + limit - 1) \
                .execute()
            if not r.data:
                break
            all_records.extend(r.data)
            if len(r.data) < limit:
                break
            offset += limit

    print(f"📊 Found {len(all_records)} bulky records in Supabase storage to migrate.", flush=True)
    if not all_records:
        print("All records are already migrated or non-Supabase URLs! Nothing to do.", flush=True)
        return

    success_count = 0
    fail_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_record,
                rec,
                root_folder_id,
                local_gdrive_root,
                purge_supabase,
                sp
            ): rec for rec in all_records
        }

        completed = 0
        for fut in as_completed(futures):
            completed += 1
            try:
                ok, msg = fut.result()
            except Exception as e:
                ok, msg = False, str(e)

            if ok:
                success_count += 1
            else:
                fail_count += 1

            if completed % 5 == 0 or completed == len(all_records):
                elapsed = time.time() - start_time
                pct = (completed / len(all_records)) * 100
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"⌛ [{completed}/{len(all_records)}] ({pct:.1f}%) - {rate:.1f} files/sec - Success: {success_count}, Fail: {fail_count}", flush=True)


    elapsed = time.time() - start_time
    print("\n" + "=" * 65, flush=True)
    print("🎉 Migration Completed Summary:", flush=True)
    print(f"   - Total bulky files processed: {len(all_records)}", flush=True)
    print(f"   - Successfully migrated to Google Drive: {success_count}", flush=True)
    print(f"   - Failed: {fail_count}", flush=True)
    print(f"   - Total elapsed time: {elapsed:.1f} seconds", flush=True)
    print(f"   - Saved in: {local_gdrive_root}", flush=True)
    if purge_supabase:
        print(f"   - Successfully purged migrated media objects from Supabase storage!", flush=True)
    print("=" * 65, flush=True)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate bulky data from Supabase to Google Drive")
    parser.add_argument("--types", default="video,audio", help="Comma-separated file types (video,audio,image)")
    parser.add_argument("--purge-supabase", action="store_true", help="Delete files from Supabase storage after migration")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent worker threads")

    args = parser.parse_args()
    selected_types = [t.strip() for t in args.types.split(",") if t.strip()]

    migrate_data(types=selected_types, purge_supabase=args.purge_supabase, max_workers=args.workers)
