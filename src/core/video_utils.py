import os
import re
import math
import wave
import struct
import shutil
import logging
import random
import datetime
import subprocess
import pathlib
from typing import List, Optional, Tuple, Dict, Any
import cv2
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .config import ARCHIVE_DIR
from .tts_utils import get_ffmpeg_executable

def download_audio_library():
    audio_dir = ARCHIVE_DIR.parent / "samples" / "Audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
        
    logging.info("Checking background music assets (15 open-source copyright-free tracks)...")
    ffmpeg_exe = get_ffmpeg_executable()
    
    chord_presets = [
        "0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(261.63*2*PI*t)*(1+0.1*sin(2*PI*0.3*t))+0.03*sin(329.63*2*PI*t)+0.02*sin(440*2*PI*t)",
        "0.04*sin(130.81*2*PI*t)+0.03*sin(196.00*2*PI*t)*(1+0.1*sin(2*PI*0.4*t))+0.03*sin(329.63*2*PI*t)+0.02*sin(392.00*2*PI*t)",
        "0.04*sin(174.61*2*PI*t)+0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(261.63*2*PI*t)+0.02*sin(349.23*2*PI*t)",
        "0.04*sin(196.00*2*PI*t)+0.03*sin(246.94*2*PI*t)*(1+0.1*sin(2*PI*0.3*t))+0.03*sin(293.66*2*PI*t)+0.02*sin(392.00*2*PI*t)",
        "0.04*sin(146.83*2*PI*t)+0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.4*t))+0.03*sin(349.23*2*PI*t)+0.02*sin(293.66*2*PI*t)",
        "0.04*sin(164.81*2*PI*t)+0.03*sin(246.94*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(392.00*2*PI*t)+0.02*sin(329.63*2*PI*t)",
        "0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.4*t))+0.03*sin(246.94*2*PI*t)+0.03*sin(329.63*2*PI*t)+0.02*sin(440*2*PI*t)",
        "0.04*sin(130.81*2*PI*t)+0.03*sin(164.81*2*PI*t)*(1+0.1*sin(2*PI*0.3*t))+0.03*sin(196.00*2*PI*t)+0.02*sin(246.94*2*PI*t)",
        "0.04*sin(174.61*2*PI*t)+0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(261.63*2*PI*t)+0.02*sin(329.63*2*PI*t)",
        "0.04*sin(196.00*2*PI*t)+0.03*sin(261.63*2*PI*t)*(1+0.1*sin(2*PI*0.4*t))+0.03*sin(293.66*2*PI*t)+0.02*sin(392.00*2*PI*t)",
        "0.04*sin(123.47*2*PI*t)+0.03*sin(185.00*2*PI*t)*(1+0.1*sin(2*PI*0.3*t))+0.03*sin(293.66*2*PI*t)+0.02*sin(246.94*2*PI*t)",
        "0.04*sin(155.56*2*PI*t)+0.03*sin(196.00*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(233.08*2*PI*t)+0.02*sin(311.13*2*PI*t)",
        "0.04*sin(207.65*2*PI*t)+0.03*sin(261.63*2*PI*t)*(1+0.1*sin(2*PI*0.4*t))+0.03*sin(311.13*2*PI*t)+0.02*sin(415.30*2*PI*t)",
        "0.04*sin(233.08*2*PI*t)+0.03*sin(293.66*2*PI*t)*(1+0.1*sin(2*PI*0.3*t))+0.03*sin(349.23*2*PI*t)+0.02*sin(466.16*2*PI*t)",
        "0.04*sin(146.83*2*PI*t)+0.03*sin(220*2*PI*t)*(1+0.1*sin(2*PI*0.5*t))+0.03*sin(329.63*2*PI*t)+0.02*sin(293.66*2*PI*t)"
    ]

    for i in range(1, 16):
        file_name = f"track_{i:02d}.mp3"
        file_path = audio_dir / file_name
        if not file_path.exists():
            preset_expr = chord_presets[(i - 1) % len(chord_presets)]
            cmd = [
                ffmpeg_exe, "-y",
                "-f", "lavfi",
                "-i", f"aevalsrc={preset_expr}:s=44100:d=120",
                "-af", "lowpass=f=1000,afade=t=in:ss=0:d=2,afade=t=out:st=118:d=2",
                "-c:a", "mp3",
                "-b:a", "192k",
                str(file_path)
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except Exception as e:
                logging.warning(f"Failed to generate synthetic track {i}: {e}")

def get_random_audio_track() -> Optional[pathlib.Path]:
    audio_dir = ARCHIVE_DIR.parent / "samples" / "Audio"
    if not audio_dir.exists():
        return None
    mp3_files = list(audio_dir.glob("*.mp3"))
    if not mp3_files:
        return None
    return random.choice(mp3_files)

def merge_audio_video(video_path: str, audio_path: str, output_path: str, video_duration: Optional[float] = None, voiceover_path: Optional[str] = None):
    logging.info(f"Muxing background audio '{os.path.basename(audio_path)}' into video...")
    ffmpeg_exe = get_ffmpeg_executable()
    
    if not video_duration:
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if frame_count > 0 and fps > 0:
                video_duration = frame_count / fps
            cap.release()
        if not video_duration:
            video_duration = 10.0
            
    st_fade = max(0.0, video_duration - 1.0)
    
    if voiceover_path and os.path.exists(voiceover_path):
        logging.info(f"Muxing AI voiceover '{os.path.basename(voiceover_path)}' with background audio...")
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(video_path),
            "-i", str(voiceover_path),
            "-i", str(audio_path),
            "-filter_complex", f"[2:a]volume=0.10,afade=t=out:st={st_fade}:d=1.0[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path)
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", f"[1:a]volume=0.35,afade=t=out:st={st_fade}:d=1.0[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path)
        ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    logging.info(f"Finalized video with audio generated: {output_path}")

def generate_countdown_sfx(output_wav: pathlib.Path, total_duration: float = 10.0, tick_interval: float = 1.0, stop_at: float = 8.0) -> pathlib.Path:
    """
    Procedurally synthesizes high-quality countdown clock ticking and resonant bell chime.
    Standard 16-bit 44.1kHz stereo PCM. Completely offline and asset-free.
    """
    sample_rate = 44100
    total_samples = int(sample_rate * total_duration)
    output_path = pathlib.Path(output_wav)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    samples = [0.0] * total_samples
    
    # 1. 1-second interval clock ticks up to stop_at
    tick_times = [i * tick_interval for i in range(1, int(stop_at) + 1)]
    for t_sec in tick_times:
        start_idx = int(t_sec * sample_rate)
        tick_duration = 0.04  # 40ms click
        tick_samples_count = int(tick_duration * sample_rate)
        for j in range(tick_samples_count):
            idx = start_idx + j
            if idx < total_samples:
                t_rel = j / sample_rate
                click = (math.sin(2 * math.pi * 1200 * t_rel) * 0.7 + 
                         math.sin(2 * math.pi * 2400 * t_rel) * 0.3)
                decay = math.exp(-t_rel * 90)
                samples[idx] += click * decay * 0.8
                
    # 2. Resonant Bell Chime at stop_at
    chime_start_idx = int(stop_at * sample_rate)
    chime_duration = 1.8  # 1.8s decay
    chime_samples_count = int(chime_duration * sample_rate)
    for j in range(chime_samples_count):
        idx = chime_start_idx + j
        if idx < total_samples:
            t_rel = j / sample_rate
            bell = (math.sin(2 * math.pi * 1568 * t_rel) * 0.5 +
                    math.sin(2 * math.pi * 3136 * t_rel) * 0.3 +
                    math.sin(2 * math.pi * 4704 * t_rel) * 0.15)
            decay = math.exp(-t_rel * 3.5)
            samples[idx] += bell * decay * 0.75
            
    with wave.open(str(output_path), 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            val = int(clamped * 32767)
            frames.extend(struct.pack('<hh', val, val))
        wf.writeframes(frames)
        
    return output_path

def merge_brainteaser_audio(
    video_path: str,
    voiceover_path: Optional[str],
    sfx_path: Optional[str],
    bg_music_path: Optional[str],
    output_path: str,
    total_duration: float = 10.0
):
    """
    Mixes voiceover, SFX ticks/chime, and background music onto a Brain Teaser Short.
    Applies audio ducking and automatic fallbacks if voiceover or music is absent.
    """
    ffmpeg_exe = get_ffmpeg_executable()
    has_vo = voiceover_path and os.path.exists(voiceover_path)
    has_sfx = sfx_path and os.path.exists(sfx_path)
    has_bg = bg_music_path and os.path.exists(bg_music_path)
    
    st_fade = max(0.0, total_duration - 1.0)
    
    inputs = ["-i", str(video_path)]
    filter_parts = []
    audio_labels = []
    
    in_idx = 1
    if has_vo:
        inputs.extend(["-i", str(voiceover_path)])
        filter_parts.append(f"[{in_idx}:a]volume=1.0[vo]")
        audio_labels.append("[vo]")
        in_idx += 1
        
    if has_sfx:
        inputs.extend(["-i", str(sfx_path)])
        filter_parts.append(f"[{in_idx}:a]volume=0.85[sfx]")
        audio_labels.append("[sfx]")
        in_idx += 1
        
    if has_bg:
        inputs.extend(["-i", str(bg_music_path)])
        bg_vol = 0.18 if (has_vo or has_sfx) else 0.35
        filter_parts.append(f"[{in_idx}:a]volume={bg_vol},afade=t=out:st={st_fade}:d=1.0[bg]")
        audio_labels.append("[bg]")
        in_idx += 1
        
    if not audio_labels:
        shutil.copy(str(video_path), str(output_path))
        return
        
    if len(audio_labels) == 1:
        final_audio = audio_labels[0]
        filter_complex = filter_parts[0]
    else:
        mix_inputs = "".join(audio_labels)
        filter_parts.append(f"{mix_inputs}amix=inputs={len(audio_labels)}:duration=longest:dropout_transition=0,atrim=0:{total_duration},apad=whole_dur={total_duration}[a]")
        final_audio = "[a]"
        filter_complex = ";".join(filter_parts)
        
    cmd = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", final_audio,
        "-t", str(total_duration),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logging.error(f"FFmpeg Brain Teaser audio merge error: {result.stderr}")
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    logging.info(f"Finalized Brain Teaser Short with multi-track audio: {output_path}")

def format_date_custom(dt: datetime.datetime) -> str:
    day = str(dt.day)
    mon = dt.strftime("%b").upper()
    year = str(dt.year)
    return f"{day} {mon} {year}"

def create_base_background_with_glow(W: int, H: int, t: float = 0.0) -> Image.Image:
    image = Image.new("RGBA", (W, H), (3, 7, 18, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    
    cyan_dx = int(40 * math.sin(2 * math.pi * 0.1 * t))
    cyan_dy = int(40 * math.cos(2 * math.pi * 0.1 * t))
    
    violet_dx = int(50 * math.cos(2 * math.pi * 0.08 * t))
    violet_dy = int(50 * math.sin(2 * math.pi * 0.08 * t))
    
    magenta_dx = int(40 * math.sin(2 * math.pi * 0.12 * t))
    magenta_dy = int(40 * math.cos(2 * math.pi * 0.12 * t))
    
    draw_glow.ellipse([(-200 + cyan_dx, -200 + cyan_dy), (600 + cyan_dx, 600 + cyan_dy)], fill=(6, 182, 212, 90))
    draw_glow.ellipse([(600 + violet_dx, 700 + violet_dy), (1400 + violet_dx, 1500 + violet_dy)], fill=(124, 58, 237, 75))
    draw_glow.ellipse([(-300 + magenta_dx, 1400 + magenta_dy), (500 + magenta_dx, 2200 + magenta_dy)], fill=(217, 70, 239, 85))
    
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(200))
    image.alpha_composite(blurred_glow)
    return image

def draw_watermark_on_image(image: Image.Image, font_bold_path: pathlib.Path):
    watermark_canvas = Image.new("RGBA", (2200, 2200), (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_canvas)
    try:
        font_watermark = ImageFont.truetype(str(font_bold_path), 150)
    except Exception:
        font_watermark = ImageFont.load_default()
    watermark_draw.text((1100, 1100), "PULSE VECTOR", font=font_watermark, fill=(255, 255, 255, 6), anchor="mm")
    rotated_watermark = watermark_canvas.rotate(40, resample=Image.BICUBIC)
    image.paste(rotated_watermark, (-560, -140), rotated_watermark)

def draw_text_with_shadow_helper(draw, text, x, y, font, shadow_color=(0, 0, 0, 180), text_color=(255, 255, 255, 255), offset=(2, 2), anchor="mm"):
    if shadow_color:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)

def generate_thumbnail_slide_image(
    date_obj: datetime.datetime,
    font_bold_path: pathlib.Path,
    font_regular_path: pathlib.Path,
    output_path: pathlib.Path,
    category_name: str = "DAILY",
    headline_hook: Optional[str] = None,
    aspect_ratio: str = "9:16"
):
    logging.info(f"Generating dynamic thumbnail slide for: {date_obj} (Category: {category_name}, Aspect: {aspect_ratio})")
    is_widescreen = (aspect_ratio == "16:9")
    W, H = (1920, 1080) if is_widescreen else (1080, 1920)
    cx = 960 if is_widescreen else 540
    
    image = create_base_background_with_glow(W, H, t=0.0)
    draw_watermark_on_image(image, font_bold_path)
    
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(card)
    card_box = [(80, 60), (1840, 1020)] if is_widescreen else [(80, 360), (1000, 1560)]
    draw_card.rounded_rectangle(
        card_box,
        radius=35 if is_widescreen else 40,
        fill=(15, 23, 42, 175),
        outline=(255, 255, 255, 35),
        width=2
    )
    image.alpha_composite(card)
    
    try:
        font_logo = ImageFont.truetype(str(font_bold_path), 26)
        font_sublogo = ImageFont.truetype(str(font_regular_path), 36)
        font_title = ImageFont.truetype(str(font_bold_path), 56 if is_widescreen else 68)
        font_size_date = 42 if category_name == "WEEKLY" else 48
        font_date = ImageFont.truetype(str(font_bold_path), font_size_date)
        font_hook_title = ImageFont.truetype(str(font_bold_path), 48)
        font_micro = ImageFont.truetype(str(font_bold_path), 28)
    except Exception:
        font_logo = font_sublogo = font_title = font_date = font_hook_title = font_micro = ImageFont.load_default()
    
    draw = ImageDraw.Draw(image)
    logo_x, logo_y = (120, 95) if is_widescreen else (140, 215)
    draw.text((logo_x, logo_y), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
    
    cat_label = category_name.upper().strip()
    
    # Format date string
    if category_name == "WEEKLY":
        week_start = date_obj - datetime.timedelta(days=6)
        if week_start.year != date_obj.year:
            formatted_date_str = f"{week_start.strftime('%d %b %Y')} to {date_obj.strftime('%d %b %Y')}".upper()
        else:
            formatted_date_str = f"{week_start.strftime('%d %b')} to {date_obj.strftime('%d %b %Y')}".upper()
    elif category_name == "MONTHLY":
        formatted_date_str = date_obj.strftime("%B %Y").upper()
    else:
        formatted_date_str = format_date_custom(date_obj)
        
    if is_widescreen:
        # 16:9 Widescreen Masterclass Layout
        badge_y = 220
        draw.rounded_rectangle([(cx - 360, badge_y), (cx + 360, badge_y + 54)], radius=27, fill=(56, 189, 248, 30), outline=(56, 189, 248, 180), width=2)
        draw_text_with_shadow_helper(draw, f"⚡ {cat_label} CURRENT AFFAIRS MASTERCLASS", cx, badge_y + 27, font_sublogo, text_color=(56, 189, 248, 255))
        
        draw_text_with_shadow_helper(draw, "COMPREHENSIVE REVISION", cx, 370, font_title, text_color=(255, 255, 255, 255))
        draw.line([(cx - 480, 440), (cx + 480, 440)], fill=(255, 255, 255, 35), width=2)
        draw_text_with_shadow_helper(draw, formatted_date_str, cx, 520, font_date, text_color=(251, 191, 36, 255))
        
        # Micro callout card
        draw.rounded_rectangle([(cx - 420, 620), (cx + 420, 720)], radius=20, fill=(30, 41, 59, 140), outline=(255, 255, 255, 30), width=1)
        draw_text_with_shadow_helper(draw, "🔥 FULL EXAM SYLLABUS COVERAGE & KEY TAKEAWAYS", cx, 670, font_micro, text_color=(229, 231, 235, 255))
        
        # Bottom CTA Pill
        draw.rounded_rectangle([(cx - 320, 800), (cx + 320, 860)], radius=25, fill=(15, 23, 42, 220), outline=(56, 189, 248, 120), width=1)
        draw_text_with_shadow_helper(draw, "▶ WATCH COMPLETE MASTERCLASS", cx, 830, font_micro, text_color=(56, 189, 248, 230))
    elif headline_hook and category_name == "DAILY":
        # --- High-Retention Headline Hook Layout ---
        # 1. Top Urgent Category Badge
        badge_y = 440
        draw.rounded_rectangle([(180, badge_y), (900, badge_y + 60)], radius=30, fill=(245, 158, 11, 40), outline=(245, 158, 11, 200), width=2)
        draw_text_with_shadow_helper(draw, "⚡ TOP STORIES TODAY", cx, badge_y + 30, font_sublogo, text_color=(251, 191, 36, 255))
        
        # 2. Date Subtitle
        draw_text_with_shadow_helper(draw, formatted_date_str, cx, 560, font_date, text_color=(148, 163, 184, 255))
        draw.line([(240, 630), (840, 630)], fill=(255, 255, 255, 30), width=2)
        
        # 3. Breaking Headline Preview Card
        preview_box = [(120, 680), (960, 1380)]
        draw.rounded_rectangle(preview_box, radius=25, fill=(30, 41, 59, 140), outline=(56, 189, 248, 90), width=2)
        
        # Micro pill: STORY #1
        draw.rounded_rectangle([(160, 720), (380, 770)], radius=15, fill=(239, 68, 68, 220))
        draw_text_with_shadow_helper(draw, "🔥 STORY #1", 270, 745, font_micro, text_color=(255, 255, 255, 255))
        
        # Clean and wrap the headline text
        clean_headline = re.sub(r"^[\d\.\-\s]+", "", headline_hook).strip()
        from .content_parser import clean_markdown_decorations
        clean_headline = clean_markdown_decorations(clean_headline)
        
        from .image_utils import wrap_text
        lines = wrap_text(clean_headline, font_hook_title, max_width=760)
        curr_y = 830
        for line in lines[:5]:
            draw_text_with_shadow_helper(draw, line, cx, curr_y, font_hook_title, text_color=(255, 255, 255, 255))
            curr_y += 65
            
        # 4. Bottom Call-To-Action Pill
        draw.rounded_rectangle([(240, 1440), (840, 1500)], radius=25, fill=(15, 23, 42, 220), outline=(255, 255, 255, 30), width=1)
        draw_text_with_shadow_helper(draw, "▶ WATCH COMPLETE DAILY BRIEFING", cx, 1470, font_micro, text_color=(56, 189, 248, 230))
    else:
        # Standard Classic Title Card
        draw_text_with_shadow_helper(draw, cat_label, cx, 660, font_sublogo, text_color=(56, 189, 248, 200))
        draw_text_with_shadow_helper(draw, "CURRENT AFFAIRS", cx, 780, font_title, text_color=(255, 255, 255, 255))
        draw.line([(240, 890), (840, 890)], fill=(255, 255, 255, 35), width=2)
        draw_text_with_shadow_helper(draw, formatted_date_str, cx, 1000, font_date, text_color=(251, 191, 36, 255))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")

def draw_bell_icon_image(W_bell: int, H_bell: int, angle: float) -> Image.Image:
    bell_img = Image.new("RGBA", (W_bell, H_bell), (0, 0, 0, 0))
    bell_draw = ImageDraw.Draw(bell_img)
    
    clapper_offset = int(5 * math.sin(math.radians(angle * 3)))
    bell_draw.ellipse([(135 + clapper_offset, 205), (165 + clapper_offset, 235)], fill=(251, 191, 36, 255))
    bell_draw.ellipse([(135, 35), (165, 65)], outline=(255, 255, 255, 255), width=6)
    
    body_points = [
        (135, 60), (165, 60),
        (170, 100), (195, 160), (220, 195),
        (80, 195), (105, 160), (130, 100)
    ]
    bell_draw.polygon(body_points, fill=(255, 255, 255, 255))
    bell_draw.rounded_rectangle([(72, 190), (228, 205)], radius=7, fill=(255, 255, 255, 255))
    
    rotated_bell = bell_img.rotate(angle, resample=Image.BICUBIC)
    return rotated_bell

def generate_animated_end_slide_frames_pipeline(
    font_bold_path: pathlib.Path,
    font_regular_path: pathlib.Path,
    output_dir: pathlib.Path,
    fps: int = 10,
    duration: float = 3.0,
    aspect_ratio: str = "9:16"
) -> List[pathlib.Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    is_widescreen = (aspect_ratio == "16:9")
    W, H = (1920, 1080) if is_widescreen else (1080, 1920)
    cx = 960 if is_widescreen else 540
    total_frames = int(fps * duration)
    
    try:
        font_bold_title = ImageFont.truetype(str(font_bold_path), 56)
        font_regular_sub = ImageFont.truetype(str(font_regular_path), 38)
        font_body = ImageFont.truetype(str(font_regular_path), 32)
        font_logo = ImageFont.truetype(str(font_bold_path), 26)
    except Exception:
        font_bold_title = font_regular_sub = font_body = font_logo = ImageFont.load_default()
    
    frame_paths = []
    
    for i in range(total_frames):
        t = i / fps
        image = create_base_background_with_glow(W, H, t=t)
        draw_watermark_on_image(image, font_bold_path)
        
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(card)
        card_box = [(80, 50), (1840, 1030)] if is_widescreen else [(80, 300), (1000, 1620)]
        draw_card.rounded_rectangle(
            card_box,
            radius=35 if is_widescreen else 40,
            fill=(15, 23, 42, 165),
            outline=(255, 255, 255, 35),
            width=2
        )
        image.alpha_composite(card)
        
        bell_angle = 18 * math.sin(2 * math.pi * 3.0 * t)
        bell_icon = draw_bell_icon_image(300, 300, bell_angle)
        bell_x = (cx - 150) if is_widescreen else 390
        bell_y = 120 if is_widescreen else 400
        image.paste(bell_icon, (bell_x, bell_y), bell_icon)
        
        alpha = min(255, int((i / 12.0) * 255))
        text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        title_y = 450 if is_widescreen else 800
        sub_y = 530 if is_widescreen else 890
        line_y = 590 if is_widescreen else 960
        desc_start_y = 640 if is_widescreen else 1040
        
        draw_text_with_shadow_helper(text_draw, "Like, Share & Subscribe", cx, title_y, font_bold_title, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(255, 255, 255, alpha))
        draw_text_with_shadow_helper(text_draw, "(Press the Bell Icon)", cx, sub_y, font_regular_sub, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(56, 189, 248, alpha))
        line_x1 = (cx - 360) if is_widescreen else 240
        line_x2 = (cx + 360) if is_widescreen else 840
        text_draw.line([(line_x1, line_y), (line_x2, line_y)], fill=(255, 255, 255, int(0.15 * alpha)), width=2)
        
        desc_lines = [
            "Which story was biggest today?",
            "Drop your perspective below! 👇"
        ]
        for idx, line in enumerate(desc_lines):
            draw_text_with_shadow_helper(text_draw, line, cx, desc_start_y + (idx * 50), font_body, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(229, 231, 235, alpha))
            
        logo_x, logo_y = (120, 85) if is_widescreen else (140, 215)
        draw_text_with_shadow_helper(text_draw, "P U L S E   V E C T O R", logo_x, logo_y, font_logo, shadow_color=(0, 0, 0, 50), text_color=(255, 255, 255, 80), anchor="la")
        
        image.alpha_composite(text_layer)
        
        frame_path = output_dir / f"frame_{i:03d}.png"
        image.convert("RGB").save(frame_path, "PNG")
        frame_paths.append(frame_path)
        
    return frame_paths

def create_transition_frames(img1, img2, num_transition_frames: int = 10, transition_type: str = "slide_left"):
    h, w, c = img1.shape
    frames = []
    
    for i in range(1, num_transition_frames + 1):
        alpha = i / float(num_transition_frames + 1)
        if transition_type == "fade":
            frame = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
        elif transition_type == "slide_left":
            shift = int(w * alpha)
            frame = np.zeros_like(img1)
            frame[:, 0:w - shift] = img1[:, shift:w]
            frame[:, w - shift:w] = img2[:, 0:shift]
        elif transition_type == "zoom_fade":
            scale = 1.0 + (0.15 * alpha)
            scaled_w, scaled_h = int(w * scale), int(h * scale)
            resized1 = cv2.resize(img1, (scaled_w, scaled_h))
            crop_x = (scaled_w - w) // 2
            crop_y = (scaled_h - h) // 2
            cropped1 = resized1[crop_y:crop_y + h, crop_x:crop_x + w]
            frame = cv2.addWeighted(cropped1, 1 - alpha, img2, alpha, 0)
        else:
            frame = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
        frames.append(frame)
        
    return frames

def compile_images_with_transitions(
    thumbnail_path: pathlib.Path,
    daily_image_paths: List[pathlib.Path],
    animated_frame_paths: List[pathlib.Path],
    output_path: pathlib.Path,
    duration_per_slide: float = 3.5,
    fps: int = 30,
    transition_sec: float = 0.5,
    per_slide_durations: Optional[List[float]] = None
):
    all_images_paths = [thumbnail_path] + list(daily_image_paths)
    loaded_imgs = []
    
    first_img = cv2.imread(str(thumbnail_path))
    if first_img is None:
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")
    h, w, _ = first_img.shape
    
    for p in all_images_paths:
        img = cv2.imread(str(p))
        if img is None:
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        loaded_imgs.append(img)
        
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    
    transitions = ["slide_left", "zoom_fade", "fade"]
    transition_frames_count = int(transition_sec * fps)
    
    for idx, current_img in enumerate(loaded_imgs):
        if per_slide_durations and idx < len(per_slide_durations):
            dur = per_slide_durations[idx]
            static_frames_count = max(1, int((dur - transition_sec) * fps))
        else:
            static_frames_count = max(1, int((duration_per_slide - transition_sec) * fps))
            
        for _ in range(static_frames_count):
            out.write(current_img)
            
        if idx < len(loaded_imgs) - 1:
            next_img = loaded_imgs[idx + 1]
            t_type = transitions[idx % len(transitions)]
            t_frames = create_transition_frames(current_img, next_img, transition_frames_count, t_type)
            for f in t_frames:
                out.write(f)
                
    if animated_frame_paths:
        if per_slide_durations and len(per_slide_durations) > len(loaded_imgs):
            outro_dur = per_slide_durations[-1]
            audio_frames = round(outro_dur * fps)
            num_anim_frames = len(animated_frame_paths)
            last_img = None
            for i in range(audio_frames):
                if i < num_anim_frames:
                    img = cv2.imread(str(animated_frame_paths[i]))
                    if img is not None:
                        if img.shape[0] != h or img.shape[1] != w:
                            img = cv2.resize(img, (w, h))
                        last_img = img
                if last_img is not None:
                    out.write(last_img)
        else:
            for frame_path in animated_frame_paths:
                img = cv2.imread(str(frame_path))
                if img is None:
                    continue
                if img.shape[0] != h or img.shape[1] != w:
                    img = cv2.resize(img, (w, h))
                out.write(img)
        
    out.release()

def compile_images_to_video_enhanced(
    thumbnail_path: pathlib.Path,
    daily_image_paths: List[pathlib.Path],
    animated_frame_paths: List[pathlib.Path],
    output_path: str,
    duration_per_static: float = 3.0,
    fps: int = 10,
    use_transitions: bool = True,
    per_slide_durations: Optional[List[float]] = None
):
    if use_transitions:
        compile_images_with_transitions(
            thumbnail_path, daily_image_paths, animated_frame_paths, pathlib.Path(output_path),
            duration_per_slide=duration_per_static, fps=30, transition_sec=0.5,
            per_slide_durations=per_slide_durations
        )
        return

    first_img = cv2.imread(str(thumbnail_path))
    if first_img is None:
        raise FileNotFoundError(f"Failed to read thumbnail image: {thumbnail_path}")
    h, w, c = first_img.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    
    frames_per_static = int(duration_per_static * fps)
    img = cv2.imread(str(thumbnail_path))
    for _ in range(frames_per_static):
        out.write(img)
        
    for img_path in daily_image_paths:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        for _ in range(frames_per_static):
            out.write(img)
            
    for frame_path in animated_frame_paths:
        img = cv2.imread(str(frame_path))
        if img is None:
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        out.write(img)
        
    out.release()

def compute_word_timings(text: str, total_duration: float, start_offset: float = 0.0) -> List[Dict[str, Any]]:
    """
    Calculates precise start and end timestamps for each word in text
    proportional to character lengths across total_duration.
    """
    words = [w.strip() for w in text.split() if w.strip()]
    if not words or total_duration <= 0:
        return []
    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        total_chars = len(words)
        
    cur_time = start_offset
    timings = []
    for w in words:
        w_dur = (len(w) / total_chars) * total_duration
        timings.append({
            "word": w,
            "start": cur_time,
            "end": cur_time + w_dur
        })
        cur_time += w_dur
    return timings

def render_karaoke_subtitle_overlay(
    draw: ImageDraw.ImageDraw,
    current_time: float,
    word_timings: List[Dict[str, Any]],
    font_subtitle: ImageFont.ImageFont,
    center_x: int = 540,
    pos_y: int = 1380,
    words_per_group: int = 4,
    active_color: Tuple[int, int, int] = (250, 204, 21),
    passive_color: Tuple[int, int, int] = (255, 255, 255),
    border_pulse: bool = True
) -> bool:
    """
    Renders an animated glowing karaoke caption box on the frame if current_time falls
    within word timings. Returns True if subtitle was rendered, False otherwise.
    """
    if not word_timings:
        return False
        
    groups = [word_timings[i:i + words_per_group] for i in range(0, len(word_timings), words_per_group)]
    
    active_group = None
    for g in groups:
        if g[0]["start"] <= current_time <= g[-1]["end"] + 0.25:
            active_group = g
            break
            
    if not active_group:
        return False
        
    word_widths = [draw.textlength(w["word"] + " ", font=font_subtitle) for w in active_group]
    tot_w = sum(word_widths)
    start_x = center_x - tot_w // 2
    
    pw = tot_w + 50
    ph = 72
    pulse_alpha = int(140 + 60 * math.sin(current_time * 8.0)) if border_pulse else 160
    border_col = (*active_color[:3], pulse_alpha)
    
    draw.rounded_rectangle(
        [center_x - pw // 2, pos_y - ph // 2, center_x + pw // 2, pos_y + ph // 2],
        radius=22,
        fill=(15, 23, 42, 225),
        outline=border_col,
        width=2
    )
    
    cur_x = start_x
    for w_obj in active_group:
        w_text = w_obj["word"]
        is_active = w_obj["start"] <= current_time <= w_obj["end"]
        color = active_color if is_active else passive_color
        draw.text((cur_x + 2, pos_y + 2), w_text, font=font_subtitle, fill=(0, 0, 0, 180), anchor="lm")
        draw.text((cur_x, pos_y), w_text, font=font_subtitle, fill=color, anchor="lm")
        cur_x += draw.textlength(w_text + " ", font=font_subtitle)
        
    return True
