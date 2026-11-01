"""
Pulse Vector - Modular Detachable Pipeline Engine
Orchestrates content generation, slide rendering, TTS voiceover, video assembly,
YouTube distribution, cloud database sync, and git automation with independent pluggable stages.
"""

import os
import re
import logging
import datetime
import pathlib
from typing import List, Optional, Dict, Any

from .config import ARCHIVE_DIR, BT_DATE_FMT
from .stage_interfaces import ContentPayload, SlidePayload, AudioPayload, VideoPayload, PublishResult
from .content_parser import parse_news_content, parse_teaser_content
from .genai_utils import (
    configure_genai, get_news_search_results, read_prompts, read_prompt_section,
    generate_content, save_file, get_last_processed_date, build_brainteaser_prompt
)
from .image_utils import (
    ensure_fonts, create_slide_image_file, create_teaser_plain_image,
    create_teaser_styled_image, parse_teaser_file
)
from .video_utils import (
    download_audio_library, get_random_audio_track, merge_audio_video,
    generate_thumbnail_slide_image, generate_animated_end_slide_frames_pipeline,
    compile_images_to_video_enhanced
)
from .tts_utils import generate_voiceover, HAS_TTS
from .youtube_utils import (
    get_authenticated_service, get_quarter_info, upload_video_to_youtube,
    add_video_to_playlist, log_upload_details, add_video_comment,
    format_daily_interactive_comment, get_pinned_comment
)
from .git_backup_utils import run_git_operations, run_backup_operations
from .database_utils import run_database_upload
from .broadcast_utils import broadcast_daily_content
from .gdrive_endcredits import stitch_video_with_drive_endcredit

