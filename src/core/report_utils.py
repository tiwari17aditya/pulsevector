"""
Pulse Vector - Automated Reporting Engine
Generates executive Weekly and Monthly email reports with categorized tabular breakdowns,
publication timestamps, YouTube links, community poll details, and cloud backup summaries.
"""

import os
import re
import glob
import smtplib
import pathlib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Tuple, Any, Optional

# Standard IST timezone (+05:30)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DEFAULT_RECIPIENT = os.environ.get("REPORT_RECIPIENT_EMAIL", "addytiwari3@gmail.com")
DEFAULT_SENDER = os.environ.get("SMTP_USER", os.environ.get("REPORT_RECIPIENT_EMAIL", "addytiwari3@gmail.com"))
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", os.environ.get("PULSE_SMTP_PASSWORD", ""))


def get_ist_now() -> datetime.datetime:
    """Returns the current datetime in IST."""
    return datetime.datetime.now(IST)


def get_weekly_report_window(target_date: Optional[datetime.date] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Computes the prior Sunday-to-Saturday window for the Weekly Report.
    Rule: On Sunday 8 Jan, the report covers Sunday 1 Jan (00:00:00 IST) to Saturday 7 Jan (23:59:59 IST).
    """
    if target_date is None:
        target_date = get_ist_now().date()
        
    # If today is Sunday (weekday == 6), previous week starts 7 days ago and ends 1 day ago.
    # If called on any other day, aligns with the most recent completed Sunday-to-Saturday cycle.
    days_since_sunday = (target_date.weekday() + 1) % 7  # 0 if Sunday, 1 if Mon, ..., 6 if Sat
    if days_since_sunday == 0:
        # Running on Sunday: Previous week is from target_date - 7 days to target_date - 1 day
        start_date = target_date - datetime.timedelta(days=7)
        end_date = target_date - datetime.timedelta(days=1)
    else:
        # Running on non-Sunday: take the most recent completed week (ending on the Saturday just passed)
        end_date = target_date - datetime.timedelta(days=days_since_sunday)
        start_date = end_date - datetime.timedelta(days=6)

    start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=IST)
    end_dt = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=IST)
    return start_dt, end_dt


def get_monthly_report_window(target_date: Optional[datetime.date] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Computes the preceding 1-month window ending on the day before the report date.
    Rule: For month of Jan (run on 31 Jan), carries info from 31 Dec to 30 Jan.
    """
    if target_date is None:
        target_date = get_ist_now().date()

    # End date is target_date - 1 day (e.g. 30 Jan for 31 Jan run)
    end_date = target_date - datetime.timedelta(days=1)

    # Start date is end of previous month or 1 month prior (e.g. 31 Dec for 31 Jan run)
    # Day 1 of target month minus 1 day gives the last day of the prior month
    first_of_month = target_date.replace(day=1)
    start_date = first_of_month - datetime.timedelta(days=1)

    start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=IST)
    end_dt = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=IST)
    return start_dt, end_dt


def parse_upload_timestamp(ts_str: str) -> Optional[datetime.datetime]:
    """Parses timestamps like '2026-09-19 05:50 IST' or '2026-07-19 21:31 IST' into an IST datetime."""
    clean_ts = ts_str.strip()
    if clean_ts.endswith("IST"):
        clean_ts = clean_ts[:-3].strip()
    
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(clean_ts, fmt)
            return dt.replace(tzinfo=IST)
        except ValueError:
            continue
    return None


