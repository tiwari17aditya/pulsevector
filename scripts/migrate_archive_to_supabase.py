import os
import sys
import glob
import time
import datetime
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Import core database functions
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
from core.database_utils import get_supabase_client, upload_file_to_storage, save_metadata
from core.config import ARCHIVE_DIR

file_type_map = {
    ".png": ("image", "images"),
    ".jpg": ("image", "images"),
    ".jpeg": ("image", "images"),
    ".mp4": ("video", "videos"),
    ".txt": ("text", "texts"),
    ".mp3": ("audio", "audio"),
    ".wav": ("audio", "audio"),
}

def process_single_file(file_path: str, archive_path: str, bucket_name: str):
    rel_path = os.path.relpath(file_path, archive_path).replace("\\", "/")
    ext = os.path.splitext(file_path)[1].lower()
    
    f_type, folder = file_type_map.get(ext, ("other", "other"))
    dest_path = f"{folder}/{rel_path}"
    
    try:
        url = upload_file_to_storage(file_path, bucket_name, dest_path)
        if url:
            mtime = os.path.getmtime(file_path)
            run_date = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()
            
            save_metadata("pipeline_runs", {
                "run_date": run_date,
                "file_type": f_type,
                "file_path": rel_path,
                "url": url
            }, on_conflict="file_path")
            return True, rel_path
        else:
            return False, rel_path
    except Exception as e:
        logging.error(f"Error uploading {rel_path}: {e}")
        return False, rel_path

def migrate_archive(bucket_name: str = "pulse-vector-media", max_files: int = None, workers: int = 16):
    print(f"🚀 Starting Multithreaded Migration of pulse_archive to Supabase ({workers} workers)...")
    logging.info(f"Starting multithreaded archive migration ({workers} workers)...")
    
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Supabase client initialization failed. Please check SUPABASE_URL and SUPABASE_KEY.")
        sys.exit(1)
        
    archive_path = str(ARCHIVE_DIR)
    if not os.path.exists(archive_path):
        print(f"❌ Archive directory not found: {archive_path}")
        sys.exit(1)
        
    print(f"📂 Scanning archive directory: {archive_path}")
    all_files = [f for f in glob.glob(os.path.join(archive_path, "**", "*"), recursive=True) if os.path.isfile(f)]
    total_files = len(all_files)
    
    if max_files:
        all_files = all_files[:max_files]
        
    print(f"📊 Found {total_files} files in archive. Processing {len(all_files)} files with {workers} parallel threads...")
    
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_file = {
            executor.submit(process_single_file, f, archive_path, bucket_name): f 
            for f in all_files
        }
        
        processed = 0
        for future in as_completed(future_to_file):
            processed += 1
            success, rel_p = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1
                
            if processed % 50 == 0 or processed == len(all_files):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                pct = (processed / len(all_files)) * 100
                print(f"⌛ Progress: [{processed}/{len(all_files)}] ({pct:.1f}%) - Rate: {rate:.1f} files/sec - Success: {success_count}, Failed: {fail_count}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("🎉 Migration Summary:")
    print(f"   - Total files processed: {len(all_files)}")
    print(f"   - Successfully uploaded & saved: {success_count}")
    print(f"   - Failed: {fail_count}")
    print(f"   - Total elapsed time: {elapsed:.2f} seconds ({len(all_files)/elapsed:.1f} files/sec)")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate local pulse_archive files to Supabase Storage & Database")
    parser.add_argument("--bucket", default="pulse-vector-media", help="Supabase storage bucket name")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    parser.add_argument("--workers", type=int, default=16, help="Number of concurrent upload threads")
    
    args = parser.parse_args()
    migrate_archive(bucket_name=args.bucket, max_files=args.limit, workers=args.workers)
