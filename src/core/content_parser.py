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
        
        # Check if hashtags were appended directly inside Reel Description with dots / spaces
        ht_in_desc = re.findall(r"#\w+", desc_raw)
        if ht_in_desc and not result["hashtags"]:
            result["hashtags"] = [t.lstrip("#") for t in ht_in_desc]
            
        # Clean off trailing . . . . . and hashtags from desc_raw
        desc_cleaned = re.sub(r"(\s*\.\s*){2,}.*", "", desc_raw, flags=re.DOTALL)
        desc_cleaned = re.sub(r"(?:\s*#\w+)+$", "", desc_cleaned).strip()
        
        desc = desc_cleaned if desc_cleaned else desc_raw.strip()
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
        parsed_tags = [t.lstrip("#") for t in raw_tags]
        if parsed_tags:
            result["hashtags"] = parsed_tags
        
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

def optimize_youtube_title(
    raw_title: str,
    content_type: str,
    target_date: datetime.datetime,
    points: List[Tuple[int, str]]
) -> str:
    """
    Transforms generic calendar titles into high-CTR curiosity-driven YouTube titles.
    Strictly enforces YouTube's 100-character title budget.
    """
    date_compact = target_date.strftime("%d %b %Y")
    is_generic = (
        not raw_title
        or raw_title.lower().startswith("daily current affairs")
        or raw_title.lower().startswith("weekly current affairs")
        or raw_title.lower().startswith("monthly current affairs")
    )
    
    if content_type == "daily":
        if is_generic and points:
            # Extract lead story preview
            lead_text = points[0][1] if isinstance(points[0], (list, tuple)) else str(points[0])
            lead_clean = re.sub(r'[\.\:\;\-\"\'\`]', '', lead_text).strip()
            # Trim lead clean to ~42 chars at word boundary
            if len(lead_clean) > 42:
                lead_clean = lead_clean[:42].rsplit(' ', 1)[0]
            candidate = f"🔥 {lead_clean} & Top News ({date_compact}) #Shorts"
            if len(candidate) <= 100:
                return candidate
        elif not is_generic and raw_title:
            if "#Shorts" not in raw_title and len(raw_title) <= 92:
                return f"{raw_title} #Shorts"
            return raw_title[:100]
        return f"⚡ Daily Current Affairs ({date_compact}) #Shorts"
        
    elif content_type == "weekly":
        start_d = target_date - datetime.timedelta(days=6)
        return f"Weekly Current Affairs Masterclass ({start_d.strftime('%d %b')} - {target_date.strftime('%d %b %Y')}) | Full Revision"
        
    elif content_type == "monthly":
        return f"Monthly Current Affairs Masterclass - {target_date.strftime('%B %Y')} | Complete Revision"
        
    return raw_title[:100] if raw_title else f"Pulse Vector | {content_type.title()} ({date_compact})"

