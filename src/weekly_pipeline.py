import os
import sys
import argparse
import datetime
import logging
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import ARCHIVE_DIR
from core.pipeline_engine import PipelineEngine
from core.genai_utils import configure_genai
from core.git_backup_utils import run_git_operations, run_backup_operations
from core.database_utils import run_database_upload

engine = PipelineEngine(ARCHIVE_DIR)

def generate_weekly_content(client, target_date):
    return engine.stage_generate_text("weekly", target_date, client=client)

def generate_weekly_slides(target_date=None):
    now = target_date or datetime.datetime.now()
    engine.stage_generate_slides("weekly", now)

def run_weekly_youtube(target_date=None, enable_tts=True):
    now = target_date or datetime.datetime.now()
    engine.stage_compile_video("weekly", now, enable_tts=enable_tts)
    engine.stage_youtube_publish("weekly", now)

def run_all(target_date=None, enable_tts=True, stages=None, dry_run=False, force=False):
    now = target_date or datetime.datetime.now()
    if stages or dry_run:
        engine.run_pipeline("weekly", target_date=now, stages=stages, enable_tts=enable_tts, dry_run=dry_run, force=force)
    else:
        client = configure_genai()
        generate_weekly_content(client, now)
        generate_weekly_slides(now)
        run_weekly_youtube(now, enable_tts=enable_tts)
        run_git_operations("Auto-update: Weekly Current Affairs Pipeline Run")
        run_backup_operations()
        run_database_upload()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Vector Weekly Pipeline")
    parser.add_argument("--date", type=str, help="Target week-ending date in YYYY-MM-DD format")
    parser.add_argument("--stages", type=str, help="Comma-separated stages (text,slides,video,youtube,sync)")
    parser.add_argument("--no-tts", action="store_true", help="Disable AI voiceover")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files")
    
    args = parser.parse_args()
    target_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
    stage_list = [s.strip() for s in args.stages.split(",")] if args.stages else None
    
    run_all(target_date=target_dt, enable_tts=not args.no_tts, stages=stage_list, dry_run=args.dry_run)
