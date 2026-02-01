import os
import shutil
import re
from datetime import datetime
from pathlib import Path

# --- Configuration ---
INPUT_DIR = "incoming_data"
ARCHIVE_DIR = "pulse_archive"

# Supported Date Formats for Brain Teasers (e.g., "10jan26")
BT_DATE_FMT = "%d%b%y"

def get_month_name(month_num_or_abbr):
    """Returns full month name from number or abbreviation."""
    try:
        if isinstance(month_num_or_abbr, int) or month_num_or_abbr.isdigit():
             return datetime(2000, int(month_num_or_abbr), 1).strftime('%B')
        else:
             return datetime.strptime(month_num_or_abbr, '%b').strftime('%B')
    except:
        return datetime.strptime(month_num_or_abbr, '%B').strftime('%B')

def parse_date_title(title_line):
    """
    Parses title line for Weekly, Daily, Monthly dates.
    Returns: (Type, Year, MonthName, CleanFilename)
    """
    # 1. Weekly: "Weekly Current Affairs ( 20-October-2025 - 26-October-2025 )"
    # 1. Weekly: "Weekly Current Affairs ( 20-October-2025 - 26-October-2025 )"
    # 1. Weekly: "Weekly Current Affairs ( 20-October-2025 - 26-October-2025 )" OR "( 10 Nov - 15 Nov 2025 )"
    # 1. Weekly: "Weekly Current Affairs ( 20-October-2025 - 26-October-2025 )" OR "( 10 Nov - 15 Nov )"
    # 1. Weekly: "Weekly Current Affairs ( 20-October-2025 - 26-October-2025 )" OR "(( 22 Dec 2025 ] - [ 28 Dec 2025 ] )" OR "( November 03 - November 09, 2025 )"
    date_pat = r"(?:(?:\d{1,2}[\s\-\–]+[A-Za-z]+)|(?:[A-Za-z]+[\s\-\–]+\d{1,2}))(?:[\s\-\–,]+\d{4})?"
    weekly_pattern = r"(Weekly)\s+Current\s+Affairs.*?(" + date_pat + r").*?-.*?(" + date_pat + r")"
    match_w = re.search(weekly_pattern, title_line, re.IGNORECASE)
    if match_w:
        end_date_str = match_w.group(2).replace('–', '-').replace(' ', '-')
        
        # If year is missing, check if it's in the start date or default to 2025
        if not re.search(r'\d{4}', end_date_str):
             # Try to find year in start date group 2
             if re.search(r'\d{4}', match_w.group(2)):
                 year = re.search(r'\d{4}', match_w.group(2)).group(0)
                 end_date_str += f"-{year}"
             else:
                 end_date_str += "-2025" # Fallback
        
        try:
            # Clean up potential leading/trailing non-date chars if any
            end_date_str = end_date_str.strip('[]() ,')
            for fmt in ['%d-%B-%Y', '%d-%b-%Y', '%B-%d-%Y', '%b-%d-%Y']:
                try:
                    dt = datetime.strptime(end_date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Date format not currently supported")
            
            return ("Weekly", str(dt.year), dt.strftime('%B'), f"weekly-{dt.strftime('%d-%b-%Y').lower()}.txt")
        except ValueError:
            pass 

    # 2. Daily Patterns
    # Pattern A: "Daily Current Affairs 31 January 2026" or "10 Dec 2025" or "[2 Dec 2025]"
    daily_pat_dmY = r"(Daily)\s+Current\s+Affairs[\s\[\(\{]*(\d{1,2})[\s\-\–]+([A-Za-z]+)[\s\-\–,]+(\d{2,4})"
    # Pattern B: "Daily Current Affairs November 3, 2025"
    daily_pat_MdY = r"(Daily)\s+Current\s+Affairs[\s\[\(\{]*([A-Za-z]+)[\s\-\–]+(\d{1,2})[\s\-\–,]+(\d{2,4})"
    # Pattern C: "Daily Current Affairs 22nov2025" (concatenated) OR "[22nov2025]"
    daily_pat_concat = r"(Daily)\s+Current\s+Affairs[\s\[\(\{]*(\d{1,2})([A-Za-z]+)(\d{4})"

    match_d = re.search(daily_pat_dmY, title_line, re.IGNORECASE)
    if match_d: # Day Month Year
        day, month_str, year = match_d.group(2), match_d.group(3), match_d.group(4)
    else:
        match_d2 = re.search(daily_pat_MdY, title_line, re.IGNORECASE)
        if match_d2: # Month Day Year
            month_str, day, year = match_d2.group(2), match_d2.group(3), match_d2.group(4)
            match_d = match_d2
        else:
            match_d3 = re.search(daily_pat_concat, title_line, re.IGNORECASE)
            if match_d3: # DayMonthYear
               day, month_str, year = match_d3.group(2), match_d3.group(3), match_d3.group(4)
               match_d = match_d3

    if match_d:
        try:
            if len(year) == 2: year = "20" + year
            
            # Normalize Month (handle Dec vs December)
            try:
                dt_month = datetime.strptime(month_str, '%B') # Try full name
            except ValueError:
                dt_month = datetime.strptime(month_str, '%b') # Try abbr
            
            dt = datetime(int(year), dt_month.month, int(day))
            return ("Daily", str(dt.year), dt.strftime('%B'), f"daily-{dt.strftime('%d-%b-%Y').lower()}.txt")
        except ValueError:
            pass

    # 3. Monthly: "Monthly Current Affairs - (November, 2026)"
    monthly_pattern = r"(Monthly)\s+Current\s+Affairs.*?\(\s*([A-Za-z]+)[,\s\-\–]+(\d{4})\s*\)"
    match_m = re.search(monthly_pattern, title_line, re.IGNORECASE)
    if match_m:
        month_str, year = match_m.group(2), match_m.group(3)
        try:
            try:
                dt_month = datetime.strptime(month_str, '%B')
            except ValueError:
                dt_month = datetime.strptime(month_str, '%b')

            return ("Monthly", str(year), dt_month.strftime('%B'), f"monthly-{dt_month.strftime('%b').lower()}-{year}.txt")
        except ValueError:
            pass

    return None

def process_text_file(filepath):
    """Reads, formats, and returns metadata for filing."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        if not lines: return None

        metadata = None
        for i in range(min(10, len(lines))):
            metadata = parse_date_title(lines[i])
            if metadata:
                break
        
        if not metadata:
            print(f"⚠️  Skipping: Could not parse title in '{filepath.name}'")
            return None

        # Format content
        formatted_content = [lines[0], ""] + [f"{i}. {p}" for i, p in enumerate(lines[1:], 1)]
        return {
            'type': 'text',
            'category': metadata[0],
            'year': metadata[1],
            'month': metadata[2],
            'filename': metadata[3],
            'content': "\n".join(formatted_content)
        }
    except Exception as e:
        print(f"❌ Error processing text '{filepath.name}': {e}")
        return None

def process_brain_teaser(filepath):
    """Parses brain teaser filename for date."""
    # Pattern: brainteaser-10jan26.png, brain-teaser-10jan26.png, sample-brain-teaser-10jan26.png
    match = re.search(r"(?:sample-)?brain-?teaser-(\d{1,2}[a-z]{3}\d{2})", filepath.name, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, BT_DATE_FMT)
            return {
                'type': 'image',
                'category': 'Brain_Teasers',
                'year': f"20{dt.strftime('%y')}", # Assuming 21st century
                'month': dt.strftime('%B'),
                'filename': filepath.name,
                'source_path': filepath
            }
        except ValueError:
            pass
    
    print(f"⚠️  Skipping Brain Teaser: Unknown format '{filepath.name}'")
    return None

def archive_item(item):
    """Moves/Writes item to the correct archive folder."""
    dest_dir = Path(ARCHIVE_DIR) / item['year'] / item['month'] / item['category']
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = dest_dir / item['filename']

    if item['type'] == 'text':
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(item['content'])
        print(f"✅ Archived Text: {dest_path}")
    
    elif item['type'] == 'image':
        shutil.copy2(item['source_path'], dest_path)
        print(f"✅ Archived Image: {dest_path}")

def main():
    print("🚀 Starting Pulse Vector Pipeline...")
    
    input_path = Path(INPUT_DIR)
    if not input_path.exists():
        print(f"⚠️  Input directory '{INPUT_DIR}' not found. Creating it...")
        input_path.mkdir()
        return

    # Process Files
    found = 0
    for filepath in input_path.iterdir():
        if filepath.is_file():
            item = None
            if filepath.suffix.lower() == '.txt':
                item = process_text_file(filepath)
            elif filepath.suffix.lower() == '.png':
                item = process_brain_teaser(filepath)
            
            if item:
                archive_item(item)
                found += 1
                # Remove source file after successful archive
                filepath.unlink() 
                print(f"🗑️  Deleted source: {filepath.name}") 

    if found == 0:
        print("No processable files found in 'incoming_data'.")
    else:
        print(f"\n✨ Pipeline Complete. Processed {found} items.")

if __name__ == "__main__":
    main()
