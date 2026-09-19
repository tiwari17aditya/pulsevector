"""
Interactive Authorization Helper for Google Drive & YouTube Data API
Generates/refreshes credentials/token.json with both YouTube and Google Drive scopes.
Outputs the exact JSON snippet to update GitHub Secrets (YOUTUBE_TOKEN_JSON).
"""

import os
import sys
import json
import pathlib
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

    token_path = PROJECT_ROOT / "credentials" / "token.json"
    creds = None

    print("\nRequested Google OAuth Scopes:")
    for s in ALL_GOOGLE_SCOPES:
        print(f"  - {s}")

    print("\nStarting local authentication flow...")
    print("Your web browser will open. Please sign in and grant the requested permissions.")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets_path),
        scopes=ALL_GOOGLE_SCOPES
    )
    creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())

    print(f"\n✅ Successfully saved updated token to: {token_path}")
    print("\n" + "=" * 65)
    print("📋 GITHUB ACTIONS SECRET UPDATE (Required for Headless Cloud Runs)")
    print("=" * 65)
    print("Copy the JSON string below and update your GitHub Secret 'YOUTUBE_TOKEN_JSON':")
    print("-" * 65)
    print(creds.to_json())
    print("-" * 65)
    print("Once updated in GitHub Secrets, your headless GitHub Actions runs will")
    print("automatically upload media to your 5 TB Google Drive while your laptop is off!")


if __name__ == "__main__":
    main()
