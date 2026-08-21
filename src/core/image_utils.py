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
from .content_parser import parse_teaser_content

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
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
    category_title: str = "DAILY CURRENT AFFAIRS"
) -> bool:
    W, H = 1080, 1920
    
    # Clean category and date strings
    clean_date = re.sub(r"^[\(\:\-\s]+|[\)\:\-\s]+$", "", date_str).strip()
    clean_cat = category_title.strip()
    
    # Base dark background
    image = Image.new("RGBA", (W, H), (3, 7, 18, 255))
    
    # Glowing Ambient Orbs
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([(-200, -200), (600, 600)], fill=(6, 182, 212, 90))
    draw_glow.ellipse([(600, 700), (1400, 1500)], fill=(124, 58, 237, 75))
    draw_glow.ellipse([(-300, 1400), (500, 2200)], fill=(217, 70, 239, 85))
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(200))
    image.alpha_composite(blurred_glow)
    
    # Glassmorphic Main Card Layer
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(card)
    card_box = [(80, 160), (1000, 1760)]
    draw_card.rounded_rectangle(
        card_box,
        radius=40,
        fill=(15, 23, 42, 165),
        outline=(255, 255, 255, 35),
        width=2
    )
    image.alpha_composite(card)
    
    # Subtle Watermark
    watermark_canvas = Image.new("RGBA", (2200, 2200), (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_canvas)
    try:
        font_watermark = ImageFont.truetype(str(font_bold_path), 150)
    except Exception:
        font_watermark = ImageFont.load_default()
        
    watermark_draw.text((1100, 1100), "PULSE VECTOR", font=font_watermark, fill=(255, 255, 255, 6), anchor="mm")
    rotated_watermark = watermark_canvas.rotate(40, resample=Image.BICUBIC)
    image.paste(rotated_watermark, (-560, -140), rotated_watermark)
    
    # Typography Setup
    try:
        font_logo = ImageFont.truetype(str(font_bold_path), 26)
        font_title = ImageFont.truetype(str(font_bold_path), 44)
        font_subtitle = ImageFont.truetype(str(font_regular_path), 30)
        font_body = ImageFont.truetype(str(font_regular_path), 38)
        font_badge = ImageFont.truetype(str(font_bold_path), 40)
        font_footer = ImageFont.truetype(str(font_regular_path), 26)
        font_source = ImageFont.truetype(str(font_regular_path), 24)
    except Exception:
        font_logo = font_title = font_subtitle = font_body = font_badge = font_footer = font_source = ImageFont.load_default()
    
    draw = ImageDraw.Draw(image)
    
    # Header Branding
    draw.text((140, 215), "P U L S E   V E C T O R", font=font_logo, fill=(255, 255, 255, 80))
    date_width = draw.textlength(clean_date, font=font_subtitle)
    draw.text((940 - date_width, 212), clean_date, font=font_subtitle, fill=(156, 163, 175, 255))
    draw.text((540, 285), clean_cat, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
    draw.line([(140, 335), (940, 335)], fill=(255, 255, 255, 25), width=1)
    
    # Points Layout (5 per page)
    start_y = 380
    max_text_width = 690
    line_spacing = 50
    available_height = 1240
    
    wrapped_items = []
    total_text_height = 0
    for num, text in page_points:
        source_name = None
        source_match = re.search(r"\[Source:\s*([^\]]+)\]", text, re.IGNORECASE)
        if source_match:
            source_name = source_match.group(1).strip()
            text = text.replace(source_match.group(0), "").strip()
            
        lines = wrap_text(text, font_body, max_text_width)
        item_height = len(lines) * line_spacing
        if source_name:
            item_height += 35
        wrapped_items.append((num, lines, source_name, item_height))
        total_text_height += item_height
        
    remaining_height = available_height - total_text_height
    if len(page_points) > 1:
        item_gap = remaining_height // (len(page_points) - 1)
        item_gap = max(40, min(220, item_gap))
    else:
        item_gap = 40
        
    current_y = start_y
    for idx, (num, lines, source_name, item_height) in enumerate(wrapped_items):
        badge_text = f"{num:02d}"
        draw.text((140, current_y + 3), badge_text, font=font_badge, fill=(56, 189, 248, 255))
        draw.line([(185, current_y + 5), (185, current_y + max(35, item_height - 5))], fill=(56, 189, 248, 80), width=2)
        
        for l_idx, line in enumerate(lines):
            draw.text((210, current_y + (l_idx * line_spacing)), line, font=font_body, fill=(243, 244, 246, 255))
            
        if source_name:
            source_y = current_y + (len(lines) * line_spacing) + 5
            draw.text((210, source_y), f"Source: {source_name}", font=font_source, fill=(56, 189, 248, 200))
            
        current_y += item_height + item_gap
            
    # Page Footer
    page_indicator = f"Page {page_num} of {total_pages}"
    draw.text((540, 1710), page_indicator, font=font_footer, fill=(156, 163, 175, 255), anchor="mm")
    
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
        
    series_text = data.get("series", "")
    wrapped_series = wrap_text(series_text, f_series, 460)
    line_h_s = 44
    series_content_h = len(wrapped_series) * line_h_s
    
    card_x1, card_x2 = 78, 578
    card_y1 = current_y + 12
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
    for opt in options:
        w = f_options.getlength(opt)
        if w > max_opt_w:
            max_opt_w = w
            
    use_vertical_stack = (max_opt_w > 200) or (len(options) != 4)
    opt_y_start = card_y2 + 20
    
    if not use_vertical_stack:
        col1_x = W / 2 - 135
        col2_x = W / 2 + 135
        box_w = 240
        box_h = 60
        gap_y = 15
        
        row1_y = opt_y_start + box_h/2
        row2_y = row1_y + box_h + gap_y
        
        coords = [
            (col1_x, row1_y),
            (col2_x, row1_y),
            (col1_x, row2_y),
            (col2_x, row2_y),
        ]
        
        for idx, opt in enumerate(options):
            cx, cy = coords[idx]
            x1, y1 = cx - box_w/2, cy - box_h/2
            x2, y2 = cx + box_w/2, cy + box_h/2
            
            draw.rounded_rectangle(
                [(x1, y1), (x2, y2)],
                radius=15,
                fill=(15, 23, 42, 120),
                outline=(255, 255, 255, 35),
                width=2
            )
            draw_teaser_text_with_shadow(draw, opt, cx, cy, f_options, text_color=(255, 255, 255))
    else:
        box_w = 500
        box_h = 48
        gap_y = 8
        
        for idx, opt in enumerate(options):
            cy = opt_y_start + box_h/2 + idx * (box_h + gap_y)
            x1 = W/2 - box_w/2
            y1 = cy - box_h/2
            x2 = W/2 + box_w/2
            y2 = cy + box_h/2
            
            draw.rounded_rectangle(
                [(x1, y1), (x2, y2)],
                radius=12,
                fill=(15, 23, 42, 120),
                outline=(255, 255, 255, 35),
                width=2
            )
            draw_teaser_text_with_shadow(
                draw, 
                opt, 
                x1 + 25, 
                cy, 
                f_options, 
                text_color=(255, 255, 255), 
                anchor="lm"
            )
        
    draw_teaser_text_with_shadow(draw, "pulse-vector", W / 2, 615, f_watermark, shadow_color=None, text_color=(255, 255, 255, 140))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")
    print(f"✅ Generated styled teaser image: {output_path.name}")
    return True

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
