import os
import re
import sys
import argparse
import datetime
import pathlib
import random
import math
import shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Add src to python path if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import ARCHIVE_DIR, BT_DATE_FMT, PULSE_PLAY_BASE_URL
from core.genai_utils import (
    configure_genai, read_prompts, generate_content, save_file,
    build_brainteaser_prompt, BRAIN_TEASER_TYPES
)
from core.image_utils import (
    ensure_fonts, parse_teaser_file, wrap_text, draw_teaser_text_with_shadow,
    verify_brainteaser_visual_boundaries
)


from core.video_utils import (
    create_base_background_with_glow, draw_watermark_on_image,
    draw_text_with_shadow_helper, download_audio_library,
    get_random_audio_track, merge_audio_video,
    generate_countdown_sfx, merge_brainteaser_audio,
    draw_bell_icon_image, compute_word_timings,
    render_karaoke_subtitle_overlay
)
from core.youtube_utils import (
    get_authenticated_service, add_video_to_playlist, upload_video_to_youtube,
    add_video_comment
)
from core.content_parser import (
    format_community_poll_text, format_teaser_challenge_comment,
    format_solution_reveal_comment, format_brainteaser_description
)
from core.broadcast_utils import broadcast_daily_content
from core.tts_utils import synthesize_text, get_audio_duration, HAS_TTS
from core.database_utils import run_database_upload
W, H = 656, 656

# --- Backgrounds Generators ---

