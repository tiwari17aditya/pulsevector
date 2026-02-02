import os
import datetime
import pathlib
import google.generativeai as genai
from dotenv import load_dotenv
from googlesearch import search
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
ARCHIVE_DIR = pathlib.Path("pulse_archive")
PROMPTS_FILE = pathlib.Path(".agent/pulse_prompts.md")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit(1)

genai.configure(api_key=API_KEY)
import time
model = genai.GenerativeModel('gemini-flash-latest')

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
        # Perform a simplistic search - in a real production script you might use a NewsAPI
        search_results = search(query, num_results=10, advanced=True)
        for result in search_results:
            results.append(f"Title: {result.title}\nDescription: {result.description}")
    except Exception as e:
        print(f"Search error: {e}")
    return "\n---\n".join(results)

def read_prompts():
    if not PROMPTS_FILE.exists():
        return None, None
    content = PROMPTS_FILE.read_text(encoding='utf-8')
    # simple parsing based on headers
    ca_prompt = ""
    bt_prompt = ""
    
    parts = content.split("## Brain Teaser Prompt")
    if len(parts) > 0:
        ca_part = parts[0].split("## Current Affairs Prompt")
        if len(ca_part) > 1:
            ca_prompt = ca_part[1].strip()
    
    if len(parts) > 1:
        bt_prompt = parts[1].strip()
        
    return ca_prompt, bt_prompt

def generate_content(prompt, context_data=""):
    full_prompt = f"{prompt}\n\nContext Data:\n{context_data}"
    response = model.generate_content(full_prompt)
    return response.text

def save_file(content, filepath):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding='utf-8')
    print(f"Saved: {filepath}")

def parse_date_from_filename(filename):
    # Format: daily-2feb-2026_formatted.txt
    try:
        # minimal parsing logic
        parts = filename.replace("daily-", "").replace("_formatted.txt", "")
        # parts is like 2feb-2026
        day_part = "".join(filter(str.isdigit, parts.split('-')[0]))
        mon_part = "".join(filter(str.isalpha, parts.split('-')[0]))
        year_part = parts.split('-')[1]
        
        date_str = f"{day_part} {mon_part} {year_part}"
        return datetime.datetime.strptime(date_str, "%d %b %Y")
    except Exception:
        return None

def get_last_processed_date(archive_dir):
    # Scan recursively for the latest daily file
    latest_date = None
    
    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file.startswith("daily-") and file.endswith("_formatted.txt"):
                d = parse_date_from_filename(file)
                if d:
                    if latest_date is None or d > latest_date:
                        latest_date = d
    
    return latest_date

def process_date(target_date, ca_prompt_template, bt_prompt_template):
    date_str = target_date.strftime("%d %B %Y")
    print(f"\nProcessing content for: {date_str}")
    
    # 1. Prepare Date Info
    date_info = {
        "date_obj": target_date,
        "date_str": date_str,
        "year": target_date.strftime("%Y"),
        "month_name": target_date.strftime("%B"),
        "d_str": str(target_date.day),
        "mon_short": target_date.strftime("%b").lower()
    }

    # 2. Current Affairs
    print("  > Generating Current Affairs...")
    search_query = f"current affairs news headlines {date_str}"
    news_context = get_news_search_results(search_query)
    
    ca_prompt_specific = f"Today is {date_str}. {ca_prompt_template}"
    ca_content = generate_content(ca_prompt_specific, news_context)
    
    processed_month_dir = ARCHIVE_DIR / date_info['year'] / date_info['month_name']
    
    ca_filename = f"daily-{date_info['d_str']}{date_info['mon_short']}-{date_info['year']}_formatted.txt"
    ca_path = processed_month_dir / "Daily" / ca_filename
    save_file(ca_content, ca_path)
    
    # 3. Brain Teaser
    print("  > Generating Brain Teaser...")
    time.sleep(10) # 10s cooldown
    bt_prompt_specific = f"Today is {date_str}. {bt_prompt_template}"
    bt_content = generate_content(bt_prompt_specific)
    
    bt_filename = f"brainteaser-{date_info['d_str']}{date_info['mon_short']}{target_date.strftime('%y')}.txt"
    bt_path = processed_month_dir / "Brain_Teasers" / bt_filename
    save_file(bt_content, bt_path)

def main():
    print("Checking for missing content...")
    ca_prompt, bt_prompt = read_prompts()
    
    if not ca_prompt:
        print("Error: Prompts not found.")
        return

    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_date = get_last_processed_date(ARCHIVE_DIR)
    
    if last_date is None:
        # First run ever? Just do today.
        start_date = today
    else:
        # Start from the day AFTER the last file
        start_date = last_date + datetime.timedelta(days=1)
    
    if start_date > today:
        print("All up to date! No new content needed.")
        return

    # Loop from start_date to today
    current_processing_date = start_date
    while current_processing_date <= today:
        process_date(current_processing_date, ca_prompt, bt_prompt)
        current_processing_date += datetime.timedelta(days=1)
    
    print("\nAll missing days processed successfully!")

if __name__ == "__main__":
    main()
