import argparse
import datetime
import logging
import os
import sys
import pathlib

SRC_DIR = pathlib.Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import current_date_str, log_file, ARCHIVE_DIR
from core.pipeline_engine import PipelineEngine
import daily_pipeline
import weekly_pipeline
import monthly_pipeline

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Content Automation Pipeline (Modular Router)")
    parser.add_argument("--daily", action="store_true", help="Run the Daily Pipeline")
    parser.add_argument("--weekly", action="store_true", help="Run the Weekly Pipeline")
    parser.add_argument("--monthly", action="store_true", help="Run the Monthly Pipeline")
    parser.add_argument("--all", action="store_true", help="Run Daily (and conditionally Weekly/Monthly based on date)")
    
    # Granular Stage Selection
    parser.add_argument("--stages", type=str, help="Comma-separated stage list: text,slides,video,youtube,sync")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--month", type=str, help="Target month in YYYY-MM format (e.g. 2026-07)")
    parser.add_argument("--no-tts", action="store_true", help="Disable AI voiceover generation")
    parser.add_argument("--dry-run", action="store_true", help="Validate pipeline stages without writing files or uploading")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing slides and videos")
    
    # Legacy flags
    parser.add_argument("--generate", action="store_true", help="Only run text generation")
    parser.add_argument("--slides", action="store_true", help="Only run slide/image generation")
    parser.add_argument("--youtube", action="store_true", help="Only run YouTube video upload")
    
    args = parser.parse_args()
    enable_tts = not args.no_tts
    
    # Resolve stages if legacy flags are used
    stage_list = None
    if args.stages:
        stage_list = [s.strip().lower() for s in args.stages.split(",")]
    elif args.generate:
        stage_list = ["text"]
    elif args.slides:
        stage_list = ["slides"]
    elif args.youtube:
        stage_list = ["youtube"]
        
    print(f"--- Pulse Vector Automation Pipeline v3.0.0 (Modular Engine) ---")
    print(f"Log File: {log_file}")
    
    target_dt = None
    if args.date:
        target_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    elif args.month:
        target_dt = datetime.datetime.strptime(args.month, "%Y-%m")
        
    now = target_dt or datetime.datetime.now()
    
    if args.daily:
        daily_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
        return

    if args.weekly:
        weekly_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
        return
        
    if args.monthly:
        monthly_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
        return

    print("Running dynamic orchestration based on date...")
    daily_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
    
    if now.weekday() == 6 or args.all:
        print("\n[Auto-Trigger] Sunday detected. Running Weekly Pipeline...")
        weekly_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
        
    is_month_end = (now + datetime.timedelta(days=1)).month != now.month
    if is_month_end or args.all:
        print("\n[Auto-Trigger] Month-End detected. Running Monthly Pipeline...")
        monthly_pipeline.run_all(target_date=now, enable_tts=enable_tts, stages=stage_list, dry_run=args.dry_run, force=args.force)
        
    print("\n✅ All automated pipelines completed.")

if __name__ == "__main__":
    main()
