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

CATEGORY_PALETTES = {
    "ECONOMY": {"pill_bg": (234, 179, 8, 45), "pill_border": (234, 179, 8, 180), "text_color": (253, 224, 71)},     # Gold/Amber
    "DEFENCE": {"pill_bg": (239, 68, 68, 45), "pill_border": (239, 68, 68, 180), "text_color": (252, 165, 165)},     # Crimson/Coral
    "TECH & AI": {"pill_bg": (6, 182, 212, 45), "pill_border": (6, 182, 212, 180), "text_color": (103, 232, 249)},   # Cyan
    "GEOPOLITICS": {"pill_bg": (139, 92, 246, 45), "pill_border": (139, 92, 246, 180), "text_color": (196, 181, 253)}, # Purple/Violet
    "ENVIRONMENT": {"pill_bg": (34, 197, 94, 45), "pill_border": (34, 197, 94, 180), "text_color": (134, 239, 172)}, # Emerald Green
    "NATIONAL": {"pill_bg": (59, 130, 246, 45), "pill_border": (59, 130, 246, 180), "text_color": (147, 197, 253)},   # Blue
    "GLOBAL": {"pill_bg": (148, 163, 184, 45), "pill_border": (148, 163, 184, 180), "text_color": (226, 232, 240)}   # Slate
}