def bg_cyberpunk(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(124 * (1 - t) + 6 * t)
            g = int(58 * (1 - t) + 182 * t)
            b = int(237 * (1 - t) + 212 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_sunset(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(249 * (1 - t) + 219 * t)
            g = int(115 * (1 - t) + 39 * t)
            b = int(22 * (1 - t) + 119 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_deep_ocean(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(15 * (1 - t) + 13 * t)
            g = int(23 * (1 - t) + 148 * t)
            b = int(42 * (1 - t) + 136 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_neon_forest(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(16 * (1 - t) + 3 * t)
            g = int(185 * (1 - t) + 7 * t)
            b = int(129 * (1 - t) + 18 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_royal_gold(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(20 * (1 - t) + 217 * t)
            g = int(15 * (1 - t) + 119 * t)
            b = int(5 * (1 - t) + 6 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_volcanic(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h)
            r = int(24 * (1 - t) + 220 * t)
            g = int(24 * (1 - t) + 38 * t)
            b = int(27 * (1 - t) + 38 * t)
            pixels[x, y] = (r, g, b, 255)
    return img

def bg_starry_night(w, h):
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            t = y / h
            r = int(10 * (1 - t) + 2 * t)
            g = int(15 * (1 - t) + 4 * t)
            b = int(30 * (1 - t) + 8 * t)
            pixels[x, y] = (r, g, b, 255)
            
    draw = ImageDraw.Draw(img)
    random.seed(137)
    for _ in range(50):
        sx = random.randint(10, w - 10)
        sy = random.randint(10, h - 10)
        size = random.choice([1, 2])
        alpha = random.randint(100, 255)
        draw.ellipse([(sx, sy), (sx + size, sy + size)], fill=(255, 255, 255, alpha))
    return img

def bg_midnight_blue(w, h):
    img = Image.new("RGBA", (w, h), (13, 17, 38, 255))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([(w/2 - 300, -100), (w/2 + 300, 500)], fill=(99, 102, 241, 100))
    draw_glow.ellipse([(w/2 - 250, h - 300), (w/2 + 250, h + 200)], fill=(236, 72, 153, 70))
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(140))
    img.alpha_composite(blurred_glow)
    return img

def bg_radial_glow(w, h):
    img = Image.new("RGBA", (w, h), (10, 10, 15, 255))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([(w/2 - 250, h/2 - 250), (w/2 + 250, h/2 + 250)], fill=(139, 92, 246, 120))
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(blurred_glow)
    return img

def bg_dark_aurora(w, h):
    img = Image.new("RGBA", (w, h), (10, 15, 26, 255))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([(-100, -100), (450, 450)], fill=(16, 185, 129, 90))
    draw_glow.ellipse([(w - 450, h - 450), (w + 100, h + 100)], fill=(56, 189, 248, 80))
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(130))
    img.alpha_composite(blurred_glow)
    return img

BACKGROUNDS = [
    bg_cyberpunk, bg_sunset, bg_deep_ocean, bg_neon_forest, bg_royal_gold,
    bg_volcanic, bg_starry_night, bg_midnight_blue, bg_radial_glow, bg_dark_aurora
]

# --- Options Placement Helpers ---

def draw_fitted_option_text(draw, opt_text, cx, cy, font_opt, max_w, anchor="lm", text_color=(255, 255, 255)):
    """Draws option text, dynamically shrinking font size if needed so it never overflows max_w."""
    font = font_opt
    font_path = getattr(font, 'path', None)
    current_sz = getattr(font, 'size', 26)
    while font.getlength(opt_text) > max_w and current_sz > 14 and font_path:
        current_sz -= 2
        font = ImageFont.truetype(str(font_path), current_sz)
    draw_teaser_text_with_shadow(draw, opt_text, cx, cy, font, text_color=text_color, anchor=anchor)

def draw_options_standard(draw, options, opt_y_start, font_opt, fill_color=(15, 23, 42, 120), outline_color=(255, 255, 255, 35)):
    max_opt_w = 0
    for opt in options:
        w = font_opt.getlength(opt)
        if w > max_opt_w:
            max_opt_w = w
            
    use_vertical = (max_opt_w > 200) or (len(options) != 4)
    
    if not use_vertical:
        col1_x = W / 2 - 135
        col2_x = W / 2 + 135
        box_w, box_h = 240, 60
        gap_y = 15
        
        row1_y = opt_y_start + box_h/2
        row2_y = row1_y + box_h + gap_y
        
        coords = [
            (col1_x, row1_y), (col2_x, row1_y),
            (col1_x, row2_y), (col2_x, row2_y)
        ]
        
        for idx, opt in enumerate(options):
            cx, cy = coords[idx]
            x1, y1 = cx - box_w/2, cy - box_h/2
            x2, y2 = cx + box_w/2, cy + box_h/2
            
            draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=15, fill=fill_color, outline=outline_color, width=2)
            draw_fitted_option_text(draw, opt, cx, cy, font_opt, max_w=box_w - 20, anchor="mm")
    else:
        box_w, box_h = 500, 48
        gap_y = 8
        total_h = len(options) * box_h + (len(options) - 1) * gap_y
        max_allowed_y = 585  # 35px clearance above watermark at 620
        if opt_y_start + total_h > max_allowed_y:
            overflow = (opt_y_start + total_h) - max_allowed_y
            box_h = max(34, box_h - int(overflow / max(len(options), 1)) - 2)
            gap_y = max(4, gap_y - 2)
            total_h = len(options) * box_h + (len(options) - 1) * gap_y
            if opt_y_start + total_h > max_allowed_y:
                opt_y_start = max(180, max_allowed_y - total_h)
                
        for idx, opt in enumerate(options):
            cy = opt_y_start + box_h/2 + idx * (box_h + gap_y)
            x1 = W/2 - box_w/2
            y1 = cy - box_h/2
            x2 = W/2 + box_w/2
            y2 = cy + box_h/2
            
            draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=12, fill=fill_color, outline=outline_color, width=2)
            draw_fitted_option_text(draw, opt, x1 + 25, cy, font_opt, max_w=box_w - 45, anchor="lm")

def draw_options_capsule(draw, options, opt_y_start, font_opt):
    max_opt_w = 0
    for opt in options:
        w = font_opt.getlength(opt)
        if w > max_opt_w:
            max_opt_w = w
            
    use_vertical = (max_opt_w > 200) or (len(options) != 4)
    fill_color = (15, 23, 42, 120)
    outline_color = (255, 255, 255, 35)
    
    if not use_vertical:
        col1_x = W / 2 - 135
        col2_x = W / 2 + 135
        box_w, box_h = 240, 60
        gap_y = 15
        
        row1_y = opt_y_start + box_h/2
        row2_y = row1_y + box_h + gap_y
        
        coords = [
            (col1_x, row1_y), (col2_x, row1_y),
            (col1_x, row2_y), (col2_x, row2_y)
        ]
        
        for idx, opt in enumerate(options):
            cx, cy = coords[idx]
            x1, y1 = cx - box_w/2, cy - box_h/2
            x2, y2 = cx + box_w/2, cy + box_h/2
            
            draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h/2, fill=fill_color, outline=outline_color, width=2)
            draw_fitted_option_text(draw, opt, cx, cy, font_opt, max_w=box_w - 20, anchor="mm")
    else:
        box_w, box_h = 500, 48
        gap_y = 8
        total_h = len(options) * box_h + (len(options) - 1) * gap_y
        max_allowed_y = 585
        if opt_y_start + total_h > max_allowed_y:
            overflow = (opt_y_start + total_h) - max_allowed_y
            box_h = max(34, box_h - int(overflow / max(len(options), 1)) - 2)
            gap_y = max(4, gap_y - 2)
            total_h = len(options) * box_h + (len(options) - 1) * gap_y
            if opt_y_start + total_h > max_allowed_y:
                opt_y_start = max(180, max_allowed_y - total_h)
                
        for idx, opt in enumerate(options):
            cy = opt_y_start + box_h/2 + idx * (box_h + gap_y)
            x1 = W/2 - box_w/2
            y1 = cy - box_h/2
            x2 = W/2 + box_w/2
            y2 = cy + box_h/2
            
            draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=box_h/2, fill=fill_color, outline=outline_color, width=2)
            draw_fitted_option_text(draw, opt, x1 + 25, cy, font_opt, max_w=box_w - 45, anchor="lm")

def draw_options_cropped(draw, options, opt_y_start, font_opt):
    max_opt_w = 0
    for opt in options:
        w = font_opt.getlength(opt)
        if w > max_opt_w:
            max_opt_w = w
            
    use_vertical = (max_opt_w > 200) or (len(options) != 4)
    fill_color = (15, 23, 42, 120)
    outline_color = (14, 165, 233, 140)
    
    if not use_vertical:
        col1_x = W / 2 - 135
        col2_x = W / 2 + 135
        box_w, box_h = 240, 56
        gap_y = 15
        c = 10
        
        row1_y = opt_y_start + box_h/2
        row2_y = row1_y + box_h + gap_y
        
        coords = [
            (col1_x, row1_y), (col2_x, row1_y),
            (col1_x, row2_y), (col2_x, row2_y)
        ]
        
        for idx, opt in enumerate(options):
            cx, cy = coords[idx]
            x1, y1 = cx - box_w/2, cy - box_h/2
            x2, y2 = cx + box_w/2, cy + box_h/2
            
            points = [
                (x1 + c, y1), (x2 - c, y1), (x2, y1 + c), (x2, y2 - c),
                (x2 - c, y2), (x1 + c, y2), (x1, y2 - c), (x1, y1 + c)
            ]
            draw.polygon(points, fill=fill_color, outline=outline_color)
            draw_fitted_option_text(draw, opt, cx, cy, font_opt, max_w=box_w - 20, anchor="mm")
    else:
        box_w, box_h = 500, 46
        gap_y = 8
        c = 8
        total_h = len(options) * box_h + (len(options) - 1) * gap_y
        max_allowed_y = 585
        if opt_y_start + total_h > max_allowed_y:
            overflow = (opt_y_start + total_h) - max_allowed_y
            box_h = max(34, box_h - int(overflow / max(len(options), 1)) - 2)
            gap_y = max(4, gap_y - 2)
            total_h = len(options) * box_h + (len(options) - 1) * gap_y
            if opt_y_start + total_h > max_allowed_y:
                opt_y_start = max(180, max_allowed_y - total_h)
                
        for idx, opt in enumerate(options):
            cy = opt_y_start + box_h/2 + idx * (box_h + gap_y)
            x1 = W/2 - box_w/2
            y1 = cy - box_h/2
            x2 = W/2 + box_w/2
            y2 = cy + box_h/2
            
            points = [
                (x1 + c, y1), (x2 - c, y1), (x2, y1 + c), (x2, y2 - c),
                (x2 - c, y2), (x1 + c, y2), (x1, y2 - c), (x1, y1 + c)
            ]
            draw.polygon(points, fill=fill_color, outline=outline_color)
            draw_fitted_option_text(draw, opt, x1 + 25, cy, font_opt, max_w=box_w - 45, anchor="lm")


# --- Layout Cards Drawing Engines ---

def draw_layout_1(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "Daily Brain Teaser:-", 328, 70, f_header, text_color=(251, 191, 36))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 160), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=20, fill=(15, 23, 42, 140), outline=(255, 255, 255, 45), width=2)
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(56, 189, 248))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options)

