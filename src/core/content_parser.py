"""
Pulse Vector - Robust Content & Markdown Parser
Handles extraction of news points, dates, YouTube metadata, and brain teasers
with high fault tolerance against LLM formatting variations.
"""

import re
import pathlib
import datetime
from typing import List, Dict, Tuple, Optional, Any
from .stage_interfaces import ContentPayload
from .config import BT_DATE_FMT

def clean_markdown_decorations(text: str) -> str:
    """Removes excessive markdown styling (bolding, headers, horizontal rules)."""
    if not text:
        return ""
    # Remove leading hashes
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*\*|\*|__|_", "", text)
    # Remove backticks
    text = re.sub(r"`", "", text)
    return text.strip()

def strip_metadata_section(content: str) -> str:
    """Returns the text content with YouTube metadata stripped out for clean point parsing."""
    markers = [
        r"(?i)^#*\s*YouTube\s+Metadata",
        r"(?i)^#*\s*Title\s*:",
        r"(?i)^#*\s*(?:Reel\s+)?Description\s*:",
        r"(?i)^#*\s*Hashtags\s*:",
        r"(?i)^#*\s*Source\s+URLs\s*:"
    ]
    for pattern in markers:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return content[:match.start()].strip()
    return content.strip()

def extract_news_points(content: str) -> List[Tuple[int, str, Optional[str]]]:
    """
    Extracts numbered news points.
    Returns list of tuples: (point_number, clean_text, source_name)
    """
    clean_body = strip_metadata_section(content)
    # Match numbered items e.g., 1. text or 1) text
    point_pattern = re.compile(r"^\s*(\d+)[\.\)]\s+(.*?)(?=\n\s*\d+[\.\)]|\Z)", re.MULTILINE | re.DOTALL)
    matches = point_pattern.findall(clean_body)
    
    points = []
    for num_str, raw_text in matches:
        num = int(num_str)
        flat_text = re.sub(r"\s+", " ", raw_text).strip()
        # Clean markdown decorations from point text
        flat_text = re.sub(r"\*\*|\*|__|_", "", flat_text).strip()
        
        # Extract Source if present
        source_match = re.search(r"\[Source:\s*([^\]]+)\]", flat_text, re.IGNORECASE)
        source_name = None
        if source_match:
            source_name = source_match.group(1).strip()
            # Keep flat_text with or without source tag based on usage
        
        points.append((num, flat_text, source_name))
        
    return points

def extract_metadata_fields(content: str) -> Dict[str, Any]:
    """
    Extracts Title, Reel Description, Hashtags, and Source URLs.
    """
    result = {
        "title": "",
        "description": "",
        "hashtags": [],
        "source_urls": {}
    }
    
    # 1. Title
    title_match = re.search(r"(?i)\*?\*?Title\*?\*?:\s*['\"`]?(.*?)['\"`]?\s*$", content, re.MULTILINE)
    if title_match:
        result["title"] = title_match.group(1).strip().strip("'\"`")
        
    # 2. Description
    desc_match = re.search(r"(?i)\*?\*?(?:Reel\s+)?Description\*?\*?:\s*(.+)", content, re.DOTALL)
    if desc_match:
        desc_raw = desc_match.group(1)
        stop_match = re.search(r"(?i)\n+\s*\*?\*?(?:Hashtags|Source\s+URLs)\*?\*?", desc_raw)
        if stop_match:
            desc_raw = desc_raw[:stop_match.start()]
        desc = desc_raw.strip()
        if len(desc) > 4950:
            desc = desc[:4947] + "..."
        result["description"] = desc
        
    # 3. Hashtags
    ht_match = re.search(r"(?i)\*?\*?Hashtags\*?\*?:\s*(.+?)(?=\n+\s*\*?\*?Source\s+URLs|\Z)", content, re.DOTALL)
    if ht_match:
        ht_text = ht_match.group(1)
        tags = re.findall(r"#\w+", ht_text)
        result["hashtags"] = tags
        
    # 4. Source URLs
    src_match = re.search(r"(?i)\*?\*?Source\s+URLs\*?\*?:\s*(.+)", content, re.DOTALL)
    if src_match:
        src_text = src_match.group(1)
        lines = src_text.splitlines()
        for line in lines:
            line_clean = line.strip().lstrip("*-• ")
            if ":" in line_clean:
                parts = line_clean.split(":", 1)
                pub = parts[0].strip()
                url = parts[1].strip()
                if url.startswith("http") or url.startswith("www"):
                    result["source_urls"][pub] = url
                    
    return result

