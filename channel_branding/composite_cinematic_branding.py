"""
Pulse Vector — Cinematic YouTube Branding Compositor
Composites the photorealistic AI-generated backgrounds and 3D emblem with
crisp typography, glassmorphic pill badges, and pixel-perfect YouTube Safe-Zone alignment.
"""

import os
import sys
import math
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
BRANDING_DIR = pathlib.Path(__file__).resolve().parent
RAW_DIR = BRANDING_DIR / "assets" / "raw_art"
BANNERS_DIR = BRANDING_DIR / "assets" / "banners"
ICONS_DIR = BRANDING_DIR / "assets" / "icons"
FONTS_DIR = ROOT_DIR / "fonts"

BANNERS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        FONTS_DIR / ("Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"),
        FONTS_DIR / "arialbd.ttf" if bold else FONTS_DIR / "arial.ttf",
        pathlib.Path("C:/Windows/Fonts/segoeuib.ttf") if bold else pathlib.Path("C:/Windows/Fonts/segoeui.ttf"),
        pathlib.Path("C:/Windows/Fonts/arialbd.ttf") if bold else pathlib.Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for c in candidates:
        if c.exists():
            try:
                return ImageFont.truetype(str(c), size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_pill_badge(draw: ImageDraw.ImageDraw, box: tuple, text: str, font: ImageFont.ImageFont,
                    fill_bg: tuple, border_color: tuple, text_color: tuple = (255, 255, 255)):
    """Draws a refined glassmorphic pill badge with centered label."""
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill_bg, outline=border_color, width=2)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (box[0] + box[2] - tw) // 2
    ty = (box[1] + box[3] - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=text_color)

def draw_pulse_ecg_line(draw: ImageDraw.ImageDraw, start_pt: tuple, end_pt: tuple,
                        color: tuple = (0, 240, 255, 255), width: int = 4):
    """Draws an electric cardiogram / pulse vector line with heartbeat peaks."""
    x0, y0 = start_pt
    x1, y1 = end_pt
    dx = x1 - x0

    points = [
        (x0, y0),
        (x0 + dx * 0.28, y0),
        (x0 + dx * 0.35, y0 - 18),
        (x0 + dx * 0.40, y0 + 16),
        (x0 + dx * 0.48, y0 - 45),   # Major QRS Spike
        (x0 + dx * 0.54, y0 + 35),
        (x0 + dx * 0.60, y0 - 10),
        (x0 + dx * 0.66, y0),
        (x0 + dx * 0.85, y0),
        (x1, y1)
    ]
    draw.line(points, fill=color, width=width, joint="curve")
    draw.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill=(255, 255, 255, 255), outline=color, width=2)

