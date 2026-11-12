import os
import re
import time
import json
import random
import logging
import datetime
import pathlib
import urllib.request
import urllib.parse
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

BRAIN_TEASER_TYPES = {
    "bodmas": {
        "name": "BODMAS & Arithmetic Traps",
        "description": "Order of operations precedence traps (division before multiplication, parentheses, zero multiplication rules, or missing operators).",
        "examples": "e.g., 6 ÷ 2(1 + 2) = ? or 50 - 50 × 0 + 2 + 2 = ?"
    },
    "cipher": {
        "name": "Alphanumeric Ciphers & Letter-Math",
        "description": "Letter indexing and word values (A=1, B=2...), letter pair progressions, or alphabet skip cyphers.",
        "examples": "e.g., If CAT = 24, DOG = 26, then BIRD = ? or AZ -> BY -> CX -> ?"
    },
    "grid": {
        "name": "3x3 Logic Grids & Missing Value Matrices",
        "description": "A 3x3 numeric grid or magic square where each row/column follows a mathematical rule, with exactly one missing cell marked with '?'. Format the grid compactly on 3 separate lines.",
        "examples": "e.g.,\n[ 4  9  2 ]\n[ 3  5  7 ]\n[ 8  1  ? ]"
    },
    "trap": {
        "name": "Cognitive Reflex Traps & Illusions",
        "description": "High-virality quick reflex logic puzzles where intuitive first impressions mislead people (Kahneman Bat & Ball CRT, clock hand angle at 3:15, or speed reflex math).",
        "examples": "e.g., Bat & Ball cost $1.10 total, bat costs $1.00 more than ball, what does ball cost? or Clock hands angle at 3:15."
    },
    "sequence": {
        "name": "Advanced Sequences & Progressions",
        "description": "Challenging number or letter series (alternating dual-step operations, Fibonacci transformations, or prime intervals).",
        "examples": "e.g., 2, 6, 12, 20, 30, ? or 3, 5, 9, 17, 33, ?"
    },
    "oddone": {
        "name": "Odd One Out & Pattern Breakers",
        "description": "A set of 4 or 5 numbers, words, or codes where exactly one item violates a subtle hidden mathematical or logical property.",
        "examples": "e.g., 121, 169, 225, 289, 361 (225 is not a prime square) or LEVEL, RADAR, KAYAK, RACE, ROTOR."
    },
    "paradox": {
        "name": "Logic Paradoxes & Probability Quick-Hits",
        "description": "A crisp probability puzzle or lateral deduction scenario with an unequivocal mathematical truth.",
        "examples": "e.g., Conditional probability (two-children problem), coin dilemmas, or deductive logic."
    },
    "detective": {
        "name": "Detective Deduction & The Alibi Trap",
        "description": "A concise 3-line micro-mystery where 3 or 4 suspects make short statements with timestamps or alibis, and exactly one statement reveals the culprit or liar through an unmistakable logical contradiction.",
        "examples": "e.g., Alex says he was in a meeting until 2:45, Blake says he arrived at 2:50 and saw Charlie leave, Charlie says he was with witnesses until 3:15. Who is lying?"
    },
    "relations": {
        "name": "Blood Relations & Family Tree Riddles",
        "description": "Clever indirect relationship riddles or coded pedigree connections (e.g., 'Pointing to X, Y said...' or generational pedigree logic) with an unequivocal kinship answer.",
        "examples": "e.g., 'Brothers and sisters I have none, but that man\\'s father is my father\\'s son.' Who is in the picture? (Answer: His son)"
    },
    "weighing": {
        "name": "Balance Scales, Weights & Water Transfer",
        "description": "Classic lateral thinking deduction scenarios: finding counterfeit coins with minimal balance scale weighings, measuring exact liquid with irregular jugs, or river crossing logistics.",
        "examples": "e.g., 9 coins, 1 is lighter counterfeit. Minimum weighings on a balance scale? (Answer: 2 weighings, split into 3-3-3)"
    },
    "spatial": {
        "name": "Mirror, Water & Spatial Reflection Traps",
        "description": "Mental geometry and spatial reasoning traps involving clock reflections (mirror/water axes), digital clock digit flips, or paper-folding symmetries.",
        "examples": "e.g., A digital 24-hr clock displays 08:15. What exact digits appear in its vertical mirror reflection? Or clock hands reflection at 3:40."
    },
    "matchstick": {
        "name": "Matchstick Equation & Geometry Fixes",
        "description": "An incorrect arithmetic equation or geometric shape (squares/triangles) where moving, removing, or adding exactly 1 or 2 matchsticks makes the mathematical statement completely valid.",
        "examples": "e.g., '6 + 4 = 4' -> Move 1 matchstick to make it correct (e.g., 0 + 4 = 4 or 8 - 4 = 4 or 5 + 4 ≠ 4)"
    },
    "age_speed": {
        "name": "Age Gap & Speed-Time Conundrums",
        "description": "Deceptive word math problems involving non-linear intuition traps: relative speeds of trains/cars, compounding age gaps that stay constant, or work-rate illusions.",
        "examples": "e.g., 'When I was 6, my sister was half my age. Today I am 70. How old is my sister?' (Answer: 67, since the difference is always 3 years, not 35)"
    }
}

