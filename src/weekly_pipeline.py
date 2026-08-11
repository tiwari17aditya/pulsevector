import os
import re
import datetime
import logging
from pathlib import Path

from core.config import ARCHIVE_DIR
from core.genai_utils import (
    configure_genai, get_current_date_info, get_news_search_results,
    generate_content, save_file, read_prompt_section
)
from core.image_utils import (
    ensure_fonts, create_slide_image_file
)
from core.video_utils import (
    download_audio_library, get_random_audio_track, merge_audio_video,
    generate_thumbnail_slide_image, generate_animated_end_slide_frames_pipeline,
    compile_images_to_video_enhanced, format_date_custom
)
from core.youtube_utils import get_authenticated_service, upload_video_to_youtube, add_video_to_playlist, log_upload_details
from core.git_backup_utils import run_git_operations, run_backup_operations
from core.database_utils import run_database_upload

def generate_weekly_content(client, target_date):
    print(f"\nProcessing Weekly content generation up to: {target_date.strftime('%d %B %Y')}")
    week_start = target_date - datetime.timedelta(days=6)
    
    start_str = week_start.strftime("%d %B %Y")
    end_str = target_date.strftime("%d %B %Y")
    
    print("  > Generating Weekly Current Affairs...")
    search_query = f"current affairs top news headlines {start_str} to {end_str}"
    news_context = get_news_search_results(search_query)
    
    weekly_prompt = read_prompt_section("Weekly Current Affairs Prompt")
    if not weekly_prompt:
        weekly_prompt = (
            "Act as a Social Media and Educational expert for the 'Pulse Vector' YouTube channel (IST timezone) "
            "to generate Weekly Current Affairs content. When given a date range [start_date] to [end_date], generate 'Weekly Current Affairs ( [start_date] - [end_date] )' "
            "with 15 numbered points (each under 25 words). Crucially, for each point, identify the reputable news publisher/source "
            "from the context (e.g. BBC News, Reuters, Bloomberg, etc.) and append it at the end of the point strictly in the format: '[Source: Publisher Name]'. "
            "Do not include URL inside the point's source brackets. Additionally, provide YouTube metadata in this order:\n"
            "- Title: 'Weekly Current Affairs ( [start_date] - [end_date] )'\n"
            "- Reel Description: A Reel Description covering top highlights (max 25 words per point) formatted as 'Catch the top... [points] . . . . . [Hashtags]'\n"
            "- Hashtags: 50 high-reach hashtags (separated by spaces, NOT as a numbered list) including popular, niche, and educational tags.\n"
            "- Source URLs: Provide a list of the source URLs you used from the context, structured as:\n"
            "  - Publisher Name: URL\n"
            "Do NOT use numbers for headings, subheadings, or the hashtags list in the YouTube metadata section to avoid conflict with the current affairs points."
        )
    
    weekly_prompt_specific = (
        f"You are generating the weekly summary for {start_str} to {end_str}.\n"
        f"CRITICAL: {weekly_prompt.replace('[start_date]', start_str).replace('[end_date]', end_str)}"
    )
    
    ca_content = generate_content(client, 'gemini-2.5-flash', weekly_prompt_specific, news_context)
    
    year_str = target_date.strftime("%Y")
    month_name = target_date.strftime("%B")
    processed_month_dir = ARCHIVE_DIR / year_str / month_name
    
    weekly_filename = f"weekly-{target_date.strftime('%d-%b-%Y').lower()}_formatted.txt"
    weekly_path = processed_month_dir / "Weekly" / weekly_filename
    save_file(ca_content, weekly_path)

