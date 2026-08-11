import argparse
import datetime
import logging
from core.config import current_date_str, log_file
from core.database_utils import run_database_upload

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Content Automation Pipeline (Router)")
    parser.add_argument("--daily", action="store_true", help="Run the Daily Pipeline")
    parser.add_argument("--weekly", action="store_true", help="Run the Weekly Pipeline")
    parser.add_argument("--monthly", action="store_true", help="Run the Monthly Pipeline")
    parser.add_argument("--all", action="store_true", help="Run Daily (and conditionally Weekly/Monthly based on date)")
    
    # Optional flags for granular control (passed down to the pipelines if implemented)
    parser.add_argument("--generate", action="store_true", help="Only run text generation")
    parser.add_argument("--slides", action="store_true", help="Only run slide/image generation")
    parser.add_argument("--youtube", action="store_true", help="Only run YouTube video upload")
    parser.add_argument("--no-tts", action="store_true", help="Disable AI voiceover generation")
    
    args = parser.parse_args()
    enable_tts = not args.no_tts
    
    print(f"--- Pulse Vector Automation Pipeline v2.0.0 ---")
    print(f"Log File: {log_file}")
    
    now = datetime.datetime.now()
    
    if args.daily:
        import daily_pipeline
        daily_pipeline.run_daily_generation()
        daily_pipeline.generate_daily_slides()
        daily_pipeline.generate_teaser_images()
        daily_pipeline.run_daily_youtube(enable_tts=enable_tts)
        daily_pipeline.run_git_operations("Auto-update: Daily Pulse Vector Pipeline Run")
        daily_pipeline.run_backup_operations()
        run_database_upload()
        return

    if args.weekly:
        import weekly_pipeline
        weekly_pipeline.run_all(enable_tts=enable_tts)
        return
        
    if args.monthly:
        import monthly_pipeline
        monthly_pipeline.run_all(enable_tts=enable_tts)
        return

    print("Running dynamic orchestration based on today's date...")
    import daily_pipeline
    daily_pipeline.run_daily_generation()
    daily_pipeline.generate_daily_slides()
    daily_pipeline.generate_teaser_images()
    daily_pipeline.run_daily_youtube(enable_tts=enable_tts)
    daily_pipeline.run_git_operations("Auto-update: Daily Pulse Vector Pipeline Run")
    daily_pipeline.run_backup_operations()
    run_database_upload()
    
    if now.weekday() == 6 or args.weekly:
        print("\n[Auto-Trigger] Sunday detected. Running Weekly Pipeline...")
        import weekly_pipeline
        weekly_pipeline.run_all(enable_tts=enable_tts)
        
    is_month_end = (now + datetime.timedelta(days=1)).month != now.month
    if is_month_end or args.monthly:
        print("\n[Auto-Trigger] Month-End detected. Running Monthly Pipeline...")
        import monthly_pipeline
        monthly_pipeline.run_all(enable_tts=enable_tts)
        
    print("\n✅ All automated pipelines completed.")

if __name__ == "__main__":
    main()