WEEKDAY_THEME_MAP = {
    0: "bodmas",     # Monday: Math Madness
    1: "cipher",     # Tuesday: Cipher Tuesday
    2: "grid",       # Wednesday: Grid Matrix
    3: "trap",       # Thursday: Mind Trap
    4: "sequence",   # Friday: Sequence Friday
    5: "oddone",     # Saturday: Lateral Saturday
    6: "paradox"     # Sunday: Mastermind Sunday
}

def build_brainteaser_prompt(
    target_date: datetime.date,
    base_prompt: str,
    teaser_type: Optional[str] = None,
    randomize: bool = True
) -> Tuple[str, str]:
    """
    Builds a category-specific prompt for Daily Brain Teaser generation.
    Returns: (final_prompt_text, selected_category_key)
    """
    date_str = target_date.strftime("%d %B %Y")
    weekday_idx = target_date.weekday()
    weekday_name = target_date.strftime("%A")
    
    selected_key = None
    if teaser_type and str(teaser_type).lower() in BRAIN_TEASER_TYPES:
        selected_key = str(teaser_type).lower()
    elif randomize:
        # Default to dynamic random selection across all 13 categories for maximum engagement
        selected_key = random.choice(list(BRAIN_TEASER_TYPES.keys()))
    else:
        selected_key = WEEKDAY_THEME_MAP.get(weekday_idx, "sequence")
        
    type_info = BRAIN_TEASER_TYPES.get(selected_key, BRAIN_TEASER_TYPES["sequence"])


    
    # Archetype-specific layout instructions
    layout_instruction = "Put the main puzzle clearly under the 'Series:' label."
    if selected_key in ["grid", "spatial"]:
        layout_instruction = "Format the 3x3 grid on 3 separate lines under 'Grid:' or 'Series:' using '|' separators (e.g., 4 | 9 | 2), with '?' marking the missing cell."
    elif selected_key == "detective":
        layout_instruction = "Provide 3 concise suspect statements under 'Suspects:' or 'Series:' in the format: Name (Role): 'Statement'."
    elif selected_key in ["bodmas", "matchstick", "age_speed"]:
        layout_instruction = "Put the exact equation/challenge clearly under 'Formula:' or 'Series:', e.g., 50 - 50 × 0 + 2 + 2 = ?"
    elif selected_key in ["sequence", "cipher"]:
        layout_instruction = "Put the progression or cipher equations clearly under 'Sequence:' or 'Series:'."
    elif selected_key == "weighing":
        layout_instruction = "List the scale balance equations clearly under 'Scales:' or 'Series:'."

    prompt = (
        f"Today is {weekday_name}, {date_str} (IST).\n\n"
        f"TARGET PUZZLE CATEGORY FOR TODAY: **{type_info['name']}**\n"
        f"Category Focus: {type_info['description']}\n"
        f"Inspirational Pattern Example: {type_info['examples']}\n\n"
        f"Generation Rules:\n"
        f"1. Generate an original, clever, moderate-difficulty puzzle strictly within the '{type_info['name']}' category.\n"
        f"2. Ensure there is a single, unequivocal, mathematically or logically verifiable correct answer.\n"
        f"3. Provide exactly 4 distinct multiple-choice options labeled a., b., c., d. (ensure options are plausible and one is the exact answer).\n"
        f"4. The puzzle must be solvable within 10 seconds on a short video or social post.\n"
        f"5. {layout_instruction}\n"
        f"6. DO NOT use raw emojis in the puzzle question, series, or options to ensure clean video rendering.\n"
        f"7. DO NOT use square brackets around option letters. Format options strictly as:\n"
        f"   a. Option Text\n"
        f"   b. Option Text\n"
        f"   c. Option Text\n"
        f"   d. Option Text\n"
        f"8. BREVITY & VISUAL FIT RULE: Keep the 'Series:' / puzzle statement strictly under 120 characters (maximum 2-3 short sentences) so that all 4 options fit comfortably on mobile screens without visual crowding.\n\n"
        f"{base_prompt}"
    )
    return prompt, selected_key

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