def extract_date_str(content: str, content_type: str, fallback_date: Optional[datetime.datetime] = None) -> str:
    """Extracts clean uppercase header date string without unwanted punctuation."""
    if content_type == "daily":
        date_match = re.search(r"(?i)Daily Current Affairs\s*[:-]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", content)
        if date_match:
            return date_match.group(1).upper().strip()
        if fallback_date:
            return fallback_date.strftime("%d %B %Y").upper()
        return ""
        
    elif content_type == "weekly":
        date_match = re.search(r"(?i)Weekly Current Affairs\s*[:-]?\s*(.+?)(?=\n|\Z)", content)
        if date_match:
            raw_d = date_match.group(1).strip()
            # Clean parentheses, colons, dashes
            raw_d = re.sub(r"^[\(\:\-\s]+|[\)\:\-\s]+$", "", raw_d)
            return raw_d.upper().strip()
        if fallback_date:
            start_d = fallback_date - datetime.timedelta(days=6)
            return f"{start_d.strftime('%d %B %Y')} - {fallback_date.strftime('%d %B %Y')}".upper()
        return ""
        
    elif content_type == "monthly":
        date_match = re.search(r"(?i)Monthly Current Affairs\s*[:-]?\s*(.+?)(?=\n|\Z)", content)
        if date_match:
            raw_d = date_match.group(1).strip()
            # Remove leading hyphens or colons
            raw_d = re.sub(r"^[\(\:\-\s]+|[\)\:\-\s]+$", "", raw_d)
            return raw_d.upper().strip()
        if fallback_date:
            return fallback_date.strftime("%B %Y").upper()
        return ""
        
    return ""

def parse_news_content(raw_text: str, content_type: str, target_date: datetime.datetime, file_path: Optional[pathlib.Path] = None) -> ContentPayload:
    """Parses raw LLM text into a structured ContentPayload."""
    points_data = extract_news_points(raw_text)
    points_tuples = [(p[0], p[1]) for p in points_data]
    
    meta = extract_metadata_fields(raw_text)
    
    # Fallback title if missing
    title = meta["title"]
    if not title:
        if content_type == "daily":
            title = f"Daily Current Affairs {target_date.strftime('%d %B %Y')}"
        elif content_type == "weekly":
            start_d = target_date - datetime.timedelta(days=6)
            title = f"Weekly Current Affairs ( {start_d.strftime('%d %B %Y')} - {target_date.strftime('%d %B %Y')} )"
        elif content_type == "monthly":
            title = f"Monthly Current Affairs - {target_date.strftime('%B %Y')}"
            
    # Fallback description if missing
    desc = meta["description"]
    if not desc and points_tuples:
        top_points = " ".join([p[1] for p in points_tuples[:5]])
        desc = f"Catch the top headlines: {top_points[:450]}... #CurrentAffairs #PulseVector"
        
    # Fallback tags if missing
    tags = meta["hashtags"]
    if not tags:
        default_tags = ["CurrentAffairs", "GlobalNews", "PulseVector", "Education"]
        if content_type == "daily":
            default_tags.append("Shorts")
        tags = [f"#{t}" for t in default_tags]
        
    date_header = extract_date_str(raw_text, content_type, target_date)
    
    return ContentPayload(
        content_type=content_type,
        target_date=target_date,
        raw_text=raw_text,
        points=points_tuples,
        title=title,
        description=desc,
        hashtags=tags,
        source_urls=meta["source_urls"],
        text_file_path=file_path,
        extra_metadata={"date_header": date_header}
    )

