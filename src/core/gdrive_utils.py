import os
import pathlib
import mimetypes
import logging
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import GOOGLE_DRIVE_FOLDER_PATH, GOOGLE_DRIVE_FOLDER_NAME, GOOGLE_DRIVE_FOLDER_ID, ARCHIVE_DIR


GDRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Cache for folder IDs to prevent redundant API queries
_FOLDER_CACHE: Dict[str, str] = {}


def get_gdrive_service(
    client_secrets_file: str = 'credentials/client_secrets.json',
    token_path: Optional[str] = None
):
    """
    Initializes and returns an authenticated Google Drive v3 client.
    Prefers credentials/gdrive_token.json, falling back to credentials/token.json.
    """
    if token_path:
        candidate_tokens = [token_path]
    else:
        candidate_tokens = [
            'credentials/gdrive_token.json',
            'gdrive_token.json',
            'credentials/token.json',
            'token.json'
        ]

    token_file = None
    for cand in candidate_tokens:
        if cand and os.path.exists(cand):
            token_file = pathlib.Path(cand)
            break

    if not token_file:
        logging.warning("Google Drive credentials token not found. Cannot access Google Drive API.")
        return None


    try:
        creds = Credentials.from_authorized_user_file(str(token_file))
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_file, 'w') as f:
                    f.write(creds.to_json())
            else:
                logging.warning("Google credentials token is invalid or cannot be refreshed.")
                return None

        # Build Google Drive v3 client
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        return service
    except Exception as e:
        logging.warning(f"Failed to initialize Google Drive service: {e}")
        return None


def find_or_create_folder(service, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
    """
    Searches for an existing active folder by name within a parent folder,
    or creates it if it doesn't exist.
    """
    cache_key = f"{parent_id or 'root'}::{folder_name}"
    if cache_key in _FOLDER_CACHE:
        return _FOLDER_CACHE[cache_key]

    query_parts = [
        f"name = '{folder_name}'",
        "mimeType = 'application/vnd.google-apps.folder'",
        "trashed = false"
    ]
    if parent_id:
        query_parts.append(f"'{parent_id}' in parents")
    else:
        query_parts.append("'root' in parents")

    query = " and ".join(query_parts)

    try:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=10
        ).execute()

        files = response.get('files', [])
        if files:
            folder_id = files[0]['id']
            _FOLDER_CACHE[cache_key] = folder_id
            return folder_id

        # Folder does not exist, create it
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            folder_metadata['parents'] = [parent_id]

        created_folder = service.files().create(
            body=folder_metadata,
            fields='id, name'
        ).execute()

        folder_id = created_folder.get('id')
        _FOLDER_CACHE[cache_key] = folder_id
        logging.info(f"Created Google Drive folder: '{folder_name}' (ID: {folder_id})")
        return folder_id
    except Exception as e:
        logging.error(f"Error finding/creating Google Drive folder '{folder_name}': {e}")
        return None


def ensure_folder_path(service, path_parts: List[str], root_folder_id: Optional[str] = None) -> Optional[str]:
    """
    Recursively ensures that a nested folder structure exists in Google Drive.
    path_parts: e.g. ["2026", "September", "Daily_Videos"]
    """
    current_parent = root_folder_id
    for part in path_parts:
        if not part.strip():
            continue
        current_parent = find_or_create_folder(service, part.strip(), parent_id=current_parent)
        if not current_parent:
            logging.error(f"Failed to resolve folder path at segment: {part}")
            return None
    return current_parent


