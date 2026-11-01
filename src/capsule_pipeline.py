"""
Pulse Vector Knowledge Capsule Pipeline
Orchestrates high-yield weekly exam insights, infographic posters, and social distribution.
"""

import os
import sys
import argparse
import datetime
import pathlib
import json
import logging
from typing import Dict, Any, Optional

SRC_DIR = pathlib.Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import ARCHIVE_DIR
from core.capsule_renderer import CapsuleRenderer
from core.video_utils import compile_images_with_transitions, merge_audio_video, get_random_audio_track
from core.tts_utils import synthesize_text, sanitize_text_for_speech, HAS_TTS

def get_sample_weekly_insights(week_date_str: str = "12 October - 18 October 2026") -> Dict[str, Any]:
    """
    Returns curated, high-yield weekly insights for competitive exams
    modeled directly after the high-density structure in samples/sample-update.jpeg.
    """
    return {
        "header": {
            "main_title": "EXAM RELEVANT CURRENT AFFAIRS 2026",
            "date_range": week_date_str,
            "subtitle": "High-Value Insights for Competitive Exams (UPSC • SSC • Banking • State PSC)"
        },
        "sections": [
            {
                "num": 1,
                "title": "BRICS 2026: NEW DELHI DECLARATION",
                "subtitle": "18th BRICS Summit | Key Highlights for Competitive Exams",
                "color": (2, 132, 199),  # Blue
                "metadata_grid": [
                    {"label": "Dates", "value": "12-13 October 2026"},
                    {"label": "Host Country", "value": "India"},
                    {"label": "Host City", "value": "New Delhi"},
                    {"label": "Venue", "value": "Bharat Mandapam, Pragati Maidan"},
                    {"label": "Theme", "value": "Building Resilience, Innovation & Trade"},
                    {"label": "Milestone", "value": "45 Pages | 140 Declarations"},
                    {"label": "BRICS Chair", "value": "India (2026)"}
                ],
                "points_title": "KEY EXAM TAKEAWAYS",
                "layout": "2x2",
                "points": [
                    "Unanimous condemnation of terrorism in all forms, including cross-border terrorism.",
                    "Called for comprehensive reform of global governance and stronger voice for Global South.",
                    "Endorsed multilateral trade cooperation, energy transition security, and local currency settlements.",
                    "Deepened collaborative initiatives in science, AI governance, and resilient global supply chains."
                ]
            },
            {
                "num": 2,
                "title": "BIMSTEC DELHI DECLARATION 2026",
                "subtitle": "First BIMSTEC Home Ministers' Conclave & Security Framework",
                "color": (16, 149, 100),  # Green
                "metadata_grid": [
                    {"label": "Date", "value": "13 October 2026"},
                    {"label": "Venue", "value": "New Delhi, India"},
                    {"label": "Headquarters", "value": "Dhaka, Bangladesh"},
                    {"label": "Members (7)", "value": "India, Bangladesh, Bhutan, Myanmar, Nepal, Sri Lanka, Thailand"}
                ],
                "points_title": "FOCUS AREAS & CORE RESOLUTIONS",
                "points": [
                    "Strengthened counter-terrorism coordination and action against violent extremist syndicates.",
                    "Combating transnational organised crime through shared intelligence repositories.",
                    "Coordinated interdiction against illicit precursor chemicals and narcotics money laundering.",
                    "Comprehensive regional action framework to dismantle human trafficking networks."
                ],
                "side_note": "BIMSTEC Convention on Combating International Terrorism, Transnational Organised Crime and Illicit Drug Trafficking has been actively in force since March 2021."
            },
            {
                "num": 3,
                "title": "e-SHRAM PORTAL COMPLETES 5 YEARS",
                "subtitle": "Universal Social Security Infrastructure for India's Unorganised Workforce",
                "color": (217, 119, 6),  # Amber
                "metadata_grid": [
                    {"label": "Launch Date", "value": "26 August 2021"},
                    {"label": "Milestone", "value": "5 Years Completed (2026)"},
                    {"label": "Nodal Ministry", "value": "Ministry of Labour & Employment"},
                    {"label": "Developed By", "value": "National Informatics Centre (NIC)"},
                    {"label": "Database", "value": "National Database of Unorganised Workers (NDUW)"},
                    {"label": "Unique ID", "value": "12-digit Universal Account Number (UAN)"}
                ],
                "stats": [
                    {"label": "Total Registrations", "value": "31.89 Crore"},
                    {"label": "Largest Age Group", "value": "18-40 Years (55.21%)"},
                    {"label": "Top Registered States", "value": "UP, Bihar, WB, MP, MH"}
                ],
                "progress_bar": {
                    "percent1": 54.28,
                    "label1": "Women 54.28%",
                    "label2": "Men 45.72%"
                },
                "points_title": "BENEFITS & SYSTEM ARCHITECTURE",
                "points": [
                    "Aadhaar-seeded centralized registry enabling full portability of social security welfare benefits.",
                    "Seamless API integration with PMSYM pension, PMJJBY insurance, and national apprenticeship portals.",
                    "e-Shram One-Stop-Solution ecosystem delivers aggregated access to healthcare, skilling, and credit.",
                    "Completely free lifelong digital registration across all Common Service Centres (CSCs)."
                ]
            }
        ],
        "footer": {
            "tags": [
                "BRICS Summit 2026",
                "New Delhi Declaration",
                "BIMSTEC Delhi Declaration",
                "Dhaka HQ",
                "e-Shram Portal",
                "NDUW",
                "12-Digit UAN",
                "UPSC Revision"
            ]
        }
    }