def generate_weekly_slides():
    print("\n🚀 Starting Weekly Slide Generation...")
    font_regular, font_bold = ensure_fonts(ARCHIVE_DIR)
    
    for root, dirs, files in os.walk(ARCHIVE_DIR):
        if "Weekly" in Path(root).parts and "Images" not in root:
            for file in files:
                if file.startswith("weekly-") and file.endswith("_formatted.txt"):
                    file_path = Path(root) / file
                    try:
                        images_dir = Path(root).parent / "Weekly_Images" / file.replace(".txt", "")
                        images_dir.mkdir(parents=True, exist_ok=True)
                        
                        content = file_path.read_text(encoding='utf-8')
                        # Strip YouTube metadata section before parsing points
                        metadata_markers = ['YouTube Metadata:', 'Title:', 'Reel Description:', 'Hashtags:', 'Source URLs:']
                        content_for_parsing = content
                        for marker in metadata_markers:
                            idx = content_for_parsing.find(marker)
                            if idx != -1:
                                content_for_parsing = content_for_parsing[:idx]
                                break
                        # Regex for points
                        point_pattern = re.compile(r"^\s*(\d+)\.\s+(.*?)(?=\n\s*\d+\.|\Z)", re.MULTILINE | re.DOTALL)
                        matches = point_pattern.findall(content_for_parsing)
                        points = [(int(m[0]), m[1].replace('\n', ' ').strip()) for m in matches]
                        
                        if not points:
                            raise ValueError(f"No points successfully parsed from {file_path}! The LLM format may be broken.")
                            
                        date_str = ""
                        date_match = re.search(r"Weekly Current Affairs\s+(.+)", content)
                        if date_match:
                            date_str = date_match.group(1).strip().upper()
                            
                        points_per_page = 5
                        total_pages = (len(points) + points_per_page - 1) // points_per_page
                        
                        all_exist = True
                        for p in range(1, total_pages + 1):
                            img_path = images_dir / f"{file_path.stem}_page-{p}.png"
                            if not img_path.exists():
                                all_exist = False
                                break
                        if all_exist:
                            continue
                            
                        print(f"Generating slides for {file} ({total_pages} pages)...")
                        for i in range(0, len(points), points_per_page):
                            page_points = points[i:i+points_per_page]
                            page_num = (i // points_per_page) + 1
                            out_path = images_dir / f"{file_path.stem}_page-{page_num}.png"
                            create_slide_image_file(date_str, page_points, page_num, total_pages, font_regular, font_bold, out_path, "WEEKLY CURRENT AFFAIRS")
                    except Exception as e:
                        print(f"❌ Error generating slides for '{file}': {e}")
                        logging.error(f"Error generating slides for '{file}': {e}", exc_info=True)

def run_weekly_youtube(target_date=None, enable_tts=True):
    print("\n🚀 Starting Weekly YouTube Video Generation & Upload...")
    now = target_date or datetime.datetime.now()
    year_str = now.strftime("%Y")
    month_name = now.strftime("%B")
    
    date_str_weekly = now.strftime("%d-%b-%Y").lower()
    weekly_playlist_title = f"Weekly Current Affairs - {year_str}"
    
    text_file = ARCHIVE_DIR / year_str / month_name / "Weekly" / f"weekly-{date_str_weekly}_formatted.txt"
    img_dir = ARCHIVE_DIR / year_str / month_name / "Weekly_Images" / f"weekly-{date_str_weekly}_formatted"
    video_path = ARCHIVE_DIR / year_str / month_name / "Weekly_Videos" / f"weekly-{date_str_weekly}_formatted.mp4"
    
    if video_path.exists():
        print(f"ℹ️ [Weekly] video {video_path.name} already exists. Skipping upload.")
        return
        
    if not text_file.exists() or not img_dir.exists():
        raise FileNotFoundError(f"❌ [Weekly] Missing text or images for {date_str_weekly}. Cannot generate video.")
        
    try:
        content = text_file.read_text(encoding='utf-8')
        
        # Robust Title parsing (case-insensitive, optional bolding, optional quotes)
        title_match = re.search(r"(?i)\*?\*?Title\*?\*?:\s*['\"`]?(.*?)['\"`]?\s*$", content, re.MULTILINE)
        
        # Robust Description parsing (case-insensitive, optional "Reel ", optional bolding)
        desc_match = re.search(r"(?i)\*?\*?(?:Reel\s+)?Description\*?\*?:\s*(.+)", content, re.DOTALL)
        
        if not title_match or not desc_match:
            raise ValueError("Could not parse Title/Description from Weekly text.")
            
        title = title_match.group(1).strip().strip("'\"`")
        desc_raw = desc_match.group(1)
        
        # Robust stop markers truncation using regex (case-insensitive, optional bolding/newlines/spaces)
        stop_match = re.search(r"(?i)\n+\s*\*?\*?(?:Hashtags|Source\s+URLs)\*?\*?", desc_raw)
        if stop_match:
            desc_raw = desc_raw[:stop_match.start()]
            
        desc = desc_raw.strip()
        if len(desc) > 4950:
            desc = desc[:4947] + '...'
        tags = ["WeeklyCurrentAffairs", "GlobalNews", "PulseVector"]
        
        font_regular, font_bold = ensure_fonts(ARCHIVE_DIR)
        
        # Thumbnail
        thumb_path = img_dir / "thumbnail.png"
        generate_thumbnail_slide_image(now, font_bold, font_regular, thumb_path, "WEEKLY")
        
        # End Animation
        anim_dir = ARCHIVE_DIR / "temp_end_frames"
        anim_frames = generate_animated_end_slide_frames_pipeline(font_bold, font_regular, anim_dir)
        
        # Voiceover & Dynamic Durations
        voiceover_data = None
        per_slide_durations = None
        voiceover_path = None
        
        if enable_tts:
            try:
                from core.tts_utils import generate_voiceover, HAS_TTS
                if HAS_TTS:
                    content_for_parsing = content
                    for marker in ['YouTube Metadata:', 'Title:', 'Reel Description:', 'Hashtags:', 'Source URLs:']:
                        idx = content_for_parsing.find(marker)
                        if idx != -1:
                            content_for_parsing = content_for_parsing[:idx]
                            break
                    point_pattern = re.compile(r"^\s*(\d+)\.\s+(.*?)(?=\n\s*\d+\.|\Z)", re.MULTILINE | re.DOTALL)
                    matches = point_pattern.findall(content_for_parsing)
                    points = [(int(m[0]), m[1].replace('\n', ' ').strip()) for m in matches]
                    
                    if points:
                        date_fmt_str = now.strftime("%B %d, %Y")
                        v_dir = video_path.parent
                        voiceover_data = generate_voiceover(points, date_fmt_str, v_dir, category_title="WEEKLY MASTERCLASS", rate="+10%")
                        if voiceover_data:
                            per_slide_durations = voiceover_data["all_slide_durations"]
                            voiceover_path = voiceover_data["full_voice_path"]
            except Exception as tts_err:
                print(f"⚠️ [TTS] Voiceover generation warning: {tts_err}. Continuing with standard durations.")
                
        # Compile
        slide_images = sorted(list(img_dir.glob("*_page-*.png")))
        temp_video = img_dir / "temp_video.mp4"
        compile_images_to_video_enhanced(
            thumb_path, slide_images, anim_frames, str(temp_video),
            duration_per_static=4.0, per_slide_durations=per_slide_durations
        )
        
        # Audio
        download_audio_library()
        audio_track = get_random_audio_track()
        
        video_path.parent.mkdir(parents=True, exist_ok=True)
        if audio_track:
            merge_audio_video(str(temp_video), str(audio_track), str(video_path), voiceover_path=voiceover_path)
        else:
            temp_video.rename(video_path)
            
        # Upload
        youtube = get_authenticated_service()
        print("Uploading to YouTube...")
        video_id = upload_video_to_youtube(youtube, str(video_path), title, desc, tags)
        print(f"✅ Upload Complete! Video ID: {video_id}")
        
        add_video_to_playlist(youtube, video_id, weekly_playlist_title)
        log_upload_details(
            title=title,
            category_name="Education (27)",
            video_type="Long-Form Masterclass",
            related_video_setting="Linked to Channel Homepage & Current Affairs Playlist",
            pinned_comment_status="Pinned Standard Comment",
            video_id=video_id
        )
        
    except Exception as e:
        print(f"❌ Failed to process Weekly YouTube video: {e}")
        raise

def run_all(target_date=None, enable_tts=True):
    now = target_date or datetime.datetime.now()
    client = configure_genai()
    generate_weekly_content(client, now)
    generate_weekly_slides()
    run_weekly_youtube(now, enable_tts=enable_tts)
    run_git_operations("Auto-update: Weekly Current Affairs Pipeline Run")
    run_backup_operations()
    run_database_upload()

if __name__ == "__main__":
    run_all()
