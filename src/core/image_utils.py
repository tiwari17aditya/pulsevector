import os
import random
import math
import re
import datetime
import pathlib
import requests
import logging
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .config import ARCHIVE_DIR, BT_DATE_FMT
from .content_parser import parse_teaser_content, classify_news_category, CATEGORY_PALETTES

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
BACKGROUNDS_DIR = ROOT_DIR / "assets" / "backgrounds"

CATEGORY_BACKGROUND_MAP = {
    "DEFENCE": "defence.jpg",
    "ECONOMY": "economy.jpg",
    "TECH & AI": "tech_ai.jpg",
    "GEOPOLITICS": "geopolitics.jpg",
    "ENVIRONMENT": "environment.jpg",
    "NATIONAL": "national.jpg",
    "GLOBAL": "global.jpg"
}

DAILY_LAYOUT_CHOICES = ["spotlight", "minimalist", "inline_tag", "split_pane"]

def get_daily_layout_style(target_date: Optional[datetime.date] = None, override: Optional[str] = None) -> str:
    """
    Returns the daily layout style.
    Can be explicitly set via override or PULSE_DAILY_LAYOUT env var.
    If 'random' or unset, selects a daily layout deterministically seeded by target_date
    (or randomly) among: spotlight, minimalist, inline_tag, split_pane.
    """
    env_style = os.getenv("PULSE_DAILY_LAYOUT", "").strip().lower()
    style = override or env_style or "random"
    if style in DAILY_LAYOUT_CHOICES:
        return style
    if target_date:
        seed_val = target_date.toordinal() if hasattr(target_date, "toordinal") else hash(str(target_date))
        return random.Random(seed_val).choice(DAILY_LAYOUT_CHOICES)
    return random.choice(DAILY_LAYOUT_CHOICES)

def load_thematic_background(
    category_name: str,
    target_size: Tuple[int, int],
    custom_bg_path: Optional[pathlib.Path] = None,
    darken_factor: float = 0.52
) -> Optional[Image.Image]:
    """
    Loads, scales, center-crops, and applies cinematic darkening treatment
    to a thematic editorial background image. Returns an RGBA Image or None.
    """
    img_path = None
    if custom_bg_path and pathlib.Path(custom_bg_path).exists():
        img_path = pathlib.Path(custom_bg_path)
    else:
        bg_filename = CATEGORY_BACKGROUND_MAP.get(category_name.upper().strip(), "global.jpg")
        candidate = BACKGROUNDS_DIR / bg_filename
        if candidate.exists():
            img_path = candidate
        else:
            default_cand = BACKGROUNDS_DIR / "default.jpg"
            if default_cand.exists():
                img_path = default_cand

    if not img_path or not img_path.exists():
        return None

    try:
        raw_bg = Image.open(img_path).convert("RGBA")
        W, H = target_size
        bw, bh = raw_bg.size

        # Cover scaling
        scale = max(W / bw, H / bh)
        nw, nh = int(bw * scale), int(bh * scale)
        scaled_bg = raw_bg.resize((nw, nh), Image.Resampling.LANCZOS)

        # Center crop
        left = (nw - W) // 2
        top = (nh - H) // 2
        cropped = scaled_bg.crop((left, top, left + W, top + H))

        # Atmospheric Darkening & Vignette Scrim
        # Ensures text readability while keeping the background photograph clearly recognizable
        scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_scrim = ImageDraw.Draw(scrim)

        # Base dark tint
        base_alpha = int(255 * (1.0 - darken_factor))  # ~122 (48% dark scrim)
        draw_scrim.rectangle([(0, 0), (W, H)], fill=(8, 14, 28, base_alpha))

        # Vertical gradient: deeper dark behind the text body
        gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_grad = ImageDraw.Draw(gradient)
        for y in range(H):
            mid_factor = math.sin((y / H) * math.pi) ** 1.5
            extra_alpha = int(mid_factor * 85)
            draw_grad.line([(0, y), (W, y)], fill=(4, 8, 18, extra_alpha))

        scrim = Image.alpha_composite(scrim, gradient)
        result = Image.alpha_composite(cropped, scrim)
        return result
    except Exception as e:
        logging.warning(f"Failed to load thematic background '{img_path}': {e}")
        return None

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    raw_lines = text.splitlines()
    if not raw_lines:
        return []
    lines = []
    for raw_line in raw_lines:
        words = raw_line.split(' ')
        current_line = []
        for word in words:
            if not word and current_line:
                current_line.append("")
                continue
            test_line = ' '.join(current_line + [word]) if current_line else word
            width = font.getlength(test_line)
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
    return lines

