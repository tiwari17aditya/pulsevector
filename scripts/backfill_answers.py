import os
import sys
import glob
import re
from google import genai
from dotenv import load_dotenv

# Reconfigure stdout to use UTF-8 to prevent encoding issues with emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def extract_correct_answer(content):
    # Check if answer is already written
    match = re.search(r'(?:correct answer|answer):\s*([a-d])', content, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None

def solve_puzzle_with_gemini(file_content):
    prompt = f"""
Solve the following brain teaser puzzle and tell me which option (a, b, c, or d) is the correct answer.
Respond with ONLY the single option letter, in lowercase (e.g. 'a', 'b', 'c', or 'd'). Do not write any other text, explanation, or code.

Puzzle:
{file_content}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        answer = response.text.strip().lower()
        # Clean answer to check if it's a single letter (a, b, c, d)
        match = re.search(r'\b([a-d])\b', answer)
        if match:
            return match.group(1)
        else:
            print(f"  ⚠️ Warning: Gemini returned unexpected answer: '{response.text}'")
            return None
    except Exception as e:
        print(f"  ❌ Error calling Gemini: {e}")
        return None

def backfill_file(file_path):
    print(f"Checking: {os.path.basename(file_path)}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    existing_ans = extract_correct_answer(content)
    if existing_ans:
        print(f"  ✅ Already has correct answer: '{existing_ans}'")
        return

    # Solve the puzzle
    ans = solve_puzzle_with_gemini(content)
    if not ans:
        print(f"  ❌ Failed to solve puzzle.")
        return

    print(f"  💡 Solved! Correct answer is: '{ans}'")

    # Insert correct answer before the prompt divider '---'
    divider_match = re.search(r'^---', content, re.MULTILINE)
    if divider_match:
        idx = divider_match.start()
        # Clean content leading up to divider, append the answer, then append the rest
        new_content = content[:idx].rstrip() + f"\n\nCorrect Answer: {ans}\n\n" + content[idx:]
    else:
        new_content = content.rstrip() + f"\n\nCorrect Answer: {ans}\n"

    # Write back to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print(f"  ✏️ Successfully appended answer to {os.path.basename(file_path)}")

def main():
    archive_dir = os.path.join(PROJECT_ROOT, "pulse_archive")
    print(f"Scanning archive directory for brain teasers: {archive_dir}")
    
    # Search for all brain teaser text files recursively
    search_path = os.path.join(archive_dir, "**", "Brain_Teasers", "Text", "brainteaser-*.txt")
    files = glob.glob(search_path, recursive=True)
    
    print(f"Found {len(files)} brain teaser files to process.")
    for file_path in files:
        backfill_file(file_path)
    
    print("\n🎉 Backfill process completed.")

if __name__ == "__main__":
    main()