def _call_openai_compatible_api(endpoint: str, api_key: str, model_name: str, prompt: str) -> Optional[str]:
    """Universal caller for OpenAI-compatible REST APIs (Groq, OpenRouter, Together AI, HuggingFace)."""
    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are an expert news researcher and educational content writer for Pulse Vector."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "PulseVector/3.0.0"
        }
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status == 200:
                body = json.loads(res.read().decode("utf-8"))
                if "choices" in body and body["choices"]:
                    text = body["choices"][0].get("message", {}).get("content", "")
                    if text and text.strip():
                        return text.strip()
    except Exception as e:
        logging.warning(f"Open-source provider {endpoint} ({model_name}) error: {e}")
    return None

def generate_content(client_obj, model_name: str, prompt: str, context_data: str = "") -> str:
    """
    Ultra-resilient Multi-Tier content generation engine:
    Tier 1: Google Gemini & Gemma Open-Source Models (gemini-2.5-flash, gemini-3.5-flash-lite, gemini-flash-latest, gemma-4-31b-it, gemma-4-26b-a4b-it)
    Tier 2: Groq Open-Source LLMs (llama-3.3-70b-versatile, deepseek-r1-distill-llama-70b, mixtral-8x7b-32768, gemma2-9b-it)
    Tier 3: OpenRouter Open-Source LLMs (meta-llama/llama-3.3-70b-instruct:free, deepseek/deepseek-r1:free, mistralai/mistral-small-3.2-24b-instruct:free)
    Tier 4: Together AI Open-Source LLMs (meta-llama/Llama-3.3-70B-Instruct-Turbo)
    """
    use_grounding = not context_data or not context_data.strip()
    full_prompt = f"{prompt}\n\nContext Data / Verified News:\n{context_data}" if context_data.strip() else prompt
    
    # 1. Tier 1: Google Gemini & Open-Source Gemma Models
    models_to_try = [model_name]
    google_fallbacks = [
        'gemini-2.5-flash',
        'gemini-3.5-flash-lite',
        'gemini-flash-latest',
        'gemma-4-31b-it',
        'gemma-4-26b-a4b-it'
    ]
    for fb in google_fallbacks:
        if fb not in models_to_try:
            models_to_try.append(fb)
            
    last_err = None
    if client_obj:
        for current_model in models_to_try:
            max_retries = 2
            base_delay = 2
            
            for attempt in range(max_retries):
                # Attempt 1: Try with Search Grounding if applicable and model supports it
                if use_grounding and 'gemini' in current_model:
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
                
                # Attempt 2 (or Direct): Standard generation
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

    # 2. Tier 2: Groq Open-Source Fallback (Llama 3.3 70B, DeepSeek R1, Mixtral)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        print("  🔄 Google models exhausted. Trying Groq Open-Source Models...")
        groq_models = ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
        for g_model in groq_models:
            print(f"  > Attempting content generation with Groq ({g_model})...")
            text = _call_openai_compatible_api("https://api.groq.com/openai/v1/chat/completions", groq_key, g_model, full_prompt)
            if text:
                return text

    # 3. Tier 3: OpenRouter Open-Source Fallback
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        print("  🔄 Trying OpenRouter Open-Source Models...")
        openrouter_models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "mistralai/mistral-small-3.2-24b-instruct:free"
        ]
        for or_model in openrouter_models:
            print(f"  > Attempting content generation with OpenRouter ({or_model})...")
            text = _call_openai_compatible_api("https://openrouter.ai/api/v1/chat/completions", openrouter_key, or_model, full_prompt)
            if text:
                return text

    # 4. Tier 4: Together AI Open-Source Fallback
    together_key = os.environ.get("TOGETHER_API_KEY")
    if together_key:
        print("  🔄 Trying Together AI Open-Source Models...")
        together_models = ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
        for tog_model in together_models:
            print(f"  > Attempting content generation with Together AI ({tog_model})...")
            text = _call_openai_compatible_api("https://api.together.xyz/v1/chat/completions", together_key, tog_model, full_prompt)
            if text:
                return text
                
    raise RuntimeError(f"All GenAI and Open-Source fallback models failed. Last error: {last_err}")

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
