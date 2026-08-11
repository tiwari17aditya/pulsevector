import os
import re
import sys
import cv2
import math
import shutil
import random
import pathlib
import datetime
import requests
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding issues with emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup paths
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
ARCHIVE_DIR = PROJECT_ROOT / "pulse_archive"
POC_DIR = PROJECT_ROOT / "POC"

FONT_BOLD = FONTS_DIR / "Roboto-Bold.ttf"
FONT_REGULAR = FONTS_DIR / "Roboto-Regular.ttf"

def format_date_custom(dt):
    # E.g., 3 Jan 2026 or 17 Jun 2026
    day = str(dt.day)
    mon = dt.strftime("%b")
    year = str(dt.year)
    return f"{day} {mon} {year}"

def create_base_background_with_glow(W, H, t=0.0):
    # 1. Base dark background
    image = Image.new("RGBA", (W, H), (3, 7, 18, 255)) # Slate-950
    
    # 2. Glow layer
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    
    # Calculate drifting offsets using time t
    # Drift cyan glow (top-left)
    cyan_dx = int(40 * math.sin(2 * math.pi * 0.1 * t))
    cyan_dy = int(40 * math.cos(2 * math.pi * 0.1 * t))
    
    # Drift violet glow (middle-right)
    violet_dx = int(50 * math.cos(2 * math.pi * 0.08 * t))
    violet_dy = int(50 * math.sin(2 * math.pi * 0.08 * t))
    
    # Drift magenta glow (bottom-left)
    magenta_dx = int(40 * math.sin(2 * math.pi * 0.12 * t))
    magenta_dy = int(40 * math.cos(2 * math.pi * 0.12 * t))
    
    # Draw glows with offsets
    draw_glow.ellipse([(-200 + cyan_dx, -200 + cyan_dy), (600 + cyan_dx, 600 + cyan_dy)], fill=(6, 182, 212, 90))
    draw_glow.ellipse([(600 + violet_dx, 700 + violet_dy), (1400 + violet_dx, 1500 + violet_dy)], fill=(124, 58, 237, 75))
    draw_glow.ellipse([(-300 + magenta_dx, 1400 + magenta_dy), (500 + magenta_dx, 2200 + magenta_dy)], fill=(217, 70, 239, 85))
    
    # Blur the glow layer heavily
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(200))
    image.alpha_composite(blurred_glow)
    return image

def draw_watermark(image, W, H):
    watermark_canvas = Image.new("RGBA", (2200, 2200), (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_canvas)
    font_watermark = ImageFont.truetype(str(FONT_BOLD), 150)
    watermark_draw.text((1100, 1100), "PULSE VECTOR", font=font_watermark, fill=(255, 255, 255, 6), anchor="mm")
    rotated_watermark = watermark_canvas.rotate(40, resample=Image.BICUBIC)
    image.paste(rotated_watermark, (-560, -140), rotated_watermark)

def draw_text_with_shadow(draw, text, x, y, font, shadow_color=(0, 0, 0, 180), text_color=(255, 255, 255, 255), offset=(2, 2), anchor="mm"):
    if shadow_color:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)

