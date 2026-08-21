import os
import re
import math
import shutil
import logging
import random
import datetime
import subprocess
import pathlib
from typing import List, Optional, Tuple
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

def generate_thumbnail_slide_image(date_obj: datetime.datetime, font_bold_path: pathlib.Path, font_regular_path: pathlib.Path, output_path: pathlib.Path, category_name: str = "DAILY"):
    logging.info(f"Generating dynamic thumbnail slide for: {date_obj} (Category: {category_name})")
    W, H = 1080, 1920
    
    image = create_base_background_with_glow(W, H, t=0.0)
    draw_watermark_on_image(image, font_bold_path)
    
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(card)
    card_box = [(80, 400), (1000, 1520)]
    draw_card.rounded_rectangle(
        card_box,
        radius=40,
        fill=(15, 23, 42, 165),
        outline=(255, 255, 255, 35),
        width=2
    )
    image.alpha_composite(card)
    
    try:
        font_logo = ImageFont.truetype(str(font_bold_path), 26)
        font_sublogo = ImageFont.truetype(str(font_regular_path), 36)
        font_title = ImageFont.truetype(str(font_bold_path), 72)
        font_size_date = 46 if category_name == "WEEKLY" else 54
        font_date = ImageFont.truetype(str(font_bold_path), font_size_date)
    except Exception:
        font_logo = font_sublogo = font_title = font_date = ImageFont.load_default()
    
    draw = ImageDraw.Draw(image)
    draw.text((140, 215), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
    
    cx = 540
    cat_label = category_name.upper().strip()
    draw_text_with_shadow_helper(draw, cat_label, cx, 660, font_sublogo, text_color=(56, 189, 248, 200))
    draw_text_with_shadow_helper(draw, "CURRENT AFFAIRS", cx, 780, font_title, text_color=(255, 255, 255, 255))
    draw.line([(240, 890), (840, 890)], fill=(255, 255, 255, 35), width=2)
    
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

def generate_animated_end_slide_frames_pipeline(font_bold_path: pathlib.Path, font_regular_path: pathlib.Path, output_dir: pathlib.Path, fps: int = 10, duration: float = 3.0) -> List[pathlib.Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    W, H = 1080, 1920
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
        card_box = [(80, 300), (1000, 1620)]
        draw_card.rounded_rectangle(
            card_box,
            radius=40,
            fill=(15, 23, 42, 165),
            outline=(255, 255, 255, 35),
            width=2
        )
        image.alpha_composite(card)
        
        bell_angle = 18 * math.sin(2 * math.pi * 3.0 * t)
        bell_icon = draw_bell_icon_image(300, 300, bell_angle)
        image.paste(bell_icon, (390, 400), bell_icon)
        
        alpha = min(255, int((i / 12.0) * 255))
        text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        cx = 540
        draw_text_with_shadow_helper(text_draw, "Like, Share & Subscribe", cx, 800, font_bold_title, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(255, 255, 255, alpha))
        draw_text_with_shadow_helper(text_draw, "(Press the Bell Icon)", cx, 890, font_regular_sub, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(56, 189, 248, alpha))
        text_draw.line([(240, 960), (840, 960)], fill=(255, 255, 255, int(0.15 * alpha)), width=2)
        
        desc_lines = [
            "to get up to date with all global",
            "current affairs in no time."
        ]
        for idx, line in enumerate(desc_lines):
            draw_text_with_shadow_helper(text_draw, line, cx, 1040 + (idx * 55), font_body, shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(229, 231, 235, alpha))
            
        draw_text_with_shadow_helper(text_draw, "P U L S E   V E C T O R", 140, 215, font_logo, shadow_color=(0, 0, 0, 50), text_color=(255, 255, 255, 80), anchor="la")
        
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
