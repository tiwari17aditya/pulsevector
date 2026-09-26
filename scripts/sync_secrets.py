"""
Pulse Vector GitHub Secrets Synchronization Utility (v1.0.0)
Reads local .env and credentials/*.json files, encrypts them via libsodium (PyNaCl),
and uploads them directly to GitHub Repository Secrets using the GitHub REST API.

Usage:
  python scripts/sync_secrets.py --dry-run
  python scripts/sync_secrets.py --token <GITHUB_PERSONAL_ACCESS_TOKEN>
  python scripts/sync_secrets.py (reads GITHUB_TOKEN or GH_TOKEN from .env)
"""

import os
import re
import sys
import json
import base64
import urllib.request
import urllib.error
import pathlib
import argparse
import subprocess
from typing import Dict, Tuple, Optional

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"

# Canonical secret mappings from .env and credentials/
KNOWN_SECRETS_KEYS = [
    "GEMINI_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "DISCORD_WEBHOOK_URL",
    "GOOGLE_DRIVE_FOLDER_ID",
    "ENABLE_GDRIVE_UPLOAD",
    "ENABLE_SUPABASE_STORAGE_UPLOAD",
    "YOUTUBE_PRIVACY_STATUS",
    "YOUTUBE_PLAYLIST_TAG",
    "SMTP_USER",
    "SMTP_APP_PASSWORD",
    "SMTP_HOST",
    "SMTP_PORT",
    "REPORT_RECIPIENT_EMAIL"
]

CREDENTIAL_FILES_MAP = {
    "YOUTUBE_CLIENT_SECRETS": CREDENTIALS_DIR / "client_secrets.json",
    "YOUTUBE_TOKEN_JSON": CREDENTIALS_DIR / "token.json",
    "GDRIVE_TOKEN_JSON": CREDENTIALS_DIR / "gdrive_token.json",
}

def parse_repo_owner_name() -> Optional[Tuple[str, str]]:
    """Extracts (owner, repo) from git remote origin."""
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = res.stdout.strip()
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", url)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass
    return None

def load_env_variables() -> Dict[str, str]:
    """Loads key-value pairs from local .env file."""
    env_vars = {}
    if not ENV_FILE.exists():
        return env_vars
    
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and val:
                env_vars[key] = val
    return env_vars

def collect_all_secrets() -> Dict[str, str]:
    """Gathers all available secrets from .env and credentials/."""
    secrets = {}
    env_vars = load_env_variables()

    # 1. Collect standard env vars
    for key in KNOWN_SECRETS_KEYS:
        val = env_vars.get(key) or os.getenv(key)
        if val:
            secrets[key] = str(val).strip()

    # 2. Collect credential JSON files
    for secret_name, file_path in CREDENTIAL_FILES_MAP.items():
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if content:
                    secrets[secret_name] = content
            except Exception as e:
                print(f"⚠️ Warning: Could not read {file_path.name}: {e}")

    return secrets

def get_repo_public_key(owner: str, repo: str, token: str) -> Tuple[str, str]:
    """Fetches the repository public key for GitHub Actions secrets encryption."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PulseVector-SecretSync"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["key_id"], data["key"]

def encrypt_secret(public_key_b64: str, secret_val: str) -> str:
    """Encrypts secret value using PyNaCl SealedBox (libsodium)."""
    try:
        from nacl import encoding, public
        pub_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder)
        sealed_box = public.SealedBox(pub_key)
        encrypted = sealed_box.encrypt(secret_val.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    except ImportError:
        raise RuntimeError("PyNaCl is required for secret encryption. Install via: pip install pynacl")

def put_github_secret(owner: str, repo: str, token: str, secret_name: str, key_id: str, encrypted_val: str) -> bool:
    """Uploads encrypted secret to GitHub Actions."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    payload = json.dumps({
        "encrypted_value": encrypted_val,
        "key_id": key_id
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "PulseVector-SecretSync"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (201, 204)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"❌ Failed to set secret '{secret_name}': HTTP {e.code} - {err_msg}")
        return False

def sync_secrets(token: Optional[str] = None, owner: Optional[str] = None, repo: Optional[str] = None, dry_run: bool = False) -> bool:
    """Main synchronization logic."""
    # Resolve owner and repo
    if not owner or not repo:
        detected = parse_repo_owner_name()
        if detected:
            owner, repo = detected
        else:
            print("❌ Could not determine GitHub repository. Specify with --owner and --repo.")
            return False

    print("==========================================================")
    print(f"  🔐 PULSE VECTOR GITHUB SECRETS SYNC")
    print(f"  Target Repository: {owner}/{repo}")
    print(f"  Mode: {'DRY RUN (Preview Only)' if dry_run else 'LIVE SYNC'}")
    print("==========================================================")

    secrets = collect_all_secrets()
    if not secrets:
        print("⚠️ No secrets found in .env or credentials/ directory.")
        return False

    print(f"🔍 Discovered {len(secrets)} secrets to synchronize:")
    for name, val in secrets.items():
        masked = val[:4] + "..." + val[-3:] if len(val) > 8 else "***"
        print(f"  • {name.ljust(30)}: [{masked}] ({len(val)} chars)")

    if dry_run:
        print("\n✅ Dry run completed successfully. All secrets are ready for upload.")
        return True

    # Resolve token
    if not token:
        env_vars = load_env_variables()
        token = env_vars.get("GITHUB_TOKEN") or env_vars.get("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    if not token:
        print("\n❌ Error: GitHub Personal Access Token (classic with 'repo' scope or fine-grained with Actions Secrets read/write) is required.")
        print("   Set GITHUB_TOKEN in your .env, or pass it via: python scripts/sync_secrets.py --token <TOKEN>")
        return False

    try:
        print(f"\n🔑 Fetching repository public key from GitHub API...")
        key_id, public_key_b64 = get_repo_public_key(owner, repo, token)
        print(f"✅ Public key retrieved successfully (Key ID: {key_id[:8]}...).")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to fetch public key: HTTP {e.code}. Check your GITHUB_TOKEN permissions.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    success_count = 0
    fail_count = 0

    print(f"\n🚀 Encrypting and uploading {len(secrets)} secrets to GitHub Actions...")
    for secret_name, secret_val in secrets.items():
        try:
            encrypted_val = encrypt_secret(public_key_b64, secret_val)
            if put_github_secret(owner, repo, token, secret_name, key_id, encrypted_val):
                print(f"  ✅ [SUCCESS] {secret_name}")
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"  ❌ [ERROR] {secret_name}: {e}")
            fail_count += 1

    print("\n----------------------------------------------------------")
    print(f"  Sync Summary: {success_count} succeeded, {fail_count} failed.")
    print("----------------------------------------------------------")
    return fail_count == 0

def main():
    parser = argparse.ArgumentParser(description="Synchronize local .env and credentials to GitHub Actions Secrets")
    parser.add_argument("--token", type=str, help="GitHub Personal Access Token (classic with repo scope or fine-grained secrets write)")
    parser.add_argument("--owner", type=str, help="GitHub repository owner (default: auto-detected)")
    parser.add_argument("--repo", type=str, help="GitHub repository name (default: auto-detected)")
    parser.add_argument("--dry-run", action="store_true", help="Preview secrets to be synced without uploading")

    args = parser.parse_args()
    success = sync_secrets(
        token=args.token,
        owner=args.owner,
        repo=args.repo,
        dry_run=args.dry_run
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
