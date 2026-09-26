"""
Pulse Vector - Automated Reporting Engine
Generates executive Weekly and Monthly email reports with categorized tabular breakdowns,
publication timestamps, YouTube links, and attached PDF dossiers of Community Polls.

Includes comprehensive error handling, sanitization, and fallback protection at every layer.
"""

import os
import re
import glob
import html
import logging
import smtplib
import pathlib
import datetime
import xml.sax.saxutils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import email.utils
from typing import Dict, List, Tuple, Any, Optional

# ReportLab imports for professional PDF generation
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Standard IST timezone (+05:30)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DEFAULT_RECIPIENT = os.environ.get("REPORT_RECIPIENT_EMAIL", "addytiwari3@gmail.com")
DEFAULT_SENDER = os.environ.get("SMTP_USER", os.environ.get("REPORT_RECIPIENT_EMAIL", "addytiwari3@gmail.com"))
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", os.environ.get("PULSE_SMTP_PASSWORD", ""))


def get_ist_now() -> datetime.datetime:
    """Returns the current datetime in IST."""
    try:
        return datetime.datetime.now(IST)
    except Exception as e:
        logging.warning(f"Error resolving IST datetime, falling back to local: {e}")
        return datetime.datetime.now()


def get_weekly_report_window(target_date: Optional[datetime.date] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Computes the prior Sunday-to-Saturday window for the Weekly Report.
    Rule: On Sunday 8 Jan, the report covers Sunday 1 Jan (00:00:00 IST) to Saturday 7 Jan (23:59:59 IST).
    """
    try:
        if target_date is None:
            target_date = get_ist_now().date()
        elif not isinstance(target_date, datetime.date):
            if isinstance(target_date, str):
                target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            else:
                target_date = get_ist_now().date()

        days_since_sunday = (target_date.weekday() + 1) % 7  # 0 if Sunday, 1 if Mon, ..., 6 if Sat
        if days_since_sunday == 0:
            start_date = target_date - datetime.timedelta(days=7)
            end_date = target_date - datetime.timedelta(days=1)
        else:
            end_date = target_date - datetime.timedelta(days=days_since_sunday)
            start_date = end_date - datetime.timedelta(days=6)

        start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=IST)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=IST)
        return start_dt, end_dt
    except Exception as e:
        logging.error(f"Error in get_weekly_report_window: {e}. Using fallback 7-day window.")
        now = get_ist_now()
        return now - datetime.timedelta(days=7), now


def get_monthly_report_window(target_date: Optional[datetime.date] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Computes the preceding 1-month window ending on the day before the report date.
    Rule: For month of Jan (run on 31 Jan), carries info from 31 Dec to 30 Jan.
    """
    try:
        if target_date is None:
            target_date = get_ist_now().date()
        elif not isinstance(target_date, datetime.date):
            if isinstance(target_date, str):
                target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            else:
                target_date = get_ist_now().date()

        end_date = target_date - datetime.timedelta(days=1)
        first_of_month = target_date.replace(day=1)
        start_date = first_of_month - datetime.timedelta(days=1)

        start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=IST)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=IST)
        return start_dt, end_dt
    except Exception as e:
        logging.error(f"Error in get_monthly_report_window: {e}. Using fallback 30-day window.")
        now = get_ist_now()
        return now - datetime.timedelta(days=30), now


def parse_upload_timestamp(ts_str: str) -> Optional[datetime.datetime]:
    """Parses timestamps like '2026-09-19 05:50 IST' or '2026-07-19 21:31 IST' into an IST datetime."""
    if not ts_str or not isinstance(ts_str, str):
        return None

    try:
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
    except Exception as e:
        logging.debug(f"Could not parse timestamp '{ts_str}': {e}")
        return None