def generate_social_post(capsule_data: Dict[str, Any]) -> str:
    """
    Generates a high-engagement social media & YouTube Community post
    based on the weekly capsule data.
    """
    header = capsule_data.get("header", {})
    sections = capsule_data.get("sections", [])
    date_range = header.get("date_range", "Weekly Insights")

    post_lines = [
        f"📚 EXAM RELEVANT CURRENT AFFAIRS CAPSULE ({date_range})",
        "🎯 High-Value Highlights for UPSC, SSC, Banking, State PSC & Competitive Exams\n",
        "Save & bookmark this 1-page visual revision cheat sheet! Here are the core insights:\n"
    ]

    for sec in sections:
        num = sec.get("num", 1)
        title = sec.get("title", "")
        sub = sec.get("subtitle", "")
        post_lines.append(f"🔹 {num}. {title}")
        if sub:
            post_lines.append(f"   ({sub})")
        
        # Add metadata highlights
        for meta in sec.get("metadata_grid", [])[:3]:
            post_lines.append(f"   • {meta.get('label')}: {meta.get('value')}")
            
        # Add stats if present
        for st in sec.get("stats", []):
            post_lines.append(f"   • {st.get('label')}: {st.get('value')}")
            
        post_lines.append("")

    post_lines.extend([
        "💡 QUICK EXAM CHALLENGE:",
        "Q: Where is the permanent Secretariat/Headquarters of BIMSTEC located?",
        "(A) New Delhi    (B) Dhaka    (C) Colombo    (D) Kathmandu",
        "👉 Drop your answer in the comments below! 👇\n",
        "#CurrentAffairs #ExamPrep #UPSC #SSC #Banking #PulseVector #KnowledgeCapsule"
    ])

    return "\n".join(post_lines)

def compile_capsule_video(capsule_data: Dict[str, Any], 
                          slide_paths: list, 
                          output_video_path: pathlib.Path, 
                          enable_tts: bool = True) -> pathlib.Path:
    """
    Compiles 1080x1920 vertical slides into an animated MP4 video short
    with smooth transitions, TTS voiceover, and background audio from samples/Audio/.
    """
    output_video_path = pathlib.Path(output_video_path)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_video_path.parent / "temp_capsule_video"
    temp_dir.mkdir(parents=True, exist_ok=True)

    raw_video = temp_dir / "raw_slides.mp4"
    voiceover_path = temp_dir / "capsule_voiceover.mp3"

    # 1. Slide timings
    slide_durations = [4.5, 7.5, 7.5, 7.5, 5.0]

    # 2. Compile video frames with transitions
    compile_images_with_transitions(
        thumbnail_path=slide_paths[0],
        daily_image_paths=slide_paths[1:],
        animated_frame_paths=[],
        output_path=raw_video,
        fps=30,
        transition_sec=0.5,
        per_slide_durations=slide_durations
    )

    # 3. Generate voiceover if TTS is enabled
    has_voice = False
    if enable_tts and HAS_TTS:
        script = (
            "Welcome to the Weekly Exam Blueprint by Pulse Vector. "
            "Here are the top three high-yield current affairs for your upcoming competitive exams. "
            "First, the BRICS 2026 New Delhi Declaration. India chaired the eighteenth summit at Bharat Mandapam, "
            "focusing on counter-terrorism and local currency trade settlement. "
            "Second, the BIMSTEC Delhi Declaration. Seven member nations strengthened regional security, "
            "anti-narcotics coordination, and transnational crime interdiction. "
            "Third, the e-Shram Portal completes five years, surpassing thirty-one crore registrations "
            "with over fifty-four percent women unorganised workers receiving portable welfare access. "
            "Now for your weekly exam challenge: Where is the permanent secretariat of BIMSTEC located? "
            "Drop your answer in the comments below!"
        )
        try:
            synthesize_text(script, voice="en-US-ChristopherNeural", rate="+10%", output_path=voiceover_path)
            if voiceover_path.exists() and voiceover_path.stat().st_size > 1000:
                has_voice = True
        except Exception as e:
            logging.warning(f"Voiceover synthesis failed, continuing with BGM only: {e}")

    # 4. Background music track
    bgm_track = get_random_audio_track()
    if not bgm_track or not bgm_track.exists():
        # Fallback to track_01.mp3
        sample_audio = ARCHIVE_DIR.parent / "samples" / "Audio" / "track_01.mp3"
        if sample_audio.exists():
            bgm_track = sample_audio

    # 5. Mux audio and video
    total_dur = sum(slide_durations)
    merge_audio_video(
        video_path=str(raw_video),
        audio_path=str(bgm_track),
        output_path=str(output_video_path),
        video_duration=total_dur,
        voiceover_path=str(voiceover_path) if has_voice else None
    )

    # Clean up temp raw video
    try:
        if raw_video.exists():
            raw_video.unlink()
        if voiceover_path.exists():
            voiceover_path.unlink()
        if temp_dir.exists() and not any(temp_dir.iterdir()):
            temp_dir.rmdir()
    except Exception:
        pass

    return output_video_path