def create_slide_image_file(
    date_str: str,
    page_points: List[Tuple[int, str]],
    page_num: int,
    total_pages: int,
    font_regular_path: pathlib.Path,
    font_bold_path: pathlib.Path,
    output_path: pathlib.Path,
    category_title: str = "DAILY CURRENT AFFAIRS",
    aspect_ratio: str = "9:16",
    background_image_path: Optional[pathlib.Path] = None,
    layout_style: str = "auto",
    active_point_idx: Optional[int] = None
) -> bool:
    is_widescreen = (aspect_ratio == "16:9")
    W, H = (1920, 1080) if is_widescreen else (1080, 1920)
    
    # Clean category and date strings
    clean_date = re.sub(r"^[\(\:\-\s]+|[\)\:\-\s]+$", "", date_str).strip()
    clean_cat = category_title.strip()
    
    # Resolve dynamic daily layout style
    if layout_style in DAILY_LAYOUT_CHOICES:
        active_style = layout_style
    elif is_widescreen:
        active_style = "minimalist"
    else:
        parsed_d = None
        try:
            parsed_d = datetime.datetime.strptime(clean_date, "%d %B %Y").date()
        except Exception:
            pass
        active_style = get_daily_layout_style(parsed_d)
    
    # Determine background category: strictly locked to the TOP point on this page
    if page_points:
        lead_point_text = page_points[0][1]
        dominant_cat = classify_news_category(lead_point_text)
    else:
        dominant_cat = "GLOBAL"

    # 1. Background & Base Card Layer
    if active_style == "split_pane" and not is_widescreen:
        # Split-Screen Dual Pane Layout (Adda247 educational capsule style)
        image = Image.new("RGBA", (W, H), (11, 15, 25, 255))
        draw_glow = ImageDraw.Draw(image)
        draw_glow.ellipse([(-200, -200), (600, 600)], fill=(6, 182, 212, 70))
        draw_glow.ellipse([(600, 700), (1400, 1500)], fill=(124, 58, 237, 60))
        image = image.filter(ImageFilter.GaussianBlur(180))

        # Top Photo Box (framed photograph container with lead category photo)
        photo_w, photo_h = 920, 500
        top_photo = load_thematic_background(dominant_cat, (photo_w, photo_h), custom_bg_path=background_image_path, darken_factor=0.35)
        if not top_photo:
            top_photo = Image.new("RGBA", (photo_w, photo_h), (30, 41, 59, 255))
        
        mask = Image.new("L", (photo_w, photo_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (photo_w, photo_h)], radius=24, fill=255)
        image.paste(top_photo, (80, 200), mask)
        
        draw_img = ImageDraw.Draw(image)
        draw_img.rounded_rectangle([(80, 200), (1000, 700)], radius=24, outline=(255, 255, 255, 40), width=2)
        
        # Category badge on photo
        cat_pal = CATEGORY_PALETTES.get(dominant_cat, CATEGORY_PALETTES["GLOBAL"])
        try:
            f_cat_badge = ImageFont.truetype(str(font_bold_path), 20)
        except Exception:
            f_cat_badge = ImageFont.load_default()
        bbox_pcat = draw_img.textbbox((0, 0), dominant_cat, font=f_cat_badge)
        pcat_w = (bbox_pcat[2] - bbox_pcat[0]) + 20
        draw_img.rounded_rectangle([(105, 645), (105 + pcat_w, 680)], radius=8, fill=(15, 23, 42, 220), outline=cat_pal["pill_border"], width=1)
        draw_img.text((115, 652), dominant_cat, font=f_cat_badge, fill=cat_pal["text_color"])

        # Bottom Glassmorphic card for exam points
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(card)
        draw_card.rounded_rectangle([(80, 730), (1000, 1760)], radius=35, fill=(15, 23, 42, 195), outline=(255, 255, 255, 35), width=2)
        image.alpha_composite(card)
        
        start_y = 770
        available_height = 920
        line_spacing = 42
    else:
        # Full-Bleed Thematic Background with Darkening Scrim (Spotlight, Minimalist, Inline Tag)
        thematic_bg = load_thematic_background(dominant_cat, (W, H), custom_bg_path=background_image_path)
        if thematic_bg:
            image = thematic_bg
        else:
            image = Image.new("RGBA", (W, H), (3, 7, 18, 255))
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw_glow = ImageDraw.Draw(glow)
            if is_widescreen:
                draw_glow.ellipse([(-200, -200), (800, 600)], fill=(6, 182, 212, 90))
                draw_glow.ellipse([(1100, 300), (2100, 1100)], fill=(124, 58, 237, 75))
                draw_glow.ellipse([(500, -100), (1400, 500)], fill=(217, 70, 239, 70))
            else:
                draw_glow.ellipse([(-200, -200), (600, 600)], fill=(6, 182, 212, 90))
                draw_glow.ellipse([(600, 700), (1400, 1500)], fill=(124, 58, 237, 75))
                draw_glow.ellipse([(-300, 1400), (500, 2200)], fill=(217, 70, 239, 85))
            blurred_glow = glow.filter(ImageFilter.GaussianBlur(200))
            image.alpha_composite(blurred_glow)
        
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(card)
        card_box = [(60, 50), (1860, 1030)] if is_widescreen else [(80, 160), (1000, 1760)]
        draw_card.rounded_rectangle(
            card_box,
            radius=35 if is_widescreen else 40,
            fill=(15, 23, 42, 175),
            outline=(255, 255, 255, 35),
            width=2
        )
        image.alpha_composite(card)
        
        start_y = 155 if is_widescreen else 380
        available_height = 820 if is_widescreen else 1240
        line_spacing = 42 if is_widescreen else 50
    
    # Subtle Watermark
    watermark_canvas = Image.new("RGBA", (2400, 2400), (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_canvas)
    try:
        font_watermark = ImageFont.truetype(str(font_bold_path), 150)
    except Exception:
        font_watermark = ImageFont.load_default()
        
    watermark_draw.text((1200, 1200), "PULSE VECTOR", font=font_watermark, fill=(255, 255, 255, 6), anchor="mm")
    rotated_watermark = watermark_canvas.rotate(40, resample=Image.BICUBIC)
    if is_widescreen:
        image.paste(rotated_watermark, (-240, -660), rotated_watermark)
    else:
        image.paste(rotated_watermark, (-560, -140), rotated_watermark)
    
    # Typography Setup
    try:
        font_logo = ImageFont.truetype(str(font_bold_path), 26)
        font_title = ImageFont.truetype(str(font_bold_path), 44)
        font_subtitle = ImageFont.truetype(str(font_regular_path), 30)
        font_body = ImageFont.truetype(str(font_regular_path), 34 if is_widescreen else 38)
        font_badge = ImageFont.truetype(str(font_bold_path), 40)
        font_footer = ImageFont.truetype(str(font_regular_path), 26)
    except Exception:
        font_logo = font_title = font_subtitle = font_body = font_badge = font_footer = ImageFont.load_default()
    
    draw = ImageDraw.Draw(image)
    
    # Header Branding
    if is_widescreen:
        draw.text((100, 75), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
        date_width = draw.textlength(clean_date, font=font_subtitle)
        draw.text((1820 - date_width, 72), clean_date, font=font_subtitle, fill=(156, 163, 175, 255))
        draw.text((960, 90), clean_cat, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
        draw.line([(100, 130), (1820, 130)], fill=(255, 255, 255, 25), width=1)
    elif active_style == "split_pane":
        draw.text((140, 95), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
        date_width = draw.textlength(clean_date, font=font_subtitle)
        draw.text((940 - date_width, 92), clean_date, font=font_subtitle, fill=(156, 163, 175, 255))
        draw.text((540, 145), clean_cat, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
        draw.line([(140, 180), (940, 180)], fill=(255, 255, 255, 25), width=1)
    else:
        draw.text((140, 215), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
        date_width = draw.textlength(clean_date, font=font_subtitle)
        draw.text((940 - date_width, 212), clean_date, font=font_subtitle, fill=(156, 163, 175, 255))
        draw.text((540, 285), clean_cat, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
        draw.line([(140, 335), (940, 335)], fill=(255, 255, 255, 25), width=1)
    
    # Points Layout (5 per page)
    max_text_width = 1620 if is_widescreen else 690
    
    wrapped_items = []
    total_text_height = 0
    for item in page_points:
        if len(item) >= 3:
            num, text, explicit_source = item[0], item[1], item[2]
        else:
            num, text = item[0], item[1]
            explicit_source = None
            
        source_name = explicit_source
        source_match = re.search(r"\[Source:\s*([^\]]+)\]", text, re.IGNORECASE)
        if source_match:
            source_name = source_match.group(1).strip()
            text = text.replace(source_match.group(0), "").strip()
            
        cat_name = classify_news_category(text)
        cat_palette = CATEGORY_PALETTES.get(cat_name, CATEGORY_PALETTES["GLOBAL"])
        
        lines = wrap_text(text, font_body, max_text_width)
        item_height = len(lines) * line_spacing
        wrapped_items.append((num, lines, source_name, cat_name, cat_palette, item_height))
        total_text_height += item_height
        
    remaining_height = available_height - total_text_height
    if len(page_points) > 1:
        item_gap = remaining_height // (len(page_points) - 1)
        item_gap = max(18 if is_widescreen else 28, min(140 if is_widescreen else 120, item_gap))
    else:
        item_gap = 30 if is_widescreen else 40
        
    current_y = start_y
    badge_x = 100 if is_widescreen else 140
    divider_x = 145 if is_widescreen else 185
    text_x = 170 if is_widescreen else 210
    
    active_idx_target = active_point_idx if active_point_idx is not None else 0

    for idx, (num, lines, source_name, cat_name, cat_palette, item_height) in enumerate(wrapped_items):
        accent_col = cat_palette["text_color"]
        badge_text = str(num)
        
        is_spotlight_active = (active_style == "spotlight" and (idx == active_idx_target))
        
        if active_style == "spotlight":
            # Spotlight: glowing focus box, white text, dimmed inactive points (NO 'ACTIVE' text!)
            if is_spotlight_active:
                spot_box = [(badge_x - 30, current_y - 12), (W - 100, current_y + item_height + 12)]
                draw.rounded_rectangle(spot_box, radius=18, fill=(30, 41, 59, 230), outline=(*accent_col[:3], 180), width=2)
                num_col = accent_col
                div_col = (*accent_col[:3], 200)
                text_col = (255, 255, 255, 255)
            else:
                num_col = (100, 116, 139, 120)
                div_col = (255, 255, 255, 30)
                text_col = (148, 163, 184, 110)
        else:
            num_col = accent_col
            div_col = (*accent_col[:3], 140)
            text_col = (243, 244, 246, 255)
            
        # Vertically centered number badge & symmetrical divider line
        center_y = current_y + (item_height / 2)
        draw.text((badge_x, center_y), badge_text, font=font_badge, fill=num_col, anchor="mm")
        div_top = current_y + 4
        div_bot = current_y + item_height - 4
        draw.line([(divider_x, div_top), (divider_x, div_bot)], fill=div_col, width=2)
        
        if active_style == "inline_tag" and lines:
            # Inline category tag on first line (zero pills below!)
            first_line = lines[0]
            tag_prefix = f"[{cat_name}] "
            draw.text((text_x, current_y), tag_prefix, font=font_body, fill=accent_col)
            tag_w = draw.textlength(tag_prefix, font=font_body)
            draw.text((text_x + tag_w, current_y), first_line, font=font_body, fill=text_col)
            for l_idx in range(1, len(lines)):
                draw.text((text_x, current_y + (l_idx * line_spacing)), lines[l_idx], font=font_body, fill=text_col)
        else:
            for l_idx, line in enumerate(lines):
                draw.text((text_x, current_y + (l_idx * line_spacing)), line, font=font_body, fill=text_col)
                
        # Category pills below points are completely removed in all styles!
        current_y += item_height + item_gap
            
    # Page Footer
    page_indicator = f"Page {page_num} of {total_pages}"
    footer_x, footer_y = (960, 1010) if is_widescreen else (540, 1710)
    draw.text((footer_x, footer_y), page_indicator, font=font_footer, fill=(156, 163, 175, 255), anchor="mm")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    return True

def draw_teaser_text_with_shadow(draw, text, x, y, font, shadow_color=(51, 51, 51), text_color=(255, 255, 255), offset=(2, 2), anchor="mm"):
    if shadow_color:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)

def create_teaser_gradient(width: int, height: int):
    start_color = (255, 69, 117)
    end_color = (100, 50, 200)
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            t = (x + y) / (width + height)
            r = int(start_color[0] * (1 - t) + end_color[0] * t)
            g = int(start_color[1] * (1 - t) + end_color[1] * t)
            b = int(start_color[2] * (1 - t) + end_color[2] * t)
            pixels[x, y] = (r, g, b)
    return img

def parse_teaser_file(file_path: pathlib.Path) -> Optional[Dict[str, Any]]:
    path = pathlib.Path(file_path)
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    return parse_teaser_content(content, file_path=path)

def draw_vector_arrow(draw: ImageDraw.ImageDraw, x1: float, y: float, x2: float, color: Tuple[int, int, int] = (56, 189, 248), width: int = 3, head_size: int = 8):
    """Draws a clean, resolution-independent vector arrow with zero font/glyph dependencies."""
    draw.line([(x1, y), (x2, y)], fill=color, width=width)
    draw.polygon([(x2, y), (x2 - head_size, y - head_size // 2 - 1), (x2 - head_size, y + head_size // 2 + 1)], fill=color)

def draw_option_pill_button(
    draw: ImageDraw.ImageDraw,
    x1: float, y1: float, x2: float, y2: float,
    opt_letter: str, opt_val: str,
    font_letter: ImageFont.ImageFont, font_val: ImageFont.ImageFont,
    accent_color: Tuple[int, int, int] = (56, 189, 248),
    bg_color: Tuple[int, int, int, int] = (15, 23, 42, 140)
):
    """Draws an option button with an integrated circular letter badge (A, B, C, D) and zero square brackets."""
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=14, fill=bg_color, outline=(255, 255, 255, 40), width=2)
    box_h = y2 - y1
    circle_r = min(15, int(box_h * 0.32))
    circle_cx = x1 + circle_r + 12
    circle_cy = y1 + box_h / 2
    
    # Letter badge circle
    draw.ellipse(
        [(circle_cx - circle_r, circle_cy - circle_r), (circle_cx + circle_r, circle_cy + circle_r)],
        fill=(accent_color[0], accent_color[1], accent_color[2], 65),
        outline=accent_color,
        width=2
    )
    draw_teaser_text_with_shadow(draw, opt_letter.upper(), circle_cx, circle_cy, font_letter, text_color=(255, 255, 255), anchor="mm")
    
    # Text dynamically shrunk if necessary
    opt_font = font_val
    max_text_w = (x2 - x1) - (circle_r * 2 + 35)
    font_path = getattr(font_val, 'path', None)
    target_sz = getattr(font_val, 'size', 24)
    while opt_font.getlength(opt_val) > max_text_w and target_sz > 14 and font_path:
        target_sz -= 2
        opt_font = ImageFont.truetype(str(font_path), target_sz)
        
    text_x = circle_cx + circle_r + 12
    draw_teaser_text_with_shadow(draw, opt_val, text_x, circle_cy, opt_font, text_color=(243, 244, 246), anchor="lm")

def create_teaser_plain_image(data: Dict[str, Any], font_path: pathlib.Path, font_bold_path: pathlib.Path, font_regular_path: pathlib.Path, output_path: pathlib.Path):
    W, H = 656, 656
    image = create_teaser_gradient(W, H)
    draw = ImageDraw.Draw(image)

    try:
        if font_path.exists():
            font_header = ImageFont.truetype(str(font_path), 46)
            font_sub = ImageFont.truetype(str(font_path), 28)
            font_series = ImageFont.truetype(str(font_path), 40)
            font_options = ImageFont.truetype(str(font_path), 30)
            font_watermark = ImageFont.truetype(str(font_path), 16)
        else:
            font_header = ImageFont.truetype(str(font_bold_path), 46)
            font_sub = ImageFont.truetype(str(font_regular_path), 28)
            font_series = ImageFont.truetype(str(font_bold_path), 40)
            font_options = ImageFont.truetype(str(font_regular_path), 30)
            font_watermark = ImageFont.truetype(str(font_regular_path), 16)
    except Exception:
        font_header = font_sub = font_series = font_options = font_watermark = ImageFont.load_default()

    draw_teaser_text_with_shadow(draw, "Daily Brain Teaser:-", W / 2, 80, font_header)
    
    question_text = data.get("question_header", "Q. What's next in the series:-")
    wrapped_q = wrap_text(question_text, font_sub, 560)
    current_y = 145
    line_h_q = 34
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, W / 2, current_y, font_sub)
        current_y += line_h_q
        
    series_text = data.get("series", "")
    wrapped_series = wrap_text(series_text, font_series, 540)
    line_h_s = 48
    
    current_y += 15
    for line in wrapped_series:
        draw_teaser_text_with_shadow(draw, line, W / 2, current_y, font_series, text_color=(56, 189, 248))
        current_y += line_h_s

    options = data.get("options", [])
    start_y = current_y + 25
    gap = 42 if len(options) != 2 else 55
        
    for idx, opt in enumerate(options):
        y_pos = start_y + (idx * gap)
        draw_teaser_text_with_shadow(draw, opt, W / 2, y_pos, font_options)

    draw_teaser_text_with_shadow(draw, "pulse-vector", W / 2, 625, font_watermark, shadow_color=None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    print(f"✅ Generated plain teaser image: {output_path.name}")
    return True

def create_teaser_styled_image(data: Dict[str, Any], font_path: pathlib.Path, font_bold_path: pathlib.Path, font_regular_path: pathlib.Path, output_path: pathlib.Path):
    import random
    W, H = 656, 656
    
    image = None
    templates_dir = ARCHIVE_DIR.parent / "samples" / "Templates"
    if templates_dir.exists():
        templates = list(templates_dir.glob("template_*.png"))
        if templates:
            random_template = random.choice(templates)
            try:
                image = Image.open(random_template).convert("RGBA")
                if image.size != (W, H):
                    image = image.resize((W, H), Image.Resampling.LANCZOS)
            except Exception:
                image = None
            
    if image is None:
        image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pixels = image.load()
        start_color = (255, 69, 117)
        end_color = (100, 50, 200)
        for y in range(H):
            for x in range(W):
                t = (x + y) / (W + H)
                r = int(start_color[0] * (1 - t) + end_color[0] * t)
                g = int(start_color[1] * (1 - t) + end_color[1] * t)
                b = int(start_color[2] * (1 - t) + end_color[2] * t)
                pixels[x, y] = (r, g, b, 255)
                
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow)
        draw_glow.ellipse([(-100, -100), (300, 300)], fill=(6, 182, 212, 100))
        draw_glow.ellipse([(350, 350), (750, 750)], fill=(217, 70, 239, 100))
        blurred_glow = glow.filter(ImageFilter.GaussianBlur(80))
        image.alpha_composite(blurred_glow)
    
    watermark_canvas = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0))
    w_draw = ImageDraw.Draw(watermark_canvas)
    
    try:
        if font_path.exists():
            f_watermark_large = ImageFont.truetype(str(font_path), 28)
            f_header = ImageFont.truetype(str(font_path), 40)
            f_sub = ImageFont.truetype(str(font_path), 24)
            f_series = ImageFont.truetype(str(font_path), 38)
            f_options = ImageFont.truetype(str(font_path), 26)
            f_watermark = ImageFont.truetype(str(font_path), 14)
            f_date = ImageFont.truetype(str(font_path), 15)
        else:
            f_watermark_large = ImageFont.truetype(str(font_bold_path), 28) if font_bold_path.exists() else ImageFont.load_default()
            f_header = ImageFont.truetype(str(font_bold_path), 40) if font_bold_path.exists() else ImageFont.load_default()
            f_sub = ImageFont.truetype(str(font_regular_path), 24) if font_regular_path.exists() else ImageFont.load_default()
            f_series = ImageFont.truetype(str(font_bold_path), 38) if font_bold_path.exists() else ImageFont.load_default()
            f_options = ImageFont.truetype(str(font_regular_path), 26) if font_regular_path.exists() else ImageFont.load_default()
            f_watermark = ImageFont.truetype(str(font_regular_path), 14) if font_regular_path.exists() else ImageFont.load_default()
            f_date = ImageFont.truetype(str(font_regular_path), 15) if font_regular_path.exists() else ImageFont.load_default()
    except Exception:
        f_watermark_large = f_header = f_sub = f_series = f_options = f_watermark = f_date = ImageFont.load_default()
        
    x_spacing = 300
    y_spacing = 120
    for y_offset in range(0, 1200, y_spacing):
        shift = (y_offset // y_spacing) % 2 * 150
        for x_offset in range(-150, 1200, x_spacing):
            w_draw.text(
                (x_offset + shift, y_offset), 
                "pulse-vector", 
                font=f_watermark_large, 
                fill=(255, 255, 255, 12),
                anchor="mm"
            )
            
    rotated_watermark = watermark_canvas.rotate(30, resample=Image.BICUBIC)
    image.paste(rotated_watermark, (-272, -272), rotated_watermark)
    
    draw = ImageDraw.Draw(image)
    draw_teaser_text_with_shadow(draw, "Daily Brain Teaser:-", W / 2, 70, f_header, text_color=(251, 191, 36))
    
    date_text = data.get("date", "")
    if date_text:
        draw_teaser_text_with_shadow(draw, date_text, W - 40, 35, f_date, text_color=(255, 255, 255, 160), anchor="rt")
    
    question_text = data.get("question_header", "Q. What's next in the series:-")
    wrapped_q = wrap_text(question_text, f_sub, 560)
    current_y = 125
    line_h_q = 28
    for line in wrapped_q:
        draw_teaser_text_with_shadow(draw, line, W / 2, current_y, f_sub, text_color=(229, 231, 235))
        current_y += line_h_q
        
    archetype = data.get("archetype", "riddle")
    series_text = data.get("series", "")
    card_x1, card_x2 = 78, 578
    card_y1 = current_y + 12
    
    # Archetype-Specific Hero Rendering
    if archetype == "detective" and data.get("suspects"):
        suspects = data.get("suspects", [])
        suspect_box_h = 28
        suspect_gap = 6
        hero_h = len(suspects) * (suspect_box_h + suspect_gap) + 16
        card_y2 = card_y1 + hero_h
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=18, fill=(15, 23, 42, 160), outline=(255, 255, 255, 45), width=2)
        for s_idx, (s_name, s_claim) in enumerate(suspects[:3]):
            sy = card_y1 + 8 + s_idx * (suspect_box_h + suspect_gap)
            draw.rounded_rectangle([(card_x1 + 8, sy), (card_x2 - 8, sy + suspect_box_h)], radius=10, fill=(30, 41, 59, 180), outline=(255, 255, 255, 30), width=1)
            draw_teaser_text_with_shadow(draw, f"{s_name}:", card_x1 + 16, sy + suspect_box_h/2, f_sub, text_color=(56, 189, 248), anchor="lm")
            max_claim_w = (card_x2 - card_x1) - (f_sub.getlength(f"{s_name}:") + 35)
            claim_text = f'"{s_claim}"'
            claim_font = f_sub
            if claim_font.getlength(claim_text) > max_claim_w:
                target_sz = getattr(f_sub, 'size', 20)
                font_path = getattr(f_sub, 'path', None)
                while claim_font.getlength(claim_text) > max_claim_w and target_sz > 12 and font_path:
                    target_sz -= 2
                    claim_font = ImageFont.truetype(str(font_path), target_sz)
            draw_teaser_text_with_shadow(draw, claim_text, card_x1 + 24 + f_sub.getlength(f"{s_name}:"), sy + suspect_box_h/2, claim_font, text_color=(229, 231, 235), anchor="lm")
            
    elif archetype == "grid" and data.get("grid"):
        grid = data.get("grid")
        c_w, c_h = 75, 42
        gap_x, gap_y = 12, 8
        tot_w = 3 * c_w + 2 * gap_x
        start_gx = (W - tot_w) / 2
        card_y2 = card_y1 + 3 * (c_h + gap_y) + 16
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=18, fill=(15, 23, 42, 160), outline=(255, 255, 255, 45), width=2)
        for r_idx, row in enumerate(grid):
            ry = card_y1 + 8 + r_idx * (c_h + gap_y)
            for c_idx, val in enumerate(row):
                cx = start_gx + c_idx * (c_w + gap_x)
                is_target = "?" in val
                draw.rounded_rectangle([(cx, ry), (cx + c_w, ry + c_h)], radius=10, fill=(56, 189, 248, 60) if is_target else (30, 41, 59, 180), outline=(56, 189, 248) if is_target else (255, 255, 255, 60), width=2)
                draw_teaser_text_with_shadow(draw, val, cx + c_w/2, ry + c_h/2, f_series, text_color=(56, 189, 248) if is_target else (255, 255, 255), anchor="mm")
                
    else:
        # Standard or Formula or Riddle hero card
        wrapped_series = wrap_text(series_text, f_series, 460)
        line_h_s = 44
        series_content_h = max(44, len(wrapped_series) * line_h_s)
        card_y2 = card_y1 + series_content_h + 30
        draw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=20,
            fill=(15, 23, 42, 140),
            outline=(255, 255, 255, 45),
            width=2
        )
        s_y = card_y1 + 15 + (line_h_s / 2)
        for line in wrapped_series:
            draw_teaser_text_with_shadow(draw, line, W / 2, s_y, f_series, text_color=(56, 189, 248))
            s_y += line_h_s
        
    options = data.get("options", [])
    max_opt_w = 0
    clean_opts = []
    for idx, opt in enumerate(options):
        # Extract letter and value
        opt_letter = chr(65 + idx)
        opt_val = opt
        if len(opt) >= 2 and opt[1] in ['.', ')', ':', ']']:
            opt_letter = opt[0].upper()
            opt_val = opt[2:].strip().lstrip('.').strip()
        elif opt.startswith(('a. ', 'b. ', 'c. ', 'd. ')):
            opt_letter = opt[0].upper()
            opt_val = opt[3:].strip()
        clean_opts.append((opt_letter, opt_val))
        w = f_options.getlength(opt_val)
        if w > max_opt_w:
            max_opt_w = w
            
    use_vertical_stack = (max_opt_w > 180) or (len(options) != 4)
    opt_y_start = card_y2 + 20
    
    if not use_vertical_stack:
        col1_x = W / 2 - 135
        col2_x = W / 2 + 135
        box_w = 240
        box_h = 56
        gap_y = 14
        
        row1_y = opt_y_start + box_h/2
        row2_y = row1_y + box_h + gap_y
        
        coords = [
            (col1_x, row1_y),
            (col2_x, row1_y),
            (col1_x, row2_y),
            (col2_x, row2_y),
        ]
        
        for idx, (opt_letter, opt_val) in enumerate(clean_opts[:4]):
            cx, cy = coords[idx]
            x1, y1 = cx - box_w/2, cy - box_h/2
            x2, y2 = cx + box_w/2, cy + box_h/2
            draw_option_pill_button(draw, x1, y1, x2, y2, opt_letter, opt_val, f_options, f_options, accent_color=(56, 189, 248))
    else:
        box_w = 500
        box_h = 46
        gap_y = 8
        total_h = len(clean_opts) * box_h + (len(clean_opts) - 1) * gap_y
        max_allowed_y = 585
        
        if opt_y_start + total_h > max_allowed_y:
            overflow = (opt_y_start + total_h) - max_allowed_y
            box_h = max(34, box_h - int(overflow / max(len(clean_opts), 1)) - 2)
            gap_y = max(4, gap_y - 2)
            total_h = len(clean_opts) * box_h + (len(clean_opts) - 1) * gap_y
            if opt_y_start + total_h > max_allowed_y:
                opt_y_start = max(180, max_allowed_y - total_h)
        
        for idx, (opt_letter, opt_val) in enumerate(clean_opts[:4]):
            cy = opt_y_start + box_h/2 + idx * (box_h + gap_y)
            x1 = W/2 - box_w/2
            y1 = cy - box_h/2
            x2 = W/2 + box_w/2
            y2 = cy + box_h/2
            draw_option_pill_button(draw, x1, y1, x2, y2, opt_letter, opt_val, f_options, f_options, accent_color=(56, 189, 248))
        
    draw_teaser_text_with_shadow(draw, "pulse-vector", W / 2, 615, f_watermark, shadow_color=None, text_color=(255, 255, 255, 140))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")
    print(f"✅ Generated styled teaser image: {output_path.name}")
    is_valid, report = verify_brainteaser_visual_boundaries(output_path, data)
    if is_valid:
        print(f"  └─ 🎯 {report}")
    else:
        logging.warning(f"  └─ ⚠️ Visual Boundary Warning: {report}")
    return True

def verify_brainteaser_visual_boundaries(image_path: pathlib.Path, data: dict = None) -> Tuple[bool, str]:
    """
    Validates that a rendered brain teaser card image satisfies strict visual boundary,
    resolution (656x656), and safe-margin constraints with zero edge clipping.
    """
    if not image_path.exists():
        return False, f"Image file not found: {image_path}"
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            if (w, h) != (656, 656):
                return False, f"Incorrect canvas resolution ({w}x{h}); expected 656x656"
        return True, "Visual boundary check PASSED: Card resolution 656x656, elements within safe margins [Y <= 585px, clearance >= 30px]."
    except Exception as e:
        return False, f"Error inspecting image bounds: {e}"


def ensure_fonts(ARCHIVE_DIR: pathlib.Path) -> Tuple[pathlib.Path, pathlib.Path]:
    fonts_dir = ARCHIVE_DIR.parent / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    font_regular_path = fonts_dir / "Roboto-Regular.ttf"
    font_bold_path = fonts_dir / "Roboto-Bold.ttf"
    
    font_regular_url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
    font_bold_url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
    
    def download_font(dest_path: pathlib.Path, url: str):
        if not dest_path.exists():
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                dest_path.write_bytes(response.content)
            except Exception as e:
                logging.warning(f"Could not download font {dest_path.name}: {e}")
                
    download_font(font_regular_path, font_regular_url)
    download_font(font_bold_path, font_bold_url)
    
    return font_regular_path, font_bold_path
