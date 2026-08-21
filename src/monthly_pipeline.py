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

def resolve_target_month(target_date=None) -> datetime.datetime:
    """If target_date is given, use it. Otherwise, if today is early in the month (day <= 3), target previous month."""
    if target_date:
        return target_date
    now = datetime.datetime.now()
    if now.day <= 3:
        # Target last day of previous month
        first_of_this_month = datetime.datetime(now.year, now.month, 1)
        prev_month_last_day = first_of_this_month - datetime.timedelta(days=1)
        return prev_month_last_day
    return now

def generate_monthly_content(client, target_date):
    t_date = resolve_target_month(target_date)
    return engine.stage_generate_text("monthly", t_date, client=client)

def generate_monthly_slides(target_date=None):
    t_date = resolve_target_month(target_date)
    engine.stage_generate_slides("monthly", t_date)

def run_monthly_youtube(target_date=None, enable_tts=True):
    t_date = resolve_target_month(target_date)
    engine.stage_compile_video("monthly", t_date, enable_tts=enable_tts)
    engine.stage_youtube_publish("monthly", t_date)

def run_all(target_date=None, enable_tts=True, stages=None, dry_run=False):
    t_date = resolve_target_month(target_date)
    if stages or dry_run:
        engine.run_pipeline("monthly", target_date=t_date, stages=stages, enable_tts=enable_tts, dry_run=dry_run)
    else:
        client = configure_genai()
        generate_monthly_content(client, t_date)
        generate_monthly_slides(t_date)
        run_monthly_youtube(t_date, enable_tts=enable_tts)
        run_git_operations("Auto-update: Monthly Current Affairs Pipeline Run")
        run_backup_operations()
        run_database_upload()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Vector Monthly Pipeline")
    parser.add_argument("--month", type=str, help="Target month in YYYY-MM format (e.g. 2026-07)")
    parser.add_argument("--stages", type=str, help="Comma-separated stages (text,slides,video,youtube,sync)")
    parser.add_argument("--no-tts", action="store_true", help="Disable AI voiceover")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without generating files")
    
    args = parser.parse_args()
    target_dt = None
    if args.month:
        target_dt = datetime.datetime.strptime(args.month, "%Y-%m")
        
    stage_list = [s.strip() for s in args.stages.split(",")] if args.stages else None
    run_all(target_date=target_dt, enable_tts=not args.no_tts, stages=stage_list, dry_run=args.dry_run)
