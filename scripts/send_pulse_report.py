#!/usr/bin/env python3
"""
Pulse Vector - Executive Email Report Dispatcher CLI
Generates and delivers weekly and monthly reports to addytiwari3@gmail.com.
"""

import os
import sys
import argparse
import pathlib
import datetime

# Ensure src/ is on sys.path
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure Windows terminal outputs UTF-8 cleanly
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from core.report_utils import (
    IST,
    get_ist_now,
    get_weekly_report_window,
    get_monthly_report_window,
    parse_youtube_upload_records,
    parse_community_poll_records,
    build_category_breakdown,
    generate_community_polls_pdf,
    render_report_html,
    render_report_text,
    send_report_email,
    DEFAULT_RECIPIENT
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pulse Vector Executive Email Report Dispatcher"
    )
    parser.add_argument(
        "--period",
        choices=["weekly", "monthly"],
        default="weekly",
        help="Report period: weekly (prior Sun-Sat) or monthly (preceding month)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target reference date in YYYY-MM-DD format (defaults to current IST date)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Optional manual start date override (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Optional manual end date override (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate report, print summary and save HTML without sending email"
    )
    parser.add_argument(
        "--to",
        type=str,
        default=DEFAULT_RECIPIENT,
        help=f"Recipient email address (default: {DEFAULT_RECIPIENT})"
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="reports",
        help="Directory to save generated HTML reports (default: reports)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    now_ist = get_ist_now()

    target_date = now_ist.date()
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Error: Invalid date format '{args.date}'. Expected YYYY-MM-DD.")
            sys.exit(1)

    # Determine reporting window
    if args.start_date and args.end_date:
        s_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
        e_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()
        start_dt = datetime.datetime.combine(s_date, datetime.time.min, tzinfo=IST)
        end_dt = datetime.datetime.combine(e_date, datetime.time.max, tzinfo=IST)
    elif args.period == "weekly":
        start_dt, end_dt = get_weekly_report_window(target_date)
    else:
        start_dt, end_dt = get_monthly_report_window(target_date)

    print(f"📊 Generating Pulse Vector {args.period.upper()} Report...")
    print(f"   Target Reference Date : {target_date}")
    print(f"   Window Range (IST)    : {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Recipient             : {args.to}")

    # Parse data sources
    uploads = parse_youtube_upload_records(start_dt, end_dt)
    polls = parse_community_poll_records(start_dt, end_dt)
    cat_summary = build_category_breakdown(uploads)

    print(f"   Found {len(uploads)} video uploads and {len(polls)} community challenge posts in period.")

    # Save directory
    save_dir = BASE_DIR / args.save_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Community Polls & Challenges PDF Attachment
    pdf_filename = f"pulse_{args.period}_community_polls_{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}.pdf"
    pdf_file_path = save_dir / pdf_filename

    generate_community_polls_pdf(
        period_name=args.period,
        start_dt=start_dt,
        end_dt=end_dt,
        polls=polls,
        output_pdf_path=str(pdf_file_path)
    )
    print(f"✅ Generated Community Polls PDF: {pdf_file_path.relative_to(BASE_DIR)}")

    # 2. Render HTML and Text Formats (with PDF badge and cloud storage section omitted)
    html_content = render_report_html(
        period_name=args.period,
        start_dt=start_dt,
        end_dt=end_dt,
        videos=uploads,
        polls=polls,
        cat_summary=cat_summary,
        pdf_attachment_name=pdf_filename
    )
    text_content = render_report_text(
        period_name=args.period,
        start_dt=start_dt,
        end_dt=end_dt,
        videos=uploads,
        polls=polls,
        cat_summary=cat_summary,
        pdf_attachment_name=pdf_filename
    )

    # 3. Save HTML artifact
    report_filename = f"pulse_{args.period}_report_{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}.html"
    report_file_path = save_dir / report_filename

    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Saved HTML Report to: {report_file_path.relative_to(BASE_DIR)}")

    # Print summary text preview to console
    print("\n" + text_content + "\n")

    # 4. Email Dispatch (with attached PDF)
    subject = f"Pulse Vector {args.period.title()} Report — {start_dt.strftime('%d %b')} to {end_dt.strftime('%d %b %Y')}"
    if args.dry_run:
        print(f"🔍 Dry-run complete. Email delivery skipped.")
        return

    print(f"📧 Sending report with PDF attachment to {args.to}...")
    success, msg = send_report_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        recipient=args.to,
        pdf_attachment_path=str(pdf_file_path)
    )

    if success:
        print(f"🎉 {msg}")
    else:
        print(f"⚠️ {msg}")
        if "not configured" in msg:
            print("\n💡 SETUP INSTRUCTIONS FOR GMAIL AUTOMATED DELIVERY:")
            print("1. Visit your Google Account -> Security -> 2-Step Verification -> App Passwords.")
            print("2. Create an App Password for 'Pulse Vector Reports'.")
            print("3. Set SMTP_APP_PASSWORD=<16-character-password> in your .env file or run:")
            print("   python scripts/sync_github_secrets.py")
            print("   to automatically push the secret to GitHub Actions.")


if __name__ == "__main__":
    main()
