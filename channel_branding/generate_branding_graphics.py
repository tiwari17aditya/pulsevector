"""
Pulse Vector — Channel Branding Graphics Generator
Generates broadcast-quality YouTube Channel Banners (2560x1440) and Channel Icons (800x800 / 1024x1024).
Adheres strictly to YouTube safe-zone guidelines:
- Banner full canvas: 2560 x 1440 px (TV display)
- Desktop display: 2560 x 423 px
- Mobile & Desktop universal safe area: 1546 x 423 px (centered: X=507..2053, Y=508..931)
- Profile Icon: 800 x 800 px (circular crop safe area)
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
BANNERS_DIR = BRANDING_DIR / "assets" / "banners"
ICONS_DIR = BRANDING_DIR / "assets" / "icons"
FONTS_DIR = ROOT_DIR / "fonts"

BANNERS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Font Helpers
# ---------------------------------------------------------------------------
def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        FONTS_DIR / ("Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf"),
        FONTS_DIR / "arialbd.ttf" if bold else FONTS_DIR / "arial.ttf",
        FONTS_DIR / "RussoOne.ttf",
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

# ---------------------------------------------------------------------------
# Drawing Helpers: Gradients, Glows & Glassmorphism
# ---------------------------------------------------------------------------
def create_radial_gradient(w: int, h: int, inner_color: tuple, outer_color: tuple, center: tuple = None) -> Image.Image:
    """Creates a smooth 2D radial gradient image."""
    cx = center[0] if center else w / 2.0
    cy = center[1] if center else h / 2.0
    max_r = math.sqrt(cx**2 + cy**2)

    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
    norm = np.clip(dist_from_center / max_r, 0.0, 1.0)

    r = (1.0 - norm) * inner_color[0] + norm * outer_color[0]
    g = (1.0 - norm) * inner_color[1] + norm * outer_color[1]
    b = (1.0 - norm) * inner_color[2] + norm * outer_color[2]
    arr = np.dstack((r, g, b)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

def draw_pill_badge(draw: ImageDraw.ImageDraw, box: tuple, text: str, font: ImageFont.ImageFont,
                    fill_bg: tuple, border_color: tuple, text_color: tuple = (255, 255, 255)):
    """Draws a sleek rounded glassmorphic pill badge with centered label."""
    draw.rounded_rectangle(box, radius=box[3] - box[1], fill=fill_bg, outline=border_color, width=2)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (box[0] + box[2] - tw) // 2
    ty = (box[1] + box[3] - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=text_color)

def draw_pulse_ecg_line(draw: ImageDraw.ImageDraw, start_pt: tuple, end_pt: tuple,
                        color: tuple = (0, 240, 255, 255), width: int = 4):
    """Draws a signature cardiogram / pulse vector line with heartbeat peaks."""
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

    # Glowing pulse dot at terminus
    draw.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill=(255, 255, 255, 255), outline=color, width=2)

# ---------------------------------------------------------------------------
# BANNER 1: Master Multi-Genre Epic Banner (2560 x 1440)
# ---------------------------------------------------------------------------
def generate_master_multigenre_banner(output_path: pathlib.Path):
    W, H = 2560, 1440
    print(f"Rendering Master Multi-Genre Banner ({W}x{H})...")

    # 1. Base Gradient: Deep Obsidian Navy to Cyber Space
    bg = create_radial_gradient(W, H, (18, 28, 48), (6, 10, 18), center=(W // 2, H // 2))
    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 2. Geometric Perspective Vector Grid in Background
    grid_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid_overlay)

    grid_color = (0, 240, 255, 18)
    for y in range(0, H, 60):
        gdraw.line([(0, y), (W, y)], fill=grid_color, width=1)
    for x in range(0, W, 80):
        gdraw.line([(x, 0), (x, H)], fill=grid_color, width=1)

    # Diagonal perspective rays radiating from center
    cx, cy = W // 2, H // 2
    for angle in range(-70, 75, 15):
        rad = math.radians(angle)
        ex = cx + int(1600 * math.cos(rad))
        ey = cy + int(1600 * math.sin(rad))
        gdraw.line([(cx, cy), (ex, ey)], fill=(255, 184, 0, 12), width=1)

    img = Image.alpha_composite(img, grid_overlay)
    draw = ImageDraw.Draw(img)

    # 3. Safe Zone Center Anchor ($X \in [507, 2053]$, $Y \in [508, 931]$)
    safe_top = 508
    safe_bottom = 931
    safe_cy = (safe_top + safe_bottom) // 2  # 720

    # Ambient Glow Aura behind Title
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([cx - 480, safe_cy - 160, cx + 480, safe_cy + 160], fill=(0, 240, 255, 35))
    glow_draw.ellipse([cx - 280, safe_cy - 90, cx + 280, safe_cy + 90], fill=(255, 184, 0, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Left Side Visual Motif: Ancient Dharma & Strategic Intellect (inside desktop band)
    dharma_x = 360
    for r_ring in [120, 95, 70]:
        draw.ellipse([dharma_x - r_ring, safe_cy - r_ring, dharma_x + r_ring, safe_cy + r_ring],
                     outline=(255, 184, 0, 45), width=2)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        draw.line([
            (dharma_x + 30 * math.cos(rad), safe_cy + 30 * math.sin(rad)),
            (dharma_x + 90 * math.cos(rad), safe_cy + 90 * math.sin(rad))
        ], fill=(255, 184, 0, 40), width=2)

    # Right Side Visual Motif: Tactical Survival Crosshair & Cyber Matrix
    tactical_x = W - 360
    draw.ellipse([tactical_x - 110, safe_cy - 110, tactical_x + 110, safe_cy + 110],
                 outline=(0, 240, 255, 45), width=2)
    draw.line([(tactical_x - 130, safe_cy), (tactical_x + 130, safe_cy)], fill=(0, 240, 255, 50), width=2)
    draw.line([(tactical_x, safe_cy - 130), (tactical_x, safe_cy + 130)], fill=(0, 240, 255, 50), width=2)
    draw.rectangle([tactical_x - 65, safe_cy - 65, tactical_x + 65, safe_cy + 65],
                   outline=(16, 185, 129, 50), width=2)

    # 4. Central Main Brand Title: "PULSE VECTOR"
    font_title = get_font(96, bold=True)
    title_text = "PULSE VECTOR"
    t_bbox = font_title.getbbox(title_text)
    tw = t_bbox[2] - t_bbox[0]
    tx = cx - tw // 2
    ty = safe_cy - 130

    # 3D Drop Shadow
    for off in [(0, 6), (0, 4), (0, 2), (-2, 0), (2, 0)]:
        draw.text((tx + off[0], ty + off[1]), title_text, font=font_title, fill=(0, 10, 25, 220))
    # Outer Cyan Glow stroke
    for gx in [-3, -2, 2, 3]:
        for gy in [-3, -2, 2, 3]:
            draw.text((tx + gx, ty + gy), title_text, font=font_title, fill=(0, 200, 255, 80))
    # Crisp Pure White Core
    draw.text((tx, ty), title_text, font=font_title, fill=(255, 255, 255, 255))

    # Electric Pulse ECG Line beneath title
    ecg_y = ty + 115
    draw_pulse_ecg_line(draw, (cx - 360, ecg_y), (cx + 360, ecg_y), color=(0, 240, 255, 240), width=4)

    # Tagline: "WHERE INTELLECT MEETS ACTION"
    font_sub = get_font(30, bold=True)
    sub_text = "WHERE INTELLECT MEETS ACTION"
    s_bbox = font_sub.getbbox(sub_text)
    sw = s_bbox[2] - s_bbox[0]
    draw.text((cx - sw // 2, ecg_y + 22), sub_text, font=font_sub, fill=(255, 184, 0, 255))

    # 5. The 4 Genre Pill Badges (Centered inside safe area)
    font_pill = get_font(21, bold=True)
    pillars = [
        ("CURRENT AFFAIRS", (0, 240, 255, 30), (0, 240, 255, 200), (200, 245, 255)),
        ("BRAIN TEASERS", (168, 85, 247, 30), (168, 85, 247, 200), (243, 232, 255)),
        ("EPIC MAHABHARAT", (255, 184, 0, 30), (255, 184, 0, 200), (254, 243, 199)),
        ("LDoE SURVIVAL", (16, 185, 129, 30), (16, 185, 129, 200), (209, 250, 229)),
    ]

    pill_w = 260
    pill_h = 44
    pill_gap = 20
    total_pills_w = len(pillars) * pill_w + (len(pillars) - 1) * pill_gap
    pill_start_x = cx - total_pills_w // 2
    pill_y = ecg_y + 76

    for i, (ptext, pbg, pborder, pfont_col) in enumerate(pillars):
        px0 = pill_start_x + i * (pill_w + pill_gap)
        draw_pill_badge(draw, (px0, pill_y, px0 + pill_w, pill_y + pill_h),
                        ptext, font_pill, pbg, pborder, text_color=pfont_col)

    # Bottom Handle & Schedule Anchor (Within Safe Area: y <= 915)
    font_footer = get_font(21, bold=False)
    footer_text = "@pulse_vector   •   DAILY SHORTS @ 7:55 AM IST   •   WEEKLY MASTERCLASSES   •   SUBSCRIBE"
    f_bbox = font_footer.getbbox(footer_text)
    fw = f_bbox[2] - f_bbox[0]
    draw.text((cx - fw // 2, pill_y + 60), footer_text, font=font_footer, fill=(148, 163, 184, 255))

    # Save RGB PNG
    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# BANNER 2: Editorial Prestige Minimalist Banner (2560 x 1440)
# ---------------------------------------------------------------------------
def generate_editorial_prestige_banner(output_path: pathlib.Path):
    W, H = 2560, 1440
    print(f"Rendering Editorial Prestige Banner ({W}x{H})...")

    # Dark Slate Obsidian
    img = Image.new("RGB", (W, H), color=(10, 14, 24))
    draw = ImageDraw.Draw(img)

    cx, cy = W // 2, H // 2
    safe_cy = 720

    # Subtle horizontal vector accent lines
    draw.line([(0, safe_cy - 180), (W, safe_cy - 180)], fill=(30, 41, 59), width=1)
    draw.line([(0, safe_cy + 180), (W, safe_cy + 180)], fill=(30, 41, 59), width=1)
    draw.line([(cx - 700, safe_cy - 180), (cx + 700, safe_cy - 180)], fill=(255, 184, 0), width=2)
    draw.line([(cx - 700, safe_cy + 180), (cx + 700, safe_cy + 180)], fill=(0, 240, 255), width=2)

    # Header category kicker
    font_kicker = get_font(24, bold=True)
    kicker = "THE OFFICIAL MULTI-GENRE INTELLIGENCE & GAMING NETWORK"
    kb = font_kicker.getbbox(kicker)
    draw.text((cx - (kb[2] - kb[0]) // 2, safe_cy - 140), kicker, font=font_kicker, fill=(255, 184, 0))

    # Giant Clean Typography
    font_main = get_font(108, bold=True)
    title = "PULSE VECTOR"
    tb = font_main.getbbox(title)
    draw.text((cx - (tb[2] - tb[0]) // 2, safe_cy - 95), title, font=font_main, fill=(255, 255, 255))

    # Middle Split Rules
    font_pillars = get_font(24, bold=True)
    p_text = "CURRENT AFFAIRS  |  BRAIN TEASERS  |  MAHABHARAT  |  LDoE SURVIVAL  |  TECH"
    pb = font_pillars.getbbox(p_text)
    draw.text((cx - (pb[2] - pb[0]) // 2, safe_cy + 42), p_text, font=font_pillars, fill=(0, 240, 255))

    # Subtle Footer
    font_sub = get_font(20, bold=False)
    foot = "@pulse_vector  •  Exam General Awareness, Cognitive Puzzles & Tactical Walkthroughs"
    fb = font_sub.getbbox(foot)
    draw.text((cx - (fb[2] - fb[0]) // 2, safe_cy + 95), foot, font=font_sub, fill=(148, 163, 184))

    img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# BANNER 3: Cyber Tactical & Gaming Hybrid Banner (2560 x 1440)
# ---------------------------------------------------------------------------
def generate_cyber_tactical_banner(output_path: pathlib.Path):
    W, H = 2560, 1440
    print(f"Rendering Cyber Tactical Banner ({W}x{H})...")

    # Dark background with cyber grid and diagonal slashes
    img = Image.new("RGB", (W, H), color=(8, 12, 20))
    draw = ImageDraw.Draw(img)

    cx, safe_cy = W // 2, 720

    # Draw hexagonal / tactical corner brackets
    for dx, dy in [(-850, -170), (850, -170), (-850, 170), (850, 170)]:
        bx, by = cx + dx, safe_cy + dy
        draw.line([(bx - 30, by), (bx + 30, by)], fill=(16, 185, 129), width=3)
        draw.line([(bx, by - 30), (bx, by + 30)], fill=(16, 185, 129), width=3)

    # Main Bold Action Title
    font_title = get_font(102, bold=True)
    title = "PULSE // VECTOR"
    tb = font_title.getbbox(title)
    draw.text((cx - (tb[2] - tb[0]) // 2, safe_cy - 125), title, font=font_title, fill=(255, 255, 255))

    # Tactical HUD Line
    draw_pulse_ecg_line(draw, (cx - 450, safe_cy + 10), (cx + 450, safe_cy + 10), color=(16, 185, 129, 255), width=3)

    # Sub-text
    font_sub = get_font(26, bold=True)
    sub = "TACTICAL SURVIVAL • ANALYTICAL INTELLECT • EPIC LORE"
    sb = font_sub.getbbox(sub)
    draw.text((cx - (sb[2] - sb[0]) // 2, safe_cy + 35), sub, font=font_sub, fill=(255, 184, 0))

    # Badges
    font_tags = get_font(20, bold=True)
    tags = "DAILY CURRENT AFFAIRS [SSC/UPSC] • 8s BRAIN TEASERS • LDoE BUNKER ALFA • MAHABHARAT CHRONICLES"
    tab = font_tags.getbbox(tags)
    draw.text((cx - (tab[2] - tab[0]) // 2, safe_cy + 85), tags, font=font_tags, fill=(0, 240, 255))

    img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# BANNER SAFE ZONE VERIFICATION OVERLAY
# ---------------------------------------------------------------------------
def generate_safe_zone_preview(banner_path: pathlib.Path, output_path: pathlib.Path):
    print("Generating Safe-Zone Verification Overlay...")
    with Image.open(banner_path) as base:
        W, H = base.size
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Desktop Band: Y=508..931 (Height 423)
        # Mobile Safe Area: X=507..2053 (Width 1546), Y=508..931 (Height 423)
        sx0, sy0 = 507, 508
        sx1, sy1 = 2053, 931

        # Shading outside Safe Area
        # Top TV area
        draw.rectangle([0, 0, W, sy0], fill=(0, 0, 0, 110))
        # Bottom TV area
        draw.rectangle([0, 0, W, sy1], fill=(0, 0, 0, 0))
        draw.rectangle([0, sy1, W, H], fill=(0, 0, 0, 110))
        # Left & Right Desktop wings
        draw.rectangle([0, sy0, sx0, sy1], fill=(255, 184, 0, 40))
        draw.rectangle([sx1, sy0, W, sy1], fill=(255, 184, 0, 40))

        # Safe Area Boundary outline
        draw.rectangle([sx0, sy0, sx1, sy1], outline=(0, 255, 0, 230), width=4)
        draw.rectangle([0, sy0, W, sy1], outline=(0, 200, 255, 180), width=2)

        # Labels
        f = get_font(28, bold=True)
        draw.text((sx0 + 20, sy0 + 15), "MOBILE & DESKTOP UNIVERSAL SAFE ZONE (1546 x 423 px)", font=f, fill=(0, 255, 0, 255))
        draw.text((60, sy0 + 15), "DESKTOP WING", font=get_font(22, bold=True), fill=(255, 184, 0, 255))
        draw.text((sx1 + 40, sy0 + 15), "DESKTOP WING", font=get_font(22, bold=True), fill=(255, 184, 0, 255))
        draw.text((60, 60), "TV ONLY CANVAS (2560 x 1440 px)", font=f, fill=(255, 255, 255, 200))

        comp = Image.alpha_composite(base.convert("RGBA"), overlay)
        comp.convert("RGB").save(str(output_path), format="PNG")
        print(f"  -> Saved: {output_path}")

# ---------------------------------------------------------------------------
# ICON 1: Master Pulse Vector Neon Avatar (1024 x 1024 & 800 x 800)
# ---------------------------------------------------------------------------
def generate_master_neon_icon(output_path: pathlib.Path, size: int = 1024):
    print(f"Rendering Master Neon Icon ({size}x{size})...")
    img = Image.new("RGBA", (size, size), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r_outer = int(size * 0.46)

    # 1. Dark Radial Background Plate
    bg = create_radial_gradient(size, size, (22, 34, 58), (8, 12, 22), center=(cx, cy))
    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 2. Glowing Outer Rings (Circular Avatar Border)
    for w_off, col in [(8, (0, 240, 255, 160)), (4, (255, 184, 0, 200)), (2, (255, 255, 255, 240))]:
        draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], outline=col, width=w_off)

    # 3. Geometric Stylized 'V' Vector
    # Thick modern cyber V
    v_top_y = cy - int(size * 0.28)
    v_bottom_y = cy + int(size * 0.28)
    v_span = int(size * 0.32)
    v_thickness = int(size * 0.08)

    # Left arm of V
    p_left_top_outer = (cx - v_span, v_top_y)
    p_left_top_inner = (cx - v_span + v_thickness, v_top_y)
    p_bottom_inner = (cx, v_bottom_y - int(v_thickness * 1.2))
    p_bottom_outer = (cx, v_bottom_y)

    # Right arm of V
    p_right_top_inner = (cx + v_span - v_thickness, v_top_y)
    p_right_top_outer = (cx + v_span, v_top_y)

    # Draw Shadow
    v_poly_left = [p_left_top_outer, p_left_top_inner, p_bottom_inner, p_bottom_outer]
    v_poly_right = [p_right_top_outer, p_right_top_inner, p_bottom_inner, p_bottom_outer]

    for off in [4, 2]:
        draw.polygon([(p[0] + off, p[1] + off) for p in v_poly_left], fill=(0, 0, 0, 180))
        draw.polygon([(p[0] + off, p[1] + off) for p in v_poly_right], fill=(0, 0, 0, 180))

    # Fill V with Electric Cyan & Gold highlights
    draw.polygon(v_poly_left, fill=(0, 220, 255, 255), outline=(255, 255, 255, 220))
    draw.polygon(v_poly_right, fill=(255, 184, 0, 255), outline=(255, 255, 255, 220))

    # 4. Transverse Glowing Cardiogram / Pulse Wave
    # Intersects through the center of the V
    pulse_y = cy + int(size * 0.02)
    p_x0 = cx - int(size * 0.40)
    p_x1 = cx + int(size * 0.40)
    draw_pulse_ecg_line(draw, (p_x0, pulse_y), (p_x1, pulse_y), color=(255, 255, 255, 255), width=max(4, size // 150))
    # Glowing Cyan halo
    draw_pulse_ecg_line(draw, (p_x0, pulse_y), (p_x1, pulse_y), color=(0, 240, 255, 140), width=max(8, size // 80))

    # 5. Core Monogram Typography: "PV" at bottom
    font_tag = get_font(int(size * 0.07), bold=True)
    mono = "PULSE VECTOR"
    mb = font_tag.getbbox(mono)
    mw = mb[2] - mb[0]
    draw.text((cx - mw // 2, cy + int(size * 0.33)), mono, font=font_tag, fill=(255, 255, 255, 240))

    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# ICON 2: Cyber Tactical Shield Avatar (1024 x 1024)
# ---------------------------------------------------------------------------
def generate_tactical_shield_icon(output_path: pathlib.Path, size: int = 1024):
    print(f"Rendering Tactical Shield Icon ({size}x{size})...")
    img = Image.new("RGBA", (size, size), (8, 12, 22, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r_hex = int(size * 0.44)

    # Draw Hexagonal Shield
    angles = [30, 90, 150, 210, 270, 330]
    hex_pts = [(cx + int(r_hex * math.cos(math.radians(a))), cy + int(r_hex * math.sin(math.radians(a)))) for a in angles]
    hex_pts_inner = [(cx + int(r_hex * 0.88 * math.cos(math.radians(a))), cy + int(r_hex * 0.88 * math.sin(math.radians(a)))) for a in angles]

    draw.polygon(hex_pts, fill=(15, 23, 42, 255), outline=(0, 240, 255, 220))
    draw.polygon(hex_pts_inner, fill=(10, 14, 26, 255), outline=(255, 184, 0, 200))

    # Central Crosshair & Pulse Vector
    font_bold = get_font(int(size * 0.28), bold=True)
    tb = font_bold.getbbox("PV")
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    draw.text((cx - tw // 2, cy - th // 2 - tb[1]), "PV", font=font_bold, fill=(255, 255, 255, 255))

    # Pulse line through PV
    draw_pulse_ecg_line(draw, (cx - int(size * 0.32), cy + int(size * 0.12)), (cx + int(size * 0.32), cy + int(size * 0.12)),
                        color=(0, 240, 255, 255), width=max(4, size // 160))

    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# ICON 3: Dharma Vector Gold Avatar (1024 x 1024)
# ---------------------------------------------------------------------------
def generate_dharma_vector_icon(output_path: pathlib.Path, size: int = 1024):
    print(f"Rendering Dharma Vector Gold Icon ({size}x{size})...")
    img = Image.new("RGBA", (size, size), (12, 10, 20, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r_wheel = int(size * 0.42)

    # Golden circular chakra wheel spokes
    for r in [r_wheel, int(r_wheel * 0.85), int(r_wheel * 0.45)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 184, 0, 220), width=max(3, size // 200))

    for a in range(0, 360, 30):
        rad = math.radians(a)
        draw.line([
            (cx + int(r_wheel * 0.45 * math.cos(rad)), cy + int(r_wheel * 0.45 * math.sin(rad))),
            (cx + int(r_wheel * 0.85 * math.cos(rad)), cy + int(r_wheel * 0.85 * math.sin(rad)))
        ], fill=(255, 215, 0, 200), width=max(3, size // 220))

    # Center Cyan Vector Point
    font_bold = get_font(int(size * 0.24), bold=True)
    tb = font_bold.getbbox("V")
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    draw.text((cx - tw // 2, cy - th // 2 - tb[1]), "V", font=font_bold, fill=(0, 240, 255, 255))

    final_img = img.convert("RGB")
    final_img.save(str(output_path), format="PNG", quality=95)
    print(f"  -> Saved: {output_path} ({output_path.stat().st_size // 1024} KB)")

# ---------------------------------------------------------------------------
# Circular Crop Preview for Icons
# ---------------------------------------------------------------------------
def generate_circle_crop_preview(icon_paths: list, output_path: pathlib.Path):
    print("Generating Circular Crop Preview...")
    canvas = Image.new("RGBA", (1800, 650), (15, 23, 42, 255))
    draw = ImageDraw.Draw(canvas)

    f_title = get_font(32, bold=True)
    draw.text((50, 40), "YOUTUBE PROFILE AVATAR CIRCULAR CROP VERIFICATION", font=f_title, fill=(255, 255, 255))

    for idx, (path, label) in enumerate(icon_paths):
        with Image.open(path) as orig:
            orig = orig.convert("RGBA").resize((440, 440), Image.Resampling.LANCZOS)
            # Create Circular Mask
            mask = Image.new("L", (440, 440), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([0, 0, 440, 440], fill=255)

            # Circular cut
            circ = Image.new("RGBA", (440, 440), (0, 0, 0, 0))
            circ.paste(orig, (0, 0), mask=mask)

            # Paste on canvas
            cx_pos = 80 + idx * 560
            canvas.paste(circ, (cx_pos, 110), mask=circ)

            # Draw outer circular outline
            draw.ellipse([cx_pos, 110, cx_pos + 440, 110 + 440], outline=(0, 240, 255, 200), width=3)
            # Label
            fl = get_font(22, bold=True)
            lb = fl.getbbox(label)
            draw.text((cx_pos + 220 - (lb[2] - lb[0]) // 2, 575), label, font=fl, fill=(255, 184, 0))

    canvas.convert("RGB").save(str(output_path), format="PNG")
    print(f"  -> Saved: {output_path}")

# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------
def main():
    print("=" * 64)
    print("  🚀 PULSE VECTOR — CHANNEL BRANDING ASSETS GENERATOR")
    print("=" * 64)

    # 1. Banners (2560x1440)
    banner_multi = BANNERS_DIR / "banner_vector_multigenre_epic.png"
    banner_prestige = BANNERS_DIR / "banner_editorial_prestige.png"
    banner_tactical = BANNERS_DIR / "banner_cyber_tactical.png"
    safe_zone_preview = BANNERS_DIR / "banner_safe_zone_preview.png"

    generate_master_multigenre_banner(banner_multi)
    generate_editorial_prestige_banner(banner_prestige)
    generate_cyber_tactical_banner(banner_tactical)
    generate_safe_zone_preview(banner_multi, safe_zone_preview)

    # 2. Icons (1024x1024 & 800x800)
    icon_neon = ICONS_DIR / "icon_pulse_vector_neon.png"
    icon_shield = ICONS_DIR / "icon_pulse_shield_tactical.png"
    icon_dharma = ICONS_DIR / "icon_dharma_vector_gold.png"
    circle_crop_preview = ICONS_DIR / "icon_circle_crop_preview.png"

    generate_master_neon_icon(icon_neon, size=1024)
    generate_tactical_shield_icon(icon_shield, size=1024)
    generate_dharma_vector_icon(icon_dharma, size=1024)

    # Also save 800x800 versions for standard YouTube spec
    with Image.open(icon_neon) as img:
        img.resize((800, 800), Image.Resampling.LANCZOS).save(str(ICONS_DIR / "icon_pulse_vector_neon_800.png"))

    generate_circle_crop_preview([
        (icon_neon, "Design 1: Master Neon Vector"),
        (icon_shield, "Design 2: Cyber Tactical Shield"),
        (icon_dharma, "Design 3: Dharma Vector Gold")
    ], circle_crop_preview)

    print("\n✅ All 2560x1440 Banners and 1024x1024 Icons generated successfully!")

if __name__ == "__main__":
    main()