def format_structured_description(
    content_type: str,
    target_date: datetime.datetime,
    points: List[Tuple[int, str]],
    raw_desc: str = "",
    hashtags: Optional[List[str]] = None,
    source_urls: Optional[Dict[str, str]] = None
) -> str:
    """
    Builds a beautifully structured, multi-section YouTube description:
      1. Clean header with date & exam/general awareness summary.
      2. Key headlines / highlights cleanly formatted with bullet points & line breaks.
      3. Community discussion / question of the day prompt.
      4. Standard social media connectivity block (YouTube, Telegram, Discord).
      5. Curated hashtag row placed neatly at the bottom.
    """
    sections = []
    date_str = target_date.strftime("%d %B %Y")
    
    # 1. Header / Intro Block
    if content_type == "daily":
        sections.append(
            f"📌 Daily Current Affairs — {date_str}\n"
            "Stay ahead with today's essential national and international developments curated for competitive exams (UPSC, SSC, Banking, Railways) and rapid daily awareness."
        )
    elif content_type == "weekly":
        start_d = target_date - datetime.timedelta(days=6)
        sections.append(
            f"📚 Weekly Current Affairs Masterclass — {start_d.strftime('%d %B %Y')} to {date_str}\n"
            "Comprehensive 16:9 widescreen revision covering the defining developments of the week for UPSC, SSC CGL, Banking, and State PSC aspirants."
        )
    elif content_type == "monthly":
        month_name = target_date.strftime("%B %Y")
        sections.append(
            f"🏆 Monthly Current Affairs Masterclass — {month_name}\n"
            "Complete deep-dive monthly revision covering all critical milestones across National, International, Economy, Science & Tech, and Governance."
        )
    else:
        sections.append(f"📌 Pulse Vector Current Affairs — {date_str}")
        
    # 2. Key Stories / Highlights (Clean Bulleted Points)
    if points:
        if content_type == "monthly":
            heading = "⚡ COMPLETE MONTHLY BREAKDOWN:"
        elif content_type == "weekly":
            heading = "⚡ MAJOR TOPICS COVERED:"
        else:
            heading = "⚡ KEY HEADLINES TODAY:"
        stories_lines = [heading]
        for idx, pt in points:
            clean_pt = re.sub(r"\[Source:[^\]]+\]", "", str(pt)).strip()
            clean_pt = clean_pt.rstrip(".- ")
            stories_lines.append(f"• {idx:02d}. {clean_pt}")
        sections.append("\n".join(stories_lines))
    elif raw_desc:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_desc) if s.strip()]
        if len(sentences) > 1:
            sections.append("⚡ TODAY'S HIGHLIGHTS:\n" + "\n".join([f"• {s}" for s in sentences]))
        else:
            sections.append(raw_desc)
            
    # 3. Discussion / Call to Action
    if content_type == "daily":
        sections.append(
            "💬 QUESTION OF THE DAY:\n"
            "Which of today's stories do you believe will have the greatest impact? Share your thoughts and perspective below — top analytical comments get pinned! 📌"
        )
    else:
        sections.append(
            "💬 DISCUSSION:\n"
            "Which key topic covered in this masterclass do you want an in-depth breakdown for next? Drop your request in the comments below! 👇"
        )
        
    # 4. Social Media Connectivity Block
    social_block = get_social_links_block("plain")
    sections.append(social_block)
    
    # 5. Curated Hashtags (Clean list of 8-10 primary tags at the bottom)
    if hashtags:
        top_tags = [f"#{t.lstrip('#')}" for t in hashtags[:10]]
        sections.append(" ".join(top_tags))
    else:
        default_tags = ["#DailyCurrentAffairs", "#CurrentAffairs", "#UPSC", "#SSC", "#Banking", "#PulseVector", "#GeneralKnowledge"]
        if content_type == "daily":
            default_tags.append("#Shorts")
        sections.append(" ".join(default_tags))
        
    full_desc = "\n\n".join(sections).strip()
    if len(full_desc) > 4950:
        full_desc = full_desc[:4947] + "..."
    return full_desc

def parse_news_content(raw_text: str, content_type: str, target_date: datetime.datetime, file_path: Optional[pathlib.Path] = None) -> ContentPayload:
    """Parses raw LLM text into a structured ContentPayload."""
    points_data = extract_news_points(raw_text)
    points_tuples = [(p[0], p[1]) for p in points_data]
    
    meta = extract_metadata_fields(raw_text)
    
    # Curiosity & Packaging Title Optimization for YouTube
    raw_title = meta["title"]
    title = optimize_youtube_title(raw_title, content_type, target_date, points_tuples)
            
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
        
    # Formatted multi-section description with clean line breaks & bulleted headlines
    desc = format_structured_description(
        content_type=content_type,
        target_date=target_date,
        points=points_tuples,
        raw_desc=meta["description"],
        hashtags=tags,
        source_urls=meta["source_urls"]
    )
        
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

