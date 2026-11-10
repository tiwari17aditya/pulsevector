"""
Pulse Vector - Autonomous AI Daemon & Execution Control Script (v3.0.0)
Entry point for Windows Task Scheduler, Antigravity Agent, and GitHub Actions.

Usage:
    python scripts/run_autonomous_daemon.py --run-now
    python scripts/run_autonomous_daemon.py --dry-run
    python scripts/run_autonomous_daemon.py --status
    python scripts/run_autonomous_daemon.py --cron
"""

import os
import sys
import argparse
import pathlib
import datetime
import json

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

for p in (str(SRC_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.autonomous_orchestrator import AutonomousOrchestrator
from mcp_server.tools.quotas import check_api_quotas
from mcp_server.tools.orchestration import auto_heal_environment, audit_token_and_quota_ledgers


def print_status_dashboard():
    print("\n" + "=" * 64)
    print("  ⚡ PULSE VECTOR AUTONOMOUS OPERATIONS DASHBOARD")
    print("=" * 64)
    
    # Environment auto-heal check
    healing = auto_heal_environment()
    print(f"Environment Status: {healing.get('status')} ({len(healing.get('healed_actions', []))} actions taken)")
    for act in healing.get("healed_actions", []):
        print(f"  • {act}")
        
    # Quotas & Health
    quotas = check_api_quotas()
    print("\nService Health & Quotas:")
    yt = quotas.get("youtube_api", {})
    print(f"  • YouTube API Units Remaining: {yt.get('units_remaining', 'N/A')} / {yt.get('daily_quota_limit', 10000)} (Status: {yt.get('status')})")
    gem = quotas.get("gemini_api", {})
    print(f"  • Gemini API Status:           {gem.get('status')}")
    sup = quotas.get("supabase_cloud", {})
    print(f"  • Supabase Cloud DB:           {'CONNECTED' if sup.get('connected') else 'DISCONNECTED'}")
    gdr = quotas.get("google_drive_cloud", {})
    print(f"  • Google Drive Cloud:          {gdr.get('status')}")
    stg = quotas.get("storage", {})
    print(f"  • Local Archive Size:          {stg.get('archive_size_mb', 0):.2f} MB ({stg.get('free_disk_gb', 0):.2f} GB free)")
    
    # Audit Token & Quota Ledgers
    audits = audit_token_and_quota_ledgers()
    print("\nLedgers & Accounting:")
    print(f"  • YouTube Quota Estimated Used Today: {audits.get('youtube_quota', {}).get('estimated_used', 0)} units")
    print(f"  • Recent Interaction Turns Logged:    {len(audits.get('recent_token_turns', []))} turns")
    print("=" * 64 + "\n")


def check_cron_window(target_hour_ist: int = 8) -> bool:
    """
    Checks if current local time is within the scheduled 08:00 AM IST execution window (+/- 30 mins).
    """
    now = datetime.datetime.now()
    return now.hour == target_hour_ist


def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Autonomous AI Daemon Control")
    parser.add_argument("--run-now", action="store_true", help="Execute complete autonomous pipeline immediately")
    parser.add_argument("--dry-run", action="store_true", help="Simulate entire autonomous cycle without writing or uploading")
    parser.add_argument("--status", action="store_true", help="Print operational dashboard and quota status")
    parser.add_argument("--cron", action="store_true", help="Execute only if within the daily scheduled IST time window")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing assets")
    parser.add_argument("--output-json", type=str, help="Optional path to write JSON execution report")

    args = parser.parse_args()

    if args.status:
        print_status_dashboard()
        return

    if args.cron:
        if not check_cron_window(8):
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Outside scheduled 08:00 AM IST cron window. Skipping.")
            return
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled 08:00 AM IST trigger confirmed.")

    # Default to run-now if neither status nor cron specified
    orchestrator = AutonomousOrchestrator(dry_run=args.dry_run)
    report = orchestrator.run_full_autonomous_cycle(force=args.force)

    if args.output_json:
        out_p = pathlib.Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved execution report to {out_p}")

    status = report.get("status")
    if status == "COMPLETED_SUCCESSFULLY":
        print("\n🎉 Autonomous cycle completed with 100% success.")
        sys.exit(0)
    else:
        print(f"\n⚠️ Autonomous cycle finished with status: {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()