def classify_news_category(headline_text: str) -> str:
    """Classifies a news headline into a primary domain category using high-precision keyword patterns."""
    text_lower = headline_text.lower()
    
    # Defence & Security
    if re.search(r"\b(military|defence|defense|missile|army|navy|air force|drdo|pentagon|war|weapon|nato|combat|troops|frigate|carrier|iaf|ins )\b", text_lower):
        return "DEFENCE"
        
    # Economy & Finance
    if re.search(r"\b(gdp|inflation|rbi|fed|economy|market|sensex|nifty|stock|trade|tariff|billion|trillion|export|import|fiscal|rupee|dollar|imf|world bank|interest rate)\b", text_lower):
        return "ECONOMY"
        
    # Tech & AI & Science
    if re.search(r"\b(ai|artificial intelligence|tech|technology|space|isro|nasa|satellite|quantum|semiconductor|chip|google|microsoft|apple|openai|cyber|robot|deepseek)\b", text_lower):
        return "TECH & AI"
        
    # Environment & Energy & Climate
    if re.search(r"\b(climate|emission|solar|renewable|carbon|cop\d+|green|energy|monsoon|wildlife|forest|cyclone|pollution|ev|battery|biodiversity)\b", text_lower):
        return "ENVIRONMENT"
        
    # Geopolitics & Foreign Relations
    if re.search(r"\b(un|unsc|summit|treaty|bilateral|diplomatic|envoy|g20|brics|sanction|iran|china|russia|ukraine|us-india|taiwan|israel|gaza|middle east)\b", text_lower):
        return "GEOPOLITICS"
        
    # National / Governance / Policy
    if re.search(r"\b(parliament|supreme court|cabinet|bill|election|pm |president|ministry|scheme|constitution|delhi|lok sabha|rajya sabha|policy|judiciary)\b", text_lower):
        return "NATIONAL"
        
    return "GLOBAL"

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
    # NOTE: We extract the raw #Word tokens from LLM output, then immediately
    # strip the '#' prefix. The YouTube Data API snippet.tags field requires plain
    # keyword strings — passing '#Word' causes HTTP 400 invalidTags errors.
    ht_match = re.search(r"(?i)\*?\*?Hashtags\*?\*?:\s*(.+?)(?=\n+\s*\*?\*?Source\s+URLs|\Z)", content, re.DOTALL)
    if ht_match:
        ht_text = ht_match.group(1)
        raw_tags = re.findall(r"#\w+", ht_text)
        # Strip '#' — keep plain keywords for YouTube API tags array
        result["hashtags"] = [t.lstrip("#") for t in raw_tags]
        
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
        
    # Fallback tags if missing — plain keywords, no '#' prefix (YouTube API requirement)
    tags = meta["hashtags"]
    if not tags:
        default_tags = ["CurrentAffairs", "GlobalNews", "PulseVector", "Education"]
        if content_type == "daily":
            default_tags.append("Shorts")
        elif content_type == "weekly":
            default_tags.append("WeeklyCurrentAffairs")
        elif content_type == "monthly":
            default_tags.append("MonthlyCurrentAffairs")
        tags = default_tags  # Already plain strings, no '#'
        
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
    question_header = "Q. Solve the puzzle:-"
    series_text = ""
    full_text = "\n".join(q_s_lines)
    
    tag_pattern = r'^[ \t]*(?:Series|Puzzle|Equation|Grid|Expression|Sequence|Problem):\s*'
    series_match = re.search(rf'{tag_pattern}(.+)', full_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    q_match = re.search(r'^[ \t]*Q\.\s*(.+?)(?=\n[ \t]*(?:Series|Puzzle|Equation|Grid|Expression|Sequence|Problem):|\Z)', full_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    if series_match:
        series_text = series_match.group(1).strip()
        if q_match:
            question_header = f"Q. {q_match.group(1).strip()}"
        else:
            parts = re.split(tag_pattern, full_text, flags=re.IGNORECASE | re.MULTILINE)
            before_series = parts[0].strip() if parts else ""
            if before_series:
                before_series = re.sub(r'^Q\.\s*', '', before_series, flags=re.IGNORECASE).strip()
                question_header = f"Q. {before_series}"
    else:
        if q_s_lines:
            first_val = q_s_lines[0]
            first_val_clean = re.sub(r'^Q\.\s*', '', first_val, flags=re.IGNORECASE).strip()
            if len(q_s_lines) > 1:
                question_header = f"Q. {first_val_clean}"
                series_text = "\n".join(q_s_lines[1:])
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
                    
    series_text = re.sub(r'\b[a-d][\.\)].*', '', series_text, flags=re.IGNORECASE | re.DOTALL).strip()
    question_header = question_header.strip()
    if not question_header.endswith(":-"):
        if question_header.endswith("?"):
            question_header = question_header + " :-"
        elif question_header.endswith(":"):
            question_header = question_header + "-"
        else:
            question_header = question_header + ":-"
            
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

def format_community_poll_text(data: Dict[str, Any]) -> str:
    """
    Formats a ready-to-post YouTube Community Poll text snippet.
    Includes Question, Puzzle/Equation, cleanly enumerated Poll options, and tags.
    """
    date_str = data.get("date", "")
    q_header = data.get("question_header", "Daily Brain Teaser")
    series = data.get("series", "").strip()
    options = data.get("options", [])
    hashtags = " ".join(data.get("hashtags", ["#BrainTeaser", "#Quiz", "#PulseVector", "#Puzzle"]))
    
    poll_lines = [
        f"🧠 Daily Brain Teaser ({date_str})",
        f"{q_header}",
    ]
    if series:
        poll_lines.append(f"\n{series}\n")
        
    poll_lines.append("Vote for your answer below! 👇")
    poll_lines.append("")
    for opt in options:
        poll_lines.append(f"• {opt}")
        
    poll_lines.append("\n" + hashtags)
    return "\n".join(poll_lines)

def format_teaser_challenge_comment(data: Dict[str, Any]) -> str:
    """Formats the initial challenge comment posted when a Brain Teaser Short is published."""
    date_str = data.get("date", "")
    return (
        f"🧠 Daily Brain Teaser Challenge ({date_str})!\n\n"
        "Can you solve it before time runs out? Drop your answer and reasoning in the comments below! 👇\n\n"
        "⏳ The verified step-by-step solution will be pinned right here in 24 hours. Turn on notifications so you don't miss it! 🔔"
    )

def format_solution_reveal_comment(yesterday_data: Dict[str, Any]) -> str:
    """Formats the official solution reveal comment for yesterday's Brain Teaser."""
    date_str = yesterday_data.get("date", "Yesterday")
    ans_letter = yesterday_data.get("correct_answer", "")
    options = yesterday_data.get("options", [])
    
    ans_display = ""
    if ans_letter:
        for opt in options:
            if opt.lower().startswith(f"{ans_letter.lower()}."):
                ans_display = opt
                break
        if not ans_display:
            ans_display = f"Option ({ans_letter.upper()})"
    else:
        ans_display = "Revealed in community discussion"
        
    return (
        f"💡 OFFICIAL SOLUTION REVEAL ({date_str}):\n\n"
        f"✅ Correct Answer: {ans_display}\n\n"
        f"Did you crack it? Try today's fresh brain teaser on the channel! 🧠🔥"
    )