def parse_youtube_upload_records(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    details_file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parses Research/youtube_upload_details.md and extracts video uploads within the [start_dt, end_dt] window.
    Isolated per-line error handling ensures malformed rows never interrupt other records.
    """
    try:
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
            logging.warning(f"Upload details tracking file not found at {details_file_path}")
            return []

        records = []
        try:
            with open(details_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(details_file_path, "r", encoding="latin-1", errors="replace") as f:
                lines = f.readlines()

        table_header_found = False
        for line_num, line in enumerate(lines, 1):
            try:
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

                if parts[0].startswith(":") or parts[0].startswith("---") or "*Template*" in parts[0]:
                    continue

                date_str, title, category, video_type, related_video, pinned_status, video_id = parts[:7]

                dt = parse_upload_timestamp(date_str)
                if not dt:
                    continue

                if start_dt <= dt <= end_dt:
                    clean_vid = video_id.strip("` \t\r\n[]")
                    yt_link = f"https://youtu.be/{clean_vid}" if clean_vid and clean_vid != "N/A" else "N/A"
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
            except Exception as line_err:
                logging.warning(f"Skipping malformed upload row {line_num}: {line_err}")
                continue

        records.sort(key=lambda x: x["datetime"])
        return records
    except Exception as e:
        logging.error(f"Failed to parse YouTube upload records: {e}")
        return []


def categorize_video(title: str, video_type: str, raw_category: str) -> str:
    """Normalizes video into executive reporting categories safely."""
    try:
        t_lower = str(title or "").lower()
        vt_lower = str(video_type or "").lower()
        rc_str = str(raw_category or "")

        if "brain teaser" in t_lower or "brainteaser" in t_lower or "brain teaser" in vt_lower:
            return "Daily Brain Teaser"
        elif "monthly current affairs" in t_lower or "monthly" in vt_lower:
            return "Monthly Current Affairs"
        elif "weekly current affairs" in t_lower or "weekly" in vt_lower or "masterclass" in vt_lower:
            return "Weekly Current Affairs"
        elif "daily current affairs" in t_lower:
            return "Daily Current Affairs"
        else:
            if "(" in rc_str:
                return rc_str.split("(")[0].strip()
            return rc_str if rc_str else "Special Feature"
    except Exception:
        return "Special Feature"


def parse_community_poll_records(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    archive_dir: str = "pulse_archive"
) -> List[Dict[str, Any]]:
    """
    Parses community polls and brain teaser challenge assets in pulse_archive/ created within the window.
    Resilient per-file error handling guarantees bad files never block others.
    """
    polls = []
    try:
        poll_files = glob.glob(os.path.join(archive_dir, "**", "poll-*.txt"), recursive=True)
        poll_files += glob.glob(os.path.join(archive_dir, "**", "brainteaser-*.txt"), recursive=True)

        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }

        seen_dates = set()

        # Ensure start_dt and end_dt have IST timezone if passed as naive datetimes
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=IST)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=IST)

        for p_path in poll_files:
            try:
                fname = os.path.basename(p_path)
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
                    continue

                try:
                    with open(p_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(p_path, "r", encoding="latin-1", errors="replace") as f:
                        content = f.read()

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
                    "options_list": options,
                    "correct_answer": correct_ans,
                    "platforms": "YouTube Community, Telegram, Discord",
                    "file_name": fname
                })
                seen_dates.add(date_key)
            except Exception as file_err:
                logging.warning(f"Error parsing poll file {p_path}: {file_err}")
                continue

        polls.sort(key=lambda x: x["datetime"])
        return polls
    except Exception as e:
        logging.error(f"Error in parse_community_poll_records: {e}")
        return []


def build_category_breakdown(videos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes category-wise counts, video formats, and percentage shares safely.
    """
    try:
        if not isinstance(videos, list):
            videos = []

        total_videos = len(videos)
        breakdown = {}

        for v in videos:
            cat = v.get("category", "Uncategorized")
            vtype = v.get("video_type", "Standard")
            if cat not in breakdown:
                breakdown[cat] = {
                    "count": 0,
                    "types": set(),
                    "videos": []
                }
            breakdown[cat]["count"] += 1
            breakdown[cat]["types"].add(vtype)
            breakdown[cat]["videos"].append(v)

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
    except Exception as e:
        logging.error(f"Error building category breakdown: {e}")
        return {"total_count": len(videos) if isinstance(videos, list) else 0, "categories": []}


def escape_reportlab_text(text: str) -> str:
    """
    Escapes special XML characters so ReportLab Paragraph never crashes on math symbols like '<', '>', or '&'.
    """
    if not text:
        return ""
    try:
        # First escape XML special entities
        escaped = xml.sax.saxutils.escape(str(text))
        # Support basic intentional formatting tags if needed, otherwise clean
        return escaped
    except Exception:
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_community_polls_pdf(
    period_name: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    polls: List[Dict[str, Any]],
    output_pdf_path: str
) -> Optional[str]:
    """
    Generates a space-efficient, high-density executive PDF table of all Community Polls & Challenges,
    mirroring the exact tabular format and styling of the email to ensure no digital paper is wasted.
    """
    if not REPORTLAB_AVAILABLE:
        logging.warning("ReportLab is not installed. Skipping PDF generation.")
        return None

    try:
        out_dir = os.path.dirname(os.path.abspath(output_pdf_path))
        os.makedirs(out_dir, exist_ok=True)

        # Space-efficient margins: 24 pt left/right, 18 pt top/bottom
        # Total printable width on A4 (595.27 pt): 547.27 pt
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=18,
            bottomMargin=18
        )

        styles = getSampleStyleSheet()

        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#4338ca')
        )

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=1
        )

        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=3
        )

        # Header style matching email: #f1f5f9 background, #475569 bold uppercase text
        th_style = ParagraphStyle(
            'TH',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#475569'),
            alignment=1  # Center
        )
        th_left = ParagraphStyle('THL', parent=th_style, alignment=0)

        td_idx = ParagraphStyle(
            'TDIdx',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor('#64748b'),
            alignment=1  # Center
        )

        td_date = ParagraphStyle(
            'TDDate',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor('#0f172a'),
            alignment=0  # Left
        )

        td_q = ParagraphStyle(
            'TDQuestion',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor('#1e293b')
        )

        # Green pill badge matching email <span style="background-color: #d1fae5; color: #065f46; ...">
        td_ans = ParagraphStyle(
            'TDAns',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#065f46'),
            alignment=1  # Center
        )

        td_plat = ParagraphStyle(
            'TDPlat',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=6.8,
            leading=8.5,
            textColor=colors.HexColor('#475569'),
            alignment=1  # Center
        )

        story = []

        # High-density Header Banner mirroring the email interactive section
        story.append(Paragraph("<b>PULSE VECTOR</b> &bull; COMMUNITY ENGAGEMENT DOSSIER", badge_style))
        story.append(Paragraph(f"{period_name.title()} Community Polls &amp; Brain Teasers", title_style))
        story.append(Paragraph(
            f"Period: <b>{start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')}</b> &bull; "
            f"Total Challenges: <b>{len(polls)}</b> &bull; "
            f"Broadcast Channels: <b>YouTube Community, Telegram, Discord</b>",
            subtitle_style
        ))
        story.append(Spacer(1, 3))

        if not polls:
            story.append(Paragraph("No community poll challenges recorded for this period.", subtitle_style))
        else:
            # Table Header exactly matching the email columns and casing
            table_data = [
                [
                    Paragraph("<b>#</b>", th_style),
                    Paragraph("<b>DATE (IST)</b>", th_left),
                    Paragraph("<b>POLL CHALLENGE &amp; OPTIONS</b>", th_left),
                    Paragraph("<b>ANSWER</b>", th_style),
                    Paragraph("<b>BROADCAST CHANNELS</b>", th_style),
                ]
            ]

            for idx, p in enumerate(polls, 1):
                try:
                    q_raw = escape_reportlab_text(p.get('question', 'Brain Teaser Challenge'))
                    ans_raw = escape_reportlab_text(p.get('correct_answer', 'Discussion'))
                    date_raw = escape_reportlab_text(p.get('date_str', ''))

                    # Build compact options text
                    if p.get("options_list"):
                        opts_str = " | ".join(escape_reportlab_text(o) for o in p["options_list"])
                    else:
                        opts_str = escape_reportlab_text(p.get("options", ""))

                    challenge_cell = f"<b>{q_raw}</b><br/><font color='#64748b' size='6.5'><b>Options:</b> {opts_str}</font>"

                    table_data.append([
                        Paragraph(str(idx), td_idx),
                        Paragraph(date_raw, td_date),
                        Paragraph(challenge_cell, td_q),
                        Paragraph(f"<b>{ans_raw}</b>", td_ans),
                        Paragraph("YouTube Community, Telegram, Discord", td_plat),
                    ])
                except Exception as row_err:
                    logging.warning(f"Skipping malformed row #{idx} in PDF: {row_err}")
                    continue

            # Column widths sum exactly to 547 pt (fits A4 with 24 pt margins perfectly)
            col_widths = [20, 58, 285, 54, 130]
            poll_table = Table(table_data, colWidths=col_widths, repeatRows=1)

            t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
                ('TOPPADDING', (0, 0), (-1, -1), 1.8),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]

            # Alternating row coloring & emerald pill background for Answer cell
            for r in range(1, len(table_data)):
                bg = colors.HexColor('#f8fafc') if r % 2 == 0 else colors.white
                t_style.append(('BACKGROUND', (0, r), (-1, r), bg))
                t_style.append(('BACKGROUND', (3, r), (3, r), colors.HexColor('#d1fae5')))

            poll_table.setStyle(TableStyle(t_style))
            story.append(poll_table)

        # Page footer decoration callback
        def _add_page_footer(canvas_obj, document_obj):
            try:
                canvas_obj.saveState()
                canvas_obj.setFont('Helvetica', 6.5)
                canvas_obj.setFillColor(colors.HexColor('#94a3b8'))
                canvas_obj.drawString(24, 8, "Pulse Vector Automation • Community Engagement Dossier")
                canvas_obj.drawRightString(595 - 24, 8, f"Page {document_obj.page}")
                canvas_obj.restoreState()
            except Exception:
                pass

        doc.build(story, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)
        return os.path.abspath(output_pdf_path)
    except Exception as e:
        logging.error(f"Failed to generate Community Polls PDF: {e}")
        return None


