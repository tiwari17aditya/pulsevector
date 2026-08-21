import os
import re
import time
import random
import logging
import datetime
import pathlib
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Tuple
from google import genai
from google.genai import types

from .config import API_KEY, PROMPTS_FILE

client = None

def configure_genai():
    global client
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in environment.")
        logging.error("GEMINI_API_KEY not found in environment.")
        raise ValueError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=API_KEY)
    return client

def get_current_date_info():
    now = datetime.datetime.now()
    return {
        "date_obj": now,
        "date_str": now.strftime("%d %B %Y"),
        "day": now.strftime("%A"),
        "is_sunday": now.weekday() == 6,
        "is_month_end": (now + datetime.timedelta(days=1)).month != now.month,
        "year": now.strftime("%Y"),
        "month_name": now.strftime("%B"),
        "month_num": now.strftime("%m"),
        "day_num": now.strftime("%d")
    }

def fetch_rss_news(query: str, max_items: int = 15) -> str:
    """Fetches high-quality headlines and source publishers from Google News RSS feed."""
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        results = []
        for item in items[:max_items]:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            source_el = item.find('source')
            source = source_el.text if source_el is not None else "News"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            if title:
                results.append(f"Title: {title}\nSource: {source}\nURL: {link}\nDate: {pub_date}")
                
        if results:
            logging.info(f"Retrieved {len(results)} news items via RSS for query '{query}'")
            return "\n---\n".join(results)
    except Exception as e:
        logging.warning(f"RSS news fetch fallback error: {e}")
    return ""

def get_news_search_results(query: str) -> str:
    """Multi-source search fetcher: tries Google News RSS first, falls back to googlesearch-python."""
    print(f"🔍 Searching for news: '{query}'")
    rss_results = fetch_rss_news(query, max_items=25)
    if rss_results:
        return rss_results
        
    results = []
    try:
        from googlesearch import search
        search_results = search(query, num_results=10, advanced=True)
        for result in search_results:
            results.append(f"Title: {result.title}\nURL: {result.url}\nDescription: {result.description}")
    except Exception as e:
        logging.warning(f"Google search error: {e}")
        
    return "\n---\n".join(results)

def read_prompts():
    ca_prompt = read_prompt_section("Current Affairs Prompt")
    bt_prompt = read_prompt_section("Brain Teaser Prompt")
    return ca_prompt, bt_prompt

def read_prompt_section(section_heading: str) -> str:
    targets_to_try = [
        PROMPTS_FILE,
        pathlib.Path(".agent/pulse_prompts.md"),
        pathlib.Path(".agent/workflows/pulse_prompts.md"),
        pathlib.Path("samples/pulse_prompts.md"),
        pathlib.Path("pulse_prompts.md")
    ]
    
    found_path = None
    for p in targets_to_try:
        if p and p.exists():
            found_path = p
            break
            
    if not found_path:
        logging.error("Prompts file completely missing!")
        return ""
        
    content = found_path.read_text(encoding='utf-8')
    pattern = re.compile(rf"^##\s+{re.escape(section_heading)}\s*$(.*?)(?=^#{{1,2}}\s|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""

def generate_content(client_obj, model_name: str, prompt: str, context_data: str = "") -> str:
    """
    Robust Gemini content generation with multi-model fallback and resilient error handling.
    If Google Search grounding fails with APIError, it automatically falls back to ungrounded generation.
    """
    use_grounding = not context_data or not context_data.strip()
    full_prompt = f"{prompt}\n\nContext Data / Verified News:\n{context_data}" if context_data.strip() else prompt
    
    models_to_try = [model_name]
    fallbacks = ['gemini-2.5-flash', 'gemini-2.5-pro']
    for fb in fallbacks:
        if fb not in models_to_try:
            models_to_try.append(fb)
            
    last_err = None
    for current_model in models_to_try:
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            # Attempt 1: Try with grounding if no context was passed
            if use_grounding:
                try:
                    logging.info(f"Generating content: {current_model} with Google Search grounding (Attempt {attempt+1}/{max_retries})")
                    print(f"  > Attempting content generation with {current_model} + Google Search grounding...")
                    response = client_obj.models.generate_content(
                        model=current_model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())],
                            temperature=0.7
                        )
                    )
                    if response and hasattr(response, 'text') and response.text and response.text.strip():
                        return response.text.strip()
                    elif response and hasattr(response, 'candidates') and response.candidates:
                        cand = response.candidates[0]
                        if cand.content and cand.content.parts:
                            text_parts = [p.text for p in cand.content.parts if hasattr(p, 'text') and p.text]
                            if text_parts and "".join(text_parts).strip():
                                return "".join(text_parts).strip()
                except Exception as g_err:
                    logging.warning(f"Google Search grounding failed on {current_model}: {g_err}. Falling back to standard generation.")
                    print(f"  ⚠️ Grounding failed ({g_err}). Falling back to standard {current_model} generation...")
            
            # Attempt 2 (or Direct): Standard generation without grounding tools
            try:
                logging.info(f"Generating content: {current_model} standard (Attempt {attempt+1}/{max_retries})")
                print(f"  > Attempting content generation with {current_model}...")
                response = client_obj.models.generate_content(
                    model=current_model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7
                    )
                )
                if response and hasattr(response, 'text') and response.text and response.text.strip():
                    return response.text.strip()
                elif response and hasattr(response, 'candidates') and response.candidates:
                    cand = response.candidates[0]
                    if cand.content and cand.content.parts:
                        text_parts = [p.text for p in cand.content.parts if hasattr(p, 'text') and p.text]
                        if text_parts and "".join(text_parts).strip():
                            return "".join(text_parts).strip()
                raise ValueError(f"Empty text payload returned from {current_model}")
            except Exception as e:
                last_err = e
                delay = base_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                if attempt < max_retries - 1:
                    logging.warning(f"Model {current_model} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    logging.warning(f"Model {current_model} failed all {max_retries} attempts: {e}")
                    
    raise RuntimeError(f"All GenAI generation attempts failed across fallback models. Last error: {last_err}")

def save_file(content: str, filepath: pathlib.Path):
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"Cannot save empty or non-string content to {filepath} (got {type(content)}: {repr(content)})")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip(), encoding='utf-8')
    print(f"💾 Saved: {filepath}")

def parse_date_from_filename(filename: str) -> Optional[datetime.datetime]:
    try:
        parts = filename.replace("daily-", "").replace("_formatted.txt", "")
        day_part = "".join(filter(str.isdigit, parts.split('-')[0]))
        mon_part = "".join(filter(str.isalpha, parts.split('-')[0]))
        year_part = parts.split('-')[1]
        
        date_str = f"{day_part} {mon_part} {year_part}"
        return datetime.datetime.strptime(date_str, "%d %b %Y")
    except Exception:
        return None

def get_last_processed_date(archive_dir: pathlib.Path) -> Optional[datetime.datetime]:
    latest_date = None
    if not archive_dir.exists():
        return None
    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file.startswith("daily-") and file.endswith("_formatted.txt"):
                d = parse_date_from_filename(file)
                if d:
                    if latest_date is None or d > latest_date:
                        latest_date = d
    return latest_date