def upload_file_to_gdrive(
    service,
    file_path: str,
    destination_folder_id: str,
    file_name: Optional[str] = None,
    overwrite: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Uploads a local file to a Google Drive folder using resumable chunked upload.
    If a file with the same name exists and overwrite=True, updates the existing file.
    """
    if not os.path.exists(file_path):
        logging.error(f"Cannot upload non-existent file: {file_path}")
        return None

    actual_name = file_name or os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    try:
        # Check if file with same name already exists in destination folder
        existing_file_id = None
        if overwrite:
            query = f"name = '{actual_name}' and '{destination_folder_id}' in parents and trashed = false"
            res = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            existing = res.get('files', [])
            if existing:
                existing_file_id = existing[0]['id']

        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True,
            chunksize=5 * 1024 * 1024  # 5 MB chunks for stable resumable uploads
        )

        if existing_file_id:
            # Update existing file content
            updated = service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size'
            ).execute()
            logging.info(f"Updated existing Google Drive file '{actual_name}' (ID: {updated.get('id')})")
            return updated
        else:
            # Create new file
            file_metadata = {
                'name': actual_name,
                'parents': [destination_folder_id]
            }
            created = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size'
            ).execute()
            logging.info(f"Uploaded new file to Google Drive: '{actual_name}' (ID: {created.get('id')})")
            return created
    except Exception as e:
        logging.error(f"Error uploading {file_path} to Google Drive: {e}")
        return None


def sync_archive_file_to_gdrive(
    file_path: str,
    root_folder_path: str = GOOGLE_DRIVE_FOLDER_PATH,
    root_folder_id: Optional[str] = GOOGLE_DRIVE_FOLDER_ID
) -> Optional[Dict[str, Any]]:
    """
    Syncs a single file from the local pulse_archive directory into Google Drive,
    mirroring the folder hierarchy inside root_folder_path (e.g. antigravity-projects-storage/pulse-vector/2026/September/Daily_Videos/...).
    Supports direct local Google Drive for Desktop sync as well as Google Drive API v3 cloud upload.
    """
    import shutil
    rel_path = ""
    try:
        rel_path = os.path.relpath(file_path, ARCHIVE_DIR)
    except Exception:
        rel_path = os.path.basename(file_path)

    local_synced = False
    # 1. Direct local sync if Google Drive for Desktop is mounted
    try:
        clean_path = root_folder_path.replace("->", "/").strip("/")
        local_drive_root = pathlib.Path("G:/My Drive") / clean_path
        if local_drive_root.parent.exists():
            dest_file = local_drive_root / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_file)
            logging.info(f"Directly synced file to Google Drive for Desktop: {dest_file}")
            local_synced = True
    except Exception as e:
        logging.warning(f"Local Google Drive sync note: {e}")

    service = get_gdrive_service()
    if not service:
        if local_synced:
            return {
                "id": "local_gdrive_sync",
                "name": os.path.basename(file_path),
                "webViewLink": f"gdrive://My Drive/{root_folder_path}/{rel_path}".replace("\\", "/")
            }
        return None

    # Resolve base folder hierarchy via API (e.g. antigravity-projects-storage -> pulse-vector)
    try:
        if not root_folder_id:
            folder_segments = [seg.strip() for seg in root_folder_path.replace("->", "/").split("/") if seg.strip()]
            root_folder_id = ensure_folder_path(service, folder_segments, root_folder_id=None)
            if not root_folder_id:
                if local_synced:
                    return {
                        "id": "local_gdrive_sync",
                        "name": os.path.basename(file_path),
                        "webViewLink": f"gdrive://My Drive/{root_folder_path}/{rel_path}".replace("\\", "/")
                    }
                return None

        parent_dir = os.path.dirname(rel_path)
        path_segments = [p for p in parent_dir.replace("\\", "/").split("/") if p]

        target_folder_id = ensure_folder_path(service, path_segments, root_folder_id=root_folder_id)
        if not target_folder_id:
            target_folder_id = root_folder_id

        api_res = upload_file_to_gdrive(service, file_path, target_folder_id)
        if api_res:
            return api_res
    except Exception as e:
        logging.warning(f"Google Drive API sync error: {e}")

    if local_synced:
        return {
            "id": "local_gdrive_sync",
            "name": os.path.basename(file_path),
            "webViewLink": f"gdrive://My Drive/{root_folder_path}/{rel_path}".replace("\\", "/")
        }
    return None



