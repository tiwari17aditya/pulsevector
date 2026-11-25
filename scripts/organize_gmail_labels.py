#!/usr/bin/env python3
"""
Pulse Vector - Gmail Rules & Label Automation Engine
1. Connects to Gmail via IMAP (using SMTP_USER & SMTP_APP_PASSWORD).
2. Creates the hierarchical Gmail labels under "Pulse Vector".
3. Automatically applies appropriate labels to all existing emails.
4. Generates standard XML import file (pulse_vector_gmail_filters.xml) for permanent Gmail filter automation.
"""

import os
import sys
import pathlib
import imaplib
import email
from email.header import decode_header
import xml.etree.ElementTree as ET
import xml.sax.saxutils
from datetime import datetime, timezone
import dotenv

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
dotenv.load_dotenv(ROOT_DIR / ".env")

LABELS_TO_CREATE = [
    "Pulse Vector",
    "Pulse Vector/Weekly Reports",
    "Pulse Vector/Monthly Reports",
    "Pulse Vector/Alerts",
    "Pulse Vector/GitHub Actions"
]

def clean_header(val):
    if not val:
        return ""
    decoded_parts = decode_header(val)
    res = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            res.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            res.append(str(part))
    return "".join(res)

def ensure_labels(m: imaplib.IMAP4_SSL):
    print("Checking and creating Gmail labels under 'Pulse Vector'...", flush=True)
    status, folders_raw = m.list()
    existing_folders = set()
    for f in folders_raw:
        folder_str = f.decode('utf-8', errors='replace')
        parts = folder_str.split(' "/" ')
        if len(parts) == 2:
            existing_folders.add(parts[1].strip('"'))
        else:
            existing_folders.add(folder_str.strip('"'))

    created = []
    for label in LABELS_TO_CREATE:
        if label not in existing_folders:
            try:
                res, data = m.create(f'"{label}"')
                if res == 'OK':
                    print(f"  ✅ Created Gmail Label: '{label}'", flush=True)
                    created.append(label)
                else:
                    print(f"  ⚠️ Could not create '{label}': {data}", flush=True)
            except Exception as e:
                print(f"  ⚠️ Exception creating '{label}': {e}", flush=True)
        else:
            print(f"  ℹ️ Label already exists: '{label}'", flush=True)
    return created

def organize_existing_emails(m: imaplib.IMAP4_SSL):
    print("\nScanning All Mail to label existing emails...", flush=True)
    m.select('"[Gmail]/All Mail"', readonly=False)

    queries = [
        ('reports', 'SUBJECT "Pulse Vector"'),
        ('github', 'SUBJECT "pulsevector"'),
    ]

    all_ids = set()
    for qname, qval in queries:
        res, data = m.search(None, qval)
        if res == 'OK' and data[0]:
            for mid in data[0].split():
                all_ids.add(mid)

    print(f"Found {len(all_ids)} relevant emails to review and label.", flush=True)
    labeled_counts = {
        "weekly": 0,
        "monthly": 0,
        "other_pv": 0,
        "github": 0
    }

    for mid in sorted(list(all_ids), key=lambda x: int(x), reverse=True):
        res, msg_data = m.fetch(mid, '(X-GM-LABELS RFC822.HEADER)')
        if res != 'OK':
            continue

        raw_header = b""
        labels_str = ""
        for item in msg_data:
            if isinstance(item, tuple):
                if b'X-GM-LABELS' in item[0]:
                    labels_str = item[0].decode('utf-8', errors='replace')
                if len(item) > 1 and isinstance(item[1], bytes):
                    raw_header = item[1]

        msg = email.message_from_bytes(raw_header)
        subject = clean_header(msg.get("Subject", ""))
        sub_lower = subject.lower()

        labels_to_add = []
        cat = ""

        if "weekly executive report" in sub_lower or "weekly report" in sub_lower:
            labels_to_add = ['"Pulse Vector"', '"Pulse Vector/Weekly Reports"']
            cat = "weekly"
        elif "monthly executive report" in sub_lower or "monthly report" in sub_lower:
            labels_to_add = ['"Pulse Vector"', '"Pulse Vector/Monthly Reports"']
            cat = "monthly"
        elif "pulse vector" in sub_lower:
            labels_to_add = ['"Pulse Vector"']
            cat = "other_pv"
        elif "pulsevector" in sub_lower:
            labels_to_add = ['"Pulse Vector"', '"Pulse Vector/GitHub Actions"', '"Pulse Vector/Alerts"']
            cat = "github"

        if labels_to_add:
            label_arg = f"({' '.join(labels_to_add)})"
            try:
                store_res, store_data = m.store(mid, '+X-GM-LABELS', label_arg)
                # Remove from inbox for hygiene (Archive it)
                m.store(mid, '-X-GM-LABELS', '(\\Inbox)')
                # Mark as not important
                m.store(mid, '-X-GM-LABELS', '(\\Important)')
                if store_res == 'OK':
                    labeled_counts[cat] += 1
                    print(f"  🏷️ Labeled, Archived & Unmarked Important [{cat.upper()}]: {subject[:55]}... -> {', '.join(labels_to_add)}", flush=True)
            except Exception as e:
                print(f"  ❌ Error labeling msg {mid}: {e}", flush=True)

    print("\nSummary of Applied Labels:")
    for k, v in labeled_counts.items():
        print(f"  • {k}: {v} email(s) labeled")

