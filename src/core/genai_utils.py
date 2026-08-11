import os
import time
import random
import logging
import datetime
import pathlib
from google import genai
from google.genai import types
from googlesearch import search
from .config import API_KEY, PROMPTS_FILE

client = None

def configure_genai():
    global client
    if not API_KEY:
        print("Error: GEMINI_API_KEY not found in environment.")
        logging.error("GEMINI_API_KEY not found in environment.")
        exit(1)
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
        "month_name": now.strftime("%B"), # Full month name
        "month_num": now.strftime("%m"),
        "day_num": now.strftime("%d") # Day number e.g., 02
    }

def get_news_search_results(query):
    print(f"Searching for: {query}")
    results = []
    try:
        search_results = search(query, num_results=10, advanced=True)
        for result in search_results:
            results.append(f"Title: {result.title}\nURL: {result.url}\nDescription: {result.description}")
    except Exception as e:
        print(f"Search error: {e}")
    return "\n---\n".join(results)

def read_prompts():
    ca_prompt = read_prompt_section("Current Affairs Prompt")
    bt_prompt = read_prompt_section("Brain Teaser Prompt")
    return ca_prompt, bt_prompt


def read_prompt_section(section_heading):
    import re
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
        logging.error(f"Prompts file completely missing!")
        return ""
        
    content = found_path.read_text(encoding='utf-8')
    
    pattern = re.compile(rf"^##\s+{re.escape(section_heading)}\s*$(.*?)(?=^#{{1,2}}\s|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""

def generate_content(client_obj, model_name, prompt, context_data=""):
    use_grounding = not context_data or not context_data.strip()
    full_prompt = f"{prompt}\n\nContext Data:\n{context_data}" if not use_grounding else prompt
    
    models_to_try = [model_name]
    fallbacks = ['gemini-2.0-flash', 'gemini-1.5-flash']
    for fb in fallbacks:
        if fb not in models_to_try:
            models_to_try.append(fb)
            
    last_err = None
    for current_model in models_to_try:
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logging.info(f"Generating content using model: {current_model} (Attempt {attempt + 1}/{max_retries})")
                if use_grounding:
                    print(f"  > Attempting content generation with {current_model} + Google Search grounding...")
                    response = client_obj.models.generate_content(
                        model=current_model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )
                else:
                    print(f"  > Attempting content generation with {current_model}...")
                    response = client_obj.models.generate_content(
                        model=current_model,
                        contents=full_prompt
                    )
                return response.text
            except Exception as e:
                last_err = e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                if attempt < max_retries - 1:
                    logging.warning(f"Model {current_model} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    logging.warning(f"Model {current_model} failed all {max_retries} attempts: {e}")
                    
    raise last_err

def save_file(content, filepath):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')
    print(f"Saved: {filepath}")

def parse_date_from_filename(filename):
    try:
        parts = filename.replace("daily-", "").replace("_formatted.txt", "")
        day_part = "".join(filter(str.isdigit, parts.split('-')[0]))
        mon_part = "".join(filter(str.isalpha, parts.split('-')[0]))
        year_part = parts.split('-')[1]
        
        date_str = f"{day_part} {mon_part} {year_part}"
        return datetime.datetime.strptime(date_str, "%d %b %Y")
    except Exception:
        return None

def get_last_processed_date(archive_dir):
    latest_date = None
    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file.startswith("daily-") and file.endswith("_formatted.txt"):
                d = parse_date_from_filename(file)
                if d:
                    if latest_date is None or d > latest_date:
                        latest_date = d
    return latest_date