def draw_layout_2(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "Brain Teaser Daily", 328, 70, f_header, text_color=(56, 189, 248))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 160), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(255, 255, 255))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1 - 3, card_y1 - 3), (card_x2 + 3, card_y2 + 3)], radius=23, outline=(34, 197, 94, 180), width=3)
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=20, fill=(0, 0, 0, 220), outline=(255, 255, 255, 60), width=1)
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(34, 197, 94))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options, fill_color=(0, 0, 0, 200), outline_color=(34, 197, 94, 80))

def draw_layout_3(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "★ DAILY CHALLENGE ★", 328, 70, f_header, text_color=(245, 158, 11))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 140), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(254, 243, 199))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=20, fill=(30, 20, 10, 160), outline=(245, 158, 11, 200), width=2)
    draw.rounded_rectangle([(card_x1 + 6, card_y1 + 6), (card_x2 - 6, card_y2 - 6)], radius=14, outline=(245, 158, 11, 100), width=1)
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(245, 158, 11))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options, fill_color=(30, 20, 10, 140), outline_color=(245, 158, 11, 120))

def draw_layout_4(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    draw_teaser_text_with_shadow(draw, "Brain Teaser", 328, 70, f_header, text_color=(236, 72, 153))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 160), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 480)
    q_box_h = len(wrapped_q) * 26 + 20
    q_y1 = 120
    q_y2 = q_y1 + q_box_h
    draw.rounded_rectangle([(78, q_y1), (578, q_y2)], radius=15, fill=(15, 23, 42, 120), outline=(236, 72, 153, 60), width=1)
    for idx, line in enumerate(wrapped_q):
        draw_teaser_text_with_shadow(draw, line, 328, q_y1 + 10 + idx*26 + 13, f_sub, text_color=(229, 231, 235))
    wrapped_series = wrap_text(data["series"], f_series, 460)
    s_y1 = q_y2 + 15
    s_y2 = s_y1 + len(wrapped_series) * 44 + 24
    draw.rounded_rectangle([(78, s_y1), (578, s_y2)], radius=15, fill=(15, 23, 42, 180), outline=(255, 255, 255, 50), width=2)
    s_y = s_y1 + 12 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(236, 72, 153))
        s_y += 44
    draw_options_standard(draw, data["options"], s_y2 + 20, f_options)

def draw_layout_5(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    draw_teaser_text_with_shadow(draw, "Daily Brain Teaser", 328, 65, f_header, text_color=(99, 102, 241))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 160), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 115
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    s_h = len(wrapped_series) * 44 + 20
    s_y1 = current_y + 15
    s_y2 = s_y1 + s_h
    draw.rounded_rectangle([(78, s_y1), (578, s_y2)], radius=s_h/2, fill=(15, 23, 42, 150), outline=(99, 102, 241, 100), width=2)
    s_y = s_y1 + 10 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(99, 102, 241))
        s_y += 44
    draw_options_capsule(draw, data["options"], s_y2 + 20, f_options)

def draw_layout_6(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    draw_teaser_text_with_shadow(draw, "BRAIN TEASER CHALLENGE", 328, 70, f_header, text_color=(14, 165, 233))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 140), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 440)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    x1, y1, x2, y2 = 78, card_y1, 578, card_y2
    c = 20
    points = [
        (x1 + c, y1), (x2 - c, y1), (x2, y1 + c), (x2, y2 - c),
        (x2 - c, y2), (x1 + c, y2), (x1, y2 - c), (x1, y1 + c)
    ]
    draw.polygon(points, fill=(15, 23, 42, 140), outline=(14, 165, 233, 160))
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(14, 165, 233))
        s_y += 44
    draw_options_cropped(draw, data["options"], card_y2 + 20, f_options)

def draw_layout_7(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "> DAILY CHALLENGE", 328, 70, f_header, text_color=(34, 197, 94))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, f"DATE: {data['date']}", 616, 35, f_date, text_color=(34, 197, 94, 200), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, f"> {line}", 328, current_y, f_sub, text_color=(74, 222, 128))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 40
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=10, fill=(0, 0, 0, 240), outline=(34, 197, 94, 150), width=2)
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y1 + 25)], radius=10, fill=(34, 197, 94, 40))
    draw.ellipse([(90, card_y1 + 8), (98, card_y1 + 16)], fill=(239, 68, 68))
    draw.ellipse([(105, card_y1 + 8), (113, card_y1 + 16)], fill=(245, 158, 11))
    draw.ellipse([(120, card_y1 + 8), (128, card_y1 + 16)], fill=(34, 197, 94))
    s_y = card_y1 + 35 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, f"[ {line} ]", 328, s_y, f_series, text_color=(34, 197, 94))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options, fill_color=(0, 0, 0, 240), outline_color=(34, 197, 94, 100))

def draw_layout_8(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "Brain Teaser Challenge", 328, 70, f_header, text_color=(255, 255, 255))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 140), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 440)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=8, fill=(15, 23, 42, 210), outline=(100, 116, 139, 100), width=1)
    draw.rectangle([(card_x1, card_y1 + 10), (card_x1 + 6, card_y2 - 10)], fill=(249, 115, 22))
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(249, 115, 22))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options, fill_color=(15, 23, 42, 180), outline_color=(100, 116, 139, 80))