def generate_gmail_filters_xml(output_path: pathlib.Path):
    """
    Generates standard Gmail Filter XML file ready for 1-click import into Gmail.
    """
    print(f"\nGenerating Gmail Filters XML: {output_path.name}...", flush=True)

    rules = [
        {
            "id": "pv_weekly_report",
            "name": "Pulse Vector Weekly Executive Reports",
            "criteria": {
                "subject": "[Pulse Vector] Weekly Executive Report"
            },
            "actions": {
                "label": "Pulse Vector/Weekly Reports",
                "shouldArchive": "true",
                "shouldNeverMarkAsImportant": "true",
                "shouldNeverSpam": "true"
            }
        },
        {
            "id": "pv_monthly_report",
            "name": "Pulse Vector Monthly Executive Reports",
            "criteria": {
                "subject": "[Pulse Vector] Monthly Executive Report"
            },
            "actions": {
                "label": "Pulse Vector/Monthly Reports",
                "shouldArchive": "true",
                "shouldNeverMarkAsImportant": "true",
                "shouldNeverSpam": "true"
            }
        },
        {
            "id": "pv_general_reports",
            "name": "All Pulse Vector General Reports and Logs",
            "criteria": {
                "subject": "[Pulse Vector]"
            },
            "actions": {
                "label": "Pulse Vector",
                "shouldArchive": "true",
                "shouldNeverMarkAsImportant": "true",
                "shouldNeverSpam": "true"
            }
        },
        {
            "id": "pv_github_actions",
            "name": "Pulse Vector GitHub Actions Notifications",
            "criteria": {
                "from": "notifications@github.com",
                "hasTheWord": "pulsevector"
            },
            "actions": {
                "label": "Pulse Vector/GitHub Actions",
                "shouldArchive": "true",
                "shouldNeverMarkAsImportant": "true",
                "shouldNeverSpam": "true"
            }
        },
        {
            "id": "pv_security_alerts",
            "name": "Pulse Vector Security and Pipeline Alerts",
            "criteria": {
                "subject": "[tiwari17aditya/pulsevector]"
            },
            "actions": {
                "label": "Pulse Vector/Alerts",
                "shouldArchive": "true",
                "shouldNeverMarkAsImportant": "true",
                "shouldNeverSpam": "true"
            }
        }
    ]

    xml_lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<feed xmlns='http://www.w3.org/2005/Atom' xmlns:apps='http://schemas.google.com/apps/2006'>",
        "  <title>Pulse Vector Mail Filters</title>",
        "  <id>tag:mail.google.com,2008:filters:</id>",
        f"  <updated>{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>",
    ]

    for rule in rules:
        title_escaped = xml.sax.saxutils.escape(rule["name"])
        xml_lines.append("  <entry>")
        xml_lines.append("    <category term='filter'></category>")
        xml_lines.append(f"    <title>{title_escaped}</title>")
        xml_lines.append(f"    <id>tag:mail.google.com,2008:filter:{rule['id']}</id>")
        xml_lines.append(f"    <updated>{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>")
        xml_lines.append("    <content></content>")

        for k, v in rule["criteria"].items():
            val_escaped = xml.sax.saxutils.escape(str(v), entities={'"': '&quot;', "'": '&apos;'})
            xml_lines.append(f"    <apps:property name='{k}' value='{val_escaped}'/>")
        for k, v in rule["actions"].items():
            val_escaped = xml.sax.saxutils.escape(str(v), entities={'"': '&quot;', "'": '&apos;'})
            xml_lines.append(f"    <apps:property name='{k}' value='{val_escaped}'/>")

        xml_lines.append("  </entry>")

    xml_lines.append("</feed>\n")

    output_path.write_text("\n".join(xml_lines), encoding="utf-8")
    print(f"✅ Created Gmail Filter XML at: {output_path.resolve()}", flush=True)

def main():
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_APP_PASSWORD")
    if not user or not pwd:
        print("ERROR: SMTP_USER or SMTP_APP_PASSWORD not configured.", flush=True)
        sys.exit(1)

    print(f"Connecting to imap.gmail.com as {user}...", flush=True)
    m = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=20)
    m.login(user, pwd)
    print("IMAP Authentication successful!\n", flush=True)

    # Step 1: Ensure hierarchical labels exist
    ensure_labels(m)

    # Step 2: Organize all existing emails
    organize_existing_emails(m)

    m.logout()

    # Step 3: Generate XML Filter file in root directory pulse-vector
    xml_path = ROOT_DIR / "pulse_vector_gmail_filters.xml"
    generate_gmail_filters_xml(xml_path)

    print("\n🎉 ALL GMAIL RULES & LABELS APPLIED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
