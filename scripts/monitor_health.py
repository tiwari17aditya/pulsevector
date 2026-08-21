"""
Pulse Vector - System & Component Health Monitor
Diagnoses Gemini API, YouTube OAuth, Supabase DB/Storage, FFmpeg, fonts, and archive health.
"""

import os
import sys
import shutil
import datetime
import pathlib
import logging

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure src/ is on sys.path
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import ARCHIVE_DIR, API_KEY
from core.tts_utils import get_ffmpeg_executable, HAS_TTS
from core.image_utils import ensure_fonts
from core.database_utils import get_supabase_client
from core.youtube_utils import SCOPES

def check_ffmpeg() -> dict:
    exe = get_ffmpeg_executable()
    found = bool(shutil.which(exe) or os.path.exists(exe))
    return {
        "status": "PASS" if found else "FAIL",
        "details": f"FFmpeg path: {exe}"
    }

def check_fonts() -> dict:
    regular, bold = ensure_fonts(ARCHIVE_DIR)
    ok = regular.exists() and bold.exists()
    return {
        "status": "PASS" if ok else "WARN",
        "details": f"Regular: {regular.name} ({regular.stat().st_size if regular.exists() else 0} B), Bold: {bold.name} ({bold.stat().st_size if bold.exists() else 0} B)"
    }

def check_audio_library() -> dict:
    audio_dir = ARCHIVE_DIR.parent / "samples" / "Audio"
    tracks = list(audio_dir.glob("*.mp3")) if audio_dir.exists() else []
    return {
        "status": "PASS" if len(tracks) >= 5 else "WARN",
        "details": f"Found {len(tracks)} background audio tracks in {audio_dir.name}"
    }

def check_gemini_api() -> dict:
    if not API_KEY:
        return {"status": "FAIL", "details": "GEMINI_API_KEY is not set in environment."}
    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Respond with the single word: OK'
        )
        if res and res.text:
            return {"status": "PASS", "details": f"Gemini API key is active. Response: '{res.text.strip()}'"}
        return {"status": "WARN", "details": "Gemini API returned empty response."}
    except Exception as e:
        return {"status": "FAIL", "details": f"Gemini API check failed: {e}"}

def check_supabase() -> dict:
    client = get_supabase_client()
    if not client:
        return {"status": "WARN", "details": "SUPABASE_URL or SUPABASE_KEY not configured."}
    try:
        res = client.table("pipeline_runs").select("id").limit(1).execute()
        return {"status": "PASS", "details": "Supabase connection and 'pipeline_runs' table verified."}
    except Exception as e:
        return {"status": "WARN", "details": f"Supabase table check warning: {e}"}

def check_youtube_auth() -> dict:
    token_path = pathlib.Path("credentials/token.json")
    if not token_path.exists():
        token_path = pathlib.Path("token.json")
    if not token_path.exists():
        return {"status": "WARN", "details": "YouTube OAuth token.json not found in credentials/."}
    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        valid = creds.valid or (creds.expired and bool(creds.refresh_token))
        return {
            "status": "PASS" if valid else "WARN",
            "details": f"Token valid: {creds.valid}, Expired: {creds.expired}, Has Refresh Token: {bool(creds.refresh_token)}"
        }
    except Exception as e:
        return {"status": "WARN", "details": f"YouTube token validation error: {e}"}

def check_archive_health() -> dict:
    if not ARCHIVE_DIR.exists():
        return {"status": "FAIL", "details": f"Archive dir '{ARCHIVE_DIR}' does not exist."}
    subdirs = [p.name for p in ARCHIVE_DIR.iterdir() if p.is_dir()]
    return {
        "status": "PASS",
        "details": f"Archive root: {ARCHIVE_DIR} (Found subdirectories: {', '.join(subdirs)})"
    }

def main():
    print("==========================================================")
    print("  🩺 PULSE VECTOR SYSTEM & COMPONENT HEALTH DIAGNOSTIC   ")
    print(f"  Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==========================================================")
    
    checks = [
        ("FFmpeg Media Engine", check_ffmpeg),
        ("Typography & Fonts", check_fonts),
        ("Background Audio Library", check_audio_library),
        ("Edge-TTS Voiceover Engine", lambda: {"status": "PASS" if HAS_TTS else "WARN", "details": f"HAS_TTS = {HAS_TTS}"}),
        ("Gemini AI API & Quota", check_gemini_api),
        ("Supabase Cloud DB & Storage", check_supabase),
        ("YouTube OAuth 2.0 Auth", check_youtube_auth),
        ("Archive Directory Health", check_archive_health),
    ]
    
    all_pass = True
    for name, fn in checks:
        try:
            res = fn()
            status = res["status"]
            details = res["details"]
            icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
            if status == "FAIL":
                all_pass = False
            print(f"{icon} [{status}] {name}")
            print(f"    └─ {details}")
        except Exception as e:
            all_pass = False
            print(f"❌ [FAIL] {name}")
            print(f"    └─ Error during check: {e}")
            
    print("==========================================================")
    if all_pass:
        print("🎉 All core pipeline systems are HEALTHY and ready to run.")
    else:
        print("⚠️ Some systems reported warnings or errors. Check details above.")
    print("==========================================================")

if __name__ == "__main__":
    main()
