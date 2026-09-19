import os
import logging
import mimetypes
from supabase import create_client, Client
from .config import ARCHIVE_DIR, ENABLE_GDRIVE_UPLOAD, ENABLE_SUPABASE_STORAGE_UPLOAD
from .gdrive_utils import sync_archive_file_to_gdrive

# Max file size for Supabase Free Tier storage uploads (in MB)
MAX_STORAGE_UPLOAD_MB = float(os.getenv("SUPABASE_MAX_FILE_MB", "45.0"))

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")
        return None

def upload_file_to_storage(file_path: str, bucket_name: str, destination_path: str) -> str:
    supabase = get_supabase_client()
    if not supabase:
        logging.warning("Supabase credentials not found. Skipping file upload.")
        return None
    
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist. Cannot upload.")
        return None
        
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_STORAGE_UPLOAD_MB:
            logging.warning(
                f"File {file_path} ({file_size_mb:.2f} MB) exceeds maximum Supabase upload size of {MAX_STORAGE_UPLOAD_MB} MB. Skipping storage upload to avoid 413 error."
            )
            return None
            
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        with open(file_path, 'rb') as f:
            res = supabase.storage.from_(bucket_name).upload(
                path=destination_path,
                file=f,
                file_options={
                    "upsert": "true",
                    "content-type": mime_type
                }
            )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(destination_path)
        logging.info(f"Successfully uploaded {file_path} to Supabase bucket '{bucket_name}' at {destination_path}")
        return public_url
    except Exception as e:
        logging.warning(f"Error uploading {file_path} to Supabase storage: {e}")
        return None

def save_metadata(table_name: str, data: dict, on_conflict: str = "file_path"):
    supabase = get_supabase_client()
    if not supabase:
        logging.warning("Supabase credentials not found. Skipping metadata insert.")
        return None
        
    try:
        res = supabase.table(table_name).upsert(data, on_conflict=on_conflict).execute()
        logging.info(f"Successfully saved metadata to {table_name}")
        return res
    except Exception as e:
        logging.warning(f"Error saving metadata to Supabase table {table_name}: {e}")
        return None

def run_database_upload(cutoff_hours: float = 24):
    import glob
    import datetime
    import time
    
    print("\n🚀 Starting Cloud Sync (Google Drive & Supabase)...")
    logging.info("Starting cloud sync...")
    
    supabase = get_supabase_client()
    
    cutoff_time = (time.time() - (cutoff_hours * 3600)) if cutoff_hours is not None else 0
    gdrive_uploaded_count = 0
    supabase_uploaded_count = 0
    metadata_count = 0

    file_configs = [
        ("*.mp4", "video", "videos"),
        ("*.png", "image", "images"),
        ("*.txt", "text", "texts"),
        ("*.mp3", "audio", "audio"),
    ]
    
    try:
        for ext, f_type, folder in file_configs:
            files = glob.glob(os.path.join(ARCHIVE_DIR, "**", ext), recursive=True)
            for file_path in files:
                if cutoff_hours is not None and os.path.getmtime(file_path) < cutoff_time:
                    continue
                    
                rel_path = os.path.relpath(file_path, ARCHIVE_DIR).replace("\\", "/")
                resolved_url = None
                
                # 1. Google Drive Cloud Upload (5 TB Storage)
                if ENABLE_GDRIVE_UPLOAD:
                    try:
                        gdrive_res = sync_archive_file_to_gdrive(file_path)
                        if gdrive_res:
                            resolved_url = gdrive_res.get('webViewLink') or gdrive_res.get('webContentLink')
                            gdrive_uploaded_count += 1
                    except Exception as e:
                        logging.warning(f"Google Drive upload warning for {rel_path}: {e}")
                
                # 2. Supabase Storage Upload (Optional / Bypassed if storage is at free limits)
                if ENABLE_SUPABASE_STORAGE_UPLOAD:
                    bucket = "pulse-vector-media"
                    dest_path = f"{folder}/{rel_path}"
                    sp_url = upload_file_to_storage(file_path, bucket, dest_path)
                    if sp_url:
                        supabase_uploaded_count += 1
                        if not resolved_url:
                            resolved_url = sp_url
                            
                # Fallback to local reference if no cloud link
                if not resolved_url:
                    resolved_url = f"local://{rel_path}"
                
                # 3. Save Execution & Media Metadata to Supabase Database
                if supabase:
                    mtime = os.path.getmtime(file_path)
                    run_date = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()
                    
                    save_metadata("pipeline_runs", {
                        "run_date": run_date,
                        "file_type": f_type,
                        "file_path": rel_path,
                        "url": resolved_url
                    })
                    metadata_count += 1
                
        print(f"✅ Cloud sync completed.")
        if ENABLE_GDRIVE_UPLOAD:
            print(f"   - Google Drive objects uploaded: {gdrive_uploaded_count}")
        if ENABLE_SUPABASE_STORAGE_UPLOAD:
            print(f"   - Supabase storage objects uploaded: {supabase_uploaded_count}")
        if supabase:
            print(f"   - Supabase metadata records synced: {metadata_count}")
            
        logging.info(f"Cloud sync completed. GDrive: {gdrive_uploaded_count}, Supabase: {supabase_uploaded_count}, Metadata: {metadata_count}")
    except Exception as e:
        print(f"⚠️ Cloud sync encountered error: {e}")
        logging.error(f"Cloud sync error: {e}")