def generate_thumbnail_slide(date_obj, output_path):
    print("Generating thumbnail/title slide...")
    W, H = 1080, 1920
    
    # Generate background
    image = create_base_background_with_glow(W, H, t=0.0)
    draw_watermark(image, W, H)
    
    # Card layer
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(card)
    card_box = [(80, 400), (1000, 1520)]
    draw_card.rounded_rectangle(
        card_box,
        radius=40,
        fill=(15, 23, 42, 165),      # Slate-900 with ~65% opacity
        outline=(255, 255, 255, 35),   # Semi-translucent white border
        width=2
    )
    image.alpha_composite(card)
    
    # Fonts
    font_logo = ImageFont.truetype(str(FONT_BOLD), 26)
    font_sublogo = ImageFont.truetype(str(FONT_REGULAR), 36)
    font_title = ImageFont.truetype(str(FONT_BOLD), 72)
    font_date = ImageFont.truetype(str(FONT_BOLD), 54)
    
    draw = ImageDraw.Draw(image)
    
    # Draw header Logo / Header Text
    draw.text((140, 215), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
    
    # Centered Title Card Content
    cx = 540
    draw_text_with_shadow(draw, "DAILY", cx, 660, font_sublogo, text_color=(56, 189, 248, 200)) # Sky-400
    draw_text_with_shadow(draw, "CURRENT AFFAIRS", cx, 780, font_title, text_color=(255, 255, 255, 255))
    
    # Separator Line
    draw.line([(240, 890), (840, 890)], fill=(255, 255, 255, 35), width=2)
    
    # Date
    formatted_date_str = format_date_custom(date_obj)
    draw_text_with_shadow(draw, formatted_date_str, cx, 1000, font_date, text_color=(251, 191, 36, 255)) # Gold color
    
    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")
    print(f"[OK] Thumbnail slide saved to: {output_path}")

def draw_bell_icon(W_bell, H_bell, angle):
    # Creates a 300x300 canvas with a bell drawn on it, rotated by 'angle'
    bell_img = Image.new("RGBA", (W_bell, H_bell), (0, 0, 0, 0))
    bell_draw = ImageDraw.Draw(bell_img)
    
    # Draw clapper at bottom center (x=150, y=205 to 235)
    # The clapper moves opposite or swings slightly too
    clapper_offset = int(5 * math.sin(math.radians(angle * 3)))
    bell_draw.ellipse([(135 + clapper_offset, 205), (165 + clapper_offset, 235)], fill=(251, 191, 36, 255)) # Gold
    
    # Top loop (x=135 to 165, y=35 to 65)
    bell_draw.ellipse([(135, 35), (165, 65)], outline=(255, 255, 255, 255), width=6)
    
    # Bell body polygon
    body_points = [
        (135, 60), (165, 60),
        (170, 100), (195, 160), (220, 195),
        (80, 195), (105, 160), (130, 100)
    ]
    bell_draw.polygon(body_points, fill=(255, 255, 255, 255))
    
    # Bottom rim flare
    bell_draw.rounded_rectangle([(72, 190), (228, 205)], radius=7, fill=(255, 255, 255, 255))
    
    # Rotate the bell image around center
    rotated_bell = bell_img.rotate(angle, resample=Image.BICUBIC)
    return rotated_bell

def generate_animated_end_slide_frames(output_dir, fps=10, duration=3.0):
    print("Generating animated end slide frames...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    W, H = 1080, 1920
    total_frames = int(fps * duration)
    
    # Fonts
    font_bold_title = ImageFont.truetype(str(FONT_BOLD), 56)
    font_regular_sub = ImageFont.truetype(str(FONT_REGULAR), 38)
    font_body = ImageFont.truetype(str(FONT_REGULAR), 32)
    font_logo = ImageFont.truetype(str(FONT_BOLD), 26)
    
    frame_paths = []
    
    for i in range(total_frames):
        t = i / fps  # Current time in seconds
        
        # 1. Base background (drifting glows)
        image = create_base_background_with_glow(W, H, t=t)
        draw_watermark(image, W, H)
        
        # 2. Draw card layer
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
        
        # 3. Draw ringing bell icon in card center (y=600)
        # Bell rings back and forth: max 15 degrees angle, 3 times per second
        bell_angle = 18 * math.sin(2 * math.pi * 3.0 * t)
        # Add a damping factor towards the end of the slide, or keep it ringing
        # Let's keep it ringing!
        bell_icon = draw_bell_icon(300, 300, bell_angle)
        
        # Paste centered at x=540, y=550 (bbox: x=390, y=400)
        image.paste(bell_icon, (390, 400), bell_icon)
        
        # 4. Draw text overlay with fade-in effect
        # Text starts fading in from frame 0 to 12 (first 1.2 seconds)
        alpha = min(255, int((i / 12.0) * 255))
        
        text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        cx = 540
        
        # Heading: "Like, Share & Subscribe"
        draw_text_with_shadow(
            text_draw, 
            "Like, Share & Subscribe", 
            cx, 800, 
            font_bold_title, 
            shadow_color=(0, 0, 0, int(0.7 * alpha)), 
            text_color=(255, 255, 255, alpha)
        )
        
        # Subtitle: "(Press the Bell Icon)"
        draw_text_with_shadow(
            text_draw, 
            "(Press the Bell Icon)", 
            cx, 890, 
            font_regular_sub, 
            shadow_color=(0, 0, 0, int(0.7 * alpha)), 
            text_color=(56, 189, 248, alpha) # Sky-400
        )
        
        # Separator line under title
        text_draw.line([(240, 960), (840, 960)], fill=(255, 255, 255, int(0.15 * alpha)), width=2)
        
        # Description
        desc_y = 1040
        desc_lines = [
            "to get up to date with all global",
            "current affairs in no time."
        ]
        for idx, line in enumerate(desc_lines):
            draw_text_with_shadow(
                text_draw, 
                line, 
                cx, desc_y + (idx * 55), 
                font_body, 
                shadow_color=(0, 0, 0, int(0.7 * alpha)), 
                text_color=(229, 231, 235, alpha) # Gray-200
            )
            
        # Draw header Logo / Header Text
        draw_text_with_shadow(
            text_draw, 
            "P U L S E   V E C T O R", 
            140, 215, 
            font_logo, 
            shadow_color=(0, 0, 0, 50), 
            text_color=(255, 255, 255, 80),
            anchor="la"
        )
        
        image.alpha_composite(text_layer)
        
        # Save frame
        frame_path = output_dir / f"frame_{i:03d}.png"
        image.convert("RGB").save(frame_path, "PNG")
        frame_paths.append(frame_path)
        
    print(f"[OK] Generated {len(frame_paths)} animated frames in: {output_dir}")
    return frame_paths

def compile_enhanced_video(thumbnail_path, daily_image_paths, animated_frame_paths, output_video_path, duration_per_static=3.0, fps=10):
    print("Compiling enhanced video...")
    
    # Read the first image to get dimensions
    first_img = cv2.imread(str(thumbnail_path))
    if first_img is None:
        raise FileNotFoundError(f"Failed to read thumbnail image: {thumbnail_path}")
    h, w, c = first_img.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (w, h))
    
    frames_per_static = int(duration_per_static * fps)
    
    # 1. Write Title/Thumbnail slide (3s)
    print("Writing title slide to video...")
    img = cv2.imread(str(thumbnail_path))
    for _ in range(frames_per_static):
        out.write(img)
        
    # 2. Write Daily content slides (3s each)
    for idx, path in enumerate(daily_image_paths):
        print(f"Writing daily slide {idx+1} to video...")
        img = cv2.imread(str(path))
        if img is None:
            print(f"Warning: Skipping unreadable daily image {path}")
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        for _ in range(frames_per_static):
            out.write(img)
            
    # 3. Write Animated End slide frames (1 frame each)
    print("Writing animated end slide frames to video...")
    for path in animated_frame_paths:
        img = cv2.imread(str(path))
        if img is None:
            print(f"Warning: Skipping unreadable end slide frame {path}")
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        out.write(img)
        
    out.release()
    print(f"[OK] Enhanced silent video saved to: {output_video_path}")

def merge_audio(video_path, audio_path, output_path, total_duration):
    print(f"Muxing audio track '{audio_path.name}' into enhanced video...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Fade out audio over the last 1.5 seconds of the video
    st_fade = max(0.0, total_duration - 1.5)
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-filter_complex", f"[1:a]volume=0.35,afade=t=out:st={st_fade}:d=1.5[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    print(f"[OK] Final enhanced video generated at: {output_path}")

def get_random_audio_track():
    audio_dir = PROJECT_ROOT / "samples" / "Audio"
    mp3_files = list(audio_dir.glob("*.mp3"))
    if not mp3_files:
        return None
    return random.choice(mp3_files)

def main():
    target_date = datetime.datetime(2026, 6, 17)
    date_str = target_date.strftime("%d%b-%Y").lower()  # e.g., "17jun-2026"
    
    # Verify input daily slides exist
    daily_images_dir = ARCHIVE_DIR / "2026" / "June" / "Daily_Images" / f"daily-{date_str}_formatted"
    
    daily_image_paths = [
        daily_images_dir / f"daily-{date_str}_formatted_page-1.png",
        daily_images_dir / f"daily-{date_str}_formatted_page-2.png",
        daily_images_dir / f"daily-{date_str}_formatted_page-3.png"
    ]
    
    for path in daily_image_paths:
        if not path.exists():
            print(f"Error: Daily slide image does not exist: {path}")
            sys.exit(1)
            
    # Output file paths
    thumbnail_path = POC_DIR / "thumbnail_poc.png"
    temp_frames_dir = POC_DIR / "temp_end_frames"
    silent_video_path = POC_DIR / "enhanced_silent_poc.mp4"
    final_video_path = POC_DIR / "enhanced_video_poc.mp4"
    
    # 1. Generate Thumbnail / Title slide
    generate_thumbnail_slide(target_date, thumbnail_path)
    
    # 2. Generate Animated End slide frames
    animated_frame_paths = generate_animated_end_slide_frames(temp_frames_dir, fps=10, duration=3.0)
    
    # 3. Compile everything to silent video
    # Title slide (3s) + 3 Daily slides (3s each = 9s) + End slide (3s) = 15s total
    total_duration = 3.0 + (len(daily_image_paths) * 3.0) + 3.0
    compile_enhanced_video(thumbnail_path, daily_image_paths, animated_frame_paths, silent_video_path, duration_per_static=3.0, fps=10)
    
    # 4. Merge audio
    audio_track = get_random_audio_track()
    if audio_track:
        merge_audio(silent_video_path, audio_track, final_video_path, total_duration)
        if silent_video_path.exists():
            silent_video_path.unlink()
    else:
        print("Warning: No audio track found to merge. Keeping silent video.")
        shutil.move(silent_video_path, final_video_path)
        
    # Clean up temporary frames
    if temp_frames_dir.exists():
        shutil.rmtree(temp_frames_dir)
        print("Cleaned up temporary end slide frames.")
        
    print("\n[SUCCESS] POC complete! Check your POC directory for output files:")
    print(f" - Thumbnail: {thumbnail_path}")
    print(f" - Video: {final_video_path}")

if __name__ == "__main__":
    import subprocess
    main()