def draw_layout_9(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "Mind Workout Daily", 328, 70, f_header, text_color=(253, 224, 71))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 140), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=25, fill=(15, 23, 42, 100), outline=(217, 70, 239, 180), width=2)
    draw.rounded_rectangle([(card_x1 + 3, card_y1 + 3), (card_x2 - 3, card_y2 - 3)], radius=22, outline=(6, 182, 212, 120), width=1)
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(253, 224, 71))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options)

def draw_layout_10(draw, data, fonts):
    f_header, f_sub, f_series, f_options, f_watermark, f_date = fonts
    card_x1, card_x2 = 78, 578
    draw_teaser_text_with_shadow(draw, "Challenge of the Day", 328, 70, f_header, text_color=(255, 255, 255))
    if data["date"]:
        draw_teaser_text_with_shadow(draw, data["date"], 616, 35, f_date, text_color=(255, 255, 255, 140), anchor="rt")
    wrapped_q = wrap_text(data["question_header"], f_sub, 560)
    current_y = 125
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, 328, current_y, f_sub, text_color=(229, 231, 235))
        current_y += 28
    wrapped_series = wrap_text(data["series"], f_series, 460)
    card_y1 = current_y + 12
    card_y2 = card_y1 + len(wrapped_series) * 44 + 30
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=15, fill=(15, 23, 42, 230), outline=(255, 255, 255, 20), width=1)
    s_y = card_y1 + 15 + 22
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, 328, s_y, f_series, text_color=(56, 189, 248))
        s_y += 44
    draw_options_standard(draw, data["options"], card_y2 + 20, f_options, fill_color=(15, 23, 42, 200), outline_color=(255, 255, 255, 15))

LAYOUTS = [
    draw_layout_1, draw_layout_2, draw_layout_3, draw_layout_4, draw_layout_5,
    draw_layout_6, draw_layout_7, draw_layout_8, draw_layout_9, draw_layout_10
]

# --- Standalone Pipeline API ---

def generate_brainteaser_content(client, target_date, teaser_type=None, randomize=True):
    print(f"\nProcessing standalone Daily Brain Teaser generation for: {target_date.strftime('%d %B %Y')}")
    date_str = target_date.strftime("%d %B %Y")
    year = target_date.strftime("%Y")
    month_name = target_date.strftime("%B")
    
    processed_month_dir = ARCHIVE_DIR / year / month_name
    bt_filename = f"brainteaser-{target_date.strftime(BT_DATE_FMT).lower()}.txt"
    bt_path = processed_month_dir / "Brain_Teasers" / "Text" / bt_filename
    
    if bt_path.exists():
        print(f"  > Brain teaser text file already exists at: {bt_path}. Skipping content generation.")
        return bt_path
        
    ca_prompt, bt_prompt = read_prompts()
    if not bt_prompt:
        raise ValueError("Could not read prompts! Please make sure pulse_prompts.md is available.")
        
    effective_type = None if teaser_type == "random" else teaser_type
    prompt_text, selected_key = build_brainteaser_prompt(
        target_date=target_date,
        base_prompt=bt_prompt,
        teaser_type=effective_type,
        randomize=(teaser_type == "random" or teaser_type is None)
    )
    type_name = BRAIN_TEASER_TYPES.get(selected_key, {}).get("name", selected_key)
    print(f"  > Querying Gemini API for Daily Brain Teaser [{type_name}]...")
    bt_content = generate_content(client, 'gemini-2.5-flash', prompt_text)
    
    save_file(bt_content, bt_path)
    
    # Also format and save 1-click YouTube Community Poll asset
    try:
        data = parse_teaser_file(bt_path)
        if data:
            poll_text = format_community_poll_text(data)
            poll_filename = f"poll-{target_date.strftime(BT_DATE_FMT).lower()}.txt"
            poll_path = processed_month_dir / "Brain_Teasers" / "Text" / poll_filename
            save_file(poll_text, poll_path)
            print(f"  > Generated 1-click Community Poll asset at: {poll_path.name}")
    except Exception as e:
        print(f"  > Warning: Could not generate Community Poll asset: {e}")
        
    return bt_path

