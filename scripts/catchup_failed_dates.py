"""
Pulse Vector - Catchup Script for Failed Dates (Post Sep 8 Fix)
Runs all missed pipelines in order: Daily -> Weekly -> Brain Teasers

Usage:
    python scripts/catchup_failed_dates.py [--dry-run] [--no-tts] [--skip-daily] [--skip-weekly] [--skip-bt]
"""

import argparse
import datetime
import sys
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT / "src"
sys.path.insert(0, str(SRC))

ARCHIVE = ROOT / "pulse_archive" / "2026" / "September"


def run(cmd: list, label: str) -> int:
    print(f"\n{'='*60}")
    print(f"  >> {label}")
    print(f"  CMD: {' '.join(str(c) for c in cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"  [WARN] {label} exited with code {result.returncode}")
    else:
        print(f"  [OK] {label} completed successfully")
    return result.returncode


def daily_video_exists(date: datetime.datetime) -> bool:
    day   = str(date.day)
    month = date.strftime("%b").lower()
    year  = date.strftime("%Y")
    tag   = f"daily-{day}{month}-{year}_formatted.mp4"
    return (ARCHIVE / "Daily_Videos" / tag).exists()


def daily_text_exists(date: datetime.datetime) -> bool:
    day   = str(date.day)
    month = date.strftime("%b").lower()
    year  = date.strftime("%Y")
    tag   = f"daily-{day}{month}-{year}_formatted.txt"
    return (ARCHIVE / "Daily" / tag).exists()


def weekly_video_exists(date: datetime.datetime) -> bool:
    tag = f"weekly-{date.strftime('%d-%b-%Y').lower()}_formatted.mp4"
    return (ARCHIVE / "Weekly_Videos" / tag).exists()


def weekly_text_exists(date: datetime.datetime) -> bool:
    tag = f"weekly-{date.strftime('%d-%b-%Y').lower()}_formatted.txt"
    return (ARCHIVE / "Weekly" / tag).exists()


def bt_image_exists(date: datetime.datetime) -> bool:
    stem = f"brainteaser-{date.strftime('%d%b%y').lower()}"
    img  = ARCHIVE / "Brain_Teasers" / "Images" / f"{stem}_styled.png"
    return img.exists()


def bt_text_exists(date: datetime.datetime) -> bool:
    stem = f"brainteaser-{date.strftime('%d%b%y').lower()}.txt"
    return (ARCHIVE / "Brain_Teasers" / "Text" / stem).exists()


def main():
    parser = argparse.ArgumentParser(description="Catchup failed pipeline dates")
    parser.add_argument("--dry-run",     action="store_true", help="Validate without uploading")
    parser.add_argument("--no-tts",      action="store_true", help="Disable TTS voiceover")
    parser.add_argument("--skip-daily",  action="store_true")
    parser.add_argument("--skip-weekly", action="store_true")
    parser.add_argument("--skip-bt",     action="store_true", help="Skip Brain Teasers")
    parser.add_argument("--force",       action="store_true", help="Force regenerate even if video exists")
    args = parser.parse_args()

    py       = sys.executable
    tts_flag = ["--no-tts"] if args.no_tts  else []
    dry_flag = ["--dry-run"] if args.dry_run else []
    frc_flag = ["--force"]  if args.force   else []
    errors   = []

    # ----------------------------------------------------------
    # SECTION 1: DAILY  (Sep 1 -> Sep 13)
    # ----------------------------------------------------------
    if not args.skip_daily:
        print("\n" + "#"*60)
        print("  SECTION 1: DAILY PIPELINE CATCHUP  (Sep 1 - Sep 13)")
        print("#"*60)

        cur = datetime.datetime(2026, 9, 1)
        end = datetime.datetime(2026, 9, 13)
        while cur <= end:
            ds = cur.strftime("%Y-%m-%d")
            if daily_video_exists(cur) and not args.force:
                print(f"  [SKIP] {ds}: video already exists")
                cur += datetime.timedelta(days=1)
                continue

            stages = "slides,video,youtube" if daily_text_exists(cur) else "text,slides,video,youtube"
            label  = f"Daily {ds} ({stages})"
            rc = run([py, str(SRC / "pipeline.py"), "--daily", "--date", ds,
                      "--stages", stages, *tts_flag, *dry_flag, *frc_flag], label)
            if rc != 0:
                errors.append(f"DAILY {ds} -> exit {rc}")
            cur += datetime.timedelta(days=1)

    # ----------------------------------------------------------
    # SECTION 2: WEEKLY  (Sep 6 text-exists + Sep 13 full)
    # ----------------------------------------------------------
    if not args.skip_weekly:
        print("\n" + "#"*60)
        print("  SECTION 2: WEEKLY PIPELINE CATCHUP")
        print("#"*60)

        weekly_dates = [
            datetime.datetime(2026, 9, 6),
            datetime.datetime(2026, 9, 13),
        ]
        for wdate in weekly_dates:
            ds = wdate.strftime("%Y-%m-%d")
            if weekly_video_exists(wdate) and not args.force:
                print(f"  [SKIP] Weekly {ds}: video already exists")
                continue
            stages = "slides,video,youtube" if weekly_text_exists(wdate) else "text,slides,video,youtube"
            label  = f"Weekly {ds} ({stages})"
            rc = run([py, str(SRC / "pipeline.py"), "--weekly", "--date", ds,
                      "--stages", stages, *tts_flag, *dry_flag, *frc_flag], label)
            if rc != 0:
                errors.append(f"WEEKLY {ds} -> exit {rc}")

    # ----------------------------------------------------------
    # SECTION 3: BRAIN TEASERS  (Sep 5 -> Sep 13)
    # ----------------------------------------------------------
    if not args.skip_bt:
        print("\n" + "#"*60)
        print("  SECTION 3: BRAIN TEASER CATCHUP  (Sep 5 - Sep 13)")
        print("#"*60)

        cur = datetime.datetime(2026, 9, 5)
        end = datetime.datetime(2026, 9, 13)
        while cur <= end:
            ds = cur.strftime("%Y-%m-%d")
            if bt_image_exists(cur) and not args.force:
                print(f"  [SKIP] BT {ds}: styled image already exists")
                cur += datetime.timedelta(days=1)
                continue

            if not bt_text_exists(cur):
                # Full pipeline: generate + slides + video + upload
                rc = run([py, str(SRC / "brainteaser_pipeline.py"), "--date", ds, *dry_flag],
                         f"BrainTeaser {ds} (full)")
                if rc != 0:
                    errors.append(f"BT-FULL {ds} -> exit {rc}")
            else:
                # Text exists -> slides first, then video+upload
                rc = run([py, str(SRC / "brainteaser_pipeline.py"), "--date", ds, "--slides-only", *dry_flag],
                         f"BrainTeaser {ds} (slides-only)")
                if rc != 0:
                    errors.append(f"BT-SLIDES {ds} -> exit {rc}")

                rc = run([py, str(SRC / "brainteaser_pipeline.py"), "--date", ds, "--video-only", *dry_flag],
                         f"BrainTeaser {ds} (video+upload)")
                if rc != 0:
                    errors.append(f"BT-VIDEO {ds} -> exit {rc}")

            cur += datetime.timedelta(days=1)

    # ----------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------
    print("\n" + "#"*60)
    print("  CATCHUP SUMMARY")
    print("#"*60)
    if errors:
        print(f"\n  [WARN] {len(errors)} pipeline(s) had errors:")
        for e in errors:
            print(f"     - {e}")
        sys.exit(1)
    else:
        print("\n  [OK] All catchup pipelines completed successfully!")


if __name__ == "__main__":
    main()
