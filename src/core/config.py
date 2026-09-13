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

# Setup logging directory and dynamic daily filename
log_dir = pathlib.Path("logs")
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
BACKUP_DIR = os.getenv("PULSE_BACKUP_DIR", r"G:\PulseVectorBackups\pulse_archive")
API_KEY = os.getenv("GEMINI_API_KEY")

BT_DATE_FMT = "%d%b%y"

# Social Media & Community Handles / Links
PULSE_PLAY_BASE_URL = os.getenv("PULSE_PLAY_URL", "https://tiwari17aditya.github.io/pulsevector/play/")
PULSE_TELEGRAM_URL = os.getenv("PULSE_TELEGRAM_URL", "https://t.me/pulsevector_daily")
PULSE_TELEGRAM_BOT = os.getenv("PULSE_TELEGRAM_BOT", "@PulseVectorOfficial_bot")
PULSE_YOUTUBE_URL = os.getenv("PULSE_YOUTUBE_URL", "https://www.youtube.com/@PulseVector")
PULSE_DISCORD_URL = os.getenv("PULSE_DISCORD_URL", "")
PULSE_INSTAGRAM_URL = os.getenv("PULSE_INSTAGRAM_URL", "")
PULSE_X_URL = os.getenv("PULSE_X_URL", "")

