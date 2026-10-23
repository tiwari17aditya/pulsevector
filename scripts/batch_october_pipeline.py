"""
Pulse Vector - October 2026 Daily Current Affairs Batch Generator & YouTube Publisher

Batches daily current affairs generation, rendering, and YouTube uploads in intervals
(default batch size = 10) to respect YouTube API quotas and upload rate limits.
"""

import os
import sys
import time
import argparse
import datetime
import pathlib
import logging
from typing import List, Optional

# Ensure src/ is on sys.path
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config import ARCHIVE_DIR
from core.pipeline_engine import PipelineEngine
from core.genai_utils import configure_genai

engine = PipelineEngine(ARCHIVE_DIR)


def is_video_already_uploaded(target_date: datetime.datetime) -> Optional[str]:
    """Checks Research/youtube_upload_details.md to see if target date has been uploaded."""
    details_file = ROOT / "Research" / "youtube_upload_details.md"
    if not details_file.exists():
        return None
    try:
        content = details_file.read_text(encoding="utf-8")
        date_str_1 = target_date.strftime("%d %B %Y")
        date_str_2 = target_date.strftime("%d %b %Y")
        date_str_3 = target_date.strftime("%Y-%m-%d")
        
        for line in content.splitlines():
            if not line.startswith("|") or "Video Title" in line or "Template" in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                title = parts[2]
                vid_id = parts[7]
                if ("Daily Current Affairs" in title or "Daily" in parts[4]) and (
                    date_str_1.lower() in title.lower()
                    or date_str_2.lower() in title.lower()
                    or date_str_3 in parts[1]
                ):
                    if vid_id and vid_id != "N/A" and not vid_id.startswith("["):
                        return vid_id
    except Exception as e:
        logging.warning(f"Error checking upload log: {e}")
    return None