def parse_youtube_upload_records(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    details_file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parses Research/youtube_upload_details.md and extracts video uploads within the [start_dt, end_dt] window.
    """
    if not details_file_path:
        candidates = [
            pathlib.Path("Research/youtube_upload_details.md"),
            pathlib.Path("youtube_upload_details.md"),
        ]
        for c in candidates:
            if c.exists():
                details_file_path = str(c)
                break

    if not details_file_path or not os.path.exists(details_file_path):
        return []

    records = []
    with open(details_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    table_header_found = False
    for line in lines:
        line_clean = line.strip()
        if not line_clean.startswith("|"):
            continue

        parts = [p.strip() for p in line_clean.split("|")[1:-1]]
        if len(parts) < 7:
            continue

        if "Date (IST)" in parts[0] or "Video Title" in parts[1]:
            table_header_found = True
            continue

        if not table_header_found:
            continue

        # Skip separator line like | :--- | :--- | ...
        if parts[0].startswith(":") or parts[0].startswith("---") or "*Template*" in parts[0]:
            continue

        date_str, title, category, video_type, related_video, pinned_status, video_id = parts[:7]

        dt = parse_upload_timestamp(date_str)
        if not dt:
            continue

        if start_dt <= dt <= end_dt:
            # Clean video_id
            clean_vid = video_id.strip("` \t\r\n[]")
            yt_link = f"https://youtu.be/{clean_vid}" if clean_vid and clean_vid != "N/A" else "N/A"

            # Determine normalized content category
            normalized_cat = categorize_video(title, video_type, category)

            records.append({
                "raw_date": date_str,
                "datetime": dt,
                "title": title,
                "category": normalized_cat,
                "raw_category": category,
                "video_type": video_type,
                "related_video": related_video,
                "pinned_status": pinned_status,
                "video_id": clean_vid,
                "youtube_url": yt_link
            })

    # Sort chronologically
    records.sort(key=lambda x: x["datetime"])
    return records


def categorize_video(title: str, video_type: str, raw_category: str) -> str:
    """Normalizes video into executive reporting categories."""
    t_lower = title.lower()
    vt_lower = video_type.lower()

    if "brain teaser" in t_lower or "brainteaser" in t_lower or "brain teaser" in vt_lower:
        return "Daily Brain Teaser"
    elif "monthly current affairs" in t_lower or "monthly" in vt_lower:
        return "Monthly Current Affairs"
    elif "weekly current affairs" in t_lower or "weekly" in vt_lower or "masterclass" in vt_lower:
        return "Weekly Current Affairs"
    elif "daily current affairs" in t_lower:
        return "Daily Current Affairs"
    else:
        # Fallback to category name if specific, or General
        if "(" in raw_category:
            return raw_category.split("(")[0].strip()
        return "Special Feature"


def parse_community_poll_records(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    archive_dir: str = "pulse_archive"
) -> List[Dict[str, Any]]:
    """
    Parses community polls and brain teaser challenge assets in pulse_archive/ created within the window.
    """
    polls = []
    poll_files = glob.glob(os.path.join(archive_dir, "**", "poll-*.txt"), recursive=True)
    poll_files += glob.glob(os.path.join(archive_dir, "**", "brainteaser-*.txt"), recursive=True)

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    seen_dates = set()

    for p_path in poll_files:
        try:
            fname = os.path.basename(p_path)
            # Try to extract date from filename e.g. poll-19sep26.txt or brainteaser-19sep26.txt
            m = re.search(r"(\d{1,2})([a-z]{3})(\d{2})", fname.lower())
            if not m:
                continue

            day, mon_str, yr_2d = int(m.group(1)), m.group(2), int(m.group(3))
            mon = month_map.get(mon_str)
            if not mon:
                continue
            year = 2000 + yr_2d

            poll_date = datetime.date(year, mon, day)
            poll_dt = datetime.datetime.combine(poll_date, datetime.time(8, 0), tzinfo=IST)

            if not (start_dt <= poll_dt <= end_dt):
                continue

            date_key = poll_date.strftime("%Y-%m-%d")
            if date_key in seen_dates and fname.startswith("brainteaser"):
                # Prefer poll-*.txt if both exist for same date
                continue

            with open(p_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse question and options
            question = ""
            options = []
            correct_ans = "Revealed in Discussion"

            for line in content.splitlines():
                l_strip = line.strip()
                if l_strip.startswith("Q.") or l_strip.startswith("Question:"):
                    question = l_strip
                elif re.match(r"^[•\-\*]?\s*[a-d]\.\s*", l_strip, re.IGNORECASE):
                    options.append(l_strip.lstrip("•-* ").strip())
                elif "Correct Answer:" in l_strip:
                    correct_ans = l_strip.replace("Correct Answer:", "").strip()

            if not question:
                first_few = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
                question = first_few[0] if first_few else "Brain Teaser Daily Challenge"

            polls.append({
                "date_str": poll_date.strftime("%d %b %Y"),
                "datetime": poll_dt,
                "question": question,
                "options": " | ".join(options) if options else "Multiple Choice (4 Options)",
                "correct_answer": correct_ans,
                "platforms": "YouTube Community, Telegram, Discord",
                "file_name": fname
            })
            seen_dates.add(date_key)
        except Exception:
            continue

    polls.sort(key=lambda x: x["datetime"])
    return polls


def build_category_breakdown(videos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes category-wise counts, video formats, and percentage shares.
    """
    total_videos = len(videos)
    breakdown = {}

    for v in videos:
        cat = v["category"]
        vtype = v["video_type"]
        if cat not in breakdown:
            breakdown[cat] = {
                "count": 0,
                "types": set(),
                "videos": []
            }
        breakdown[cat]["count"] += 1
        breakdown[cat]["types"].add(vtype)
        breakdown[cat]["videos"].append(v)

    # Calculate percentages and format types
    result = []
    for cat, data in sorted(breakdown.items(), key=lambda x: x[1]["count"], reverse=True):
        count = data["count"]
        share = (count / total_videos * 100) if total_videos > 0 else 0
        result.append({
            "category": cat,
            "count": count,
            "types_display": ", ".join(sorted(data["types"])),
            "share_percent": f"{share:.1f}%"
        })

    return {
        "total_count": total_videos,
        "categories": result
    }


def render_report_html(
    period_name: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    videos: List[Dict[str, Any]],
    polls: List[Dict[str, Any]],
    cat_summary: Dict[str, Any],
    extra_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Renders an executive, responsive, modern dark-gradient HTML email report.
    """
    period_title = period_name.title()
    date_range_display = f"{start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')}"
    generated_at_str = get_ist_now().strftime("%d %b %Y, %I:%M %p IST")

    total_uploads = cat_summary["total_count"]
    total_polls = len(polls)
    category_rows = cat_summary["categories"]

    # Category counts lookup
    cat_counts = {c["category"]: c["count"] for c in category_rows}
    ca_count = cat_counts.get("Daily Current Affairs", 0)
    bt_count = cat_counts.get("Daily Brain Teaser", 0)
    weekly_count = cat_counts.get("Weekly Current Affairs", 0)
    monthly_count = cat_counts.get("Monthly Current Affairs", 0)

    # Build category breakdown rows HTML
    cat_table_rows_html = ""
    for c in category_rows:
        cat_table_rows_html += f"""
        <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #1e293b;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #6366f1; margin-right: 8px;"></span>
                {c['category']}
            </td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: center; font-weight: 700; color: #0f172a; font-size: 15px;">
                {c['count']}
            </td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #475569; font-size: 13px;">
                {c['types_display']}
            </td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600; color: #4338ca;">
                <span style="background-color: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{c['share_percent']}</span>
            </td>
        </tr>
        """

    if not cat_table_rows_html:
        cat_table_rows_html = """<tr><td colspan="4" style="padding: 16px; text-align: center; color: #64748b;">No uploads recorded during this period.</td></tr>"""

    # Build video uploads table rows HTML
    video_table_rows_html = ""
    for idx, v in enumerate(videos, 1):
        clean_vid = v.get("video_id", "N/A")
        yt_url = v.get("youtube_url", "#")
        link_badge = f"""<a href="{yt_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #ef4444, #dc2626); color: #ffffff; text-decoration: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px;">▶ {clean_vid}</a>""" if clean_vid != "N/A" else '<span style="color: #94a3b8; font-size: 12px;">N/A</span>'

        badge_color = "#3b82f6"
        if "Brain" in v["category"]:
            badge_color = "#8b5cf6"
        elif "Weekly" in v["category"]:
            badge_color = "#10b981"
        elif "Monthly" in v["category"]:
            badge_color = "#f59e0b"

        video_table_rows_html += f"""
        <tr style="background-color: {'#f8fafc' if idx % 2 == 0 else '#ffffff'};">
            <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: #64748b; font-size: 13px;">{idx}</td>
            <td style="padding: 12px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #0f172a; white-space: nowrap; font-family: monospace;">
                <strong>{v['raw_date']}</strong>
            </td>
            <td style="padding: 12px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #1e293b; line-height: 1.4;">
                {v['title']}
            </td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; text-align: center;">
                <span style="background-color: {badge_color}18; color: {badge_color}; border: 1px solid {badge_color}40; padding: 3px 8px; border-radius: 8px; font-weight: 600; font-size: 11px; white-space: nowrap;">
                    {v['category']}
                </span>
            </td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
                {v['video_type']}
            </td>
            <td style="padding: 12px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">
                {link_badge}
            </td>
        </tr>
        """

    if not video_table_rows_html:
        video_table_rows_html = """<tr><td colspan="6" style="padding: 20px; text-align: center; color: #64748b;">No video uploads found for the specified timeframe.</td></tr>"""

    # Build community polls table rows HTML
    poll_table_rows_html = ""
    for idx, p in enumerate(polls, 1):
        poll_table_rows_html += f"""
        <tr style="background-color: {'#f8fafc' if idx % 2 == 0 else '#ffffff'};">
            <td style="padding: 10px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: #64748b; font-size: 12px;">{idx}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; font-weight: 600; color: #0f172a; white-space: nowrap;">{p['date_str']}</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #334155; line-height: 1.4;">
                <strong>{p['question']}</strong><br>
                <span style="font-size: 11px; color: #64748b;">Options: {p['options']}</span>
            </td>
            <td style="padding: 10px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; text-align: center; font-weight: 600; color: #059669;">
                <span style="background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 6px;">{p['correct_answer']}</span>
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 11px; color: #475569; text-align: center;">
                YouTube Community, Telegram, Discord
            </td>
        </tr>
        """

    if not poll_table_rows_html:
        poll_table_rows_html = """<tr><td colspan="5" style="padding: 16px; text-align: center; color: #64748b;">No community poll challenges generated in this window.</td></tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pulse Vector {period_title} Executive Report</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #334155;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 25px 10px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 800px; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);">
                    
                    <!-- HEADER BANNER -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); padding: 35px 30px; text-align: left; border-bottom: 4px solid #6366f1;">
                            <table width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <div style="display: inline-block; background-color: rgba(99, 102, 241, 0.2); border: 1px solid #818cf8; border-radius: 20px; padding: 4px 14px; margin-bottom: 12px;">
                                            <span style="color: #a5b4fc; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">
                                                PULSE VECTOR &bull; EXECUTIVE REPORTING
                                            </span>
                                        </div>
                                        <h1 style="color: #ffffff; font-size: 26px; margin: 0 0 6px 0; font-weight: 800; letter-spacing: -0.5px;">
                                            {period_title} Performance Report
                                        </h1>
                                        <p style="color: #cbd5e1; font-size: 14px; margin: 0; font-weight: 500;">
                                            Reporting Period: <strong style="color: #38bdf8;">{date_range_display}</strong>
                                        </p>
                                    </td>
                                    <td align="right" valign="top" style="display: none; @media (min-width: 500px) {{ display: table-cell; }}">
                                        <div style="background-color: rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 10px 14px; text-align: right; border: 1px solid rgba(255, 255, 255, 0.1);">
                                            <span style="display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase;">Generated</span>
                                            <span style="font-size: 12px; color: #f8fafc; font-weight: 600;">{generated_at_str}</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- EXECUTIVE KPI METRIC CARDS -->
                    <tr>
                        <td style="padding: 24px 30px 10px 30px; background-color: #f8fafc;">
                            <table width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <!-- Card 1 -->
                                    <td width="23%" style="background-color: #ffffff; border-radius: 10px; padding: 14px 12px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total Uploads</div>
                                        <div style="font-size: 28px; font-weight: 800; color: #4338ca; margin: 4px 0 2px 0;">{total_uploads}</div>
                                        <div style="font-size: 10px; color: #10b981; font-weight: 600;">Videos Published</div>
                                    </td>
                                    <td width="2%">&nbsp;</td>
                                    <!-- Card 2 -->
                                    <td width="23%" style="background-color: #ffffff; border-radius: 10px; padding: 14px 12px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Current Affairs</div>
                                        <div style="font-size: 28px; font-weight: 800; color: #0284c7; margin: 4px 0 2px 0;">{ca_count + weekly_count + monthly_count}</div>
                                        <div style="font-size: 10px; color: #0284c7; font-weight: 600;">Shorts + Masterclass</div>
                                    </td>
                                    <td width="2%">&nbsp;</td>
                                    <!-- Card 3 -->
                                    <td width="23%" style="background-color: #ffffff; border-radius: 10px; padding: 14px 12px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Brain Teasers</div>
                                        <div style="font-size: 28px; font-weight: 800; color: #7c3aed; margin: 4px 0 2px 0;">{bt_count}</div>
                                        <div style="font-size: 10px; color: #7c3aed; font-weight: 600;">9:16 Visual Puzzles</div>
                                    </td>
                                    <td width="2%">&nbsp;</td>
                                    <!-- Card 4 -->
                                    <td width="23%" style="background-color: #ffffff; border-radius: 10px; padding: 14px 12px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Community Polls</div>
                                        <div style="font-size: 28px; font-weight: 800; color: #059669; margin: 4px 0 2px 0;">{total_polls}</div>
                                        <div style="font-size: 10px; color: #059669; font-weight: 600;">Broadcast & Polls</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- SECTION 1: CATEGORY-WISE BREAKDOWN TABLE -->
                    <tr>
                        <td style="padding: 24px 30px 10px 30px;">
                            <div style="border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 14px;">
                                <h2 style="font-size: 17px; margin: 0; color: #0f172a; font-weight: 700;">
                                    📊 Category-Wise Upload Summary
                                </h2>
                                <p style="font-size: 12px; color: #64748b; margin: 3px 0 0 0;">
                                    Distribution and percentage share of uploaded content across pipeline formats.
                                </p>
                            </div>
                            <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                <thead>
                                    <tr style="background-color: #f1f5f9;">
                                        <th style="padding: 10px 14px; text-align: left; font-size: 12px; color: #475569; font-weight: 700; text-transform: uppercase;">Content Category</th>
                                        <th style="padding: 10px 14px; text-align: center; font-size: 12px; color: #475569; font-weight: 700; text-transform: uppercase;">Videos Uploaded</th>
                                        <th style="padding: 10px 14px; text-align: left; font-size: 12px; color: #475569; font-weight: 700; text-transform: uppercase;">Formats / Aspect Ratio</th>
                                        <th style="padding: 10px 14px; text-align: right; font-size: 12px; color: #475569; font-weight: 700; text-transform: uppercase;">Share</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {cat_table_rows_html}
                                </tbody>
                            </table>
                        </td>
                    </tr>

                    <!-- SECTION 2: COMPLETE UPLOADED VIDEOS DIRECTORY TABLE -->
                    <tr>
                        <td style="padding: 20px 30px 10px 30px;">
                            <div style="border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 14px;">
                                <h2 style="font-size: 17px; margin: 0; color: #0f172a; font-weight: 700;">
                                    🎬 Published Videos & Live Timestamps
                                </h2>
                                <p style="font-size: 12px; color: #64748b; margin: 3px 0 0 0;">
                                    Comprehensive record of live videos, release times (IST), formats, and YouTube links.
                                </p>
                            </div>
                            <div style="overflow-x: auto;">
                                <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                    <thead>
                                        <tr style="background-color: #0f172a; color: #ffffff;">
                                            <th style="padding: 10px 8px; text-align: center; font-size: 11px; font-weight: 700; text-transform: uppercase; width: 40px;">#</th>
                                            <th style="padding: 10px 12px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; width: 140px;">Time of Live (IST)</th>
                                            <th style="padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase;">Video Title</th>
                                            <th style="padding: 10px 10px; text-align: center; font-size: 11px; font-weight: 700; text-transform: uppercase; width: 110px;">Category</th>
                                            <th style="padding: 10px 10px; text-align: center; font-size: 11px; font-weight: 700; text-transform: uppercase; width: 90px;">Type</th>
                                            <th style="padding: 10px 12px; text-align: center; font-size: 11px; font-weight: 700; text-transform: uppercase; width: 90px;">YouTube</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {video_table_rows_html}
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>

                    <!-- SECTION 3: COMMUNITY POSTS & POLLS TABLE -->
                    <tr>
                        <td style="padding: 20px 30px 20px 30px;">
                            <div style="border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 14px;">
                                <h2 style="font-size: 17px; margin: 0; color: #0f172a; font-weight: 700;">
                                    💬 Community Posts, Polls & Engagement
                                </h2>
                                <p style="font-size: 12px; color: #64748b; margin: 3px 0 0 0;">
                                    1-Click Daily Brain Teaser community polls, MCQ options, answers, and broadcast channels.
                                </p>
                            </div>
                            <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                                <thead>
                                    <tr style="background-color: #f1f5f9;">
                                        <th style="padding: 10px 8px; text-align: center; font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase; width: 40px;">#</th>
                                        <th style="padding: 10px 12px; text-align: left; font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase; width: 90px;">Date</th>
                                        <th style="padding: 10px 14px; text-align: left; font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase;">Poll Challenge & Options</th>
                                        <th style="padding: 10px 10px; text-align: center; font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase; width: 90px;">Answer</th>
                                        <th style="padding: 10px 12px; text-align: center; font-size: 11px; color: #475569; font-weight: 700; text-transform: uppercase; width: 140px;">Broadcast Channels</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {poll_table_rows_html}
                                </tbody>
                            </table>
                        </td>
                    </tr>

                    <!-- SECTION 4: CLOUD STORAGE & BACKUP STATUS -->
                    <tr>
                        <td style="padding: 10px 30px 24px 30px;">
                            <div style="background-color: #f8fafc; border-radius: 10px; padding: 16px 20px; border: 1px solid #e2e8f0;">
                                <table width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td>
                                            <h3 style="font-size: 14px; margin: 0 0 4px 0; color: #1e293b; font-weight: 700;">
                                                ☁️ Cloud Storage & Archive Infrastructure
                                            </h3>
                                            <p style="font-size: 12px; color: #64748b; margin: 0; line-height: 1.4;">
                                                &bull; <strong>Google Drive Cloud</strong>: Active (5 TB Quota) &mdash; <code>MyDrive/antigravity-projects-storage/pulse-vector/</code><br>
                                                &bull; <strong>Supabase Free Tier Database</strong>: Metadata runs and logs synchronized.<br>
                                                &bull; <strong>YouTube Distribution Quota</strong>: Active &bull; Channel: <code>@PulseVector</code>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>

                    <!-- FOOTER -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 24px 30px; text-align: center; border-top: 1px solid #1e293b;">
                            <p style="color: #cbd5e1; font-size: 12px; margin: 0 0 6px 0; font-weight: 500;">
                                <strong>Pulse Vector</strong> &bull; Where Ancient History Meets Modern Knowledge
                            </p>
                            <p style="color: #64748b; font-size: 11px; margin: 0;">
                                Automated Dispatch System &bull; Delivered to {DEFAULT_RECIPIENT} &bull; Generated {generated_at_str}
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def render_report_text(
    period_name: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    videos: List[Dict[str, Any]],
    polls: List[Dict[str, Any]],
    cat_summary: Dict[str, Any]
) -> str:
    """Renders plain text fallback for email clients without HTML support."""
    lines = [
        f"==================================================================",
        f"       PULSE VECTOR — {period_name.upper()} PERFORMANCE REPORT",
        f"==================================================================",
        f"Period: {start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')}",
        f"Generated At: {get_ist_now().strftime('%d %b %Y, %I:%M %p IST')}",
        "",
        "--- 1. CATEGORY BREAKDOWN ---",
    ]
    for c in cat_summary["categories"]:
        lines.append(f"- {c['category']}: {c['count']} videos ({c['share_percent']}) | Formats: {c['types_display']}")

    lines.append("")
    lines.append(f"Total Videos Uploaded: {cat_summary['total_count']}")
    lines.append(f"Total Community Polls: {len(polls)}")
    lines.append("")
    lines.append("--- 2. UPLOADED VIDEOS (LIVE TIMESTAMPS & LINKS) ---")
    for idx, v in enumerate(videos, 1):
        lines.append(f"{idx}. [{v['raw_date']}] {v['title']}")
        lines.append(f"   Category: {v['category']} | Type: {v['video_type']} | Link: {v['youtube_url']}")

    if polls:
        lines.append("")
        lines.append("--- 3. COMMUNITY POLLS & CHALLENGES ---")
        for idx, p in enumerate(polls, 1):
            lines.append(f"{idx}. [{p['date_str']}] {p['question']}")
            lines.append(f"   Options: {p['options']} | Answer: {p['correct_answer']}")

    lines.append("")
    lines.append("==================================================================")
    lines.append("Cloud Storage: Google Drive 5 TB (Synced) | Channel: @PulseVector")
    return "\n".join(lines)


def send_report_email(
    subject: str,
    html_content: str,
    text_content: str,
    recipient: str = DEFAULT_RECIPIENT,
    sender: str = DEFAULT_SENDER,
    smtp_host: str = SMTP_HOST,
    smtp_port: int = SMTP_PORT,
    smtp_password: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends the multi-part HTML/Plain-text report email via SMTP (SSL/TLS).
    Returns (success: bool, status_message: str).
    """
    if smtp_password is None:
        smtp_password = SMTP_PASSWORD

    if not smtp_password:
        return False, (
            "SMTP password / Google App Password is not configured. "
            "Please configure SMTP_APP_PASSWORD in environment or GitHub Secrets to enable automatic inbox delivery."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Pulse Vector Automation <{sender}>"
    msg["To"] = recipient
    msg["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    part1 = MIMEText(text_content, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(sender, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender, smtp_password)
                server.send_message(msg)
        return True, f"Successfully delivered email report to {recipient}"
    except Exception as e:
        return False, f"Failed to send email via SMTP ({smtp_host}:{smtp_port}): {e}"
