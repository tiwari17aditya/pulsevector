"""
Automated GitHub Actions Secrets Synchronizer for Pulse Vector
Encrypts and uploads all local environment and credential secrets directly to GitHub Secrets via the GitHub REST API.
"""

import os
import sys
import json
import base64
import pathlib
import requests
from dotenv import load_dotenv
from nacl import encoding, public

# Set UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypts a secret string with GitHub repository's libsodium public key."""
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def get_repo_public_key(owner: str, repo: str, token: str):
    """Fetches the public key used to encrypt Actions secrets."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch public key ({response.status_code}): {response.text}")
    data = response.json()
    return data["key_id"], data["key"]


def set_github_secret(owner: str, repo: str, token: str, secret_name: str, encrypted_value: str, key_id: str):
    """Uploads an encrypted secret to GitHub Actions."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in (201, 204):
        return True
    else:
        raise Exception(f"Failed to set secret {secret_name} ({response.status_code}): {response.text}")


def collect_project_secrets() -> dict:
    """Gathers all environment secrets and credential JSON contents."""
    secrets_map = {}

    # 1. Environment variables from .env
    env_keys = [
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "DISCORD_WEBHOOK_URL",
        "YOUTUBE_PRIVACY_STATUS",
        "YOUTUBE_PLAYLIST_TAG",
        "GOOGLE_DRIVE_FOLDER_ID",
    ]
    for k in env_keys:
        val = os.getenv(k)
        if val:
            secrets_map[k] = val.strip()

    # 2. YouTube Client Secrets JSON
    client_secrets = PROJECT_ROOT / "credentials" / "client_secrets.json"
    if client_secrets.exists():
        secrets_map["YOUTUBE_CLIENT_SECRETS"] = client_secrets.read_text(encoding="utf-8").strip()

    # 3. YouTube Token JSON
    yt_token = PROJECT_ROOT / "credentials" / "token.json"
    if yt_token.exists():
        secrets_map["YOUTUBE_TOKEN_JSON"] = yt_token.read_text(encoding="utf-8").strip()

    # 4. Google Drive Token JSON
    gdrive_token = PROJECT_ROOT / "credentials" / "gdrive_token.json"
    if gdrive_token.exists():
        secrets_map["GDRIVE_TOKEN_JSON"] = gdrive_token.read_text(encoding="utf-8").strip()

    return secrets_map


def main():
    owner = "tiwari17aditya"
    repo = "pulsevector"
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("❌ Error: GITHUB_TOKEN not found in environment or .env file.")
        sys.exit(1)

    print("=" * 65)
    print("🔐 Pulse Vector - Automated GitHub Secrets Synchronizer")
    print(f"🎯 Target Repository: {owner}/{repo}")
    print("=" * 65)

    print("\n1️⃣ Gathering local credentials and environment variables...")
    secrets_to_upload = collect_project_secrets()
    print(f"   Found {len(secrets_to_upload)} secrets ready for cloud deployment:")
    for s_name in sorted(secrets_to_upload.keys()):
        print(f"   - {s_name}")

    print("\n2️⃣ Fetching repository public encryption key from GitHub...")
    key_id, public_key = get_repo_public_key(owner, repo, token)
    print(f"   Key ID: {key_id}")

    print("\n3️⃣ Encrypting and pushing secrets to GitHub Actions...")
    success_count = 0
    for name, value in secrets_to_upload.items():
        try:
            encrypted_val = encrypt_secret(public_key, value)
            set_github_secret(owner, repo, token, name, encrypted_val, key_id)
            print(f"   ✅ [OK] {name} synced successfully.")
            success_count += 1
        except Exception as e:
            print(f"   ❌ [FAIL] {name}: {e}")

    print("\n" + "=" * 65)
    print(f"🎉 Completed! {success_count}/{len(secrets_to_upload)} GitHub Secrets synchronized.")
    print("Your GitHub Actions cloud workflows now have all credentials configured")
    print("and will run fully autonomously without any manual intervention!")
    print("=" * 65)


if __name__ == "__main__":
    main()
