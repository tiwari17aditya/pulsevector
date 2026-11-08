import os
import sys
import logging
import pathlib
import datetime
from dotenv import load_dotenv

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding issues with emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logging directory anchored to project root and dynamic daily filename
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)
current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = log_dir / f"pipeline_{current_date_str}.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Configuration and Paths (with Env Overrides)
ARCHIVE_DIR = pathlib.Path(os.getenv("PULSE_ARCHIVE_DIR", "pulse_archive"))
INPUT_DIR = pathlib.Path(os.getenv("PULSE_INPUT_DIR", "incoming_data"))
PROMPTS_FILE = pathlib.Path(os.getenv("PULSE_PROMPTS_FILE", ".agent/pulse_prompts.md"))
# External Backup Path (only activate when G: drive is mounted on Windows)
_default_backup = r"G:\My Drive\antigravity-projects-storage\pulse-vector\pulse_archive"
BACKUP_DIR = os.getenv(
    "PULSE_BACKUP_DIR",
    _default_backup if os.name == "nt" and os.path.exists(r"G:\My Drive") else None
)
API_KEY = os.getenv("GEMINI_API_KEY")

BT_DATE_FMT = "%d%b%y"

# Cloud Storage & Google Drive Configuration
GOOGLE_DRIVE_FOLDER_PATH = os.getenv("GOOGLE_DRIVE_FOLDER_PATH", "antigravity-projects-storage/pulse-vector")
GOOGLE_DRIVE_FOLDER_NAME = os.getenv("GOOGLE_DRIVE_FOLDER_NAME", "pulse-vector")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1j8pokFycYk6YSu1drLZBrpRRn4pu7KfV")
ENABLE_GDRIVE_UPLOAD = os.getenv("ENABLE_GDRIVE_UPLOAD", "true").lower() in ("true", "1", "yes")
ENABLE_SUPABASE_STORAGE_UPLOAD = os.getenv("ENABLE_SUPABASE_STORAGE_UPLOAD", "false").lower() in ("true", "1", "yes")


# Social Media & Community Handles / Links
PULSE_PLAY_BASE_URL = os.getenv("PULSE_PLAY_URL", "https://tiwari17aditya.github.io/pulsevector/play/")
PULSE_TELEGRAM_URL = os.getenv("PULSE_TELEGRAM_URL", "https://t.me/pulsevector_daily")
PULSE_TELEGRAM_BOT = os.getenv("PULSE_TELEGRAM_BOT", "@PulseVectorOfficial_bot")
PULSE_YOUTUBE_URL = os.getenv("PULSE_YOUTUBE_URL", "https://www.youtube.com/@Pulse_vector")
PULSE_DISCORD_URL = os.getenv("PULSE_DISCORD_URL", "")
PULSE_INSTAGRAM_URL = os.getenv("PULSE_INSTAGRAM_URL", "")
PULSE_X_URL = os.getenv("PULSE_X_URL", "")


