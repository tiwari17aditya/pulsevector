"""
Pulse Vector - Interactive Meta Developer & Instagram Auth Assistant
Guides developers through exchanging short-lived tokens for 60-day long-lived tokens,
auto-discovering the Instagram Business Account ID, and persisting credentials to .env.
"""

import os
import sys
import re
import pathlib
import datetime
from typing import Optional, Dict

# Ensure src/ is on path
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.meta_utils import (
    exchange_for_long_lived_token,
    discover_instagram_account_id,
    get_meta_credentials,
    GRAPH_API_BASE
)


def update_env_file(key_value_pairs: Dict[str, str], env_path: pathlib.Path = pathlib.Path(".env")):
    """Safely updates or appends environment variables to .env without clobbering existing keys."""
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines = []
    
    for line in lines:
        matched = False
        for k, v in key_value_pairs.items():
            if re.match(rf"^\s*{re.escape(k)}\s*=", line):
                new_lines.append(f"{k}={v}")
                updated_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    # Append any remaining keys
    for k, v in key_value_pairs.items():
        if k not in updated_keys:
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")
            new_lines.append(f"{k}={v}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"✅ Updated {env_path.name} with keys: {', '.join(key_value_pairs.keys())}")


def test_current_credentials():
    """Tests existing Meta credentials configured in environment or .env."""
    print("\n🔍 Checking existing Meta credentials...")
    creds = get_meta_credentials()
    token = creds.get("access_token")
    acc_id = creds.get("account_id")
    app_id = creds.get("app_id")

    if not token or not acc_id:
        print("❌ Meta credentials are not fully configured in .env.")
        print("   META_ACCESS_TOKEN:    " + ("Configured" if token else "MISSING"))
        print("   INSTAGRAM_ACCOUNT_ID: " + ("Configured" if acc_id else "MISSING"))
        print("   META_APP_ID:          " + ("Configured" if app_id else "Optional/Missing"))
        return False

    print("✅ Credentials found in .env.")
    print(f"   INSTAGRAM_ACCOUNT_ID: {acc_id}")
    print(f"   META_ACCESS_TOKEN:    {token[:6]}...{token[-4:]} ({len(token)} chars)")

    # Test token validity via discover
    print("\n📡 Testing connection to Meta Graph API...")
    info = discover_instagram_account_id(token)
    if info:
        print(f"🎉 Connected successfully!")
        print(f"   Facebook Page:      {info.get('page_name')} (ID: {info.get('page_id')})")
        print(f"   Instagram Account:  @{info.get('instagram_username')} (ID: {info.get('instagram_account_id')})")
        return True
    else:
        print("⚠️ Token could not resolve linked Instagram Account. It may be expired or lack permissions.")
        return False


def run_interactive_wizard():
    """Runs interactive token exchange and discovery wizard."""
    print("=" * 60)
    print("  🚀 PULSE VECTOR — META DEVELOPER AUTHENTICATION SETUP")
    print("=" * 60)
    print("This wizard will:")
    print("1. Take your Meta App ID, App Secret, and Short-Lived Access Token")
    print("2. Exchange it for a 60-day Long-Lived Access Token")
    print("3. Auto-detect your Instagram Business Account ID from your Facebook Page")
    print("4. Persist the credentials into your local .env file")
    print("-" * 60)

    app_id = input("\nEnter your Meta App ID: ").strip()
    if not app_id:
        print("❌ App ID is required.")
        return

    app_secret = input("Enter your Meta App Secret: ").strip()
    if not app_secret:
        print("❌ App Secret is required.")
        return

    short_token = input("Enter your Short-Lived User Token (from Graph API Explorer): ").strip()
    if not short_token:
        print("❌ Token is required.")
        return

    print("\n⏳ Exchanging for 60-Day Long-Lived Access Token...")
    res = exchange_for_long_lived_token(short_token, app_id, app_secret)
    if not res or "access_token" not in res:
        print("❌ Failed to exchange token. Please verify your App ID, App Secret, and token.")
        return

    long_lived_token = res["access_token"]
    expires_in = res.get("expires_in", 5184000)
    days = expires_in // 86400
    print(f"🎉 Success! Generated Long-Lived Token (valid for ~{days} days).")

    print("\n🔍 Discovering linked Instagram Business Account...")
    acc_info = discover_instagram_account_id(long_lived_token)
    page_id = None
    if acc_info:
        ig_id = acc_info["instagram_account_id"]
        ig_user = acc_info.get("instagram_username", "Unknown")
        page_name = acc_info.get("page_name", "Unknown")
        page_id = acc_info.get("page_id")
        print(f"🎉 Found Instagram Business Account: @{ig_user} (ID: {ig_id})")
        print(f"   Linked via Facebook Page: '{page_name}' (Page ID: {page_id})")
    else:
        print("⚠️ Could not auto-detect Instagram Account ID from Facebook Page.")
        ig_id = input("Please manually enter your numeric Instagram Business Account ID: ").strip()

    if not ig_id:
        print("❌ Instagram Account ID is required for Reels/Photo publishing.")
        return

    updates = {
        "META_APP_ID": app_id,
        "META_APP_SECRET": app_secret,
        "META_ACCESS_TOKEN": long_lived_token,
        "INSTAGRAM_ACCOUNT_ID": ig_id,
    }
    if page_id:
        updates["FACEBOOK_PAGE_ID"] = page_id

    confirm = input("\nSave these credentials to .env? (y/n) [y]: ").strip().lower()
    if confirm in ("", "y", "yes"):
        update_env_file(updates)
        print("\n🎉 Setup complete! Pulse Vector is ready to publish to Instagram Reels.")
    else:
        print("Skipped updating .env.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_current_credentials()
    else:
        # Check if already configured
        creds = get_meta_credentials()
        if creds.get("access_token") and creds.get("account_id"):
            print("Meta credentials already found in .env.")
            choice = input("Do you want to (1) Test existing credentials, or (2) Re-run setup wizard? [1]: ").strip()
            if choice == "2":
                run_interactive_wizard()
            else:
                test_current_credentials()
        else:
            run_interactive_wizard()


if __name__ == "__main__":
    main()
