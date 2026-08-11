import os
import re
import sys
import random
import datetime
import pathlib
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding issues with emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Project directory paths
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

# Correct raw URL for ComicNeue-Bold.ttf in the official Google Fonts repository
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Bold.ttf"
FONT_PATH = FONTS_DIR / "ComicNeue-Bold.ttf"

# Fallback fonts
ROBOTO_BOLD = FONTS_DIR / "Roboto-Bold.ttf"
ROBOTO_REGULAR = FONTS_DIR / "Roboto-Regular.ttf"

def download_font():
    if not FONT_PATH.exists():
        print(f"Downloading {FONT_PATH.name} from Google Fonts...")
        try:
            r = requests.get(FONT_URL, timeout=30)
            r.raise_for_status()
            FONT_PATH.write_bytes(r.content)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading font: {e}. Will fall back to local Roboto font.")

def create_gradient(width, height):
    # Vibrant pinkish-red/hot pink to medium blue-purple
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

def parse_teaser_file(file_path):
    path = pathlib.Path(file_path)
    if not path.exists():
        print(f"Error: File {file_path} not found.")
        return None

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None

    first_line = lines[0]
    
    # 1. Parse question and series
    q_index = first_line.find("Q. ")
    if q_index != -1:
        q_text = first_line[q_index + 3:].strip()
    else:
        q_text = first_line
        
    series_text = ""
    question_header = "Q. what's next in the series:-"
    
    if ":" in q_text:
        parts = q_text.split(":", 1)
        question_part = parts[0].strip()
        series_part = parts[1].strip()
        
        # Format the question header
        if "what number comes next" in question_part.lower() or "what's next" in question_part.lower():
            question_header = "Q. what's next in the series:-"
        else:
            question_header = f"Q. {question_part.lower()}:-"
        series_text = series_part
    else:
        series_text = q_text

    # 2. Parse options
    options = []
    for line in lines[1:]:
        if line.startswith("---") or "image generation" in line.lower() or "image_generation" in line.lower():
            break
        # Match options starting with a-d
        if re.match(r"^[a-d]\.\s*", line):
            options.append(line)
            
    # 3. Parse date
    date_text = ""
    match_date = re.search(r"(?:Daily Brain Teaser|Brain Teaser)\s*-\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", first_line, re.IGNORECASE)
    if match_date:
        date_text = match_date.group(1).strip()
    else:
        # Fallback to filename date format brainteaser-16jun26
        match_fn = re.search(r"brainteaser-(\d{1,2}[a-zA-Z]{3}\d{2})", path.name, re.IGNORECASE)
        if match_fn:
            date_str = match_fn.group(1)
            try:
                dt = datetime.datetime.strptime(date_str, "%d%b%y")
                date_text = dt.strftime("%d %B %Y")
            except Exception:
                pass
        if not date_text:
            date_text = datetime.datetime.now().strftime("%d %B %Y")
            
    return {
        "question_header": question_header,
        "series": series_text,
        "options": options,
        "date": date_text
    }

def draw_text_with_shadow(draw, text, x, y, font, shadow_color=(51, 51, 51), text_color=(255, 255, 255), offset=(2, 2), anchor="mm"):
    # Draw shadow
    if shadow_color:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color, anchor=anchor)
    # Draw text
    draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)

