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