def get_social_links_block(
    format_type: str = "plain",
    youtube_url: Optional[str] = None,
    telegram_url: Optional[str] = None,
    discord_url: Optional[str] = None,
    instagram_url: Optional[str] = None,
    x_url: Optional[str] = None,
    include_divider: bool = True
) -> str:
    """
    Constructs a standardized, unified social media links block.
    Supports formats:
      - 'plain' / 'text' / 'youtube': Plain text URLs (for YouTube descriptions)
      - 'html' / 'telegram': HTML <a> tags (for Telegram captions)
      - 'markdown' / 'discord': Markdown [Label](url) links (for Discord embeds)
    
    Includes:
      - YouTube channel
      - Telegram community channel
      - Discord community server
    
    Explicitly excludes bot handles (@PulseVectorOfficial_bot) and interactive web play links.
    """
    from .config import (
        PULSE_YOUTUBE_URL, PULSE_TELEGRAM_URL, PULSE_DISCORD_URL,
        PULSE_INSTAGRAM_URL, PULSE_X_URL
    )
    
    yt = youtube_url or PULSE_YOUTUBE_URL or "https://www.youtube.com/@Pulse_vector"
    tg = telegram_url or PULSE_TELEGRAM_URL or "https://t.me/pulsevector_daily"
    dc = discord_url if discord_url is not None else (PULSE_DISCORD_URL or "https://discord.gg/pulsevector")
    insta = instagram_url or PULSE_INSTAGRAM_URL
    x = x_url or PULSE_X_URL
    
    fmt = (format_type or "plain").lower()
    
    if fmt in ("html", "telegram"):
        lines = []
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🌐 <b>CONNECT WITH PULSE VECTOR:</b>")
        lines.append(f"📺 <a href=\"{yt}\">Subscribe on YouTube</a>")
        lines.append(f"💬 <a href=\"{tg}\">Telegram Community</a>")
        if dc:
            lines.append(f"👾 <a href=\"{dc}\">Discord Community</a>")
        if insta:
            lines.append(f"📸 <a href=\"{insta}\">Instagram</a>")
        if x:
            lines.append(f"🐦 <a href=\"{x}\">X (Twitter)</a>")
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
        
    elif fmt in ("markdown", "md", "discord"):
        lines = []
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🌐 **CONNECT WITH PULSE VECTOR:**")
        lines.append(f"📺 **[Subscribe on YouTube]({yt})**")
        lines.append(f"💬 **[Telegram Community]({tg})**")
        if dc:
            lines.append(f"👾 **[Discord Community]({dc})**")
        if insta:
            lines.append(f"📸 **[Instagram]({insta})**")
        if x:
            lines.append(f"🐦 **[X (Twitter)]({x})**")
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
        
    else:  # 'plain', 'text', 'youtube'
        lines = []
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🌐 CONNECT WITH PULSE VECTOR:")
        lines.append(f"📺 Subscribe on YouTube: {yt}")
        lines.append(f"💬 Telegram Community: {tg}")
        if dc:
            lines.append(f"👾 Discord Community: {dc}")
        if insta:
            lines.append(f"📸 Instagram: {insta}")
        if x:
            lines.append(f"🐦 X (Twitter): {x}")
        if include_divider:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)


def format_brainteaser_description(
    data: Dict[str, Any],
    date_str: str,
    formatted_hashtags: List[str],
    date_file_str: str = "",
    play_url: Optional[str] = None,
    telegram_url: Optional[str] = None,
    youtube_url: Optional[str] = None,
    discord_url: Optional[str] = None,
    instagram_url: Optional[str] = None,
    x_url: Optional[str] = None
) -> str:
    """
    Constructs the official, rich YouTube description for a Daily Brain Teaser Short.
    Includes question details, series, options, answer call-to-action,
    and verified social media & community handles.
    """
    from .config import PULSE_PLAY_BASE_URL
    
    if play_url is None:
        if date_file_str:
            play_url = f"{PULSE_PLAY_BASE_URL.rstrip('/')}/?challenge={date_file_str}"
        else:
            play_url = PULSE_PLAY_BASE_URL
            
    desc_lines = [
        f"Daily Brain Teaser - {date_str} 🧠",
        "",
        data.get("question_header", ""),
        data.get("series", ""),
        ""
    ]
    for opt in data.get("options", []):
        desc_lines.append(opt)
        
    social_block = get_social_links_block(
        format_type="plain",
        youtube_url=youtube_url,
        telegram_url=telegram_url,
        discord_url=discord_url,
        instagram_url=instagram_url,
        x_url=x_url,
        include_divider=True
    )
        
    desc_lines.extend([
        "",
        "Comment your answer below! 👇",
        "Correct answer pinned in 24 hours.",
        "",
        f"🎮 Play Interactively: {play_url}",
        "",
        social_block,
        "",
        " ".join(formatted_hashtags)
    ])
    
    description = "\n".join(desc_lines)
    if len(description) > 4950:
        description = description[:4947] + "..."
    return description