def run_capsule_pipeline(target_date: Optional[datetime.datetime] = None, 
                         output_dir: Optional[pathlib.Path] = None,
                         generate_video: bool = False,
                         dry_run: bool = False) -> Dict[str, Any]:
    """
    Main entry point for running the knowledge capsule generation pipeline.
    """
    now = target_date or datetime.datetime.now()
    year_str = now.strftime("%Y")
    month_name = now.strftime("%B")
    day_str = now.strftime("%d%b%Y").lower()

    if output_dir is None:
        target_dir = ARCHIVE_DIR / year_str / month_name / "Weekly_Capsules"
    else:
        target_dir = pathlib.Path(output_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    capsule_slug = f"weekly_capsule_{day_str}"
    output_image_base = target_dir / capsule_slug
    post_text_file = target_dir / f"{capsule_slug}_post.txt"
    json_meta_file = target_dir / f"{capsule_slug}.json"
    output_video_file = target_dir / f"{capsule_slug}.mp4"

    logging.info(f"Generating Weekly Knowledge Capsule for {now.strftime('%d %B %Y')}...")

    # Load / Build capsule data
    capsule_data = get_sample_weekly_insights(week_date_str="12 October - 18 October 2026")

    if dry_run:
        logging.info(f"[DRY RUN] Would generate JPEG poster at: {output_image_base}.jpeg")
        logging.info(f"[DRY RUN] Would generate Social Post at: {post_text_file}")
        if generate_video:
            logging.info(f"[DRY RUN] Would compile MP4 video at: {output_video_file}")
        return {
            "status": "dry_run",
            "jpeg_path": str(output_image_base) + ".jpeg",
            "post_path": str(post_text_file),
            "video_path": str(output_video_file) if generate_video else None
        }

    # 1. Render JPEG & PNG Poster (High-Definition 1600px with chroma subsampling=0)
    renderer = CapsuleRenderer(width=1600)
    jpeg_result = renderer.render_capsule(capsule_data, output_image_base)
    logging.info(f"✅ Generated JPEG Capsule Poster: {jpeg_result}")

    # 2. Generate and write Social Post text
    social_text = generate_social_post(capsule_data)
    with open(post_text_file, "w", encoding="utf-8") as f:
        f.write(social_text)
    logging.info(f"✅ Generated Social Post Text: {post_text_file}")

    # 3. Save JSON metadata
    with open(json_meta_file, "w", encoding="utf-8") as f:
        json.dump(capsule_data, f, indent=2)
    logging.info(f"✅ Saved Capsule JSON Metadata: {json_meta_file}")

    # 4. Optional: Render Vertical Slides and Compile Video Short
    video_result_path = None
    if generate_video:
        slides_dir = target_dir / f"{capsule_slug}_slides"
        slide_paths = renderer.render_vertical_slides(capsule_data, slides_dir)
        video_result_path = compile_capsule_video(capsule_data, slide_paths, output_video_file, enable_tts=True)
        logging.info(f"✅ Compiled Capsule Video Short: {video_result_path}")

    return {
        "status": "success",
        "jpeg_path": str(jpeg_result),
        "png_path": str(output_image_base.with_suffix(".png")),
        "post_path": str(post_text_file),
        "json_path": str(json_meta_file),
        "video_path": str(video_result_path) if video_result_path else None,
        "post_text": social_text
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Vector Knowledge Capsule Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--video", action="store_true", help="Compile animated MP4 video short")
    parser.add_argument("--dry-run", action="store_true", help="Preview paths without rendering")
    parser.add_argument("--output-dir", type=str, help="Custom output directory")
    args = parser.parse_args()

    target_dt = datetime.datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
    out_dir = pathlib.Path(args.output_dir) if args.output_dir else None

    result = run_capsule_pipeline(target_date=target_dt, output_dir=out_dir, generate_video=args.video, dry_run=args.dry_run)
    print(f"\n[Capsule Pipeline Finished] Status: {result.get('status')}")
    if result.get("jpeg_path"):
        print(f"JPEG Poster: {result.get('jpeg_path')}")
    if result.get("post_path"):
        print(f"Post Text:   {result.get('post_path')}")
    if result.get("video_path"):
        print(f"MP4 Video:   {result.get('video_path')}")
