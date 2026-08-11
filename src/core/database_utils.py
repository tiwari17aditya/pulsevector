import os
import logging
from supabase import create_client, Client
from .config import ARCHIVE_DIR

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

import mimetypes

def upload_file_to_storage(file_path: str, bucket_name: str, destination_path: str) -> str:
    supabase = get_supabase_client()
    if not supabase:
        logging.warning("Supabase credentials not found. Skipping file upload.")
        return None
    
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} does not exist. Cannot upload.")
        return None
        
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        with open(file_path, 'rb') as f:
            # Upsert the file in storage with content-type to enable inline UI previews
            res = supabase.storage.from_(bucket_name).upload(
                path=destination_path,
                file=f,
                file_options={
                    "upsert": "true",
                    "content-type": mime_type
                }
            )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(destination_path)
        logging.info(f"Successfully uploaded {file_path} to Supabase bucket '{bucket_name}' at {destination_path} with MIME '{mime_type}'")
        return public_url
    except Exception as e:
        logging.error(f"Error uploading file to Supabase: {e}")
        return None

def save_metadata(table_name: str, data: dict, on_conflict: str = "file_path"):
    supabase = get_supabase_client()
    if not supabase:
        logging.warning("Supabase credentials not found. Skipping metadata insert.")
        return None
        
    try:
        # Use upsert with on_conflict to avoid duplicate key errors
        res = supabase.table(table_name).upsert(data, on_conflict=on_conflict).execute()
        logging.info(f"Successfully saved metadata to {table_name}")
        return res
    except Exception as e:
        logging.error(f"Error saving metadata to Supabase: {e}")
        return None

def run_database_upload(cutoff_hours: float = 24):
    import glob
    import datetime
    import time
    
    print("\n🚀 Starting Database Upload (Supabase)...")
    logging.info("Starting database upload...")
    
    cutoff_time = (time.time() - (cutoff_hours * 3600)) if cutoff_hours is not None else 0
    
    uploaded_count = 0
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
                bucket = "pulse-vector-media"
                dest_path = f"{folder}/{rel_path}"
                
                url = upload_file_to_storage(file_path, bucket, dest_path)
                if url:
                    mtime = os.path.getmtime(file_path)
                    run_date = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()
                    save_metadata("pipeline_runs", {
                        "run_date": run_date,
                        "file_type": f_type,
                        "file_path": rel_path,
                        "url": url
                    })
                    uploaded_count += 1
                
        print(f"✅ Database upload completed. Uploaded {uploaded_count} files.")
        logging.info(f"Database upload completed. Uploaded {uploaded_count} files.")
    except Exception as e:
        print(f"❌ Database upload failed: {e}")
        logging.error(f"Database upload failed: {e}")

