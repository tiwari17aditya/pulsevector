"""
Pulse Vector MCP Server - Content Deduplication & Archive Search Tool
Scans past 90 days of Pulse Vector Current Affairs and Brain Teasers to prevent
topic repetition, recycling puzzle formulas, or duplicate news generation.
"""

import re
import pathlib
import datetime
from typing import Dict, Any, List, Optional

from core.config import ARCHIVE_DIR
from core.content_parser import extract_news_points, parse_teaser_content

def _tokenize(text: str) -> set:
    """Normalizes and extracts a set of lower-case alphanumeric word tokens."""
    tokens = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    # Exclude common stopwords
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "have", "were", "been",
        "india", "daily", "current", "affairs", "news", "point", "what", "which", "series"
    }
    return {t for t in tokens if t not in stopwords}

def _calculate_similarity(tokens_a: set, tokens_b: set) -> float:
    """Computes Jaccard similarity coefficient between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return intersection / union if union > 0 else 0.0

def query_content_deduplication(
    query: str,
    lookback_days: int = 90,
    content_type: str = "all"
) -> Dict[str, Any]:
    """
    Checks if a news headline, topic, or brain teaser formula has appeared in the archive.
    
    Args:
        query: Headline, question, or topic to check.
        lookback_days: Number of days in the past to inspect (default 90).
        content_type: 'news', 'teaser', or 'all'.
    """
    if not query or not query.strip():
        return {
            "query": query,
            "is_duplicate": False,
            "similarity_score": 0.0,
            "closest_match": None,
            "items_scanned": 0,
            "recommendation": "EMPTY_QUERY"
        }

    q_tokens = _tokenize(query)
    now = datetime.datetime.now()
    cutoff_date = now - datetime.timedelta(days=lookback_days)
    
    scanned_items = 0
    best_match_text = None
    best_match_date = None
    best_match_file = None
    max_similarity = 0.0

    # Scan archive directories
    if ARCHIVE_DIR.exists():
        for txt_file in ARCHIVE_DIR.rglob("*.txt"):
            try:
                # Basic date filtering based on file mtime or path
                mtime = datetime.datetime.fromtimestamp(txt_file.stat().st_mtime)
                if mtime < cutoff_date:
                    continue
                
                content = txt_file.read_text(encoding="utf-8", errors="ignore")
                file_name_lower = txt_file.name.lower()
                
                # News points
                if content_type in ("all", "news") and ("daily" in file_name_lower or "weekly" in file_name_lower or "monthly" in file_name_lower):
                    points = extract_news_points(content)
                    for _, pt_text, _ in points:
                        scanned_items += 1
                        pt_tokens = _tokenize(pt_text)
                        sim = _calculate_similarity(q_tokens, pt_tokens)
                        if sim > max_similarity:
                            max_similarity = sim
                            best_match_text = pt_text
                            best_match_date = mtime.strftime("%Y-%m-%d")
                            best_match_file = txt_file.name
                            
                # Brain teaser puzzles
                if content_type in ("all", "teaser") and "brainteaser" in file_name_lower:
                    teaser_data = parse_teaser_content(content)
                    t_text = f"{teaser_data.get('question_header', '')} {teaser_data.get('series', '')}"
                    if t_text.strip():
                        scanned_items += 1
                        t_tokens = _tokenize(t_text)
                        sim = _calculate_similarity(q_tokens, t_tokens)
                        if sim > max_similarity:
                            max_similarity = sim
                            best_match_text = t_text
                            best_match_date = mtime.strftime("%Y-%m-%d")
                            best_match_file = txt_file.name
            except Exception:
                continue

    # Threshold: >= 0.65 indicates probable duplicate/heavy overlap
    is_duplicate = max_similarity >= 0.65
    recommendation = "DUPLICATE_DETECTED_REPHRASE" if is_duplicate else "SAFE_TO_GENERATE"

    return {
        "query": query,
        "is_duplicate": is_duplicate,
        "similarity_score": round(max_similarity, 3),
        "closest_match": {
            "text": best_match_text[:200] if best_match_text else None,
            "date": best_match_date,
            "source_file": best_match_file
        } if best_match_text else None,
        "items_scanned": scanned_items,
        "lookback_days": lookback_days,
        "recommendation": recommendation
    }