def create_plain_image(data, output_path):
    W, H = 656, 656
    image = create_gradient(W, H)
    draw = ImageDraw.Draw(image)

    # Resolve fonts (Comic Neue if downloaded, otherwise Roboto-Bold / Roboto-Regular)
    try:
        if FONT_PATH.exists():
            font_header = ImageFont.truetype(str(FONT_PATH), 46)
            font_sub = ImageFont.truetype(str(FONT_PATH), 32)
            font_series = ImageFont.truetype(str(FONT_PATH), 42)
            font_options = ImageFont.truetype(str(FONT_PATH), 34)
            font_watermark = ImageFont.truetype(str(FONT_PATH), 16)
        else:
            print("Comic Neue font missing. Using Roboto Bold/Regular fallbacks...")
            font_header = ImageFont.truetype(str(ROBOTO_BOLD), 46)
            font_sub = ImageFont.truetype(str(ROBOTO_REGULAR), 32)
            font_series = ImageFont.truetype(str(ROBOTO_BOLD), 42)
            font_options = ImageFont.truetype(str(ROBOTO_REGULAR), 34)
            font_watermark = ImageFont.truetype(str(ROBOTO_REGULAR), 16)
    except Exception as e:
        print(f"Error loading TrueType font: {e}. Using default font.")
        font_header = font_sub = font_series = font_options = font_watermark = ImageFont.load_default()

    # Draw Header
    draw_text_with_shadow(draw, "Daily Brain Teaser:-", W / 2, 140, font_header)

    # Draw Question Header
    draw_text_with_shadow(draw, data["question_header"], W / 2, 225, font_sub)

    # Draw Series
    draw_text_with_shadow(draw, data["series"], W / 2, 305, font_series)

    # Draw Options (vertical centered list)
    options = data["options"]
    start_y = 390
    gap = 50
    if len(options) == 2:
        gap = 65
        start_y = 410
        
    for idx, opt in enumerate(options):
        y_pos = start_y + (idx * gap)
        draw_text_with_shadow(draw, opt, W / 2, y_pos, font_options)

    # Draw Watermark at bottom
    draw_text_with_shadow(draw, "pulse-vector", W / 2, 625, font_watermark, shadow_color=None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    print(f"✅ Plain Brain Teaser image saved to: {output_path}")
    return True

def create_styled_image(data, output_path):
    W, H = 656, 656
    
    # 1. Background image: Try loading a random template from samples/Templates/
    image = None
    templates_dir = PROJECT_ROOT / "samples" / "Templates"
    templates = list(templates_dir.glob("template_*.png"))
    
    if templates:
        random_template = random.choice(templates)
        print(f"Selected random template background: {random_template.name}")
        try:
            image = Image.open(random_template).convert("RGBA")
            if image.size != (W, H):
                image = image.resize((W, H), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Failed to load template {random_template.name}: {e}. Falling back to default gradient.")
            
    if image is None:
        # Fallback background diagonal gradient
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
                
        # Add mesh glows
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow)
        draw_glow.ellipse([(-100, -100), (300, 300)], fill=(6, 182, 212, 100))
        draw_glow.ellipse([(350, 350), (750, 750)], fill=(217, 70, 239, 100))
        blurred_glow = glow.filter(ImageFilter.GaussianBlur(80))
        image.alpha_composite(blurred_glow)
    
    # 2. Add repeating diagonal watermark "pulse-vector"
    # A positive rotation of 30 degrees rotates counter-clockwise.
    # Text originally drawn horizontally will go from bottom-left to top-right.
    watermark_canvas = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0))
    w_draw = ImageDraw.Draw(watermark_canvas)
    
    # Resolve fonts
    fallback_bold = ROBOTO_BOLD if ROBOTO_BOLD.exists() else None
    fallback_regular = ROBOTO_REGULAR if ROBOTO_REGULAR.exists() else None
    
    try:
        if FONT_PATH.exists():
            f_watermark_large = ImageFont.truetype(str(FONT_PATH), 28) # repeating watermark size
            f_header = ImageFont.truetype(str(FONT_PATH), 44)
            f_sub = ImageFont.truetype(str(FONT_PATH), 28)
            f_series = ImageFont.truetype(str(FONT_PATH), 42)
            f_options = ImageFont.truetype(str(FONT_PATH), 32)
            f_watermark = ImageFont.truetype(str(FONT_PATH), 14)
            f_date = ImageFont.truetype(str(FONT_PATH), 16)
        else:
            f_watermark_large = ImageFont.truetype(str(fallback_bold), 28) if fallback_bold else ImageFont.load_default()
            f_header = ImageFont.truetype(str(fallback_bold), 44) if fallback_bold else ImageFont.load_default()
            f_sub = ImageFont.truetype(str(fallback_regular), 28) if fallback_regular else ImageFont.load_default()
            f_series = ImageFont.truetype(str(fallback_bold), 42) if fallback_bold else ImageFont.load_default()
            f_options = ImageFont.truetype(str(fallback_regular), 32) if fallback_regular else ImageFont.load_default()
            f_watermark = ImageFont.truetype(str(fallback_regular), 14) if fallback_regular else ImageFont.load_default()
            f_date = ImageFont.truetype(str(fallback_regular), 16) if fallback_regular else ImageFont.load_default()
    except Exception:
        f_watermark_large = f_header = f_sub = f_series = f_options = f_watermark = f_date = ImageFont.load_default()
        
    # Draw repeating pattern
    x_spacing = 300
    y_spacing = 120
    for y_offset in range(0, 1200, y_spacing):
        shift = (y_offset // y_spacing) % 2 * 150
        for x_offset in range(-150, 1200, x_spacing):
            w_draw.text(
                (x_offset + shift, y_offset), 
                "pulse-vector", 
                font=f_watermark_large, 
                fill=(255, 255, 255, 12), # low opacity (5%)
                anchor="mm"
            )
            
    # Rotate the watermark canvas by 30 degrees to make it go from bottom-left to top-right
    rotated_watermark = watermark_canvas.rotate(30, resample=Image.BICUBIC)
    image.paste(rotated_watermark, (-272, -272), rotated_watermark)
    
    # Draw logic on top
    draw = ImageDraw.Draw(image)
    
    # Header
    draw_text_with_shadow(draw, "Daily Brain Teaser:-", W / 2, 80, f_header, text_color=(251, 191, 36)) # Gold color
    
    # Date at top-right corner
    date_text = data.get("date", "")
    if date_text:
        draw_text_with_shadow(draw, date_text, W - 40, 45, f_date, text_color=(255, 255, 255, 180), anchor="rt")
    
    # Question Header
    draw_text_with_shadow(draw, data["question_header"], W / 2, 150, f_sub, text_color=(229, 231, 235))
    
    # Series Container (Glassmorphic Card)
    card_x1, card_y1, card_x2, card_y2 = 78, 205, 578, 295
    draw.rounded_rectangle(
        [(card_x1, card_y1), (card_x2, card_y2)],
        radius=20,
        fill=(15, 23, 42, 140), # Slate-900 with opacity
        outline=(255, 255, 255, 45),
        width=2
    )
    # Draw Series text inside
    draw_text_with_shadow(draw, data["series"], W / 2, (card_y1 + card_y2) / 2, f_series, text_color=(56, 189, 248)) # Sky blue
    
    # Draw Options in 2x2 grid
    options = data["options"]
    col1_x = W / 2 - 135
    col2_x = W / 2 + 135
    
    box_w = 240
    box_h = 70
    
    row1_y = 370
    row2_y = 475
    
    coords = [
        (col1_x, row1_y), # a
        (col2_x, row1_y), # b
        (col1_x, row2_y), # c
        (col2_x, row2_y), # d
    ]
    
    for idx, opt in enumerate(options):
        if idx >= len(coords):
            break
        cx, cy = coords[idx]
        x1, y1 = cx - box_w/2, cy - box_h/2
        x2, y2 = cx + box_w/2, cy + box_h/2
        
        # Draw Glassmorphic Box
        draw.rounded_rectangle(
            [(x1, y1), (x2, y2)],
            radius=15,
            fill=(15, 23, 42, 120),
            outline=(255, 255, 255, 35),
            width=2
        )
        
        # Draw option text inside box
        draw_text_with_shadow(draw, opt, cx, cy, f_options, text_color=(255, 255, 255))
        
    # Draw Watermark at the bottom
    draw_text_with_shadow(draw, "pulse-vector", W / 2, 615, f_watermark, shadow_color=None, text_color=(255, 255, 255, 140))
    
    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")
    print(f"✅ Recreated STYLED Brain Teaser image saved to: {output_path}")
    return True

def generate_teaser_images(file_path):
    download_font()
    data = parse_teaser_file(file_path)
    if not data:
        print("Failed to parse teaser content.")
        return False

    txt_path = pathlib.Path(file_path)
    plain_img_path = txt_path.with_name(f"{txt_path.stem}.png")
    styled_img_path = txt_path.with_name(f"{txt_path.stem}_styled.png")

    create_plain_image(data, plain_img_path)
    create_styled_image(data, styled_img_path)
    return True

if __name__ == "__main__":
    import sys
    default_txt = PROJECT_ROOT / "pulse_archive/2026/June/Brain_Teasers/brainteaser-16jun26.txt"
    target_file = sys.argv[1] if len(sys.argv) > 1 else str(default_txt)
    
    print(f"Generating teaser images for: {target_file}")
    generate_teaser_images(target_file)