# ---------------------------------------------------------------------------
# 1. Master Multi-Genre Cinematic Banner (2560 x 1440)
# ---------------------------------------------------------------------------
def composite_multigenre_banner(raw_bg_path: pathlib.Path, output_path: pathlib.Path):
    W, H = 2560, 1440
    print(f"Compositing Master Multi-Genre Cinematic Banner ({W}x{H})...")

    with Image.open(raw_bg_path) as bg_raw:
        # Resize/crop to 2560x1440
        bg = bg_raw.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)

    # 1. Soft Dark Vignette in the Center Safe Zone to make typography pop
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    cx, cy = W // 2, 720

    # Draw dark radial backing behind central text
    for r in range(550, 200, -20):
        alpha = int(140 * (1.0 - (r - 200) / 350))
        vdraw.ellipse([cx - r - 150, cy - r // 2 - 30, cx + r + 150, cy + r // 2 + 30], fill=(5, 10, 20, alpha))
    vignette = vignette.filter(ImageFilter.GaussianBlur(30))

    img = Image.alpha_composite(bg, vignette)
    draw = ImageDraw.Draw(img)

    # 2. Main Title: "PULSE VECTOR"
    font_title = get_font(104, bold=True)
    title_text = "PULSE VECTOR"
    tb = font_title.getbbox(title_text)
    tw = tb[2] - tb[0]
    tx = cx - tw // 2
    ty = cy - 135

    # 3D Shadow Layers
    for off in [(0, 8), (0, 6), (0, 4), (-3, 0), (3, 0)]:
        draw.text((tx + off[0], ty + off[1]), title_text, font=font_title, fill=(0, 0, 0, 230))
    # Glowing Cyan Edge
    for gx in [-3, -2, 2, 3]:
        for gy in [-3, -2, 2, 3]:
            draw.text((tx + gx, ty + gy), title_text, font=font_title, fill=(0, 240, 255, 90))
    # Crisp Pure White Core
    draw.text((tx, ty), title_text, font=font_title, fill=(255, 255, 255, 255))

    # Electric Pulse ECG Line
    ecg_y = ty + 125
    draw_pulse_ecg_line(draw, (cx - 400, ecg_y), (cx + 400, ecg_y), color=(0, 240, 255, 255), width=4)

    # Tagline: "WHERE INTELLECT MEETS ACTION"
    font_sub = get_font(32, bold=True)
    sub_text = "WHERE INTELLECT MEETS ACTION"
    sb = font_sub.getbbox(sub_text)
    sw = sb[2] - sb[0]
    # Shadow + Text
    draw.text((cx - sw // 2 + 2, ecg_y + 24), sub_text, font=font_sub, fill=(0, 0, 0, 220))
    draw.text((cx - sw // 2, ecg_y + 22), sub_text, font=font_sub, fill=(255, 184, 0, 255))

    # 3. Four Glassmorphic Category Badges
    font_pill = get_font(21, bold=True)
    pillars = [
        ("CURRENT AFFAIRS", (0, 240, 255, 45), (0, 240, 255, 230), (220, 248, 255)),
        ("BRAIN TEASERS", (168, 85, 247, 45), (168, 85, 247, 230), (245, 235, 255)),
        ("EPIC MAHABHARAT", (255, 184, 0, 45), (255, 184, 0, 230), (255, 245, 210)),
        ("LDoE SURVIVAL", (16, 185, 129, 45), (16, 185, 129, 230), (215, 255, 235)),
    ]

    pill_w = 265
    pill_h = 44
    pill_gap = 20
    total_w = len(pillars) * pill_w + (len(pillars) - 1) * pill_gap
    start_x = cx - total_w // 2
    pill_y = ecg_y + 78

    for i, (ptext, pbg, pborder, pfont_col) in enumerate(pillars):
        px0 = start_x + i * (pill_w + pill_gap)
        draw_pill_badge(draw, (px0, pill_y, px0 + pill_w, pill_y + pill_h),
                        ptext, font_pill, pbg, pborder, text_color=pfont_col)

    # 4. Footer Line: Handle, Schedule & Subscribe CTA
    font_foot = get_font(21, bold=False)
    foot = "@pulse_vector   •   DAILY SHORTS @ 7:55 AM IST   •   WEEKLY MASTERCLASSES   •   SUBSCRIBE"
    fb = font_foot.getbbox(foot)
    fw = fb[2] - fb[0]
    draw.text((cx - fw // 2 + 2, pill_y + 60), foot, font=font_foot, fill=(0, 0, 0, 220))
    draw.text((cx - fw // 2, pill_y + 58), foot, font=font_foot, fill=(203, 213, 225, 255))

    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# 2. Editorial Geopolitical Intelligence Banner (2560 x 1440)
# ---------------------------------------------------------------------------
def composite_editorial_banner(raw_bg_path: pathlib.Path, output_path: pathlib.Path):
    W, H = 2560, 1440
    print(f"Compositing Editorial Geopolitical Banner ({W}x{H})...")

    with Image.open(raw_bg_path) as bg_raw:
        bg = bg_raw.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)

    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    cx, cy = W // 2, 720

    for r in range(600, 200, -20):
        alpha = int(150 * (1.0 - (r - 200) / 400))
        vdraw.ellipse([cx - r - 200, cy - r // 2 - 20, cx + r + 200, cy + r // 2 + 20], fill=(8, 14, 28, alpha))
    vignette = vignette.filter(ImageFilter.GaussianBlur(35))

    img = Image.alpha_composite(bg, vignette)
    draw = ImageDraw.Draw(img)

    # Kicker
    font_kicker = get_font(24, bold=True)
    kicker = "INTELLIGENCE • STRATEGY • COGNITIVE CHALLENGES"
    kb = font_kicker.getbbox(kicker)
    draw.text((cx - (kb[2] - kb[0]) // 2, cy - 145), kicker, font=font_kicker, fill=(255, 184, 0, 255))

    # Bold Clean Title
    font_title = get_font(110, bold=True)
    title_text = "PULSE VECTOR"
    tb = font_title.getbbox(title_text)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2 + 3, cy - 100 + 3), title_text, font=font_title, fill=(0, 0, 0, 240))
    draw.text((cx - tw // 2, cy - 100), title_text, font=font_title, fill=(255, 255, 255, 255))

    # Clean Divider Line
    draw.line([(cx - 480, cy + 30), (cx + 480, cy + 30)], fill=(0, 240, 255, 200), width=2)

    # Sub-Pillars
    font_sub = get_font(23, bold=True)
    sub = "GLOBAL CURRENT AFFAIRS  |  BRAIN TEASERS  |  MAHABHARAT  |  LDoE SURVIVAL"
    sb = font_sub.getbbox(sub)
    draw.text((cx - (sb[2] - sb[0]) // 2, cy + 46), sub, font=font_sub, fill=(224, 242, 254, 255))

    # Handle & Schedule
    font_foot = get_font(20, bold=False)
    foot = "@pulse_vector  •  Exam General Awareness, Logical Riddles & Tactical Walkthroughs"
    fb = font_foot.getbbox(foot)
    draw.text((cx - (fb[2] - fb[0]) // 2, cy + 95), foot, font=font_foot, fill=(148, 163, 184, 255))

    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# 3. 3D Titanium & Gold Profile Icons (1024x1024 and 800x800)
# ---------------------------------------------------------------------------
def composite_3d_avatar_icons(raw_avatar_path: pathlib.Path):
    print("Compositing 3D Titanium & Gold Profile Avatars...")
    with Image.open(raw_avatar_path) as av_raw:
        av = av_raw.convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(av)
    cx, cy = 512, 512
    r_outer = 485

    # Glowing Cyan & Gold Edge Rings on outer circumference
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], outline=(0, 240, 255, 230), width=6)
    draw.ellipse([cx - r_outer + 6, cy - r_outer + 6, cx + r_outer - 6, cy + r_outer - 6], outline=(255, 184, 0, 180), width=3)

    # Master 1024x1024
    master_p = ICONS_DIR / "icon_pulse_vector_3d_master.png"
    av.convert("RGB").save(str(master_p), format="PNG", quality=95)
    print(f"  -> Saved: {master_p} ({master_p.stat().st_size // 1024} KB)")

    # Standard 800x800
    std_p = ICONS_DIR / "icon_pulse_vector_3d_800.png"
    av.resize((800, 800), Image.Resampling.LANCZOS).convert("RGB").save(str(std_p), format="PNG", quality=95)
    print(f"  -> Saved: {std_p} ({std_p.stat().st_size // 1024} KB)")

    # Circular Crop Verification
    crop_canvas = Image.new("RGBA", (1200, 600), (12, 16, 28, 255))
    cdraw = ImageDraw.Draw(crop_canvas)

    f_head = get_font(28, bold=True)
    cdraw.text((50, 40), "YOUTUBE PROFILE AVATAR — 3D TITANIUM CIRCULAR CROP VERIFICATION", font=f_head, fill=(255, 255, 255))

    # Create circular cut
    mask = Image.new("L", (440, 440), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse([0, 0, 440, 440], fill=255)

    av_small = av.resize((440, 440), Image.Resampling.LANCZOS)
    circ = Image.new("RGBA", (440, 440), (0, 0, 0, 0))
    circ.paste(av_small, (0, 0), mask=mask)

    # 1. Dark Theme Preview
    crop_canvas.paste(circ, (120, 100), mask=circ)
    cdraw.ellipse([120, 100, 560, 540], outline=(0, 240, 255, 220), width=3)
    cdraw.text((220, 555), "Dark YouTube Mode", font=get_font(20, bold=True), fill=(203, 213, 225))

    # 2. Light Theme Preview
    cdraw.rectangle([660, 100, 1100, 540], fill=(245, 247, 250, 255))
    crop_canvas.paste(circ, (660, 100), mask=circ)
    cdraw.ellipse([660, 100, 1100, 540], outline=(15, 23, 42, 180), width=3)
    cdraw.text((760, 555), "Light YouTube Mode", font=get_font(20, bold=True), fill=(203, 213, 225))

    crop_p = ICONS_DIR / "icon_circle_crop_preview.png"
    crop_canvas.convert("RGB").save(str(crop_p), format="PNG", quality=95)
    print(f"  -> Saved: {crop_p} ({crop_p.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# 4. Safe-Zone Overlay Generator
# ---------------------------------------------------------------------------
def generate_safe_zone_overlay(banner_path: pathlib.Path, output_path: pathlib.Path):
    print("Generating Safe-Zone Verification Overlay...")
    with Image.open(banner_path) as base:
        W, H = base.size
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        sx0, sy0 = 507, 508
        sx1, sy1 = 2053, 931

        # Shading outside Safe Area
        draw.rectangle([0, 0, W, sy0], fill=(0, 0, 0, 120))
        draw.rectangle([0, sy1, W, H], fill=(0, 0, 0, 120))
        draw.rectangle([0, sy0, sx0, sy1], fill=(255, 184, 0, 35))
        draw.rectangle([sx1, sy0, W, sy1], fill=(255, 184, 0, 35))

        draw.rectangle([sx0, sy0, sx1, sy1], outline=(0, 255, 0, 240), width=4)
        draw.rectangle([0, sy0, W, sy1], outline=(0, 200, 255, 180), width=2)

        f = get_font(28, bold=True)
        draw.text((sx0 + 20, sy0 + 15), "MOBILE & DESKTOP UNIVERSAL SAFE ZONE (1546 x 423 px)", font=f, fill=(0, 255, 0, 255))
        draw.text((60, sy0 + 15), "DESKTOP WING", font=get_font(22, bold=True), fill=(255, 184, 0, 255))
        draw.text((sx1 + 40, sy0 + 15), "DESKTOP WING", font=get_font(22, bold=True), fill=(255, 184, 0, 255))
        draw.text((60, 60), "TV ONLY CANVAS (2560 x 1440 px)", font=f, fill=(255, 255, 255, 200))

        comp = Image.alpha_composite(base.convert("RGBA"), overlay)
        comp.convert("RGB").save(str(output_path), format="PNG")
        print(f"  -> Saved: {output_path}")

def main():
    print("=" * 64)
    print("  🚀 PULSE VECTOR — CINEMATIC BRANDING COMPOSITOR")
    print("=" * 64)

    raw_nexus = RAW_DIR / "banner_nexus_raw.jpg"
    raw_editorial = RAW_DIR / "banner_editorial_raw.jpg"
    raw_avatar = RAW_DIR / "avatar_emblem_raw.jpg"

    b_nexus = BANNERS_DIR / "banner_cinematic_multigenre_master.png"
    b_editorial = BANNERS_DIR / "banner_cinematic_editorial_master.png"
    safe_overlay = BANNERS_DIR / "banner_safe_zone_preview.png"

    # Composite Banners
    composite_multigenre_banner(raw_nexus, b_nexus)
    composite_editorial_banner(raw_editorial, b_editorial)
    generate_safe_zone_overlay(b_nexus, safe_overlay)

    # Composite Avatars
    composite_3d_avatar_icons(raw_avatar)

    print("\n✅ All cinematic 2560x1440 banners & 3D icons composited successfully!")

if __name__ == "__main__":
    main()
