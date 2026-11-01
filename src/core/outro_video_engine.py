"""
Pulse Vector Outro Video Engine
Broadcast-quality animated YouTube End Credit Scene Video Generator (7.5-9.0s @ 30fps).
Engineered using the LastDayOnEarth animated tail architecture:
- Dynamic button squash-and-stretch scaling (scale = 1.0 + 0.18 * sin(...))
- Animated cursor / cartoon hand trajectories
- Complete animated triad: LIKE -> SHARE -> SUBSCRIBE state transitions
- Oversized wobbling golden bell towers with radiating soundwave shockwaves
- Synchronized audio mixing: Background music + 1760Hz bell chime SFX
- Dynamic parameter handling: conditional URLs, previous/next video titles, and random rotation

Supports the 5 finalized channel archetypes selected by the creator:
1. Vox Kinetic Split (Top recommendation)
2. MrBeast Hype Studio
3. Think School Exam Hub
4. Kurzgesagt Cosmic Flat-Art
5. Veritasium Curiosity Loop
"""

import os
import math
import random
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("OutroVideoEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FONTS_DIR = ROOT_DIR / "fonts"
AUDIO_DIR = ROOT_DIR / "assets" / "audio"
SAMPLES_DIR = ROOT_DIR / "samples" / "End_Credits_Videos"

FINALIST_CHANNELS = ["vox", "mrbeast", "thinkschool", "kurzgesagt", "veritasium", "pulse_vertical"]


class OutroVideoEngine:
    """Generates broadcast-quality animated 1080p MP4 outro tail videos for the 5 finalized channel archetypes."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        fonts_dir: Optional[Path] = None,
        audio_dir: Optional[Path] = None,
    ) -> None:
        self.output_dir = output_dir or SAMPLES_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir = fonts_dir or FONTS_DIR
        self.audio_dir = audio_dir or AUDIO_DIR

    # -------------------------------------------------------------------------
    # Typography Helpers
    # -------------------------------------------------------------------------
    def get_font(self, size: int, style: str = "roboto_bold") -> ImageFont.ImageFont:
        """Resolves expressive fonts: Bangers, LuckiestGuy, RussoOne, Roboto-Bold."""
        font_files = {
            "bangers": self.fonts_dir / "Bangers.ttf",
            "luckiest": self.fonts_dir / "LuckiestGuy.ttf",
            "russo": self.fonts_dir / "RussoOne.ttf",
            "impact": self.fonts_dir / "impact.ttf",
            "roboto_bold": self.fonts_dir / "Roboto-Bold.ttf",
            "roboto_regular": self.fonts_dir / "Roboto-Regular.ttf",
        }
        target = font_files.get(style.lower(), font_files["roboto_bold"])
        if target.exists():
            try:
                return ImageFont.truetype(str(target), size)
            except Exception:
                pass
        for name in ["arialbd.ttf", "arial.ttf", "segoeuib.ttf"]:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    # -------------------------------------------------------------------------
    # Vector Drawing & Animation Primitives (LDoE Reference)
    # -------------------------------------------------------------------------
    def draw_comic_text(
        self,
        draw: ImageDraw.ImageDraw,
        pos: Tuple[int, int],
        text: str,
        font: ImageFont.ImageFont,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
        stroke_width: int = 4,
        shadow_offset: Tuple[int, int] = (4, 4),
        anchor: Optional[str] = None,
    ) -> Tuple[int, int]:
        """Renders punchy comic typography with 3D drop shadow and thick stroke."""
        x, y = pos
        sx, sy = shadow_offset
        if sx or sy:
            draw.text((x + sx, y + sy), text, font=font, fill=(15, 23, 42, 220), stroke_width=stroke_width, stroke_fill=(0, 0, 0, 220), anchor=anchor)
        draw.text((x, y), text, font=font, fill=fill_color, stroke_width=stroke_width, stroke_fill=stroke_color, anchor=anchor)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def draw_animated_button(
        self,
        draw: ImageDraw.ImageDraw,
        box: Tuple[int, int, int, int],
        bg_color: Tuple[int, int, int, int],
        border_color: Tuple[int, int, int, int],
        text: str,
        font: ImageFont.ImageFont,
        text_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        radius: int = 20,
        scale: float = 1.0,
        badge_text: Optional[str] = None,
        badge_font: Optional[ImageFont.ImageFont] = None,
    ) -> None:
        """Draws a bold button with squash/stretch scaling and optional badge."""
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = (x2 - x1) * scale, (y2 - y1) * scale
        sb = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]

        # 3D Drop Shadow
        draw.rounded_rectangle([sb[0] + 4, sb[1] + 6, sb[2] + 4, sb[3] + 6], radius=int(radius * scale), fill=(0, 0, 0, 180))
        # Outer Border
        draw.rounded_rectangle([sb[0] - 3, sb[1] - 3, sb[2] + 3, sb[3] + 3], radius=int(radius * scale), fill=(0, 0, 0, 255))
        # Inner Accent Border
        draw.rounded_rectangle([sb[0] - 1, sb[1] - 1, sb[2] + 1, sb[3] + 1], radius=int(radius * scale), fill=border_color)
        # Face
        draw.rounded_rectangle(sb, radius=int(radius * scale), fill=bg_color)

        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2 - 2), text, fill=text_color, font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))

        if badge_text and badge_font:
            bb = draw.textbbox((0, 0), badge_text, font=badge_font)
            bw, bh = bb[2] - bb[0], bb[3] - bb[1]
            bx = sb[2] - bw - 15
            by = sb[1] - 14
            draw.rounded_rectangle([bx - 6, by - 3, bx + bw + 6, by + bh + 3], radius=8, fill=(245, 158, 11, 255), outline=(0, 0, 0, 255), width=2)
            draw.text((bx, by), badge_text, fill=(0, 0, 0, 255), font=badge_font)

    def draw_standalone_bell(
        self,
        draw: ImageDraw.ImageDraw,
        center: Tuple[int, int],
        angle_deg: float,
        ringing: bool,
        scale: float = 1.0,
        size: int = 56,
    ) -> None:
        """Draws an oversized animated golden bell with tilting clapper and radiating soundwaves."""
        cx, cy = center
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        eff_size = size * scale

        def rot(px: float, py: float) -> Tuple[float, float]:
            dx, dy = px - cx, py - cy
            return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)

        # Glow Aura
        glow_r = int(eff_size * 1.5)
        glow_color = (251, 191, 36, 60) if ringing else (30, 41, 59, 100)
        draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r], fill=glow_color)

        top = rot(cx, cy - eff_size * 0.95)
        bl = rot(cx - eff_size * 0.85, cy + eff_size * 0.5)
        br = rot(cx + eff_size * 0.85, cy + eff_size * 0.5)

        draw.polygon([(p[0] + 4, p[1] + 4) for p in [top, bl, br]], fill=(0, 0, 0, 160))
        bell_gold = (253, 224, 71, 255) if ringing else (251, 191, 36, 255)
        draw.polygon([top, bl, br], fill=bell_gold, outline=(0, 0, 0, 255))

        rim_y = cy + eff_size * 0.5
        draw.ellipse([cx - eff_size * 0.85, rim_y - eff_size * 0.15, cx + eff_size * 0.85, rim_y + eff_size * 0.15], fill=(245, 158, 11, 255), outline=(0, 0, 0, 255), width=2)

        clapper = rot(cx, cy + eff_size * 0.65)
        cr = eff_size * 0.22
        draw.ellipse([clapper[0] - cr, clapper[1] - cr, clapper[0] + cr, clapper[1] + cr], fill=(180, 83, 9, 255), outline=(0, 0, 0, 255), width=2)

        loop = rot(cx, cy - eff_size * 1.1)
        lr = eff_size * 0.18
        draw.ellipse([loop[0] - lr, loop[1] - lr, loop[0] + lr, loop[1] + lr], outline=(0, 0, 0, 255), width=3)

        if ringing:
            arc_w = max(3, int(4 * scale))
            for step in [20, 40, 60, 80]:
                ring_r = int(eff_size + step * max(1.0, scale * 0.75))
                draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=-60, end=60, fill=(251, 191, 36, 230), width=arc_w)
                draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=120, end=240, fill=(251, 191, 36, 230), width=arc_w)

    def draw_cartoon_hand(self, draw: ImageDraw.ImageDraw, pos: Tuple[int, int], clicking: bool = False) -> None:
        """Draws the animated white cartoon glove cursor (LDoE signature)."""
        cx, cy = pos
        scale = 0.9 if clicking else 1.0
        points = [
            (cx, cy),
            (cx + 24 * scale, cy + 24 * scale),
            (cx + 12 * scale, cy + 24 * scale),
            (cx + 22 * scale, cy + 44 * scale),
            (cx - 2 * scale, cy + 48 * scale),
            (cx - 16 * scale, cy + 44 * scale),
            (cx - 14 * scale, cy + 28 * scale),
            (cx - 6 * scale, cy + 22 * scale),
            (cx - 2 * scale, cy + 18 * scale),
        ]
        draw.polygon([(p[0] + 4, p[1] + 4) for p in points], fill=(0, 0, 0, 160))
        draw.polygon(points, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        draw.line([(cx + 4 * scale, cy + 32 * scale), (cx + 14 * scale, cy + 34 * scale)], fill=(203, 213, 225, 255), width=2)

    def draw_modern_cursor(self, draw: ImageDraw.ImageDraw, pos: Tuple[int, int], clicking: bool = False) -> None:
        """Draws a sleek tech arrow cursor with drop shadow."""
        x, y = pos
        s = 0.9 if clicking else 1.0
        poly = [
            (x, y),
            (x + int(20 * s), y + int(14 * s)),
            (x + int(11 * s), y + int(16 * s)),
            (x + int(15 * s), y + int(28 * s)),
            (x + int(9 * s), y + int(30 * s)),
            (x + int(5 * s), y + int(18 * s)),
            (x, y + int(24 * s)),
        ]
        draw.polygon([(p[0] + 3, p[1] + 3) for p in poly], fill=(0, 0, 0, 150))
        draw.polygon(poly, fill=(255, 255, 255), outline=(0, 0, 0), width=2)

    # -------------------------------------------------------------------------
    # 1. VOX KINETIC SPLIT (8.0s) — TOP CHOICE
    # Features complete Like -> Share -> Subscribe animated dock & dynamic video titles
    # -------------------------------------------------------------------------
    def render_frames_vox(
        self,
        temp_dir: Path,
        duration: float = 8.0,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        ctx = context or {}
        next_title = ctx.get("next_video_title") or "RECOMMENDED NEXT BRIEFING"
        playlist_title = ctx.get("playlist_title") or "CURRENT AFFAIRS MASTERCLASS"

        font_h = self.get_font(32, "roboto_bold")
        font_card = self.get_font(22, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        font_btn = self.get_font(24, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (15, 23, 42))
            draw = ImageDraw.Draw(bg)

            # Header
            draw.text((120, 75), "PULSE VECTOR", font=font_h, fill=(255, 255, 255))
            draw.text((1800, 75), "DAILY INTEL BRIEFING", font=font_sub, fill=(148, 163, 184), anchor="ra")
            line_w = min(1.0, t / 0.5) * 1680
            draw.line([(120, 120), (120 + int(line_w), 120)], fill=(56, 189, 248), width=2)

            # Left Card: Next Video (YouTube End Screen Safe Zone)
            c1_x = int(min(1.0, max(0.0, (t - 0.3) / 0.5)) * 140)
            c1_box = [(c1_x, 210), (c1_x + 640, 580)]
            draw.rounded_rectangle(c1_box, radius=20, fill=(30, 41, 59), outline=(6, 182, 212), width=3)
            draw.rounded_rectangle([(c1_x + 35, 235), (c1_x + 220, 275)], radius=8, fill=(234, 179, 8))
            draw.text((c1_x + 128, 255), "WATCH NEXT", font=font_sub, fill=(15, 23, 42), anchor="mm")
            # Video Play Button
            draw.ellipse([(c1_x + 280, 345), (c1_x + 360, 425)], fill=(225, 29, 72))
            draw.polygon([(c1_x + 315, 370), (c1_x + 315, 400), (c1_x + 338, 385)], fill=(255, 255, 255))
            # Conditional Title
            disp_next = (next_title[:32] + "...") if len(next_title) > 35 else next_title
            draw.text((c1_x + 320, 465), disp_next, font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.text((c1_x + 320, 500), "Auto-selected for your watch history", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # Center Channel Avatar
            cx, cy = 960, 395
            draw.ellipse([(cx - 70, cy - 70), (cx + 70, cy + 70)], fill=(37, 99, 235), outline=(56, 189, 248), width=3)
            draw.text((cx, cy), "PV", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((cx, cy + 95), "PULSE VECTOR", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Right Card: Series Playlist (YouTube End Screen Safe Zone)
            c2_x = 1920 - int(min(1.0, max(0.0, (t - 0.5) / 0.5)) * 780)
            c2_box = [(c2_x, 210), (c2_x + 640, 580)]
            draw.rounded_rectangle(c2_box, radius=20, fill=(30, 41, 59), outline=(168, 85, 247), width=3)
            draw.rounded_rectangle([(c2_x + 35, 235), (c2_x + 250, 275)], radius=8, fill=(168, 85, 247))
            draw.text((c2_x + 142, 255), "SERIES PLAYLIST", font=font_sub, fill=(255, 255, 255), anchor="mm")
            # Playlist Icon
            draw.ellipse([(c2_x + 280, 345), (c2_x + 360, 425)], fill=(168, 85, 247))
            draw.polygon([(c2_x + 315, 370), (c2_x + 315, 400), (c2_x + 338, 385)], fill=(255, 255, 255))
            disp_pl = (playlist_title[:32] + "...") if len(playlist_title) > 35 else playlist_title
            draw.text((c2_x + 320, 465), disp_pl, font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.text((c2_x + 320, 500), "Complete Syllabus Masterclasses", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # Bottom Interactive Dock: Full LIKE, SHARE, SUBSCRIBE Animated Triad
            dock_box = [(140, 680), (1780, 880)]
            draw.rounded_rectangle(dock_box, radius=22, fill=(15, 23, 42), outline=(56, 189, 248, 60), width=2)

            # 1. LIKE Button
            like_active = t >= 2.0
            like_scale = 1.0 + (0.16 * math.sin((t - 2.0) * 14) if 2.0 <= t <= 2.6 else 0.0)
            self.draw_animated_button(
                draw, (200, 740, 560, 830),
                (30, 58, 138) if like_active else (30, 41, 59),
                (56, 189, 248) if like_active else (71, 85, 105),
                "LIKED! (+1)" if like_active else "SMASH LIKE!",
                font_btn, scale=like_scale
            )

            # 2. SHARE Button
            share_active = t >= 3.4
            share_scale = 1.0 + (0.16 * math.sin((t - 3.4) * 14) if 3.4 <= t <= 4.0 else 0.0)
            self.draw_animated_button(
                draw, (620, 740, 980, 830),
                (16, 185, 129) if share_active else (30, 41, 59),
                (52, 211, 153) if share_active else (71, 85, 105),
                "SHARED!" if share_active else "SHARE VIDEO",
                font_btn, scale=share_scale
            )

            # 3. SUBSCRIBE Hero Button
            sub_active = t >= 4.8
            sub_scale = 1.0 + (0.20 * math.sin((t - 4.8) * 12) if 4.8 <= t <= 5.5 else 0.0)
            self.draw_animated_button(
                draw, (1040, 740, 1540, 830),
                (22, 101, 52) if sub_active else (225, 29, 72),
                (34, 197, 94) if sub_active else (251, 113, 133),
                "SUBSCRIBED" if sub_active else "SUBSCRIBE NOW",
                font_btn, scale=sub_scale
            )

            # 4. Animated Bell with Progressive Enlargement Climax
            bell_ring = t >= 5.8
            bell_angle = math.sin((t - 5.8) * 28) * 24.0 if bell_ring else 0.0

            if bell_ring:
                zoom_p = min(1.0, (t - 5.8) / (duration - 5.8 - 0.7))
                ease_zoom = 1.0 - (1.0 - zoom_p) ** 2
                
                dim_alpha = int(min(220, zoom_p * 260))
                dim_overlay = Image.new("RGB", (1920, 1080), (10, 14, 26))
                bg.paste(dim_overlay, (0, 0), Image.new("L", (1920, 1080), dim_alpha))
                draw = ImageDraw.Draw(bg)

                curr_cx = int(1660 + (960 - 1660) * ease_zoom)
                curr_cy = int(785 + (540 - 785) * ease_zoom)
                curr_scale = 0.85 + zoom_p * 3.4
                bell_center = (curr_cx, curr_cy)

                pedestal_r = int(120 * min(2.0, curr_scale * 0.75))
                draw.ellipse([bell_center[0] - pedestal_r, bell_center[1] - pedestal_r, bell_center[0] + pedestal_r, bell_center[1] + pedestal_r], fill=(22, 27, 34), outline=(251, 191, 36), width=int(4 * min(2.5, curr_scale)))
                self.draw_standalone_bell(draw, bell_center, bell_angle, ringing=True, scale=curr_scale, size=52)

                font_dyn = self.get_font(int(28 + zoom_p * 18), "roboto_bold")
                call_y = int(curr_cy + (52 * curr_scale * 0.72) + 20)
                draw.text((curr_cx, call_y), "ALL NOTIFICATIONS ON!", font=font_dyn, fill=(253, 224, 71), anchor="mm")
            else:
                self.draw_standalone_bell(draw, (1660, 785), bell_angle, False, scale=0.85, size=46)

            # Cursor trajectory across all 3 actions
            c_pos, c_click = None, False
            if 1.4 <= t < 2.3:
                p = (t - 1.4) / 0.9
                c_pos = (int(260 + p * 120), int(810 - math.sin(p * math.pi) * 40))
                c_click = 1.9 <= t <= 2.15
            elif 2.7 <= t < 3.7:
                p = (t - 2.7) / 1.0
                c_pos = (int(420 + p * 380), int(785 - math.sin(p * math.pi) * 40))
                c_click = 3.3 <= t <= 3.55
            elif 4.1 <= t < 5.2:
                p = (t - 4.1) / 1.1
                c_pos = (int(820 + p * 470), int(785 - math.sin(p * math.pi) * 45))
                c_click = 4.7 <= t <= 4.95
            elif 5.5 <= t < 6.5:
                p = (t - 5.5) / 1.0
                c_pos = (int(1300 + p * 360), int(785 - math.sin(p * math.pi) * 40))
                c_click = 5.9 <= t <= 6.15

            if c_pos:
                self.draw_modern_cursor(draw, c_pos, clicking=c_click)

            # Bottom Micro Text
            draw.text((960, 930), "NEXT BRIEFING DROPS AT 06:00 AM IST • PULSE VECTOR KNOWLEDGE MATRIX", font=self.get_font(16, "roboto_bold"), fill=(100, 116, 139), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # 2. MRBEAST HYPE STUDIO (8.5s)
    # Features intense urgency, Like + Share + Hero Subscribe + Wobbling Bell
    # -------------------------------------------------------------------------
    def render_frames_mrbeast(
        self,
        temp_dir: Path,
        duration: float = 8.5,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        font_head = self.get_font(64, "bangers")
        font_sub = self.get_font(28, "russo")
        font_btn = self.get_font(38, "bangers")
        font_hero = self.get_font(46, "bangers")
        font_badge = self.get_font(20, "russo")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGBA", (1920, 1080), (10, 12, 18, 255))
            draw = ImageDraw.Draw(bg)

            # Pulsing Neon Border
            pulse = math.sin(t * 3.5) * 0.15 + 0.85
            draw.rectangle([100, 80, 1820, 88], fill=(239, 68, 68, int(255 * pulse)))
            draw.rectangle([100, 990, 1820, 998], fill=(239, 68, 68, int(255 * pulse)))

            # Main Title
            h_text = "WAIT! SUBSCRIBE IN THE NEXT 5 SECONDS!"
            self.draw_comic_text(draw, (960, 160), h_text, font_head, fill_color=(255, 230, 0, 255), anchor="mm")
            s_text = "BEFORE THE NEXT HIGH-YIELD BRIEFING DROPS AT 06:00 AM IST!"
            self.draw_comic_text(draw, (960, 225), s_text, font_sub, fill_color=(255, 255, 255, 240), stroke_width=2, anchor="mm")

            # Like & Share Buttons
            like_active = t >= 1.6
            like_scale = 1.0 + (0.18 * math.sin((t - 1.6) * 14) if 1.6 <= t <= 2.2 else 0.0)
            self.draw_animated_button(draw, (200, 340, 680, 460), (6, 182, 212, 255) if like_active else (30, 41, 59, 230), (34, 211, 238, 255) if like_active else (71, 85, 105, 200), "LIKED! (+100 AURA)" if like_active else "SMASH LIKE!", font_btn, scale=like_scale, badge_text="FREE BUFF", badge_font=font_badge)

            share_active = t >= 2.8
            share_scale = 1.0 + (0.18 * math.sin((t - 2.8) * 14) if 2.8 <= t <= 3.4 else 0.0)
            self.draw_animated_button(draw, (740, 340, 1220, 460), (16, 185, 129, 255) if share_active else (30, 41, 59, 230), (52, 211, 153, 255) if share_active else (71, 85, 105, 200), "SHARED TO CLAN!" if share_active else "SHARE VIDEO", font_btn, scale=share_scale, badge_text="REINFORCE", badge_font=font_badge)

            # Giant Hero Subscribe Slam Bar
            sub_active = t >= 4.2
            sub_scale = 1.0 + (0.22 * math.sin((t - 4.2) * 12) if 4.2 <= t <= 4.9 else 0.0)
            self.draw_animated_button(draw, (200, 520, 1220, 680), (15, 23, 42, 255) if sub_active else (220, 38, 38, 255), (34, 197, 94, 255) if sub_active else (239, 68, 68, 255), "SUBSCRIBED! YOU ARE LEGENDARY" if sub_active else "SUBSCRIBE OR ELSE!", font_hero, scale=sub_scale, badge_text="TOP TIER", badge_font=font_badge)

            # Oversized Standalone Bell with Progressive Enlargement Climax
            bell_ring = t >= 5.6
            bell_angle = math.sin((t - 5.6) * 28) * 26.0 if bell_ring else 0.0

            if bell_ring:
                zoom_p = min(1.0, (t - 5.6) / (duration - 5.6 - 0.7))
                ease_zoom = 1.0 - (1.0 - zoom_p) ** 2
                
                dim_alpha = int(min(220, zoom_p * 260))
                dim_overlay = Image.new("RGBA", (1920, 1080), (10, 12, 18, dim_alpha))
                bg.paste(dim_overlay, (0, 0), dim_overlay)
                draw = ImageDraw.Draw(bg)

                curr_cx = int(1530 + (960 - 1530) * ease_zoom)
                curr_cy = int(510 + (490 - 510) * ease_zoom)
                curr_scale = 1.1 + zoom_p * 3.2
                bell_center = (curr_cx, curr_cy)

                pedestal_r = int(130 * min(2.0, curr_scale * 0.75))
                draw.ellipse([bell_center[0] - pedestal_r, bell_center[1] - pedestal_r, bell_center[0] + pedestal_r, bell_center[1] + pedestal_r], fill=(24, 30, 42, 240), outline=(251, 191, 36, 230), width=int(4 * min(2.5, curr_scale)))
                self.draw_standalone_bell(draw, bell_center, bell_angle, ringing=True, scale=curr_scale, size=60)

                font_dyn = self.get_font(int(28 + zoom_p * 18), "bangers")
                call_y = int(curr_cy + (60 * curr_scale * 0.72) + 20)
                self.draw_comic_text(draw, (curr_cx, call_y), "ALL NOTIFICATIONS ON!", font_dyn, fill_color=(253, 224, 71, 255), anchor="mm")
            else:
                bell_center = (1530, 510)
                draw.ellipse([bell_center[0] - 130, bell_center[1] - 130, bell_center[0] + 130, bell_center[1] + 130], fill=(24, 30, 42, 240), outline=(251, 191, 36, 230), width=4)
                self.draw_standalone_bell(draw, bell_center, bell_angle, False, scale=1.1, size=60)
                self.draw_comic_text(draw, (bell_center[0], bell_center[1] + 115), "RING THE BELL!", font_sub, fill_color=(255, 255, 255, 230), anchor="mm")

            # Cursor Trajectory
            c_pos, c_click = None, False
            if 1.0 <= t < 1.8:
                p = (t - 1.0) / 0.8
                c_pos = (int(300 + p * 140), int(480 - math.sin(p * math.pi) * 60))
                c_click = 1.5 <= t <= 1.7
            elif 2.2 <= t < 3.0:
                p = (t - 2.2) / 0.8
                c_pos = (int(440 + p * 540), int(420 - math.sin(p * math.pi) * 60))
                c_click = 2.7 <= t <= 2.9
            elif 3.4 <= t < 4.4:
                p = (t - 3.4) / 1.0
                c_pos = (int(980 - p * 270), int(420 + p * 180 - math.sin(p * math.pi) * 50))
                c_click = 4.1 <= t <= 4.35
            elif 4.8 <= t < 5.8:
                p = (t - 4.8) / 1.0
                c_pos = (int(710 + p * 820), int(600 - p * 90 - math.sin(p * math.pi) * 70))
                c_click = 5.5 <= t <= 5.75
            if c_pos:
                self.draw_cartoon_hand(draw, c_pos, clicking=c_click)

            # Footer
            self.draw_comic_text(draw, (960, 890), "DROP YOUR PERSPECTIVE IN THE COMMENTS • NEW INTEL DAILY!", font_sub, fill_color=(203, 213, 225, 230), stroke_width=2, anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)), (0, 0), Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)))
            bg.convert("RGB").save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # 3. THINK SCHOOL EXAM RESOURCE HUB (8.5s)
    # Features top PDF capsule banner, Next Lecture container, and student Like/Share/Sub bar
    # -------------------------------------------------------------------------
    def render_frames_thinkschool(
        self,
        temp_dir: Path,
        duration: float = 8.5,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        ctx = context or {}
        next_lecture = ctx.get("next_video_title") or "NEXT SYLLABUS LECTURE"

        font_h = self.get_font(26, "roboto_bold")
        font_card = self.get_font(22, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        font_btn = self.get_font(22, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (15, 23, 42))
            draw = ImageDraw.Draw(bg)

            # Top Banner
            draw.rounded_rectangle([(120, 60), (1800, 145)], radius=18, fill=(14, 52, 122), outline=(37, 99, 235), width=2)
            draw.text((160, 102), "REVISE SMARTER • FREE PDF STUDY CAPSULE", font=font_h, fill=(250, 204, 21), anchor="lm")
            draw.text((1760, 102), "DOWNLOAD LINK IN DESCRIPTION & TELEGRAM", font=font_card, fill=(255, 255, 255), anchor="rm")

            col_w = (1800 - 120 - 60) // 3
            # Col 1: Telegram
            x1 = 120
            draw.rounded_rectangle([(x1, 185), (x1 + col_w, 660)], radius=20, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
            draw.text((x1 + col_w // 2, 240), "TELEGRAM CAPSULES", font=font_card, fill=(56, 189, 248), anchor="mm")
            draw.text((x1 + col_w // 2, 310), "35,000+ Aspirants", font=font_card, fill=(250, 204, 21), anchor="mm")
            draw.text((x1 + col_w // 2, 360), "Daily 1-Page PDF Infographics", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.text((x1 + col_w // 2, 400), "Exam Quick Revision Compilations", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.rounded_rectangle([(x1 + 40, 560), (x1 + col_w - 40, 620)], radius=12, fill=(2, 132, 199))
            draw.text((x1 + col_w // 2, 590), "JOIN @pulsevector_daily", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Col 2: Next Lecture
            x2 = x1 + col_w + 30
            draw.rounded_rectangle([(x2, 185), (x2 + col_w, 660)], radius=20, fill=(30, 41, 59), outline=(234, 179, 8), width=2)
            draw.text((x2 + col_w // 2, 240), "UP NEXT FOR REVISION", font=font_card, fill=(234, 179, 8), anchor="mm")
            draw.rounded_rectangle([(x2 + 30, 290), (x2 + col_w - 30, 510)], radius=12, fill=(15, 23, 42))
            draw.polygon([(x2 + col_w // 2 - 15, 380), (x2 + col_w // 2 - 15, 420), (x2 + col_w // 2 + 20, 400)], fill=(234, 179, 8))
            disp_lec = (next_lecture[:28] + "...") if len(next_lecture) > 30 else next_lecture
            draw.text((x2 + col_w // 2, 460), disp_lec, font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.rounded_rectangle([(x2 + 40, 560), (x2 + col_w - 40, 620)], radius=12, fill=(225, 29, 72))
            draw.text((x2 + col_w // 2, 590), "WATCH NEXT LECTURE", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Col 3: Discord Room
            x3 = x2 + col_w + 30
            draw.rounded_rectangle([(x3, 185), (x3 + col_w, 660)], radius=20, fill=(30, 41, 59), outline=(168, 85, 247), width=2)
            draw.text((x3 + col_w // 2, 240), "24/7 STUDY ROOM", font=font_card, fill=(168, 85, 247), anchor="mm")
            draw.text((x3 + col_w // 2, 310), "Peer Problem Solving", font=font_card, fill=(196, 181, 253), anchor="mm")
            draw.text((x3 + col_w // 2, 360), "Daily MCQs & Time Tests", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.text((x3 + col_w // 2, 400), "Direct Mentor Interaction", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.rounded_rectangle([(x3 + 40, 560), (x3 + col_w - 40, 620)], radius=12, fill=(109, 40, 217))
            draw.text((x3 + col_w // 2, 590), "ENTER DISCORD HUB", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Bottom Student Action Bar: Complete LIKE, SHARE, SUBSCRIBE Sequence
            bar_box = [(120, 710), (1800, 870)]
            draw.rounded_rectangle(bar_box, radius=20, fill=(15, 23, 42), outline=(59, 130, 246, 60), width=2)

            like_active = t >= 2.0
            like_scale = 1.0 + (0.16 * math.sin((t - 2.0) * 14) if 2.0 <= t <= 2.6 else 0.0)
            self.draw_animated_button(draw, (180, 755, 520, 835), (30, 58, 138) if like_active else (30, 41, 59), (56, 189, 248) if like_active else (71, 85, 105), "LIKED! (+1)" if like_active else "LIKE BRIEFING", font_btn, scale=like_scale)

            share_active = t >= 3.4
            share_scale = 1.0 + (0.16 * math.sin((t - 3.4) * 14) if 3.4 <= t <= 4.0 else 0.0)
            self.draw_animated_button(draw, (580, 755, 960, 835), (16, 185, 129) if share_active else (30, 41, 59), (52, 211, 153) if share_active else (71, 85, 105), "SHARED!" if share_active else "SHARE WITH PEERS", font_btn, scale=share_scale)

            sub_active = t >= 4.8
            sub_scale = 1.0 + (0.20 * math.sin((t - 4.8) * 12) if 4.8 <= t <= 5.5 else 0.0)
            self.draw_animated_button(draw, (1020, 755, 1580, 835), (22, 101, 52) if sub_active else (225, 29, 72), (34, 197, 94) if sub_active else (251, 113, 133), "SUBSCRIBED & BELL ON" if sub_active else "SUBSCRIBE TO CHANNEL", font_btn, scale=sub_scale)

            bell_ring = t >= 6.0
            bell_angle = math.sin((t - 6.0) * 28) * 24.0 if bell_ring else 0.0
            self.draw_standalone_bell(draw, (1680, 795), bell_angle, bell_ring, scale=0.85, size=46)

            # Cursor
            c_pos, c_click = None, False
            if 1.4 <= t < 2.3:
                p = (t - 1.4) / 0.9
                c_pos = (int(240 + p * 110), int(810 - math.sin(p * math.pi) * 35))
                c_click = 1.9 <= t <= 2.15
            elif 2.7 <= t < 3.7:
                p = (t - 2.7) / 1.0
                c_pos = (int(380 + p * 380), int(795 - math.sin(p * math.pi) * 35))
                c_click = 3.3 <= t <= 3.55
            elif 4.1 <= t < 5.2:
                p = (t - 4.1) / 1.1
                c_pos = (int(780 + p * 500), int(795 - math.sin(p * math.pi) * 40))
                c_click = 4.7 <= t <= 4.95
            if c_pos:
                self.draw_modern_cursor(draw, c_pos, clicking=c_click)

            draw.text((960, 920), "PULSE VECTOR  •  Your Dedicated Daily Exam Preparation Companion  •  Alerts at 6:00 AM IST", font=font_sub, fill=(100, 116, 139), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # 4. KURZGESAGT COSMIC FLAT-ART (8.0s)
    # Twinkling starfield, wobbling planet, candy Like/Share/Sub buttons
    # -------------------------------------------------------------------------
    def render_frames_kurzgesagt(
        self,
        temp_dir: Path,
        duration: float = 8.0,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        font_h = self.get_font(48, "luckiest")
        font_sub = self.get_font(26, "luckiest")
        font_btn = self.get_font(32, "luckiest")
        total_frames = int(duration * fps)
        stars = [(int(1920 * (math.sin(i * 12.3) * 0.5 + 0.5)), int(1080 * (math.cos(i * 7.7) * 0.5 + 0.5))) for i in range(40)]

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGBA", (1920, 1080), (14, 11, 38, 255))
            draw = ImageDraw.Draw(bg)

            # Twinkling Stars
            for i, (sx, sy) in enumerate(stars):
                brightness = int(180 + 75 * math.sin(t * 4.0 + i))
                draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 255, 255, brightness))

            # Wobbling Planet
            planet_wobble = math.sin(t * 2.0) * 15
            px, py = 1600, int(350 + planet_wobble)
            draw.ellipse([px - 140, py - 140, px + 140, py + 140], fill=(244, 63, 94, 255), outline=(251, 113, 133, 255), width=4)
            draw.arc([px - 200, py - 50, px + 200, py + 50], start=-30, end=210, fill=(253, 224, 71, 230), width=6)

            # Header
            self.draw_comic_text(draw, (960, 160), "DON'T LET THE UNIVERSE FORGET YOU!", font_h, fill_color=(255, 230, 0, 255), anchor="mm")
            self.draw_comic_text(draw, (960, 230), "SUBSCRIBE FOR YOUR DAILY DOSE OF EXISTENTIAL CLARITY", font_sub, fill_color=(255, 255, 255, 240), stroke_width=2, anchor="mm")

            # Like, Share, Subscribe Candy Button Sequence
            like_active = t >= 1.8
            like_scale = 1.0 + (0.18 * math.sin((t - 1.8) * 14) if 1.8 <= t <= 2.4 else 0.0)
            self.draw_animated_button(draw, (220, 440, 560, 560), (6, 182, 212, 255) if like_active else (30, 41, 59, 230), (34, 211, 238, 255) if like_active else (71, 85, 105, 200), "LIKED! ★" if like_active else "LIKE STAR", font_btn, scale=like_scale)

            share_active = t >= 3.0
            share_scale = 1.0 + (0.18 * math.sin((t - 3.0) * 14) if 3.0 <= t <= 3.6 else 0.0)
            self.draw_animated_button(draw, (620, 440, 960, 560), (16, 185, 129, 255) if share_active else (30, 41, 59, 230), (52, 211, 153, 255) if share_active else (71, 85, 105, 200), "SHARED! 🚀" if share_active else "SHARE TO ALL", font_btn, scale=share_scale)

            sub_active = t >= 4.4
            sub_scale = 1.0 + (0.22 * math.sin((t - 4.4) * 12) if 4.4 <= t <= 5.1 else 0.0)
            self.draw_animated_button(draw, (1020, 440, 1520, 560), (22, 101, 52, 255) if sub_active else (220, 38, 38, 255), (34, 197, 94, 255) if sub_active else (251, 113, 133, 255), "PLANET SAVED!" if sub_active else "SUBSCRIBE NOW!", font_btn, scale=sub_scale)

            # Cartoon Pointer Glove
            c_pos, c_click = None, False
            if 1.2 <= t < 2.1:
                p = (t - 1.2) / 0.9
                c_pos = (int(300 + p * 90), int(620 - math.sin(p * math.pi) * 50))
                c_click = 1.7 <= t <= 1.95
            elif 2.4 <= t < 3.3:
                p = (t - 2.4) / 0.9
                c_pos = (int(420 + p * 370), int(600 - math.sin(p * math.pi) * 50))
                c_click = 2.9 <= t <= 3.15
            elif 3.7 <= t < 4.8:
                p = (t - 3.7) / 1.1
                c_pos = (int(820 + p * 450), int(600 - math.sin(p * math.pi) * 50))
                c_click = 4.3 <= t <= 4.55
            if c_pos:
                self.draw_cartoon_hand(draw, c_pos, clicking=c_click)

            self.draw_comic_text(draw, (960, 840), "NEW KNOWLEDGE DROPS TOMORROW AT 06:00 AM IST", font_sub, fill_color=(203, 213, 225, 230), stroke_width=2, anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)), (0, 0), Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)))
            bg.convert("RGB").save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # 5. VERITASIUM CURIOSITY LOOP (8.5s)
    # Dynamic question prompt, 24h pinned comment spotlight, Like/Share/Sub sequence
    # -------------------------------------------------------------------------
    def render_frames_veritasium(
        self,
        temp_dir: Path,
        duration: float = 8.5,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        ctx = context or {}
        question = ctx.get("question_text") or "Which international summit resolution will reshape global trade alliances by 2027?"

        font_h = self.get_font(38, "roboto_bold")
        font_card = self.get_font(22, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        font_btn = self.get_font(22, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (10, 15, 30))
            draw = ImageDraw.Draw(bg)

            # Central Inquiry Box
            draw.rounded_rectangle([(160, 110), (1760, 890)], radius=28, fill=(15, 23, 42), outline=(234, 179, 8), width=3)
            draw.rounded_rectangle([(960 - 200, 140), (960 + 200, 195)], radius=14, fill=(234, 179, 8))
            draw.text((960, 167), "QUESTION OF THE DAY", font=font_card, fill=(15, 23, 42), anchor="mm")

            # Dynamic Question Hook
            draw.text((960, 270), question, font=font_h, fill=(250, 204, 21), anchor="mm")

            # Dual Instruction Panels
            draw.rounded_rectangle([(240, 360), (920, 520)], radius=18, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
            draw.text((270, 400), "DROP YOUR PERSPECTIVE IN COMMENTS", font=font_card, fill=(56, 189, 248))
            draw.text((270, 440), "Share your exam insight, rationale, or critique.", font=font_sub, fill=(203, 213, 225))
            draw.text((270, 470), "Debate with thousands of aspirants daily.", font=font_sub, fill=(148, 163, 184))

            draw.rounded_rectangle([(1000, 360), (1680, 520)], radius=18, fill=(30, 41, 59), outline=(225, 29, 72), width=2)
            draw.text((1030, 400), "TOP COMMUNITY PERSPECTIVE PINNED", font=font_card, fill=(244, 63, 94))
            draw.text((1030, 440), "The most rigorous analysis is pinned for 24 hours.", font=font_sub, fill=(203, 213, 225))
            draw.text((1030, 470), "Spotlighted in tomorrow's 06:00 AM debrief.", font=font_sub, fill=(148, 163, 184))

            # Bottom Action Dock: LIKE, SHARE, SUBSCRIBE Animated Triad
            dock_box = [(240, 580), (1680, 780)]
            draw.rounded_rectangle(dock_box, radius=20, fill=(2, 6, 23), outline=(56, 189, 248, 60), width=2)

            like_active = t >= 2.0
            like_scale = 1.0 + (0.16 * math.sin((t - 2.0) * 14) if 2.0 <= t <= 2.6 else 0.0)
            self.draw_animated_button(draw, (280, 640, 640, 720), (30, 58, 138) if like_active else (30, 41, 59), (56, 189, 248) if like_active else (71, 85, 105), "PERSPECTIVE LIKED" if like_active else "LIKE DEBATE", font_btn, scale=like_scale)

            share_active = t >= 3.4
            share_scale = 1.0 + (0.16 * math.sin((t - 3.4) * 14) if 3.4 <= t <= 4.0 else 0.0)
            self.draw_animated_button(draw, (700, 640, 1060, 720), (16, 185, 129) if share_active else (30, 41, 59), (52, 211, 153) if share_active else (71, 85, 105), "SHARED!" if share_active else "SHARE DEBATE", font_btn, scale=share_scale)

            sub_active = t >= 4.8
            sub_scale = 1.0 + (0.20 * math.sin((t - 4.8) * 12) if 4.8 <= t <= 5.5 else 0.0)
            self.draw_animated_button(draw, (1120, 640, 1640, 720), (22, 101, 52) if sub_active else (225, 29, 72), (34, 197, 94) if sub_active else (251, 113, 133), "SUBSCRIBED & BELL ACTIVE" if sub_active else "SUBSCRIBE & JOIN DEBATE", font_btn, scale=sub_scale)

            # Modern Cursor Trajectory
            c_pos, c_click = None, False
            if 1.4 <= t < 2.3:
                p = (t - 1.4) / 0.9
                c_pos = (int(340 + p * 120), int(710 - math.sin(p * math.pi) * 35))
                c_click = 1.9 <= t <= 2.15
            elif 2.7 <= t < 3.7:
                p = (t - 2.7) / 1.0
                c_pos = (int(500 + p * 380), int(680 - math.sin(p * math.pi) * 35))
                c_click = 3.3 <= t <= 3.55
            elif 4.1 <= t < 5.2:
                p = (t - 4.1) / 1.1
                c_pos = (int(920 + p * 450), int(680 - math.sin(p * math.pi) * 40))
                c_click = 4.7 <= t <= 4.95
            if c_pos:
                self.draw_modern_cursor(draw, c_pos, clicking=c_click)

            draw.text((960, 830), "TOMORROW'S BRIEFING DROPS AT 06:00 AM IST • PULSE VECTOR", font=font_sub, fill=(100, 116, 139), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # 6. PULSE VECTOR VERTICAL (9:16 Shorts @ 1080x1920, 8.5s)
    # Features dynamic Like -> Share -> Subscribe with cartoon hand clicks,
    # progressive Bell Enlargement (zooming 3.2x into center focal point),
    # soundwave shockwaves, and final clean fade-out to pure black.
    # -------------------------------------------------------------------------
    def render_frames_pulse_vertical(
        self,
        temp_dir: Path,
        duration: float = 8.5,
        fps: int = 30,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        total_frames = int(duration * fps)

        font_header = self.get_font(44, "luckiest")
        font_sub = self.get_font(24, "russo")
        font_btn = self.get_font(38, "bangers")
        font_badge = self.get_font(22, "russo")
        font_callout = self.get_font(38, "bangers")

        for f in range(total_frames):
            t = f / fps

            bg = Image.new("RGBA", (1080, 1920), (10, 14, 22, 255))
            draw = ImageDraw.Draw(bg)

            # Ambient subtle grid/gradient
            pulse = math.sin(t * 3.0) * 0.15 + 0.85
            for y in range(0, 1920, 8):
                factor = y / 1920.0
                r = int(10 + 16 * factor * pulse)
                g = int(14 + 18 * factor)
                b = int(24 + 30 * factor * pulse)
                draw.rectangle([(0, y), (1080, y + 8)], fill=(r, g, b, 255))

            # Cyan & Crimson Accent Borders
            draw.rectangle([60, 140, 1020, 148], fill=(56, 189, 248, int(220 * pulse)))
            draw.rectangle([60, 1780, 1020, 1788], fill=(239, 68, 68, int(220 * pulse)))

            # Header: PULSE VECTOR
            h_text = "P U L S E   V E C T O R"
            self.draw_comic_text(draw, (540, 220), h_text, font_header, fill_color=(255, 255, 255, 255), anchor="mm")
            s_text = "DAILY INTELLIGENCE BRIEFING • UPGRADE YOUR FEED"
            self.draw_comic_text(draw, (540, 275), s_text, font_sub, fill_color=(56, 189, 248, 230), stroke_width=2, anchor="mm")

            # Main Central Action Card
            card_box = [(90, 360), (990, 1680)]
            draw.rounded_rectangle(card_box, radius=40, fill=(15, 23, 42, 200), outline=(255, 255, 255, 35), width=2)

            # 1. LIKE Button
            like_active = t >= 1.6
            like_scale = 1.0 + (0.16 * math.sin((t - 1.6) * 14) if 1.6 <= t <= 2.2 else 0.0)
            self.draw_animated_button(
                draw, (160, 440, 920, 560),
                (6, 182, 212, 255) if like_active else (30, 41, 59, 230),
                (34, 211, 238, 255) if like_active else (71, 85, 105, 200),
                "LIKED! (+100 AURA)" if like_active else "SMASH LIKE!",
                font_btn, scale=like_scale, badge_text="FREE BUFF", badge_font=font_badge
            )

            # 2. SHARE Button
            share_active = t >= 2.8
            share_scale = 1.0 + (0.16 * math.sin((t - 2.8) * 14) if 2.8 <= t <= 3.4 else 0.0)
            self.draw_animated_button(
                draw, (160, 600, 920, 720),
                (16, 185, 129, 255) if share_active else (30, 41, 59, 230),
                (52, 211, 153, 255) if share_active else (71, 85, 105, 200),
                "SHARED TO NETWORK!" if share_active else "SHARE INTEL",
                font_btn, scale=share_scale, badge_text="BROADCAST", badge_font=font_badge
            )

            # 3. SUBSCRIBE Hero Button
            sub_active = t >= 4.0
            sub_scale = 1.0 + (0.20 * math.sin((t - 4.0) * 12) if 4.0 <= t <= 4.7 else 0.0)
            self.draw_animated_button(
                draw, (160, 760, 920, 900),
                (15, 23, 42, 255) if sub_active else (220, 38, 38, 255),
                (34, 197, 94, 255) if sub_active else (239, 68, 68, 255),
                "SUBSCRIBED & BASE DEFENDED!" if sub_active else "SUBSCRIBE TO CHANNEL!",
                font_btn, scale=sub_scale, badge_text="ESSENTIAL", badge_font=font_badge
            )

            # Cursor Trajectory
            c_pos, c_click = None, False
            if 1.0 <= t < 1.8:
                p = (t - 1.0) / 0.8
                c_pos = (int(300 + p * 240), int(530 - math.sin(p * math.pi) * 60))
                c_click = 1.5 <= t <= 1.7
            elif 2.2 <= t < 3.0:
                p = (t - 2.2) / 0.8
                c_pos = (int(540 + p * 120), int(680 - math.sin(p * math.pi) * 60))
                c_click = 2.7 <= t <= 2.9
            elif 3.4 <= t < 4.2:
                p = (t - 3.4) / 0.8
                c_pos = (int(500 + p * 160), int(850 - math.sin(p * math.pi) * 60))
                c_click = 3.9 <= t <= 4.15
            elif 4.6 <= t < 5.4:
                p = (t - 4.6) / 0.8
                c_pos = (int(450 + p * 150), int(1120 - math.sin(p * math.pi) * 60))
                c_click = 5.0 <= t <= 5.25

            if c_pos:
                self.draw_cartoon_hand(draw, c_pos, clicking=c_click)

            # 4. Standalone Bell & Progressive Enlargement Climax
            bell_ringing = t >= 5.0
            bell_angle = math.sin((t - 5.0) * 28) * 25.0 if bell_ringing else 0.0

            if t >= 5.4:
                zoom_p = min(1.0, (t - 5.4) / (duration - 5.4 - 0.8))
                ease_zoom = 1.0 - (1.0 - zoom_p) ** 2
                
                dim_alpha = int(min(225, zoom_p * 265))
                dim_overlay = Image.new("RGBA", (1080, 1920), (10, 14, 22, dim_alpha))
                bg.paste(dim_overlay, (0, 0), dim_overlay)
                draw = ImageDraw.Draw(bg)

                curr_cx = 540
                curr_cy = int(1220 - ease_zoom * 70)
                curr_scale = 1.0 + zoom_p * 3.2
                bell_center = (curr_cx, curr_cy)

                pedestal_r = int(110 * min(2.2, curr_scale))
                draw.ellipse(
                    [bell_center[0] - pedestal_r, bell_center[1] - pedestal_r, bell_center[0] + pedestal_r, bell_center[1] + pedestal_r],
                    fill=(22, 27, 34, 240),
                    outline=(251, 191, 36, 240),
                    width=int(4 * min(2.5, curr_scale))
                )

                self.draw_standalone_bell(draw, bell_center, bell_angle, ringing=True, scale=curr_scale, size=58)

                font_dyn_callout = self.get_font(int(34 + zoom_p * 18), "bangers")
                call_text = "ALL NOTIFICATIONS ON!"
                tb = draw.textbbox((0, 0), call_text, font=font_dyn_callout)
                tw = tb[2] - tb[0]
                call_y = int(curr_cy + (58 * curr_scale * 0.72) + 25)
                self.draw_comic_text(draw, ((1080 - tw) // 2, call_y), call_text, font_dyn_callout, fill_color=(253, 224, 71, 255), stroke_width=4)
            else:
                bell_center = (540, 1220)
                draw.ellipse([bell_center[0] - 110, bell_center[1] - 110, bell_center[0] + 110, bell_center[1] + 110], fill=(22, 27, 34, 240), outline=(251, 191, 36, 240), width=4)
                self.draw_standalone_bell(draw, bell_center, bell_angle, ringing=bell_ringing, scale=1.0, size=58)
                b_msg = "DING DING DING!" if bell_ringing else "RING THE BELL!"
                self.draw_comic_text(draw, (540, 1340), b_msg, font_callout, fill_color=(253, 224, 71, 255) if bell_ringing else (255, 255, 255, 230), anchor="mm")

            # Footer
            f_msg = "NEXT BRIEFING DROPS TOMORROW 06:00 AM IST"
            self.draw_comic_text(draw, (540, 1620), f_msg, font_sub, fill_color=(148, 163, 184, 220), stroke_width=2, anchor="mm")

            # Final 0.8s Fade-Out to Black
            if t >= duration - 0.8:
                fade_alpha = int(((t - (duration - 0.8)) / 0.8) * 255)
                fade_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, fade_alpha))
                bg.paste(fade_overlay, (0, 0), fade_overlay)

            frame_path = temp_dir / f"frame_{f:04d}.jpg"
            bg.convert("RGB").save(str(frame_path), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # FFmpeg Compiler & Dispatcher
    # -------------------------------------------------------------------------
    def compile_video(
        self,
        temp_dir: Path,
        output_file: Path,
        duration: float,
        fps: int = 30,
        audio_filename: str = "clean_soul.mp3",
        bell_time: Optional[float] = None,
    ) -> Path:
        """Assembles frames + audio track + synchronized bell chime into broadcast MP4."""
        audio_path = self.audio_dir / audio_filename
        if not audio_path.exists():
            for alt in ["clean_soul.mp3", "electro_cabello.mp3", "decisions.mp3"]:
                if (self.audio_dir / alt).exists():
                    audio_path = self.audio_dir / alt
                    break

        fadeout = 1.0
        if bell_time is not None:
            filter_complex = (
                f"[1:a]afade=t=in:st=0:d=0.3,afade=t=out:st={duration - fadeout}:d={fadeout},volume=0.85[bg];"
                f"[2:a]adelay={int(bell_time * 1000)}|{int(bell_time * 1000)},volume=1.4[chime];"
                f"[bg][chime]amix=inputs=2:duration=first:dropout_transition=0[aout]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%04d.jpg"),
                "-i", str(audio_path),
                "-f", "lavfi", "-i", "sine=frequency=1760:duration=0.8",
                "-t", str(duration),
                "-filter_complex", filter_complex,
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(output_file),
            ]
        else:
            filter_complex = f"[1:a]afade=t=in:st=0:d=0.3,afade=t=out:st={duration - fadeout}:d={fadeout},volume=0.9[aout]"
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%04d.jpg"),
                "-i", str(audio_path),
                "-t", str(duration),
                "-filter_complex", filter_complex,
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(output_file),
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg assembly failed: {res.stderr[-400:]}")
        return output_file

    def generate_single_outro_video(
        self,
        channel_key: str,
        output_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Renders one of the 5 finalized channel animated outro videos."""
        dispatch = {
            "vox": (self.render_frames_vox, 8.0, "clean_soul.mp3", 6.0),
            "mrbeast": (self.render_frames_mrbeast, 8.5, "electro_cabello.mp3", 5.6),
            "thinkschool": (self.render_frames_thinkschool, 8.5, "clear_waters.mp3", 6.0),
            "kurzgesagt": (self.render_frames_kurzgesagt, 8.0, "carefree.mp3", 4.4),
            "veritasium": (self.render_frames_veritasium, 8.5, "decisions.mp3", 4.8),
            "pulse_vertical": (self.render_frames_pulse_vertical, 8.5, "electro_cabello.mp3", 5.0),
        }

        key = channel_key.lower().strip()
        if key not in dispatch:
            raise ValueError(f"Unknown channel_key '{channel_key}'. Choose from: {list(dispatch.keys())}")

        func, duration, audio_file, bell_t = dispatch[key]
        target = output_path or (self.output_dir / f"outro_{key}.mp4")
        temp_dir = self.output_dir / f"temp_{key}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Rendering frames for {key} ({duration}s @ 30fps)...")
            func(temp_dir=temp_dir, duration=duration, fps=30, context=context)
            logger.info(f"Assembling video via FFmpeg -> {target.name}...")
            self.compile_video(temp_dir, target, duration=duration, fps=30, audio_filename=audio_file, bell_time=bell_t)
            logger.info(f"Successfully created: {target} ({target.stat().st_size // 1024} KB)")
            return target
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # RANDOM ROTATION & FUTURE INTEGRATION DISPATCHER
    # -------------------------------------------------------------------------
    @classmethod
    def get_random_outro_channel(cls, allowed_channels: Optional[List[str]] = None) -> str:
        """Selects a random outro channel archetype from the finalized pool."""
        pool = allowed_channels or FINALIST_CHANNELS
        return random.choice(pool)

    def render_dynamic_outro(
        self,
        channel: Optional[str] = None,
        output_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Master outro entry point for future video pipeline integration.
        If channel is None, automatically picks a random channel from the 5 finalists.
        Passes video context (next_video_title, playlist_url, etc.) dynamically.
        """
        selected_ch = channel or self.get_random_outro_channel()
        logger.info(f"Dynamic outro selected: {selected_ch}")
        return self.generate_single_outro_video(selected_ch, output_path=output_path, context=context)