def generate_brainteaser_slides(target_date, style_idx=None, bg_idx=None):
    print(f"\n🚀 Rendering Daily Brain Teaser Images for: {target_date.strftime('%d %B %Y')}...")
    year = target_date.strftime("%Y")
    month_name = target_date.strftime("%B")
    
    processed_month_dir = ARCHIVE_DIR / year / month_name
    bt_filename = f"brainteaser-{target_date.strftime(BT_DATE_FMT).lower()}.txt"
    bt_path = processed_month_dir / "Brain_Teasers" / "Text" / bt_filename
    
    if not bt_path.exists():
        raise FileNotFoundError(f"Missing brain teaser text file at {bt_path}. Please run text generation first.")
        
    images_dir = processed_month_dir / "Brain_Teasers" / "Images"
    base_name = bt_path.slate if hasattr(bt_path, 'slate') else bt_path.stem
    styled_path = images_dir / f"{base_name}_styled.png"
    plain_path = images_dir / f"{base_name}_plain.png"
    
    if styled_path.exists() and plain_path.exists():
        print(f"  > Brain teaser slides already exist. Skipping slide generation.")
        return
        
    data = parse_teaser_file(bt_path)
    if not data:
        raise ValueError(f"Could not parse data from {bt_path}. The file format may be invalid.")
        
    font_regular_path, font_bold_path = ensure_fonts(ARCHIVE_DIR)
    
    import hashlib
    date_iso = target_date.strftime("%Y-%m-%d")
    
    if bg_idx is not None:
        selected_bg_idx = bg_idx
    else:
        bg_hash = hashlib.sha256(f"bg_{date_iso}".encode()).hexdigest()
        selected_bg_idx = int(bg_hash, 16) % len(BACKGROUNDS)
        
    if style_idx is not None:
        selected_layout_idx = style_idx
    else:
        layout_hash = hashlib.sha256(f"layout_{date_iso}".encode()).hexdigest()
        selected_layout_idx = int(layout_hash, 16) % len(LAYOUTS)
    
    print(f"  > Selected Style Layout: {selected_layout_idx + 1}/10, Background: {selected_bg_idx + 1}/10")
    
    bg_img_generator = BACKGROUNDS[selected_bg_idx]
    layout_renderer = LAYOUTS[selected_layout_idx]
    
    # 2. Render Styled Card
    styled_img = bg_img_generator(W, H)
    styled_draw = ImageDraw.Draw(styled_img)
    
    fonts = (
        ImageFont.truetype(str(font_bold_path), 40),
        ImageFont.truetype(str(font_regular_path), 24),
        ImageFont.truetype(str(font_bold_path), 38),
        ImageFont.truetype(str(font_regular_path), 26),
        ImageFont.truetype(str(font_regular_path), 14),
        ImageFont.truetype(str(font_regular_path), 15)
    )
    
    layout_renderer(styled_draw, data, fonts)
    
    f_watermark = ImageFont.truetype(str(font_regular_path), 14)
    draw_teaser_text_with_shadow(styled_draw, "pulse-vector", W / 2, 620, f_watermark, shadow_color=None, text_color=(255, 255, 255, 140))
    
    images_dir = processed_month_dir / "Brain_Teasers" / "Images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = bt_path.slate if hasattr(bt_path, 'slate') else bt_path.stem
    styled_path = images_dir / f"{base_name}_styled.png"
    styled_img.convert("RGB").save(styled_path, "PNG")
    print(f"  > Generated Styled image card at: {styled_path}")
    
    # 3. Render Plain Card
    plain_path = images_dir / f"{base_name}_plain.png"
    
    plain_bg_img = bg_cyberpunk(W, H)
    plain_draw = ImageDraw.Draw(plain_bg_img)
    
    font_header = ImageFont.truetype(str(font_bold_path), 46)
    font_sub = ImageFont.truetype(str(font_regular_path), 28)
    font_series = ImageFont.truetype(str(font_bold_path), 40)
    font_options = ImageFont.truetype(str(font_regular_path), 30)
    
    draw_teaser_text_with_shadow(plain_draw, "Daily Brain Teaser:-", W / 2, 80, font_header)
    
    wrapped_q = wrap_text(data["question_header"], font_sub, 560)
    current_y = 145
    for line in wrapped_q:
        draw_teaser_text_with_shadow(plain_draw, line, W / 2, current_y, font_sub)
        current_y += 34
        
    wrapped_series = wrap_text(data["series"], font_series, 540)
    current_y += 15
    for line in wrapped_series:
        draw_teaser_text_with_shadow(plain_draw, line, W / 2, current_y, font_series, text_color=(56, 189, 248))
        current_y += 48
        
    start_y = current_y + 25
    gap = 42
    total_opt_h = len(data["options"]) * gap
    max_allowed_plain_y = 585
    if start_y + total_opt_h > max_allowed_plain_y:
        gap = max(28, int((max_allowed_plain_y - start_y) / max(len(data["options"]), 1)))
        if start_y + len(data["options"]) * gap > max_allowed_plain_y:
            start_y = max(180, max_allowed_plain_y - len(data["options"]) * gap)
            
    for idx, opt in enumerate(data["options"]):
        draw_fitted_option_text(plain_draw, opt, W / 2, start_y + (idx * gap), font_options, max_w=540, anchor="mm")
        
    draw_teaser_text_with_shadow(plain_draw, "pulse-vector", W / 2, 625, f_watermark, shadow_color=None)
    
    plain_bg_img.convert("RGB").save(plain_path, "PNG")
    print(f"  > Generated Plain image card at: {plain_path}")
    
    # 4. Mandatory Visual Boundaries & Layout Integrity Verification
    is_styled_ok, styled_msg = verify_brainteaser_visual_boundaries(styled_path, data)
    is_plain_ok, plain_msg = verify_brainteaser_visual_boundaries(plain_path, data)
    if is_styled_ok and is_plain_ok:
        print(f"  └─ 🎯 {styled_msg}")
    else:
        logging.warning(f"  └─ ⚠️ Boundary Check Notice: Styled={styled_msg}, Plain={plain_msg}")


def create_countdown_bell_ring(draw, cx, cy, radius, progress, text, font_timer):
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(255, 255, 255, 30), width=8)
    angle = int(360 * progress)
    draw.arc([(cx - radius, cy - radius), (cx + radius, cy + radius)], start=-90, end=-90 + angle, fill=(56, 189, 248), width=8)