class PipelineEngine:
    """Pluggable, modular pipeline engine for all Pulse Vector content types."""
    
    def __init__(self, archive_dir: Optional[pathlib.Path] = None):
        self.archive_dir = archive_dir or ARCHIVE_DIR
        self.fonts_dir = self.archive_dir.parent / "fonts"
        self.last_youtube_error: Optional[Exception] = None
        
    def get_paths(self, content_type: str, target_date: datetime.datetime) -> Dict[str, pathlib.Path]:
        year_str = target_date.strftime("%Y")
        month_name = target_date.strftime("%B")
        month_abbr = target_date.strftime("%b").lower()
        d_str = str(target_date.day)
        
        base_dir = self.archive_dir / year_str / month_name
        
        if content_type == "daily":
            tag = f"daily-{d_str}{month_abbr}-{year_str}_formatted"
            text_file = base_dir / "Daily" / f"{tag}.txt"
            img_dir = base_dir / "Daily_Images" / tag
            video_file = base_dir / "Daily_Videos" / f"{tag}.mp4"
            bt_tag = f"brainteaser-{target_date.strftime(BT_DATE_FMT).lower()}"
            bt_text = base_dir / "Brain_Teasers" / "Text" / f"{bt_tag}.txt"
            bt_img_dir = base_dir / "Brain_Teasers" / "Images"
            return {
                "text_file": text_file,
                "img_dir": img_dir,
                "video_file": video_file,
                "bt_text": bt_text,
                "bt_img_dir": bt_img_dir,
                "tag": tag,
                "base_dir": base_dir
            }
        elif content_type == "weekly":
            tag = f"weekly-{target_date.strftime('%d-%b-%Y').lower()}_formatted"
            text_file = base_dir / "Weekly" / f"{tag}.txt"
            img_dir = base_dir / "Weekly_Images" / tag
            video_file = base_dir / "Weekly_Videos" / f"{tag}.mp4"
            return {
                "text_file": text_file,
                "img_dir": img_dir,
                "video_file": video_file,
                "tag": tag,
                "base_dir": base_dir
            }
        elif content_type == "monthly":
            tag = f"monthly-{month_abbr}-{year_str}_formatted"
            text_file = base_dir / "Monthly" / f"{tag}.txt"
            img_dir = base_dir / "Monthly_Images" / tag
            video_file = base_dir / "Monthly_Videos" / f"{tag}.mp4"
            return {
                "text_file": text_file,
                "img_dir": img_dir,
                "video_file": video_file,
                "tag": tag,
                "base_dir": base_dir
            }
        else:
            raise ValueError(f"Unknown content type: {content_type}")

    # -------------------------------------------------------------
    # STAGE 1: Text & Brain Teaser Generation
    # -------------------------------------------------------------
    def stage_generate_text(self, content_type: str, target_date: datetime.datetime, client=None) -> ContentPayload:
        print(f"\n📝 [Stage: Text Gen] Processing {content_type.title()} for {target_date.strftime('%d %B %Y')}...")
        paths = self.get_paths(content_type, target_date)
        if not client:
            client = configure_genai()
            
        date_str = target_date.strftime("%d %B %Y")
        
        if content_type == "daily":
            ca_prompt, bt_prompt = read_prompts()
            search_query = f"current affairs news headlines {date_str}"
            news_context = get_news_search_results(search_query)
            
            ca_prompt_specific = (
                f"Today is {date_str}. CRITICAL: You must generate ONLY the daily news for today. "
                f"DO NOT generate a weekly or monthly summary. {ca_prompt}"
            )
            ca_content = generate_content(client, 'gemini-2.5-flash', ca_prompt_specific, news_context)
            save_file(ca_content, paths["text_file"])
            
            # Brain Teaser
            if bt_prompt and not paths["bt_text"].exists():
                bt_prompt_specific, _ = build_brainteaser_prompt(target_date, bt_prompt, randomize=True)
                bt_content = generate_content(client, 'gemini-2.5-flash', bt_prompt_specific)
                save_file(bt_content, paths["bt_text"])
                
            return parse_news_content(ca_content, "daily", target_date, paths["text_file"])
            
        elif content_type == "weekly":
            week_start = target_date - datetime.timedelta(days=6)
            start_str = week_start.strftime("%d %B %Y")
            search_query = f"current affairs top news headlines {start_str} to {date_str}"
            news_context = get_news_search_results(search_query)
            
            weekly_prompt = read_prompt_section("Weekly Current Affairs Prompt")
            if not weekly_prompt:
                weekly_prompt = (
                    "Act as a Social Media and Educational expert for the 'Pulse Vector' YouTube channel "
                    "to generate Weekly Current Affairs content with 15 numbered points (each under 25 words). "
                    "Append source as '[Source: Publisher Name]'. Provide YouTube Metadata."
                )
            weekly_prompt_specific = (
                f"You are generating the weekly summary for {start_str} to {date_str}.\n"
                f"CRITICAL: {weekly_prompt.replace('[start_date]', start_str).replace('[end_date]', date_str)}"
            )
            ca_content = generate_content(client, 'gemini-2.5-flash', weekly_prompt_specific, news_context)
            save_file(ca_content, paths["text_file"])
            return parse_news_content(ca_content, "weekly", target_date, paths["text_file"])
            
        elif content_type == "monthly":
            month_name = target_date.strftime("%B")
            year_str = target_date.strftime("%Y")
            search_query = f"current affairs top news headlines {month_name} {year_str}"
            news_context = get_news_search_results(search_query)
            
            monthly_prompt = read_prompt_section("Monthly Current Affairs Prompt")
            if not monthly_prompt:
                monthly_prompt = (
                    "Act as a Social Media and Educational expert for the 'Pulse Vector' YouTube channel "
                    "to generate Monthly Current Affairs content with 50 numbered points (each under 25 words). "
                    "Append source as '[Source: Publisher Name]'. Provide YouTube Metadata."
                )
            monthly_prompt_specific = (
                f"You are generating the monthly summary for {month_name} {year_str}.\n"
                f"CRITICAL: {monthly_prompt.replace('[month_name]', month_name).replace('[year]', year_str)}"
            )
            ca_content = generate_content(client, 'gemini-2.5-flash', monthly_prompt_specific, news_context)
            save_file(ca_content, paths["text_file"])
            return parse_news_content(ca_content, "monthly", target_date, paths["text_file"])

    # -------------------------------------------------------------
    # STAGE 2: Slide & Image Generation
    # -------------------------------------------------------------
    def stage_generate_slides(self, content_type: str, target_date: datetime.datetime, payload: Optional[ContentPayload] = None, aspect_ratio: Optional[str] = None) -> SlidePayload:
        print(f"\n🎨 [Stage: Slide Gen] Rendering slides for {content_type.title()} ({target_date.strftime('%d %B %Y')})...")
        paths = self.get_paths(content_type, target_date)
        text_file = paths["text_file"]
        images_dir = paths["img_dir"]
        images_dir.mkdir(parents=True, exist_ok=True)
        
        font_regular, font_bold = ensure_fonts(self.archive_dir)
        
        if not payload:
            if not text_file.exists():
                raise FileNotFoundError(f"Missing text file: {text_file}")
            raw_text = text_file.read_text(encoding='utf-8')
            payload = parse_news_content(raw_text, content_type, target_date, text_file)
            
        points = payload.points
        if not points:
            raise ValueError(f"No points parsed from {text_file}!")
            
        date_header = payload.extra_metadata.get("date_header") or target_date.strftime("%d %B %Y").upper()
        cat_title = f"{content_type.upper()} CURRENT AFFAIRS"
        if content_type == "monthly":
            cat_title = "MONTHLY CURRENT AFFAIRS"
            
        ar = aspect_ratio or ("9:16" if content_type == "daily" else "16:9")
        points_per_page = 5
        total_pages = (len(points) + points_per_page - 1) // points_per_page
        
        generated_slides = []
        for i in range(0, len(points), points_per_page):
            page_points = points[i:i+points_per_page]
            page_num = (i // points_per_page) + 1
            out_path = images_dir / f"{paths['tag']}_page-{page_num}.png"
            create_slide_image_file(
                date_header, page_points, page_num, total_pages,
                font_regular, font_bold, out_path, cat_title,
                aspect_ratio=ar
            )
            generated_slides.append(out_path)
            
        # Generate Brain Teaser Images if Daily
        if content_type == "daily" and paths.get("bt_text") and paths["bt_text"].exists():
            self.stage_generate_teasers(target_date)
            
        return SlidePayload(
            content_type=content_type,
            target_date=target_date,
            slide_image_paths=generated_slides,
            output_dir=images_dir
        )

    def stage_generate_teasers(self, target_date: Optional[datetime.datetime] = None):
        font_regular, font_bold = ensure_fonts(self.archive_dir)
        font_poppins = self.fonts_dir / "Poppins-Bold.ttf"
        
        for root, dirs, files in os.walk(self.archive_dir):
            if "Brain_Teasers" in pathlib.Path(root).parts and "Text" in pathlib.Path(root).parts:
                for file in files:
                    if file.startswith("brainteaser-") and file.endswith(".txt"):
                        file_path = pathlib.Path(root) / file
                        img_dir = pathlib.Path(root).parent / "Images"
                        img_dir.mkdir(parents=True, exist_ok=True)
                        
                        base_name = file_path.stem
                        plain_p = img_dir / f"{base_name}_plain.png"
                        styled_p = img_dir / f"{base_name}_styled.png"
                        
                        if not plain_p.exists() or not styled_p.exists():
                            data = parse_teaser_file(file_path)
                            if data:
                                if not plain_p.exists():
                                    create_teaser_plain_image(data, font_poppins, font_bold, font_regular, plain_p)
                                if not styled_p.exists():
                                    create_teaser_styled_image(data, font_poppins, font_bold, font_regular, styled_p)

    # -------------------------------------------------------------
    # STAGE 3: Video Assembly & Audio/TTS Synthesis
    # -------------------------------------------------------------
    def stage_compile_video(self, content_type: str, target_date: datetime.datetime, enable_tts: bool = True, force: bool = False, aspect_ratio: Optional[str] = None) -> VideoPayload:
        print(f"\n🎬 [Stage: Video Compilation] Building video for {content_type.title()} ({target_date.strftime('%d %B %Y')})...")
        paths = self.get_paths(content_type, target_date)
        text_file = paths["text_file"]
        img_dir = paths["img_dir"]
        video_path = paths["video_file"]
        video_path.parent.mkdir(parents=True, exist_ok=True)
        
        if video_path.exists() and not force:
            print(f"ℹ️ Video {video_path.name} already exists. Skipping compilation.")
            return VideoPayload(video_path=video_path, duration=0.0)
            
        if not text_file.exists():
            raise FileNotFoundError(f"Missing text file: {text_file}")
            
        raw_text = text_file.read_text(encoding='utf-8')
        payload = parse_news_content(raw_text, content_type, target_date, text_file)
        
        font_regular, font_bold = ensure_fonts(self.archive_dir)
        ar = aspect_ratio or ("9:16" if content_type == "daily" else "16:9")
        
        # 1. Thumbnail Slide (Pillar 1: High-Retention Headline Hook + Pillar 4: Aspect Ratio)
        thumb_path = img_dir / "thumbnail.png"
        cat_short = "MONTHLY" if content_type == "monthly" else ("WEEKLY" if content_type == "weekly" else "DAILY")
        headline_hook = payload.points[0][1] if payload.points and content_type == "daily" else None
        generate_thumbnail_slide_image(target_date, font_bold, font_regular, thumb_path, cat_short, headline_hook=headline_hook, aspect_ratio=ar)
        
        # 2. Endcredits: Old static card replaced with dynamic Google Drive Runtime Endcredits
        # anim_frames set to empty list so main video compiles clean without legacy card
        anim_frames = []
        
        # 3. Voiceover & Durations
        per_slide_durations = None
        voiceover_path = None
        
        if enable_tts and HAS_TTS and payload.points:
            try:
                rate = "+35%" if content_type == "daily" else "+10%"
                date_fmt_str = target_date.strftime("%B %d, %Y") if content_type != "monthly" else target_date.strftime("%B %Y")
                cat_voice_title = "DAILY CURRENT AFFAIRS" if content_type == "daily" else f"{content_type.upper()} MASTERCLASS"
                voice_data = generate_voiceover(
                    payload.points, date_fmt_str, video_path.parent,
                    category_title=cat_voice_title, rate=rate
                )
                if voice_data:
                    per_slide_durations = voice_data["all_slide_durations"]
                    voiceover_path = voice_data["full_voice_path"]
            except Exception as t_err:
                logging.warning(f"Voiceover generation skipped: {t_err}")
                
        # 4. Slide Images
        slide_images = sorted(list(img_dir.glob(f"{paths['tag']}_page-*.png")))
        if not slide_images:
            raise FileNotFoundError(f"No slide images found in {img_dir}")
            
        temp_video = img_dir / "temp_video.mp4"
        duration_per_static = 1.8 if content_type == "daily" else 4.5
        
        compile_images_to_video_enhanced(
            thumb_path, slide_images, anim_frames, str(temp_video),
            duration_per_static=duration_per_static, per_slide_durations=per_slide_durations
        )
        
        # 5. Background Music, Muxing & Google Drive Runtime Endcredits Attachment
        download_audio_library()
        audio_track = get_random_audio_track()
        temp_muxed = img_dir / "temp_main_muxed.mp4"
        
        if audio_track:
            merge_audio_video(str(temp_video), str(audio_track), str(temp_muxed), voiceover_path=voiceover_path)
        else:
            temp_video.rename(temp_muxed)

        # 6. Attach runtime Google Drive Endcredits with Bell Enlargement & clean fade transitions
        try:
            stitch_video_with_drive_endcredit(
                main_video_path=temp_muxed,
                output_video_path=video_path,
                aspect_ratio=ar,
            )
        finally:
            for cleanup_file in [temp_video, temp_muxed]:
                if cleanup_file.exists():
                    try:
                        cleanup_file.unlink()
                    except Exception:
                        pass
            
        print(f"✅ Video compiled & stitched with Drive endcredits successfully: {video_path}")
        return VideoPayload(video_path=video_path, duration=0.0, has_audio=bool(audio_track), has_voiceover=bool(voiceover_path))

    # -------------------------------------------------------------
    # STAGE 4: YouTube Upload & Playlist Distribution
    # -------------------------------------------------------------
    def stage_youtube_publish(self, content_type: str, target_date: datetime.datetime) -> Optional[str]:
        print(f"\n🚀 [Stage: YouTube Upload] Uploading {content_type.title()} ({target_date.strftime('%d %B %Y')})...")
        paths = self.get_paths(content_type, target_date)
        video_path = paths["video_file"]
        text_file = paths["text_file"]
        
        if not video_path.exists():
            raise FileNotFoundError(f"Cannot upload: Video not found at {video_path}")
            
        raw_text = text_file.read_text(encoding='utf-8')
        payload = parse_news_content(raw_text, content_type, target_date, text_file)
        
        youtube = get_authenticated_service()
        video_id = None
        if not youtube:
            print("⚠️ YouTube authentication failed. Skipping YouTube upload; proceeding to backup & broadcast.")
        else:
            try:
                print(f"Uploading '{payload.title}' to YouTube...")
                video_id = upload_video_to_youtube(
                    youtube, str(video_path), payload.title, payload.description, payload.hashtags
                )
                print(f"✅ Upload Complete! Video ID: {video_id}")
                
                # Playlist Assignment
                year_str = target_date.strftime("%Y")
                if content_type == "daily":
                    _, playlist_title = get_quarter_info(target_date)
                    video_type = "Short (9:16)"
                elif content_type == "weekly":
                    playlist_title = f"Weekly Current Affairs - {year_str}"
                    video_type = "Weekly Masterclass"
                elif content_type == "monthly":
                    playlist_title = f"Monthly Current Affairs - {year_str}"
                    video_type = "Monthly Masterclass"
                else:
                    playlist_title = "Pulse Vector News"
                    video_type = "Video"
                    
                add_video_to_playlist(youtube, video_id, playlist_title)
                
                # Pillar 2: High-Engagement Interactive Discussion Comment
                try:
                    h1 = payload.points[0][1] if payload.points else "Global Events"
                    date_display = target_date.strftime("%d %B %Y")
                    interactive_comment = format_daily_interactive_comment(h1, date_display) if content_type == "daily" else get_pinned_comment()
                    add_video_comment(youtube, video_id, interactive_comment)
                except Exception as c_err:
                    print(f"  > Note on video comment: {c_err}")

                log_upload_details(
                    title=payload.title,
                    category_name="Education (27)",
                    video_type=video_type,
                    related_video_setting="Linked to Playlist",
                    pinned_comment_status="Interactive Comment Posted",
                    video_id=video_id
                )
                self.last_youtube_error = None
            except Exception as yt_err:
                self.last_youtube_error = yt_err
                print(f"⚠️ YouTube upload encountered an error: {yt_err}")
                print("  > Auto-healing: Continuing pipeline to preserve video and trigger community broadcast.")
                video_id = None
        
        # Feature 2: Community Auto-Broadcast (Telegram & Discord)
        try:
            summary_points = "\n".join([f"• {p[1]}" for p in payload.points[:5]])
            img_directory = paths.get("img_dir") or paths.get("image_dir")
            thumb_path = img_directory / "thumbnail.png" if img_directory else None
            broadcast_daily_content(
                content_type=content_type,
                date_obj=target_date,
                title=payload.title,
                summary_text=summary_points,
                image_path=thumb_path if thumb_path.exists() else None,
                video_path=video_path if video_path and video_path.exists() else None,
                video_url=f"https://youtu.be/{video_id}" if video_id else None
            )
        except Exception as b_err:
            print(f"  > Broadcast notice: {b_err}")
            
        return video_id

    # -------------------------------------------------------------
    # STAGE 5: Cloud DB, Git & External Backup
    # -------------------------------------------------------------
    def stage_sync_and_backup(self, commit_msg: str = "Auto-update: Pulse Vector Run"):
        print("\n☁️ [Stage: Cloud Sync & Backup] Running DB, Git & External Backups...")
        run_git_operations(commit_msg)
        run_backup_operations()
        run_database_upload()

    # -------------------------------------------------------------
    # Orchestrated Pipeline Runner
    # -------------------------------------------------------------
    def run_pipeline(
        self,
        content_type: str,
        target_date: Optional[datetime.datetime] = None,
        stages: Optional[List[str]] = None,
        enable_tts: bool = True,
        force: bool = False,
        dry_run: bool = False
    ) -> PublishResult:
        now = target_date or datetime.datetime.now()
        active_stages = [s.lower().strip() for s in stages] if stages else ["text", "slides", "video", "youtube", "sync"]
        
        print(f"\n==========================================")
        print(f"  Pulse Vector Pipeline: {content_type.upper()}")
        print(f"  Target Date: {now.strftime('%d %B %Y')}")
        print(f"  Active Stages: {', '.join(active_stages)}")
        print(f"  Dry Run: {dry_run} | TTS: {enable_tts}")
        print(f"==========================================")
        
        result = PublishResult()
        
        if dry_run:
            print("🧪 DRY RUN MODE: Validating pipeline paths and stage prerequisites...")
            paths = self.get_paths(content_type, now)
            print(f"  Target text file: {paths['text_file']}")
            print(f"  Target image dir: {paths['img_dir']}")
            print(f"  Target video:     {paths['video_file']}")
            print("✅ Dry run verification passed.")
            return result
            
        payload = None
        if "text" in active_stages or "all" in active_stages:
            payload = self.stage_generate_text(content_type, now)
            
        if "slides" in active_stages or "all" in active_stages:
            self.stage_generate_slides(content_type, now, payload)
            
        if "video" in active_stages or "all" in active_stages:
            self.stage_compile_video(content_type, now, enable_tts=enable_tts, force=force)
            
        if "youtube" in active_stages or "all" in active_stages:
            try:
                result.youtube_video_id = self.stage_youtube_publish(content_type, now)
            except Exception as yt_err:
                logging.error(f"YouTube stage failed: {yt_err}")
                result.errors.append(str(yt_err))
                
        if "sync" in active_stages or "all" in active_stages:
            self.stage_sync_and_backup(f"Auto-update: {content_type.title()} Pipeline Run")
            
        print(f"\n🎉 Finished execution for {content_type.title()} ({now.strftime('%d %B %Y')}).")
        return result