def update_youtube_quota_log(uploads_today: List[dict]):
    """Appends upload records to Research/youtube_quota_log.md."""
    quota_log_file = ROOT / "Research" / "youtube_quota_log.md"
    if not quota_log_file.exists() or not uploads_today:
        return

    today_str = datetime.datetime.now().strftime("%B %d, %Y")
    now_d_str = datetime.datetime.now().strftime("%d %b %Y")
    
    total_new_uploads = len(uploads_today)
    # Estimate query cost per video upload (~1600 quota units for videos.insert + comment + playlist)
    cost_per_upload = 1600
    total_query_cost = total_new_uploads * cost_per_upload
    uploads_left = max(0, 100 - total_new_uploads)
    query_left = max(0, 10000 - total_query_cost)

    entry_lines = [
        f"\n## 📊 Daily Quota Log ({today_str})\n",
        "| Date | Video Category | Video ID | Action taken | Video Count | Uploads Left | Query Cost (est) | Query Quota Left |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for idx, u in enumerate(uploads_today, 1):
        rem_up = 100 - idx
        rem_q = max(0, 10000 - (idx * cost_per_upload))
        entry_lines.append(
            f"| **{u['date']}** | Daily | `{u['video_id']}` | Uploaded & Added to Playlist | {idx} video{'s' if idx > 1 else ''} | {rem_up} left | ~{cost_per_upload} units | {rem_q} units |"
        )
    entry_lines.append(f"\n*Total Videos Uploaded Today*: {total_new_uploads} / 100  ")
    entry_lines.append(f"*Total Query Quota Consumed Today*: ~{total_query_cost} units  ")
    entry_lines.append(f"*Remaining YouTube Quota*: {uploads_left} uploads and ~{query_left} query units\n")

    try:
        content = quota_log_file.read_text(encoding="utf-8")
        content += "\n" + "\n".join(entry_lines)
        quota_log_file.write_text(content, encoding="utf-8")
        print(f"✅ Appended {total_new_uploads} uploads to {quota_log_file.name}")
    except Exception as e:
        logging.error(f"Failed to update youtube_quota_log.md: {e}")


def run_batch_pipeline(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    batch_size: int = 10,
    interval_seconds: int = 10,
    batch_interval_seconds: int = 20,
    enable_tts: bool = True,
    dry_run: bool = False,
    force: bool = False
):
    print("=" * 65)
    print("  🚀 PULSE VECTOR — OCTOBER BATCH GENERATOR & PUBLISHER")
    print(f"  Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"  Batch Size: {batch_size} | Interval: {interval_seconds}s | Batch Interval: {batch_interval_seconds}s")
    print(f"  Dry Run: {dry_run} | Force: {force} | TTS: {enable_tts}")
    print("=" * 65)

    # 1. Collect all dates in range
    dates: List[datetime.datetime] = []
    curr = start_date
    while curr <= end_date:
        dates.append(curr)
        curr += datetime.timedelta(days=1)

    print(f"📋 Total Days to Process: {len(dates)}")

    # 2. Divide into batches
    batches = [dates[i:i + batch_size] for i in range(0, len(dates), batch_size)]
    print(f"📦 Total Batches: {len(batches)}")

    genai_client = configure_genai()
    uploaded_records = []
    limit_hit = False

    for batch_idx, batch in enumerate(batches, 1):
        b_start_str = batch[0].strftime("%d %b")
        b_end_str = batch[-1].strftime("%d %b %Y")
        print("\n" + "#" * 65)
        print(f"  >> BATCH {batch_idx}/{len(batches)}: {b_start_str} to {b_end_str} ({len(batch)} days)")
        print("#" * 65)

        for d_idx, dt in enumerate(batch, 1):
            date_str = dt.strftime("%Y-%m-%d")
            display_str = dt.strftime("%d %B %Y")
            paths = engine.get_paths("daily", dt)
            print(f"\n--- [{batch_idx}.{d_idx}] Processing: {display_str} ({date_str}) ---")

            # 1. Text Generation
            if not paths["text_file"].exists() or force:
                print(f"  [1/4] Generating Text for {date_str}...")
                engine.stage_generate_text("daily", dt, client=genai_client)
            else:
                print(f"  [1/4] Text file already exists: {paths['text_file'].name}")

            # 2. Slide Generation
            slide_images = list(paths["img_dir"].glob(f"{paths['tag']}_page-*.png")) if paths["img_dir"].exists() else []
            if not slide_images or force:
                print(f"  [2/4] Rendering Slides for {date_str}...")
                engine.stage_generate_slides("daily", dt)
            else:
                print(f"  [2/4] Slides already exist ({len(slide_images)} slides).")

            # 3. Video Compilation
            if not paths["video_file"].exists() or force:
                print(f"  [3/4] Compiling Video for {date_str}...")
                engine.stage_compile_video("daily", dt, enable_tts=enable_tts, force=force)
            else:
                print(f"  [3/4] Video already exists: {paths['video_file'].name}")

            # 4. YouTube Upload
            existing_vid = is_video_already_uploaded(dt)
            if existing_vid and not force:
                print(f"  [4/4] ⏩ Video already uploaded to YouTube (ID: {existing_vid}). Skipping.")
                continue

            if dry_run:
                print(f"  [4/4] 🧪 [DRY RUN] Skipping YouTube upload for {date_str}.")
                continue

            if limit_hit:
                print(f"  [4/4] ⚠️ YouTube limit was hit earlier. Skipping upload for {date_str} (video preserved).")
                continue

            print(f"  [4/4] 🚀 Publishing to YouTube for {date_str}...")
            try:
                vid_id = engine.stage_youtube_publish("daily", dt)
                if vid_id:
                    print(f"  ✅ Upload successful! Video ID: {vid_id}")
                    uploaded_records.append({
                        "date": dt.strftime("%d %b %Y"),
                        "video_id": vid_id,
                        "title": f"Daily Current Affairs {dt.strftime('%d %B %Y')}"
                    })
                    print(f"  ⏳ Waiting {interval_seconds}s interval before next upload...")
                    time.sleep(interval_seconds)
                else:
                    print(f"  ⚠️ Upload did not return a Video ID. It may have failed or quota exhausted.")
            except Exception as yt_err:
                err_msg = str(yt_err).lower()
                print(f"  ❌ YouTube upload error on {date_str}: {yt_err}")
                if "quotaexceeded" in err_msg or "uploadlimitexceeded" in err_msg or "daily limit" in err_msg:
                    print("\n" + "!" * 65)
                    print("  🚨 YouTube API Quota or Daily Upload Limit Exceeded!")
                    print("  Halting remaining YouTube uploads for this session.")
                    print("  All slides, voiceovers, and videos are saved locally.")
                    print("!" * 65)
                    limit_hit = True

        # End of Batch Sync
        print(f"\n📦 Finished Batch {batch_idx}/{len(batches)}. Syncing Git and Backups...")
        commit_title = f"Auto-update: October Daily Current Affairs Batch {batch_idx} ({b_start_str} to {b_end_str})"
        engine.stage_sync_and_backup(commit_msg=commit_title)

        if batch_idx < len(batches) and not limit_hit:
            print(f"\n☕ Batch {batch_idx} complete. Waiting {batch_interval_seconds}s before starting Batch {batch_idx + 1}...")
            time.sleep(batch_interval_seconds)

    # Final summary & log updates
    if uploaded_records:
        update_youtube_quota_log(uploaded_records)

    print("\n" + "=" * 65)
    print("  🏁 BATCH PROCESSING SUMMARY")
    print(f"  Total Days Targeted: {len(dates)}")
    print(f"  Videos Uploaded This Session: {len(uploaded_records)}")
    if limit_hit:
        print("  ⚠️ YouTube upload limit/quota was encountered during the run.")
    else:
        print("  ✅ All eligible videos processed successfully!")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Vector October Batch Generator & Publisher")
    parser.add_argument("--start-date", type=str, default="2026-10-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2026-10-23", help="End date (YYYY-MM-DD)")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of days per batch (default: 10)")
    parser.add_argument("--interval", type=int, default=8, help="Seconds between video uploads in batch (default: 8)")
    parser.add_argument("--batch-interval", type=int, default=15, help="Seconds between batches (default: 15)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without uploading to YouTube")
    parser.add_argument("--force", action="store_true", help="Force regenerate slides and videos")
    parser.add_argument("--no-tts", action="store_true", help="Disable TTS voiceover")

    args = parser.parse_args()
    start_dt = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")

    run_batch_pipeline(
        start_date=start_dt,
        end_date=end_dt,
        batch_size=args.batch_size,
        interval_seconds=args.interval,
        batch_interval_seconds=args.batch_interval,
        enable_tts=not args.no_tts,
        dry_run=args.dry_run,
        force=args.force
    )