def generate_brainteaser_video(target_date):
    print(f"\n🚀 Compiling Shorts Video for: {target_date.strftime('%d %B %Y')}...")
    year = target_date.strftime("%Y")
    month_name = target_date.strftime("%B")
    
    processed_month_dir = ARCHIVE_DIR / year / month_name
    bt_filename = f"brainteaser-{target_date.strftime(BT_DATE_FMT).lower()}.txt"
    bt_path = processed_month_dir / "Brain_Teasers" / "Text" / bt_filename
    
    if not bt_path.exists():
        raise FileNotFoundError(f"Missing brain teaser text file at {bt_path}. Please run content generation first.")
        
    images_dir = processed_month_dir / "Brain_Teasers" / "Images"
    styled_path = images_dir / f"{bt_path.stem}_styled.png"
    
    if not styled_path.exists():
        raise FileNotFoundError(f"Missing brain teaser styled image at {styled_path}. Please render slides first.")
        
    videos_dir = processed_month_dir / "Brain_Teasers" / "Videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    temp_video_path = videos_dir / f"temp_{bt_path.stem}_raw.mp4"
    final_video_path = videos_dir / f"{bt_path.stem}.mp4"
    
    if final_video_path.exists():
        print(f"  > Video already exists at: {final_video_path}")
        return final_video_path
        
    download_audio_library()
    
    font_regular_path, font_bold_path = ensure_fonts(ARCHIVE_DIR)
    font_title = ImageFont.truetype(str(font_bold_path), 54)
    font_subtitle = ImageFont.truetype(str(font_regular_path), 32)
    font_timer = ImageFont.truetype(str(font_bold_path), 48)
    font_bold_title = ImageFont.truetype(str(font_bold_path), 56)
    font_regular_sub = ImageFont.truetype(str(font_regular_path), 38)
    font_body = ImageFont.truetype(str(font_regular_path), 32)
    font_logo = ImageFont.truetype(str(font_bold_path), 26)
    
    card_img = Image.open(styled_path).convert("RGBA")
    
    fps = 10
    total_duration = 12.0
    total_frames = int(fps * total_duration)
    
    W_canvas, H_canvas = 1080, 1920
    
    # 1. Synthesize Intro Voiceover Hook & compute word timings for Karaoke Subtitles
    # High-retention ego-challenge hooks that trigger immediate viewer engagement in the first 3 seconds
    RETENTION_HOOKS = [
        {
            "badge": "🔥 95% FAIL THIS TEST!",
            "subtitle": "Can you solve it before zero?",
            "speech": "Ninety-five percent of people fail this puzzle! Can you solve it in eight seconds?"
        },
        {
            "badge": "⚡ ONLY 5% SPOT THE RULE!",
            "subtitle": "Think fast! What is the answer?",
            "speech": "Only five percent of people spot the pattern! What is the missing answer?"
        },
        {
            "badge": "🧠 GENIUS IQ CHALLENGE!",
            "subtitle": "Beat the clock & solve it!",
            "speech": "Genius challenge! Find the correct answer before the timer hits zero!"
        },
        {
            "badge": "⏱️ SPEED REASONING TEST!",
            "subtitle": "Can you beat 90% of viewers?",
            "speech": "Speed test! Can you beat ninety percent of viewers and solve this now?"
        }
    ]
    hook_data = RETENTION_HOOKS[target_date.day % len(RETENTION_HOOKS)]
    intro_hook = hook_data["speech"]
    temp_vo_path = videos_dir / f"temp_{bt_path.stem}_vo.mp3"
    vo_timings = []
    if HAS_TTS:
        try:
            synthesize_text(intro_hook, voice="en-US-ChristopherNeural", rate="+25%", output_path=temp_vo_path)
            vo_dur = get_audio_duration(temp_vo_path)
            vo_timings = compute_word_timings(intro_hook, vo_dur, start_offset=0.25)
            print("  > Synthesized Brain Teaser voiceover intro with karaoke timings.")
        except Exception as e:
            print(f"  > Warning: Failed synthesizing voiceover intro: {e}")
            if temp_vo_path.exists():
                temp_vo_path.unlink()
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(temp_video_path), fourcc, fps, (W_canvas, H_canvas))
    
    print("  > Rendering video frames...")
    for i in range(total_frames):
        t = i / fps
        frame_img = create_base_background_with_glow(W_canvas, H_canvas, t=t)
        draw_watermark_on_image(frame_img, font_bold_path)
        
        if i < 80:
            card_x = (W_canvas - 656) // 2
            card_y = (H_canvas - 656) // 2
            frame_img.paste(card_img, (card_x, card_y), card_img)
            
            draw = ImageDraw.Draw(frame_img)
            draw_text_with_shadow_helper(draw, hook_data["badge"], W_canvas/2, 450, font_title, text_color=(251, 191, 36))
            draw_text_with_shadow_helper(draw, hook_data["subtitle"], W_canvas/2, 530, font_subtitle, text_color=(229, 231, 235))
            
            remaining_secs = math.ceil((80 - i) / fps)
            progress = (80 - i) / 80.0
            
            cx, cy = W_canvas/2, 1480
            create_countdown_bell_ring(draw, cx, cy, radius=65, progress=progress, text=str(remaining_secs), font_timer=font_timer)
            draw_text_with_shadow_helper(draw, str(remaining_secs), cx, cy, font_timer, text_color=(255, 255, 255))
            draw_text_with_shadow_helper(draw, "Seconds left to think...", W_canvas/2, 1610, font_subtitle, text_color=(156, 163, 175))
            
            # Feature 1: Dynamic Animated Karaoke Subtitles
            if vo_timings and t <= vo_timings[-1]["end"] + 0.3:
                render_karaoke_subtitle_overlay(
                    draw, t, vo_timings, font_subtitle=font_subtitle,
                    center_x=int(W_canvas / 2), pos_y=1350
                )
        else:
            # Full Current Affairs Style Outro Card
            t_outro = (i - 80) / fps
            alpha = min(255, int(((i - 80) / 8.0) * 255))
            
            card = Image.new("RGBA", (W_canvas, H_canvas), (0, 0, 0, 0))
            draw_card = ImageDraw.Draw(card)
            card_box = [(80, 300), (1000, 1620)]
            draw_card.rounded_rectangle(
                card_box,
                radius=40,
                fill=(15, 23, 42, 165),
                outline=(255, 255, 255, 35),
                width=2
            )
            frame_img.alpha_composite(card)
            
            # Animated swinging bell icon (exact from Current Affairs)
            bell_angle = 18 * math.sin(2 * math.pi * 3.0 * t_outro)
            bell_icon = draw_bell_icon_image(300, 300, bell_angle)
            frame_img.paste(bell_icon, (390, 400), bell_icon)
            
            text_layer = Image.new("RGBA", (W_canvas, H_canvas), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            
            cx = 540
            draw_text_with_shadow_helper(
                text_draw, "Like, Share & Subscribe", cx, 800, font_bold_title, 
                shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(255, 255, 255, alpha)
            )
            draw_text_with_shadow_helper(
                text_draw, "(Press the Bell Icon)", cx, 890, font_regular_sub, 
                shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(56, 189, 248, alpha)
            )
            text_draw.line([(240, 960), (840, 960)], fill=(255, 255, 255, int(0.15 * alpha)), width=2)
            
            desc_lines = [
                "Drop your answer in the comments below,",
                "and subscribe for daily mind challenges!"
            ]
            for idx, line in enumerate(desc_lines):
                draw_text_with_shadow_helper(
                    text_draw, line, cx, 1040 + (idx * 55), font_body, 
                    shadow_color=(0, 0, 0, int(0.7 * alpha)), text_color=(229, 231, 235, alpha)
                )
                
            draw_text_with_shadow_helper(
                text_draw, "P U L S E   V E C T O R", 140, 215, font_logo, 
                shadow_color=(0, 0, 0, 50), text_color=(255, 255, 255, 80), anchor="la"
            )
            frame_img.alpha_composite(text_layer)
            
        frame_cv = cv2.cvtColor(np.array(frame_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        out.write(frame_cv)
        
    out.release()
    
    # 2. Generate Countdown SFX (woodblock ticks + chime)
    temp_sfx_path = videos_dir / f"temp_{bt_path.stem}_sfx.wav"
    try:
        generate_countdown_sfx(temp_sfx_path, total_duration=total_duration, stop_at=8.0)
    except Exception as e:
        print(f"  > Warning: Failed generating countdown SFX: {e}")
        temp_sfx_path = None
        
    # 3. Mux multi-track audio (voiceover + SFX + background music)
    audio_track = get_random_audio_track()
    if audio_track:
        print(f"  > Muxing multi-track audio with background music: {audio_track.name}")
    else:
        print("  > Muxing audio without background music...")
        
    vo_file = str(temp_vo_path) if temp_vo_path and temp_vo_path.exists() else None
    sfx_file = str(temp_sfx_path) if temp_sfx_path and temp_sfx_path.exists() else None
    bg_file = str(audio_track) if audio_track else None
    
    merge_brainteaser_audio(
        video_path=str(temp_video_path),
        voiceover_path=vo_file,
        sfx_path=sfx_file,
        bg_music_path=bg_file,
        output_path=str(final_video_path),
        total_duration=total_duration
    )
    
    # Clean up temporary audio & video artifacts
    for p in [temp_video_path, temp_sfx_path, temp_vo_path]:
        if p and p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        
    print(f"  > Generated H.264 Shorts video card with SFX & voiceover at: {final_video_path}")
    return final_video_path

def publish_teaser_to_youtube(video_path, data, target_date, privacy_status=None):
    print(f"\n🚀 Publishing Shorts Video to YouTube (Privacy: {privacy_status or 'default'})...")
    try:
        token_exists = os.path.exists('credentials/token.json') or os.path.exists('token.json')
        secrets_exists = os.path.exists('credentials/client_secrets.json') or os.path.exists('client_secrets.json')
        if not token_exists and not secrets_exists:
            print("  > Warning: YouTube credentials (credentials/token.json or client_secrets.json) not found. Skipping upload.")
            return False
            
        secrets_file = 'credentials/client_secrets.json' if os.path.exists('credentials/client_secrets.json') else 'client_secrets.json'
        youtube = get_authenticated_service(secrets_file)
        
        date_str = target_date.strftime("%B %d, %Y")
        year_str = target_date.strftime("%Y")
        
        date_compact = target_date.strftime("%d %b")
        CURIOSITY_TITLES = [
            f"🧠 Can You Solve This in 8s? Daily Brain Teaser ({date_compact}) #Shorts",
            f"🔥 95% Fail This Logic Test! Can You Beat It? ({date_compact}) #Shorts",
            f"⚡ Spot the Pattern Challenge! Daily Brain Teaser ({date_compact}) #Shorts",
            f"🧩 Genius IQ Puzzle: Find the Missing Value! ({date_compact}) #Shorts"
        ]
        title = CURIOSITY_TITLES[target_date.day % len(CURIOSITY_TITLES)]
        
        # Get hashtags from parsed data or use rich default list
        file_hashtags = data.get("hashtags", [])
        if not file_hashtags:
            file_hashtags = [
                "#BrainTeaser", "#DailyPuzzle", "#MindChallenge", "#LogicPuzzle", "#SeriesQuestion",
                "#NumberSequence", "#PuzzleOfTheDay", "#ChallengeYourMind", "#BrainGames", "#IQTest",
                "#ProblemSolving", "#CriticalThinking", "#BrainWorkout", "#MentalFitness", "#DailyChallenge",
                "#QuizTime", "#TestYourBrain", "#ThinkFast", "#SmartGames", "#BrainPower",
                "#CognitiveSkills", "#PuzzleLover", "#SharpenYourMind", "#MathPuzzle", "#FunChallenge",
                "#SolveIt", "#MindBender", "#EngageYourBrain", "#Puzzled", "#LogicGames",
                "#Brainy", "#FiguringItOut", "#MentalGym", "#MindGame", "#SmartThinking",
                "#BrainBooster", "#DailyMindTeaser", "#PuzzleFun", "#GetSmart", "#WorkoutYourBrain",
                "#ThinkingCap", "#SmartyPants", "#Brainiac", "#Mindfulness", "#Focus",
                "#Concentration", "#DailyDoseOfSmart", "#GeniusChallenge", "#PulseVector", "#Puzzles"
            ]
            
        # Ensure hashtags are formatted properly
        formatted_hashtags = []
        for tag in file_hashtags:
            if not tag.startswith("#"):
                tag = f"#{tag}"
            formatted_hashtags.append(tag)
            
        # Construct clean keyword tags for YouTube (max 500 chars total)
        youtube_tags = []
        for tag in formatted_hashtags:
            clean_tag = tag.replace("#", "")
            if clean_tag not in youtube_tags:
                youtube_tags.append(clean_tag)
                
        final_tags = []
        current_len = 0
        for tag in youtube_tags:
            tag_len = len(tag) + (1 if final_tags else 0)
            if current_len + tag_len > 400:  # safe margin under 500 chars
                break
            final_tags.append(tag)
            current_len += tag_len
            
        date_file_str = target_date.strftime(BT_DATE_FMT)
        description = format_brainteaser_description(
            data=data,
            date_str=date_str,
            formatted_hashtags=formatted_hashtags,
            date_file_str=date_file_str
        )
            
        print("  > Uploading video...")
        video_id = upload_video_to_youtube(youtube, str(video_path), title, description, final_tags, category_id="27", privacy_status=privacy_status)
        print(f"  > YouTube Upload Success! Video ID: {video_id}")
        
        playlist_title = f"Daily Brain Teasers - {year_str}"
        print(f"  > Adding to playlist: {playlist_title}...")
        add_video_to_playlist(youtube, video_id, playlist_title)
        
        # Feature 4: Automated Brain Teaser Challenge & Solution Reveal System
        comments_dir = ARCHIVE_DIR / year_str / target_date.strftime("%B") / "Brain_Teasers" / "Comments"
        comments_dir.mkdir(parents=True, exist_ok=True)
        
        # Save today's challenge comment asset
        challenge_comment = format_teaser_challenge_comment(data)
        today_comment_file = comments_dir / f"challenge-comment-{date_file_str}.txt"
        today_comment_file.write_text(challenge_comment, encoding="utf-8")
        print(f"  > Saved challenge comment asset to: {today_comment_file}")
        
        # Save & attempt yesterday's solution reveal
        yesterday_date = target_date - datetime.timedelta(days=1)
        yesterday_file_str = yesterday_date.strftime(BT_DATE_FMT)
        yesterday_txt_path = ARCHIVE_DIR / yesterday_date.strftime("%Y") / yesterday_date.strftime("%B") / "Brain_Teasers" / "Text" / f"brainteaser-{yesterday_file_str}.txt"
        
        if yesterday_txt_path.exists():
            y_data = parse_teaser_file(yesterday_txt_path)
            if y_data and y_data.get("correct_answer"):
                solution_comment = format_solution_reveal_comment(y_data)
                sol_file = comments_dir / f"solution-reveal-{yesterday_file_str}.txt"
                sol_file.write_text(solution_comment, encoding="utf-8")
                print(f"  > Generated official solution reveal for {yesterday_file_str} at: {sol_file}")
        
        # Post interactive challenge comment to video
        try:
            add_video_comment(youtube, video_id, challenge_comment)
            print(f"  > Posted interactive challenge comment to video: {video_id}")
        except Exception as e:
            print(f"  > Note on video comment: {e}")
            
        # Feature 2: Community Auto-Broadcast (Telegram & Discord)
        try:
            teaser_title = f"Daily Brain Teaser: {date_str} 🧠"
            teaser_summary = (
                f"{data.get('question_header', '')}\n{data.get('series', '')}\n\n"
                f"Options:\n" + "\n".join([f"• {opt}" for opt in data.get('options', [])]) +
                f"\n\n🧠 Drop your answer in the comments! Solution revealed in 24 hours."
            )
            img_path = ARCHIVE_DIR / year_str / target_date.strftime("%B") / "Brain_Teasers" / "Images" / f"brainteaser-{date_file_str}.png"
            v_path = pathlib.Path(video_path) if video_path else None
            broadcast_daily_content(
                content_type="Brain Teaser",
                date_obj=target_date,
                title=teaser_title,
                summary_text=teaser_summary,
                image_path=img_path if img_path and img_path.exists() else None,
                video_path=v_path if v_path and v_path.exists() else None,
                video_url=f"https://youtu.be/{video_id}"
            )
        except Exception as b_err:
            print(f"  > Broadcast notice: {b_err}")

            
        return True
    except Exception as e:
        print(f"  > Error publishing to YouTube: {e}")
        return False

def run_all(target_date=None, force_style=None, force_bg=None, teaser_type=None, privacy_status=None):
    now = datetime.datetime.now()
    is_evening = False
    if target_date is None:
        if now.hour >= 12:
            target_date = now + datetime.timedelta(days=1)
            is_evening = True
            print(f"Evening run detected. Scheduling for tomorrow: {target_date.strftime('%Y-%m-%d')}")
        else:
            target_date = now
            print(f"Morning run detected. Scheduling for today: {target_date.strftime('%Y-%m-%d')}")
            
    client = configure_genai()
    
    bt_path = generate_brainteaser_content(client, target_date, teaser_type=teaser_type)
    generate_brainteaser_slides(target_date, style_idx=force_style, bg_idx=force_bg)
    
    if is_evening:
        print("  > Evening run: Skipping video compilation and YouTube upload to prevent publishing 1 day in advance.")
        print("    Content text and image cards have been prepared and will be pushed to Git.")
        print("    YouTube upload will be executed in the morning run.")
        return
        
    video_path = generate_brainteaser_video(target_date)
    
    data = parse_teaser_file(bt_path)
    if data:
        publish_teaser_to_youtube(video_path, data, target_date, privacy_status=privacy_status)
        
    run_database_upload()
        
    print("\n[OK] Brain Teaser execution complete.")

def main():
    parser = argparse.ArgumentParser(description="Pulse Vector Daily Brain Teaser Autonomous Pipeline")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--type", type=str, choices=list(BRAIN_TEASER_TYPES.keys()) + ["random"], help="Specify puzzle type (bodmas, cipher, grid, trap, sequence, oddone, paradox, detective, relations, weighing, spatial, matchstick, age_speed, random)")

    parser.add_argument("--privacy", type=str, choices=["public", "private", "unlisted"], default=None, help="Force YouTube privacy status")
    parser.add_argument("--generate-only", action="store_true", help="Only generate text content from GenAI")
    parser.add_argument("--slides-only", action="store_true", help="Only render image slide cards")
    parser.add_argument("--video-only", action="store_true", help="Only compile Shorts video")
    parser.add_argument("--style", type=int, help="Force layout style (1 to 10)")
    parser.add_argument("--bg", type=int, help="Force background style (1 to 10)")
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format! Use YYYY-MM-DD.")
            sys.exit(1)
            
    force_style_idx = (args.style - 1) if (args.style and 1 <= args.style <= 10) else None
    force_bg_idx = (args.bg - 1) if (args.bg and 1 <= args.bg <= 10) else None
    
    if args.generate_only:
        if target_date is None:
            target_date = datetime.datetime.now()
        client = configure_genai()
        generate_brainteaser_content(client, target_date, teaser_type=args.type)
    elif args.slides_only:
        if target_date is None:
            target_date = datetime.datetime.now()
        generate_brainteaser_slides(target_date, style_idx=force_style_idx, bg_idx=force_bg_idx)
    elif args.video_only:
        if target_date is None:
            target_date = datetime.datetime.now()
        generate_brainteaser_video(target_date)
    else:
        run_all(target_date, force_style=force_style_idx, force_bg=force_bg_idx, teaser_type=args.type, privacy_status=args.privacy)

if __name__ == "__main__":
    main()
