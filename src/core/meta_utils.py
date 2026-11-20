"""
Pulse Vector - Meta Developer & Instagram Graph API Engine
Automates publishing of Daily Current Affairs and Brain Teaser vertical videos (.mp4)
as Instagram Reels and slide cards as Instagram Posts via Meta Graph API v21.0.
"""

import os
import re
import time
import logging
import pathlib
import requests
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_meta_credentials() -> Dict[str, Optional[str]]:
    """
    Retrieves Meta / Instagram Graph API credentials from environment or .env file.
    Returns dictionary with:
      - access_token: Long-lived User/Page access token
      - account_id: Numeric Instagram Business Account ID
      - app_id: Meta App ID (optional for publishing, required for token exchange)
      - app_secret: Meta App Secret (optional for publishing, required for token exchange)
    """
    def _read_env(key: str) -> Optional[str]:
        val = os.getenv(key)
        if val:
            return val
        env_file = pathlib.Path(".env")
        if env_file.exists():
            try:
                content = env_file.read_text(encoding="utf-8")
                match = re.search(rf"^\s*{re.escape(key)}\s*=\s*['\"]?(.*?)['\"]?\s*$", content, re.MULTILINE)
                if match:
                    return match.group(1).strip()
            except Exception:
                pass
        return None

    return {
        "access_token": _read_env("META_ACCESS_TOKEN") or _read_env("INSTAGRAM_ACCESS_TOKEN"),
        "account_id": _read_env("INSTAGRAM_ACCOUNT_ID"),
        "app_id": _read_env("META_APP_ID"),
        "app_secret": _read_env("META_APP_SECRET"),
    }


def exchange_for_long_lived_token(
    short_lived_token: str,
    app_id: str,
    app_secret: str,
    timeout: int = 15
) -> Optional[Dict[str, Any]]:
    """
    Exchanges a short-lived user access token (1-2 hours) for a 60-day Long-Lived Token.
    Endpoint: GET https://graph.facebook.com/v21.0/oauth/access_token
    """
    if not short_lived_token or not app_id or not app_secret:
        logger.warning("[Meta Graph API] Missing token or app credentials for long-lived exchange.")
        return None

    url = f"{GRAPH_API_BASE}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        data = response.json()
        if response.status_code == 200 and "access_token" in data:
            logger.info("[Meta Graph API] Successfully exchanged short-lived token for long-lived token.")
            return data
        else:
            err_msg = data.get("error", {}).get("message", "Unknown error")
            logger.error(f"[Meta Graph API] Long-lived token exchange failed: {err_msg} (code: {response.status_code})")
            return None
    except Exception as e:
        logger.error(f"[Meta Graph API] Exception during long-lived token exchange: {e}")
        return None


def discover_instagram_account_id(
    access_token: str,
    timeout: int = 15
) -> Optional[Dict[str, str]]:
    """
    Queries /me/accounts to find connected Facebook Pages and their linked Instagram Business Accounts.
    Returns dict with {"page_id": ..., "page_name": ..., "instagram_account_id": ...} or None.
    """
    if not access_token:
        return None

    url = f"{GRAPH_API_BASE}/me/accounts"
    params = {
        "fields": "id,name,instagram_business_account{id,username}",
        "access_token": access_token,
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        data = response.json()
        if response.status_code != 200:
            err_msg = data.get("error", {}).get("message", "Unknown error")
            logger.error(f"[Meta Graph API] Failed to fetch accounts: {err_msg}")
            return None

        accounts = data.get("data", [])
        for acc in accounts:
            ig_acc = acc.get("instagram_business_account")
            if ig_acc and "id" in ig_acc:
                return {
                    "page_id": acc.get("id", ""),
                    "page_name": acc.get("name", ""),
                    "instagram_account_id": ig_acc.get("id", ""),
                    "instagram_username": ig_acc.get("username", ""),
                }

        logger.warning("[Meta Graph API] No Facebook Page with a linked Instagram Business Account was found.")
        return None
    except Exception as e:
        logger.error(f"[Meta Graph API] Exception querying connected accounts: {e}")
        return None


def create_reels_container(
    video_url: str,
    caption: str,
    access_token: str,
    ig_user_id: str,
    share_to_feed: bool = True,
    timeout: int = 30
) -> Optional[str]:
    """
    Step 1 of Instagram Reels Publishing: Creates an upload container for the video.
    Endpoint: POST /{ig-user-id}/media
    Returns container_id (str) or None.
    """
    url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption[:2200],  # Instagram caption max 2200 chars
        "share_to_feed": "true" if share_to_feed else "false",
        "access_token": access_token,
    }

    try:
        response = requests.post(url, data=payload, timeout=timeout)
        data = response.json()
        if response.status_code == 200 and "id" in data:
            container_id = data["id"]
            logger.info(f"[Meta Graph API] Created Reels container ID: {container_id}")
            return container_id
        else:
            err = data.get("error", {})
            logger.error(
                f"[Meta Graph API] Failed to create Reels container: {err.get('message', 'Unknown')} "
                f"(type: {err.get('type')}, code: {err.get('code')})"
            )
            return None
    except Exception as e:
        logger.error(f"[Meta Graph API] Exception creating Reels container: {e}")
        return None


