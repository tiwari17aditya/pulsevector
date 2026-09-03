"""
Pulse Vector - GitHub Actions Secrets Auto-Synchronizer
Automatically fetches environment variables from .env and OAuth JSON files in credentials/
encrypts them using PyNaCl/Libsodium, and pushes them directly into GitHub Actions Secrets.
Zero manual copy-pasting required.
"""

import os
import sys
import json
import base64
import argparse
import pathlib
import subprocess
import requests
from dotenv import dotenv_values

try:
    from nacl import encoding, public
except ImportError:
    print("❌ PyNaCl is required. Install it using: pip install pynacl")
    sys.exit(1)

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

def get_repo_slug() -> str:
    """Extracts owner/repo from local git remote origin."""
    try:
        res = subprocess.run(["git", "remote", "get-url", "origin"], cwd=str(ROOT_DIR), capture_output=True, text=True)
        url = res.stdout.strip()
        if "github.com" in url:
            # Handle both HTTPS and SSH
            # https://github.com/owner/repo.git OR git@github.com:owner/repo.git
            clean = url.replace("https://github.com/", "").replace("git@github.com:", "")
            if clean.endswith(".git"):
                clean = clean[:-4]
            return clean
    except Exception:
        pass
    return "tiwari17aditya/pulsevector"

def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypts a secret string using the repository public key via Libsodium SealedBox."""
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def get_repo_public_key(owner_repo: str, github_token: str):
    """Fetches the repository public key for GitHub Actions Secrets."""
    url = f"https://api.github.com/repos/{owner_repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"❌ Failed to fetch public key ({resp.status_code}): {resp.text}")
        return None

def set_github_secret(owner_repo: str, github_token: str, secret_name: str, encrypted_val: str, key_id: str) -> bool:
    """Pushes an encrypted secret to GitHub Actions via the REST API."""
    url = f"https://api.github.com/repos/{owner_repo}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = {
        "encrypted_value": encrypted_val,
        "key_id": key_id
    }
    resp = requests.put(url, headers=headers, json=payload)
    return resp.status_code in [201, 204]

def collect_local_secrets() -> dict:
    """Collects all required secrets from local .env and credentials/ files."""
    secrets_map = {}
    
    # 1. Read .env
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        env_dict = dotenv_values(str(env_file))
        keys_to_sync = [
            "GEMINI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "DISCORD_WEBHOOK_URL",
            "YOUTUBE_PRIVACY_STATUS",
            "YOUTUBE_PLAYLIST_TAG"
        ]
        for k in keys_to_sync:
            v = env_dict.get(k) or os.environ.get(k)
            if v and not v.startswith("your_"):
                secrets_map[k] = v.strip()
                
    # 2. Read credentials/client_secrets.json
    cs_file = ROOT_DIR / "credentials" / "client_secrets.json"
    if cs_file.exists():
        try:
            secrets_map["YOUTUBE_CLIENT_SECRETS"] = cs_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"⚠️ Could not read client_secrets.json: {e}")
            
    # 3. Read credentials/token.json
    tok_file = ROOT_DIR / "credentials" / "token.json"
    if tok_file.exists():
        try:
            secrets_map["YOUTUBE_TOKEN_JSON"] = tok_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"⚠️ Could not read token.json: {e}")
            
    return secrets_map

def main():
    parser = argparse.ArgumentParser(description="Auto-sync local .env and credentials to GitHub Actions Secrets")
    parser.add_argument("--token", help="GitHub Personal Access Token (classic or fine-grained with Actions Secrets write permission)")
    args = parser.parse_args()
    
    owner_repo = get_repo_slug()
    print("=" * 65)
    print("  🔒 PULSE VECTOR: GITHUB ACTIONS SECRETS AUTO-SYNCHRONIZER")
    print("=" * 65)
    print(f"Target Repository: {owner_repo}")
    
    # Check for token in args, env, or .env
    env_dict = dotenv_values(str(ROOT_DIR / ".env")) if (ROOT_DIR / ".env").exists() else {}
    gh_token = args.token or os.environ.get("GITHUB_TOKEN") or env_dict.get("GITHUB_TOKEN") or env_dict.get("GH_PAT")
    
    if not gh_token:
        print("\n🔑 A GitHub Personal Access Token (PAT) is required to push secrets.")
        print("   Create a token at: https://github.com/settings/tokens (classic with 'repo' scope)")
        print("   OR fine-grained token with 'Repository secrets: Read and Write' permission.\n")
        try:
            gh_token = input("Enter your GitHub PAT (or paste in .env as GITHUB_TOKEN=ghp_...): ").strip()
        except EOFError:
            pass
            
    if not gh_token:
        print("❌ No GitHub token provided. Aborting sync.")
        sys.exit(1)
        
    # 1. Fetch Repository Public Key
    print("\n▶ Fetching repository public encryption key from GitHub API...")
    key_data = get_repo_public_key(owner_repo, gh_token)
    if not key_data:
        sys.exit(1)
        
    key_id = key_data["key_id"]
    public_key_b64 = key_data["key"]
    print(f"✅ Retrieved public key ID: {key_id}")
    
    # 2. Collect Local Secrets
    local_secrets = collect_local_secrets()
    print(f"\n▶ Found {len(local_secrets)} secrets to synchronize from .env and credentials/:")
    for s_name in local_secrets.keys():
        print(f"   • {s_name}")
        
    # 3. Encrypt and Upload Each Secret
    print("\n▶ Encrypting and pushing secrets to GitHub Actions...")
    success_count = 0
    for s_name, s_val in local_secrets.items():
        try:
            enc_val = encrypt_secret(public_key_b64, s_val)
            ok = set_github_secret(owner_repo, gh_token, s_name, enc_val, key_id)
            if ok:
                print(f"  ✅ [SYNCED] {s_name}")
                success_count += 1
            else:
                print(f"  ❌ [FAILED] {s_name}")
        except Exception as e:
            print(f"  ❌ [ERROR] {s_name}: {e}")
            
    print("\n" + "=" * 65)
    print(f"🎉 Synchronization Complete! ({success_count}/{len(local_secrets)} secrets successfully uploaded)")
    print("=" * 65)
    print(f"Verify secrets at: https://github.com/{owner_repo}/settings/secrets/actions")

if __name__ == "__main__":
    main()
