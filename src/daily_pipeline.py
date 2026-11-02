import os
import sys
import time
import argparse
import datetime
import logging
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import ARCHIVE_DIR, BT_DATE_FMT
from core.pipeline_engine import PipelineEngine
from core.genai_utils import (
    configure_genai, read_prompts, get_last_processed_date
)
from core.git_backup_utils import run_git_operations, run_backup_operations
from core.database_utils import run_database_upload

engine = PipelineEngine(ARCHIVE_DIR)

def generate_daily_content(client, target_date, ca_prompt=None, bt_prompt=None):
    return engine.stage_generate_text("daily", target_date, client=client)

def run_daily_generation(target_date=None):
    print("\n🚀 Starting Daily Content Generation...")
    client = configure_genai()
    ca_prompt, bt_prompt = read_prompts()
    if not ca_prompt or not bt_prompt:
        return
        
    now = target_date or datetime.datetime.now()
    start_date = datetime.datetime(2026, 6, 15)
    last_processed = get_last_processed_date(ARCHIVE_DIR)
    
    if last_processed:
        next_date = last_processed + datetime.timedelta(days=1)
        if next_date > now:
            print("All up to date! No new content needed.")
            return
        current_target = next_date
    else:
        current_target = start_date
        
    while current_target.date() <= now.date():
        engine.stage_generate_text("daily", current_target, client=client)
        current_target += datetime.timedelta(days=1)
        if current_target.date() <= now.date():
            time.sleep(3)

def generate_daily_slides(target_date=None):
    if target_date:
        engine.stage_generate_slides("daily", target_date)
        return
        
    # Process all missing slides in archive
    for root, dirs, files in os.walk(ARCHIVE_DIR):
        if "Daily" in Path(root).parts and "Images" not in root:
            for file in files:
                if file.startswith("daily-") and file.endswith("_formatted.txt"):
                    text_path = Path(root) / file
                    try:
                        from core.genai_utils import parse_date_from_filename
                        d = parse_date_from_filename(file)
                        if d:
                            engine.stage_generate_slides("daily", d)
                    except Exception as e:
                        logging.error(f"Error rendering daily slides for {file}: {e}")

def generate_teaser_images(target_date=None):
    print("\n🚀 Starting Daily Brain Teaser Image Generation...")
    engine.stage_generate_teasers(target_date)
    print("Brain Teaser Card Generation Complete!")

def run_daily_youtube(target_date=None, enable_tts=True):
    now = target_date or datetime.datetime.now()
    engine.stage_compile_video("daily", now, enable_tts=enable_tts)
    engine.stage_youtube_publish("daily", now)

def run_all(target_date=None, enable_tts=True, stages=None, dry_run=False, force=False):
    now = target_date or datetime.datetime.now()
    if stages or dry_run:
        engine.run_pipeline("daily", target_date=now, stages=stages, enable_tts=enable_tts, dry_run=dry_run, force=force)
    else:
        run_daily_generation(now)
        generate_daily_slides(now)
        generate_teaser_images(now)
        run_daily_youtube(now, enable_tts=enable_tts)
        run_git_operations("Auto-update: Daily Pulse Vector Pipeline Run")
        run_backup_operations()
        run_database_upload()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Vector Daily Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--stages", type=str, help="Comma-separated stages (text,slides,video,youtube,sync)")
    parser.add_argument("--no-tts", action="store_true", help="Disable AI voiceover")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing slides and videos")
    
    args = parser.parse_args()
    target_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
    stage_list = [s.strip() for s in args.stages.split(",")] if args.stages else None
    
    run_all(target_date=target_dt, enable_tts=not args.no_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