def poll_container_status(
    container_id: str,
    access_token: str,
    max_wait_seconds: int = 120,
    poll_interval: int = 5,
    timeout: int = 15
) -> bool:
    """
    Step 2 of Instagram Reels Publishing: Polls container status until 'FINISHED'.
    Status codes:
      - FINISHED: Ready to publish
      - IN_PROGRESS: Video transcoding in progress
      - ERROR: Transcoding failed
      - EXPIRED: Container expired (>24h)
    """
    url = f"{GRAPH_API_BASE}/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": access_token,
    }

    start_time = time.time()
    while (time.time() - start_time) < max_wait_seconds:
        try:
            response = requests.get(url, params=params, timeout=timeout)
            data = response.json()
            status_code = data.get("status_code", "").upper()

            if status_code == "FINISHED":
                logger.info(f"[Meta Graph API] Container {container_id} is FINISHED and ready to publish.")
                return True
            elif status_code == "IN_PROGRESS":
                logger.debug(f"[Meta Graph API] Container {container_id} transcoding IN_PROGRESS. Retrying in {poll_interval}s...")
                time.sleep(poll_interval)
            elif status_code in ("ERROR", "EXPIRED"):
                err_detail = data.get("status", "Unknown transcoding failure")
                logger.error(f"[Meta Graph API] Container {container_id} failed with status: {status_code} ({err_detail})")
                return False
            else:
                logger.debug(f"[Meta Graph API] Container {container_id} unknown status: {status_code}. Waiting...")
                time.sleep(poll_interval)
        except Exception as e:
            logger.warning(f"[Meta Graph API] Transient error polling container status: {e}. Retrying...")
            time.sleep(poll_interval)

    logger.error(f"[Meta Graph API] Timed out waiting for container {container_id} after {max_wait_seconds}s.")
    return False


def publish_media_container(
    container_id: str,
    access_token: str,
    ig_user_id: str,
    timeout: int = 30
) -> Optional[str]:
    """
    Step 3 of Instagram Reels/Photo Publishing: Publishes the validated container.
    Endpoint: POST /{ig-user-id}/media_publish
    Returns published media_id (str) or None.
    """
    url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    try:
        response = requests.post(url, data=payload, timeout=timeout)
        data = response.json()
        if response.status_code == 200 and "id" in data:
            media_id = data["id"]
            logger.info(f"[Meta Graph API] Successfully published Instagram media ID: {media_id}")
            return media_id
        else:
            err = data.get("error", {})
            logger.error(
                f"[Meta Graph API] Failed to publish container: {err.get('message', 'Unknown')} "
                f"(type: {err.get('type')}, code: {err.get('code')})"
            )
            return None
    except Exception as e:
        logger.error(f"[Meta Graph API] Exception publishing container {container_id}: {e}")
        return None


def publish_instagram_reel(
    video_url: str,
    caption: str,
    access_token: Optional[str] = None,
    ig_user_id: Optional[str] = None,
    share_to_feed: bool = True,
    max_wait_seconds: int = 120
) -> Optional[str]:
    """
    Complete high-level workflow for publishing an Instagram Reel:
    1. Validates credentials (falls back to get_meta_credentials).
    2. Creates media container.
    3. Polls until transcoding is FINISHED.
    4. Publishes container.
    Returns Instagram media_id or None if publishing failed or unconfigured.
    """
    creds = get_meta_credentials()
    token = access_token or creds["access_token"]
    user_id = ig_user_id or creds["account_id"]

    if not token or not user_id:
        logger.info("[Meta Graph API] Missing META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID. Skipping Instagram Reel broadcast.")
        return None

    if not video_url or not video_url.startswith("http"):
        logger.warning(f"[Meta Graph API] Invalid public video_url: '{video_url}'. Instagram requires a public HTTPS URL.")
        return None

    logger.info(f"[Meta Graph API] Starting Instagram Reel publication for account {user_id}...")

    # Step 1: Create Container
    container_id = create_reels_container(
        video_url=video_url,
        caption=caption,
        access_token=token,
        ig_user_id=user_id,
        share_to_feed=share_to_feed
    )
    if not container_id:
        return None

    # Step 2: Poll Status
    ready = poll_container_status(
        container_id=container_id,
        access_token=token,
        max_wait_seconds=max_wait_seconds
    )
    if not ready:
        return None

    # Step 3: Publish Container
    media_id = publish_media_container(
        container_id=container_id,
        access_token=token,
        ig_user_id=user_id
    )
    return media_id


def publish_instagram_photo(
    image_url: str,
    caption: str,
    access_token: Optional[str] = None,
    ig_user_id: Optional[str] = None,
    timeout: int = 30
) -> Optional[str]:
    """
    Publishes a single photo/slide post to Instagram:
    Endpoint: POST /{ig-user-id}/media -> POST /{ig-user-id}/media_publish
    """
    creds = get_meta_credentials()
    token = access_token or creds["access_token"]
    user_id = ig_user_id or creds["account_id"]

    if not token or not user_id:
        logger.info("[Meta Graph API] Missing credentials. Skipping Instagram photo broadcast.")
        return None

    if not image_url or not image_url.startswith("http"):
        logger.warning(f"[Meta Graph API] Invalid public image_url: '{image_url}'.")
        return None

    # Step 1: Create Photo Container
    url = f"{GRAPH_API_BASE}/{user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption[:2200],
        "access_token": token,
    }

    try:
        res = requests.post(url, data=payload, timeout=timeout)
        data = res.json()
        if res.status_code != 200 or "id" not in data:
            logger.error(f"[Meta Graph API] Failed photo container: {data.get('error', {}).get('message')}")
            return None
        container_id = data["id"]
    except Exception as e:
        logger.error(f"[Meta Graph API] Exception creating photo container: {e}")
        return None

    # Step 2: Publish Container
    return publish_media_container(
        container_id=container_id,
        access_token=token,
        ig_user_id=user_id,
        timeout=timeout
    )