def parse_teaser_content(raw_text: str, target_date: Optional[datetime.datetime] = None, file_path: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Robust parser for Brain Teasers."""
    clean_content = raw_text
    for marker in ['---', 'image generation', 'image_generation', 'Image Generation']:
        idx = clean_content.lower().find(marker.lower())
        if idx != -1:
            clean_content = clean_content[:idx]
            
    lines = [line.strip() for line in clean_content.splitlines() if line.strip()]
    if not lines:
        return {}
        
    # Date
    date_text = ""
    first_line = lines[0]
    match_date = re.search(r"(?:Daily Brain Teaser|Brain Teaser)\s*-\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", first_line, re.IGNORECASE)
    if match_date:
        date_text = match_date.group(1).strip()
    elif target_date:
        date_text = target_date.strftime("%d %B %Y")
    else:
        date_text = datetime.datetime.now().strftime("%d %B %Y")
        
    # Options
    option_matches = re.findall(r'\b([a-d])[\.\)]\s*([^\n]+?)(?=\s+\b[a-d][\.\)]|\n|$)', clean_content, re.IGNORECASE)
    options = [f"{opt_letter.lower()}. {opt_val.strip()}" for opt_letter, opt_val in option_matches]
    
    # Question and Series
    q_s_content = clean_content
    q_s_content = re.sub(r'^(?:Daily Brain Teaser|Brain Teaser)\s*-\s*\d{1,2}\s+[A-Za-z]+\s+\d{4}\s*🧠\s*', '', q_s_content, flags=re.IGNORECASE)
    opt_start = re.search(r'\b[a-d][\.\)]\s*', q_s_content, re.IGNORECASE)
    if opt_start:
        q_s_content = q_s_content[:opt_start.start()]
    q_s_content = re.sub(r'#\w+', '', q_s_content)
    
    q_s_lines = [l.strip() for l in q_s_content.splitlines() if l.strip()]
    question_header = "Q. What's next in the series:-"
    series_text = ""
    full_text = "\n".join(q_s_lines)
    
    series_match = re.search(r'Series:\s*(.+)', full_text, re.IGNORECASE)
    q_match = re.search(r'Q\.\s*(.+?)(?=\nSeries:|\Z)', full_text, re.IGNORECASE | re.DOTALL)
    
    if series_match:
        series_text = series_match.group(1).strip()
        if q_match:
            question_header = f"Q. {q_match.group(1).strip()}"
        else:
            before_series = full_text.split("Series:")[0].strip()
            if before_series:
                before_series = re.sub(r'^Q\.\s*', '', before_series, flags=re.IGNORECASE).strip()
                question_header = f"Q. {before_series}"
    else:
        if q_s_lines:
            first_val = q_s_lines[0]
            first_val_clean = re.sub(r'^Q\.\s*', '', first_val, flags=re.IGNORECASE).strip()
            if len(q_s_lines) > 1:
                question_header = f"Q. {first_val_clean}"
                series_text = q_s_lines[1]
            else:
                if ":" in first_val_clean:
                    parts = first_val_clean.split(":", 1)
                    q_part = parts[0].strip()
                    s_part = parts[1].strip()
                    if "what number comes next" in q_part.lower() or "what's next" in q_part.lower():
                        question_header = "Q. What's next in the series"
                    else:
                        question_header = f"Q. {q_part}"
                    series_text = s_part
                else:
                    series_text = first_val_clean
                    
    series_text = re.sub(r'\b[a-d][\.\)].*', '', series_text, flags=re.IGNORECASE).strip()
    question_header = question_header.strip()
    if not question_header.endswith(":-"):
        if question_header.endswith("?"):
            question_header = question_header + " :-"
        else:
            question_header = question_header + " :-"
            
    if question_header.startswith("Q. "):
        rest = question_header[3:]
        if rest:
            question_header = "Q. " + rest[0].upper() + rest[1:]
            
    hashtags = re.findall(r'#\w+', raw_text)
    answer_match = re.search(r'(?:Correct Answer|Answer):\s*([a-d])', clean_content, re.IGNORECASE)
    correct_answer = answer_match.group(1).lower() if answer_match else None
    
    return {
        "question_header": question_header,
        "series": series_text,
        "options": options,
        "date": date_text,
        "hashtags": hashtags,
        "correct_answer": correct_answer,
        "file_path": file_path
    }
