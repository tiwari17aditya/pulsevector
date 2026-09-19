"""
Interactive Authorization Helper for Google Drive & YouTube Data API
Generates/refreshes credentials/token.json with both YouTube and Google Drive scopes.
Outputs the exact JSON snippet to update GitHub Secrets (YOUTUBE_TOKEN_JSON).
"""

import os
import sys
import json
import pathlib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from google_auth_oauthlib.flow import InstalledAppFlow

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.youtube_utils import ALL_GOOGLE_SCOPES, YOUTUBE_SCOPES, GDRIVE_SCOPES


def main():
    print("=" * 65)
    print("🔑 Pulse Vector - Google OAuth (YouTube + Google Drive) Setup")
    print("=" * 65)

    client_secrets_path = PROJECT_ROOT / "credentials" / "client_secrets.json"
    if not client_secrets_path.exists() and (PROJECT_ROOT / "client_secrets.json").exists():
        client_secrets_path = PROJECT_ROOT / "client_secrets.json"

    if not client_secrets_path.exists():
        print(f"❌ Error: client_secrets.json not found at {client_secrets_path}")
        print("Please place your OAuth client secrets file in credentials/client_secrets.json.")
        sys.exit(1)

    token_path = PROJECT_ROOT / "credentials" / "gdrive_token.json"
    creds = None

    print("\nRequested Google OAuth Scopes (Google Drive Only):", flush=True)
    for s in GDRIVE_SCOPES:
        print(f"  - {s}", flush=True)

    print("\nStarting local authentication flow for Google Drive...", flush=True)
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets_path),
        scopes=GDRIVE_SCOPES
    )
    
    port = 8090
    url_file_path = PROJECT_ROOT / "credentials" / "auth_url.txt"
    url_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    class UrlWriterMessage:
        def format(self, **kwargs):
            url = kwargs.get('url', '')
            with open(url_file_path, 'w', encoding='utf-8') as f:
                f.write(url)
            return (
                "\n" + "=" * 65 + "\n"
                "👉 AUTHORIZATION LINK (Click to authorize Google Drive):\n" +
                url + "\n" +
                "=" * 65 + "\n"
            )
            
    creds = flow.run_local_server(
        port=port,
        open_browser=True,
        prompt='consent',
        access_type='offline',
        authorization_prompt_message=UrlWriterMessage()
    )




    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as token_file:

        token_file.write(creds.to_json())

    print(f"\n✅ Successfully saved updated token to: {token_path}")
    print("\n" + "=" * 65)
    print("📋 GITHUB ACTIONS SECRET UPDATE (For Headless Cloud Runs)")
    print("=" * 65)
    print("Copy the JSON string below and add it to GitHub Secrets as 'GDRIVE_TOKEN_JSON':")
    print("-" * 65)
    print(creds.to_json())
    print("-" * 65)
    print("Your headless GitHub Actions runs will now be able to upload media directly")
    print("to your 5 TB Google Drive via the API even when your laptop is turned off!")



if __name__ == "__main__":
    main()
