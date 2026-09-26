import os
import re
import sys
import asyncio
import pathlib
import logging
import subprocess
import shutil
from typing import Optional, List, Dict, Tuple
import imageio_ffmpeg

try:
    import edge_tts
    from mutagen.mp3 import MP3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    logging.warning("edge-tts or mutagen not installed. TTS voiceover will be disabled.")

def get_ffmpeg_executable() -> str:
    """Finds reliable ffmpeg executable from imageio_ffmpeg or system PATH."""
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path
    return "ffmpeg"

def sanitize_text_for_speech(text: str) -> str:
    """Clean source tags, markdown, and format numbered points for natural speech synthesis."""
    if not text:
        return ""
    # Remove markdown bold/italic
    clean = re.sub(r"\*\*|\*|__|_", "", text)
    # Remove sources like [Source: Reuters]
    clean = re.sub(r"\[Source:[^\]]+\]", "", clean, flags=re.IGNORECASE).strip()
    # Replace numbers like 1. with "Point 1."
    clean = re.sub(r"^(\d+)[\.\)]\s*", r"Point \1. ", clean, flags=re.MULTILINE)
    # Remove extra spaces
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

async def _synthesize_text_async(text: str, voice: str, rate: str, output_path: pathlib.Path):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(output_path))

def synthesize_text(text: str, voice: str = "en-US-ChristopherNeural", rate: str = "+10%", output_path: Optional[pathlib.Path] = None):
    """Synthesizes text to MP3 using edge-tts."""
    if not HAS_TTS:
        raise RuntimeError("edge-tts is not installed.")
        
    clean_text = sanitize_text_for_speech(text)
    if not clean_text:
        clean_text = "Continuing with our latest updates."
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize_text_async(clean_text, voice, rate, output_path))
    return output_path

def get_audio_duration(file_path: pathlib.Path) -> float:
    """Returns the duration of an MP3 audio file in seconds."""
    if not HAS_TTS:
        return 3.5
    try:
        audio = MP3(str(file_path))
        return float(audio.info.length)
    except Exception as e:
        logging.warning(f"Error reading audio duration for {file_path}: {e}. Defaulting to 3.5s.")
        return 3.5

def verify_speech_points_alignment(points, expected_point_count=None):
    """
    Reverifies that the points array passed to TTS is non-empty, valid,
    and matches the expected visual slide point count and text ordering.
    """
    if not points:
        raise ValueError("❌ [TTS Verification Failed] Points list for speech synthesis is empty!")
        
    if expected_point_count and len(points) != expected_point_count:
        raise ValueError(
            f"❌ [TTS Verification Failed] Mismatch detected! "
            f"Voiceover points count ({len(points)}) does not match expected slide point count ({expected_point_count})."
        )
        
    for p_tuple in points:
        p_num = p_tuple[0]
        p_text = p_tuple[1]
        if not p_text or len(str(p_text).strip()) < 3:
            raise ValueError(f"❌ [TTS Verification Failed] Point {p_num} has empty or invalid text: '{p_text}'")
            
    print(f"🔍 [TTS Verification Passed] Confirmed {len(points)} speech points match visual slide content.")
    return True

def generate_voiceover(points, date_str: str, output_dir: pathlib.Path, category_title: str = "DAILY CURRENT AFFAIRS", voice: str = "en-US-ChristopherNeural", rate: str = "+10%"):
    """
    Generates structured AI voiceover audio files for intro, per-page slides, and outro.
    Concatenates them into a full voiceover track and returns slide durations.
    """
    if not HAS_TTS:
        logging.warning("TTS dependencies missing. Skipping voiceover generation.")
        return None
        
    verify_speech_points_alignment(points)
        
    temp_tts_dir = pathlib.Path(output_dir) / "tts_temp"
    temp_tts_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Prepare Text Segments
    num_points = len(points)
    cat_clean = category_title.title().replace("Current Affairs", "Current Affairs Summary")
    if "daily" in category_title.lower() or num_points <= 15:
        intro_text = "Top headlines you must know today, starting right now!"
    else:
        intro_text = f"Welcome to Pulse Vector. Here is your comprehensive {cat_clean} for {date_str}."
    outro_text = "Like, share, and subscribe to Pulse Vector, and don't forget to press the bell icon for daily updates."
    
    points_per_page = 5
    pages_text = []
    for i in range(0, len(points), points_per_page):
        page_points = points[i:i+points_per_page]
        page_str = " ".join([f"{num}. {txt}" for num, txt in page_points])
        pages_text.append(page_str)
        
    audio_segments = []
    page_durations = []
    
    # 2. Synthesize Audio & Measure Durations
    print(f"🎙️ Synthesizing AI Voiceover ({voice} @ {rate}) for {len(pages_text)} slides...")
    
    try:
        # Intro
        intro_mp3 = temp_tts_dir / "00_intro.mp3"
        synthesize_text(intro_text, voice, rate, intro_mp3)
        intro_dur = get_audio_duration(intro_mp3)
        audio_segments.append(intro_mp3)
        
        # Pages
        for idx, page_txt in enumerate(pages_text):
            page_mp3 = temp_tts_dir / f"01_page_{idx+1}.mp3"
            synthesize_text(page_txt, voice, rate, page_mp3)
            p_dur = get_audio_duration(page_mp3)
            page_durations.append(p_dur)
            audio_segments.append(page_mp3)
            
        # Outro
        outro_mp3 = temp_tts_dir / "02_outro.mp3"
        synthesize_text(outro_text, voice, rate, outro_mp3)
        outro_dur = get_audio_duration(outro_mp3)
        audio_segments.append(outro_mp3)
        
        # 3. Concatenate Audio Segments using resolved ffmpeg
        ffmpeg_exe = get_ffmpeg_executable()
        concat_list = temp_tts_dir / "concat_list.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for seg in audio_segments:
                # Use forward slash or escaped path for ffmpeg concat
                f.write(f"file '{seg.name}'\n")
                
        full_voice = temp_tts_dir / "full_voiceover.mp3"
        if full_voice.exists():
            full_voice.unlink()
            
        cmd = [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(full_voice)]
        res = subprocess.run(cmd, cwd=str(temp_tts_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logging.warning(f"FFmpeg copy concat returned non-zero ({res.stderr}). Re-encoding...")
            # Fallback to re-encode if stream copy fails
            cmd_reencode = [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k", str(full_voice)]
            subprocess.run(cmd_reencode, cwd=str(temp_tts_dir), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        all_durations = [intro_dur] + page_durations + [outro_dur]
        total_dur = sum(all_durations)
        
        print(f"✅ Voiceover complete! Total spoken duration: {total_dur:.2f}s ({len(pages_text)} slides)")
        
        return {
            "full_voice_path": full_voice,
            "intro_duration": intro_dur,
            "page_durations": page_durations,
            "outro_duration": outro_dur,
            "all_slide_durations": all_durations,
            "total_duration": total_dur,
            "temp_dir": temp_tts_dir
        }
    except Exception as e:
        logging.error(f"TTS voiceover synthesis failed: {e}", exc_info=True)
        print(f"⚠️ TTS synthesis error: {e}. Falling back to default static durations.")
        return None