def render_report_html(
    period_name: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    videos: List[Dict[str, Any]],
    polls: List[Dict[str, Any]],
    cat_summary: Dict[str, Any],
    pdf_attachment_name: Optional[str] = None
) -> str:
    """
    Renders an executive, responsive, modern dark-gradient HTML email report.
    All user strings are HTML-escaped to prevent formatting injection or rendering breakage.
    """
    try:
        period_title = period_name.title()
        date_range_display = f"{start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')}"
        generated_at_str = get_ist_now().strftime("%d %b %Y, %I:%M %p IST")

        total_uploads = cat_summary.get("total_count", len(videos))
        total_polls = len(polls)
        category_rows = cat_summary.get("categories", [])

        cat_counts = {c["category"]: c["count"] for c in category_rows}
        ca_count = cat_counts.get("Daily Current Affairs", 0)
        bt_count = cat_counts.get("Daily Brain Teaser", 0)
        weekly_count = cat_counts.get("Weekly Current Affairs", 0)
        monthly_count = cat_counts.get("Monthly Current Affairs", 0)

        # Build category breakdown rows HTML
        cat_table_rows_html = ""
        for c in category_rows:
            cat_safe = html.escape(str(c.get('category', '')))
            count_safe = html.escape(str(c.get('count', 0)))
            types_safe = html.escape(str(c.get('types_display', '')))
            share_safe = html.escape(str(c.get('share_percent', '0%')))

            cat_table_rows_html += f"""
            <tr>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #1e293b;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #6366f1; margin-right: 8px;"></span>
                    {cat_safe}
                </td>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: center; font-weight: 700; color: #0f172a; font-size: 15px;">
                    {count_safe}
                </td>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #475569; font-size: 13px;">
                    {types_safe}
                </td>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600; color: #4338ca;">
                    <span style="background-color: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{share_safe}</span>
                </td>
            </tr>
            """

        if not cat_table_rows_html:
            cat_table_rows_html = """<tr><td colspan="4" style="padding: 16px; text-align: center; color: #64748b;">No uploads recorded during this period.</td></tr>"""

        # Build video uploads table rows HTML
        video_table_rows_html = ""
        for idx, v in enumerate(videos, 1):
            clean_vid = html.escape(str(v.get("video_id", "N/A")))
            yt_url = html.escape(str(v.get("youtube_url", "#")))
            title_safe = html.escape(str(v.get("title", "Untitled Video")))
            date_safe = html.escape(str(v.get("raw_date", "")))
            cat_safe = html.escape(str(v.get("category", "General")))
            vtype_safe = html.escape(str(v.get("video_type", "Video")))

            link_badge = f"""<a href="{yt_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #ef4444, #dc2626); color: #ffffff; text-decoration: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px;">▶ {clean_vid}</a>""" if clean_vid != "N/A" else '<span style="color: #94a3b8; font-size: 12px;">N/A</span>'

            badge_color = "#3b82f6"
            if "Brain" in cat_safe:
                badge_color = "#8b5cf6"
            elif "Weekly" in cat_safe:
                badge_color = "#10b981"
            elif "Monthly" in cat_safe:
                badge_color = "#f59e0b"

            video_table_rows_html += f"""
            <tr style="background-color: {'#f8fafc' if idx % 2 == 0 else '#ffffff'};">
                <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: #64748b; font-size: 13px;">{idx}</td>
                <td style="padding: 12px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #0f172a; white-space: nowrap; font-family: monospace;">
                    <strong>{date_safe}</strong>
                </td>
                <td style="padding: 12px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; font-weight: 600; color: #1e293b; line-height: 1.4;">
                    {title_safe}
                </td>
                <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; text-align: center;">
                    <span style="background-color: {badge_color}18; color: {badge_color}; border: 1px solid {badge_color}40; padding: 3px 8px; border-radius: 8px; font-weight: 600; font-size: 11px; white-space: nowrap;">
                        {cat_safe}
                    </span>
                </td>
                <td style="padding: 12px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
                    {vtype_safe}
                </td>
                <td style="padding: 12px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">
                    {link_badge}
                </td>
            </tr>
            """

        if not video_table_rows_html:
            video_table_rows_html = """<tr><td colspan="6" style="padding: 20px; text-align: center; color: #64748b;">No video uploads found for the specified timeframe.</td></tr>"""

        # Attached PDF Callout Card
        pdf_display_name = html.escape(str(pdf_attachment_name or f"Pulse_Vector_{period_title}_Community_Polls.pdf"))

        html_out = f"""<!DOCTYPE html>
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
                                        <div style="font-size: 10px; color: #059669; font-weight: 600;">Attached PDF Dossier</div>
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

                    <!-- SECTION 3: COMMUNITY POSTS & POLLS (ATTACHED PDF DOSSIER) -->
                    <tr>
                        <td style="padding: 15px 30px 25px 30px;">
                            <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #86efac; border-radius: 12px; padding: 22px 24px;">
                                <table width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td>
                                            <div style="display: inline-block; background-color: #22c55e; color: #ffffff; border-radius: 12px; padding: 3px 10px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                                                📎 Attached PDF Dossier Included
                                            </div>
                                            <h3 style="font-size: 16px; margin: 0 0 6px 0; color: #14532d; font-weight: 800;">
                                                Community Polls & Challenges Document ({total_polls} Polls)
                                            </h3>
                                            <p style="font-size: 13px; color: #166534; margin: 0 0 10px 0; line-height: 1.5;">
                                                All Daily Brain Teaser community polls, multiple-choice options (A/B/C/D), verified solutions, and multi-platform broadcast records (YouTube Community, Telegram, Discord) are compiled into the attached PDF:
                                            </p>
                                            <div style="display: inline-block; background-color: #ffffff; border: 1px solid #bbf7d0; border-radius: 8px; padding: 6px 14px; font-size: 12px; font-weight: 700; color: #047857;">
                                                📄 {pdf_display_name}
                                            </div>
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
                                Automated Dispatch System &bull; Delivered to {html.escape(DEFAULT_RECIPIENT)} &bull; Generated {generated_at_str}
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
        return html_out
    except Exception as e:
        logging.error(f"Error rendering report HTML: {e}")
        return f"<html><body><h1>Pulse Vector Performance Report</h1><p>Error rendering full report template: {html.escape(str(e))}</p><p>Total videos: {len(videos)}</p></body></html>"


def render_report_text(
    period_name: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    videos: List[Dict[str, Any]],
    polls: List[Dict[str, Any]],
    cat_summary: Dict[str, Any],
    pdf_attachment_name: Optional[str] = None
) -> str:
    """Renders plain text fallback for email clients without HTML support."""
    try:
        lines = [
            f"==================================================================",
            f"       PULSE VECTOR — {period_name.upper()} PERFORMANCE REPORT",
            f"==================================================================",
            f"Period: {start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')}",
            f"Generated At: {get_ist_now().strftime('%d %b %Y, %I:%M %p IST')}",
            "",
            "--- 1. CATEGORY BREAKDOWN ---",
        ]
        for c in cat_summary.get("categories", []):
            lines.append(f"- {c['category']}: {c['count']} videos ({c['share_percent']}) | Formats: {c['types_display']}")

        lines.append("")
        lines.append(f"Total Videos Uploaded: {cat_summary.get('total_count', len(videos))}")
        lines.append(f"Total Community Polls: {len(polls)}")
        lines.append("")
        lines.append("--- 2. UPLOADED VIDEOS (LIVE TIMESTAMPS & LINKS) ---")
        for idx, v in enumerate(videos, 1):
            lines.append(f"{idx}. [{v.get('raw_date', '')}] {v.get('title', 'Video')}")
            lines.append(f"   Category: {v.get('category', 'General')} | Type: {v.get('video_type', 'Standard')} | Link: {v.get('youtube_url', 'N/A')}")

        if polls:
            lines.append("")
            pdf_name = pdf_attachment_name or f"Pulse_Vector_{period_name.title()}_Community_Polls.pdf"
            lines.append(f"--- 3. COMMUNITY POLLS & CHALLENGES (ATTACHED PDF: {pdf_name}) ---")
            lines.append(f"{len(polls)} community challenge polls compiled into the attached PDF dossier.")

        lines.append("")
        lines.append("==================================================================")
        lines.append(f"Pulse Vector Automation • Channel: @Pulse_vector")
        return "\n".join(lines)
    except Exception as e:
        logging.error(f"Error rendering report text: {e}")
        return f"Pulse Vector Report ({period_name}): {len(videos)} videos uploaded."


def send_report_email(
    subject: str,
    html_content: str,
    text_content: str,
    recipient: str = DEFAULT_RECIPIENT,
    sender: str = DEFAULT_SENDER,
    smtp_host: str = SMTP_HOST,
    smtp_port: int = SMTP_PORT,
    smtp_password: Optional[str] = None,
    pdf_attachment_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends the multi-part HTML/Plain-text report email with optional PDF attachment via SMTP (SSL/TLS).
    Resilient error handling protects against bad credentials, network timeouts, or corrupt attachments.
    """
    if smtp_password is None:
        smtp_password = SMTP_PASSWORD

    if not smtp_password:
        return False, (
            "SMTP password / Google App Password is not configured. "
            "Please configure SMTP_APP_PASSWORD in environment or GitHub Secrets to enable automatic inbox delivery."
        )

    try:
        # Outer multipart container for mixed content (body + attachment)
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"Pulse Vector Automation <{sender}>"
        msg["To"] = recipient
        msg["Reply-To"] = recipient
        msg["Message-ID"] = email.utils.make_msgid(domain="pulsevector.automation")
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["X-Auto-Response-Suppress"] = "All"
        msg["Auto-Submitted"] = "auto-generated"

        # Alternative container for text and HTML bodies
        msg_body = MIMEMultipart("alternative")
        part1 = MIMEText(text_content, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        msg_body.attach(part1)
        msg_body.attach(part2)
        msg.attach(msg_body)

        # Attach PDF if provided and exists (graceful degradation if missing)
        if pdf_attachment_path:
            if os.path.exists(pdf_attachment_path):
                try:
                    with open(pdf_attachment_path, "rb") as f:
                        pdf_data = f.read()
                    pdf_part = MIMEApplication(pdf_data, _subtype="pdf")
                    pdf_filename = os.path.basename(pdf_attachment_path)
                    pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                    msg.attach(pdf_part)
                except Exception as attach_err:
                    logging.warning(f"Could not attach PDF {pdf_attachment_path} ({attach_err}). Proceeding with email send.")
            else:
                logging.warning(f"PDF attachment path {pdf_attachment_path} does not exist. Sending report without attachment.")

        # SMTP Transmission with timeout
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(sender, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender, smtp_password)
                server.send_message(msg)

        # Gmail skips Primary Inbox for self-sent emails (From == To) by default.
        # When recipient is sender, also append directly to INBOX via IMAP so it appears right at the top of the inbox.
        if recipient and sender and recipient.strip().lower() == sender.strip().lower():
            try:
                import imaplib
                imap_host = smtp_host.replace("smtp", "imap")
                with imaplib.IMAP4_SSL(imap_host, 993, timeout=15) as imap_client:
                    imap_client.login(sender, smtp_password)
                    imap_client.append('INBOX', '', None, msg.as_bytes())
            except Exception as imap_err:
                logging.debug(f"IMAP inbox sync note (message was still sent via SMTP): {imap_err}")

        return True, f"Successfully delivered email report to {recipient}"
    except smtplib.SMTPAuthenticationError as auth_err:
        return False, f"SMTP Authentication failed: Invalid username or App Password ({auth_err})"
    except (smtplib.SMTPConnectError, TimeoutError, ConnectionRefusedError) as conn_err:
        return False, f"SMTP Connection failed to {smtp_host}:{smtp_port} ({conn_err})"
    except Exception as e:
        return False, f"Failed to send email via SMTP ({smtp_host}:{smtp_port}): {e}"
