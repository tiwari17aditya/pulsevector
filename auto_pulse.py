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

def main():
    date_info = get_current_date_info()
    print(f"Running Pulse Vector Automation for: {date_info['date_str']}")
    
    ca_prompt_template, bt_prompt_template = read_prompts()
    
    if not ca_prompt_template:
        print("Error: Could not read prompts from .agent/pulse_prompts.md")
        return

    # --- 1. Current Affairs ---
    print("Generating Current Affairs...")
    search_query = f"current affairs news headlines {date_info['date_str']}"
    news_context = get_news_search_results(search_query)
    
    # Inject date into prompt interpretation
    ca_prompt_specific = f"Today is {date_info['date_str']}. {ca_prompt_template}"
    
    ca_content = generate_content(ca_prompt_specific, news_context)
    
    # Save CA
    # Structure: pulse_archive/[Year]/[FullMonthName]/Daily/daily-[d][mon]-[yyyy]_formatted.txt
    # Example: daily-2feb-2026_formatted.txt
    
    # Construct filename parts
    d_str = str(date_info['date_obj'].day) # '2' not '02'
    mon_short = date_info['date_obj'].strftime("%b").lower() # 'feb'
    yyyy = date_info['year']
    
    ca_filename = f"daily-{d_str}{mon_short}-{yyyy}_formatted.txt"
    ca_path = ARCHIVE_DIR / date_info['year'] / date_info['month_name'] / "Daily" / ca_filename
    
    save_file(ca_content, ca_path)

    # --- 2. Brain Teasers ---
    print("Generating Brain Teaser...")
    time.sleep(10) # 10s cooldown to respect API rate limits
    bt_prompt_specific = f"Today is {date_info['date_str']}. {bt_prompt_template}"
    bt_content = generate_content(bt_prompt_specific)
    
    # Save BT
    # Structure: Brain_Teasers/brainteaser-[d][mon][yy].txt
    yy = date_info['date_obj'].strftime("%y") # '26'
    bt_filename = f"brainteaser-{d_str}{mon_short}{yy}.txt"
    bt_path = ARCHIVE_DIR / date_info['year'] / date_info['month_name'] / "Brain_Teasers" / bt_filename
    
    save_file(bt_content, bt_path)
    
    print("Automation Complete!")

if __name__ == "__main__":
    main()
