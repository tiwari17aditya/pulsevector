"""
Pulse Vector Outro Video Engine
Broadcast-quality animated YouTube End Credit Scene Video Generator (7-9.5s clips).
Takes architectural inspiration from the LastDayOnEarth project outro generator:
dynamic squash-and-stretch button animations, animated cursor/glove trajectories,
oversized wobbling golden bell towers with soundwave arcs, and synchronized SFX chimes.

Renders 10 distinct, publication-grade animated outro MP4 videos modeled after
the most famous YouTube channels.
"""

import os
import math
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


class OutroVideoEngine:
    """Generates broadcast-quality animated 1080p MP4 outro tail videos for 10 famous YouTube channels."""

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
    # Font & Typography Helpers
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
    # Vector Geometry & Comic Drawing Primitives (LDoE Reference)
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
        """Renders punchy comic-style typography with 3D drop shadow and thick stroke."""
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
        radius: int = 24,
        scale: float = 1.0,
        badge_text: Optional[str] = None,
        badge_font: Optional[ImageFont.ImageFont] = None,
    ) -> None:
        """Draws a bold, punchy button with squash/stretch scaling and optional badge."""
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
        # Button Face
        draw.rounded_rectangle(sb, radius=int(radius * scale), fill=bg_color)

        # Center Text
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2 - 2), text, fill=text_color, font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))

        # Comic badge
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

        # Bell Body Points
        top = rot(cx, cy - eff_size * 0.95)
        bl = rot(cx - eff_size * 0.85, cy + eff_size * 0.5)
        br = rot(cx + eff_size * 0.85, cy + eff_size * 0.5)

        # Shadow
        draw.polygon([(p[0] + 4, p[1] + 4) for p in [top, bl, br]], fill=(0, 0, 0, 160))
        # Body
        bell_gold = (253, 224, 71, 255) if ringing else (251, 191, 36, 255)
        draw.polygon([top, bl, br], fill=bell_gold, outline=(0, 0, 0, 255))

        # Rim
        rim_y = cy + eff_size * 0.5
        draw.ellipse([cx - eff_size * 0.85, rim_y - eff_size * 0.15, cx + eff_size * 0.85, rim_y + eff_size * 0.15], fill=(245, 158, 11, 255), outline=(0, 0, 0, 255), width=2)

        # Clapper Ball
        clapper = rot(cx, cy + eff_size * 0.65)
        cr = eff_size * 0.22
        draw.ellipse([clapper[0] - cr, clapper[1] - cr, clapper[0] + cr, clapper[1] + cr], fill=(180, 83, 9, 255), outline=(0, 0, 0, 255), width=2)

        # Top Loop
        loop = rot(cx, cy - eff_size * 1.1)
        lr = eff_size * 0.18
        draw.ellipse([loop[0] - lr, loop[1] - lr, loop[0] + lr, loop[1] + lr], outline=(0, 0, 0, 255), width=3)

        # Radiating comic soundwaves if ringing
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
        # Shadow
        draw.polygon([(p[0] + 4, p[1] + 4) for p in points], fill=(0, 0, 0, 160))
        # Fill & Outline
        draw.polygon(points, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        draw.line([(cx + 4 * scale, cy + 32 * scale), (cx + 14 * scale, cy + 34 * scale)], fill=(203, 213, 225, 255), width=2)

    def draw_modern_cursor(self, draw: ImageDraw.ImageDraw, pos: Tuple[int, int], clicking: bool = False) -> None:
        """Draws a sleek tech arrow cursor with drop shadow."""
        x, y = pos
        s = 0.9 if clicking else 1.0
        poly = [(x, y), (x + int(20 * s), y + int(14 * s)), (x + int(11 * s), y + int(16 * s)), (x + int(15 * s), y + int(28 * s)), (x + int(9 * s), y + int(30 * s)), (x + int(5 * s), y + int(18 * s)), (x, y + int(24 * s))]
        # Shadow
        draw.polygon([(p[0] + 3, p[1] + 3) for p in poly], fill=(0, 0, 0, 150))
        # Cursor
        draw.polygon(poly, fill=(255, 255, 255), outline=(0, 0, 0), width=2)

    # -------------------------------------------------------------------------
    # 10 FAMOUS YOUTUBE CHANNEL OUTRO FRAME RENDERERS
    # -------------------------------------------------------------------------

    # 1. MrBeast Hype Studio (8.5s)
    def render_frames_mrbeast(self, temp_dir: Path, duration: float = 8.5, fps: int = 30) -> int:
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

            # Oversized Standalone Bell
            bell_ring = t >= 5.6
            bell_angle = math.sin((t - 5.6) * 28) * 26.0 if bell_ring else 0.0
            bell_center = (1530, 510)
            draw.ellipse([bell_center[0] - 130, bell_center[1] - 130, bell_center[0] + 130, bell_center[1] + 130], fill=(24, 30, 42, 240), outline=(251, 191, 36, 230), width=4)
            self.draw_standalone_bell(draw, bell_center, bell_angle, bell_ring, scale=1.1, size=60)
            b_msg = "DING DING DING!" if bell_ring else "RING THE BELL!"
            self.draw_comic_text(draw, (bell_center[0], bell_center[1] + 115), b_msg, font_sub, fill_color=(253, 224, 71, 255) if bell_ring else (255, 255, 255, 230), anchor="mm")

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

            # Fade
            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)), (0, 0), Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)))
            bg.convert("RGB").save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 2. Vox Kinetic Motion Graphics (8.0s)
    def render_frames_vox(self, temp_dir: Path, duration: float = 8.0, fps: int = 30) -> int:
        font_h = self.get_font(32, "roboto_bold")
        font_card = self.get_font(24, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (15, 23, 42))
            draw = ImageDraw.Draw(bg)

            # Header Line & Animated Text
            draw.text((120, 80), "PULSE VECTOR", font=font_h, fill=(255, 255, 255))
            draw.text((1800, 80), "DAILY INTEL BRIEFING", font=font_sub, fill=(148, 163, 184), anchor="ra")
            line_w = min(1.0, t / 0.6) * 1680
            draw.line([(120, 130), (120 + int(line_w), 130)], fill=(56, 189, 248), width=2)

            # Card 1 Glide in
            c1_x = int(min(1.0, max(0.0, (t - 0.4) / 0.6)) * 140)
            c1_box = [(c1_x, 240), (c1_x + 640, 620)]
            draw.rounded_rectangle(c1_box, radius=20, fill=(30, 41, 59), outline=(6, 182, 212), width=3)
            draw.rounded_rectangle([(c1_x + 40, 270), (c1_x + 240, 310)], radius=8, fill=(234, 179, 8))
            draw.text((c1_x + 140, 290), "WATCH NEXT", font=font_sub, fill=(15, 23, 42), anchor="mm")
            draw.ellipse([(c1_x + 280, 390), (c1_x + 360, 470)], fill=(225, 29, 72))
            draw.polygon([(c1_x + 315, 415), (c1_x + 315, 445), (c1_x + 335, 430)], fill=(255, 255, 255))
            draw.text((c1_x + 320, 510), "RECOMMENDED FOR YOU", font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.text((c1_x + 320, 545), "Based on your watch history", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # Center Avatar
            cx, cy = 960, 430
            draw.ellipse([(cx - 70, cy - 70), (cx + 70, cy + 70)], fill=(37, 99, 235), outline=(56, 189, 248), width=3)
            draw.text((cx, cy), "PV", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((cx, cy + 95), "PULSE VECTOR", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Card 2 Glide in from right
            c2_x = 1920 - int(min(1.0, max(0.0, (t - 0.6) / 0.6)) * 780)
            c2_box = [(c2_x, 240), (c2_x + 640, 620)]
            draw.rounded_rectangle(c2_box, radius=20, fill=(30, 41, 59), outline=(168, 85, 247), width=3)
            draw.rounded_rectangle([(c2_x + 40, 270), (c2_x + 280, 310)], radius=8, fill=(168, 85, 247))
            draw.text((c2_x + 160, 290), "SERIES PLAYLIST", font=font_sub, fill=(255, 255, 255), anchor="mm")
            draw.ellipse([(c2_x + 280, 390), (c2_x + 360, 470)], fill=(168, 85, 247))
            draw.polygon([(c2_x + 315, 415), (c2_x + 315, 445), (c2_x + 335, 430)], fill=(255, 255, 255))
            draw.text((c2_x + 320, 510), "OCTOBER MASTERCLASS", font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.text((c2_x + 320, 545), "Complete Syllabus Compilations", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # Bottom Subscribe Strip
            sub_active = t >= 3.8
            sub_w = 1.0 + (0.12 * math.sin((t - 3.8) * 14) if 3.8 <= t <= 4.4 else 0.0)
            b_box = [(140, 740), (1780, 860)]
            draw.rounded_rectangle(b_box, radius=18, fill=(15, 23, 42), outline=(255, 255, 255, 30), width=1)
            btn_box = [(180, 765), (460, 835)]
            draw.rounded_rectangle(btn_box, radius=14, fill=(15, 23, 42) if sub_active else (225, 29, 72), outline=(34, 197, 94) if sub_active else (225, 29, 72), width=2)
            draw.text((320, 800), "SUBSCRIBED" if sub_active else "SUBSCRIBE", font=font_card, fill=(255, 255, 255), anchor="mm")
            draw.text((520, 800), "Hit the notification bell to receive tomorrow's 6:00 AM briefing instantly.", font=font_sub, fill=(255, 255, 255), anchor="lm")

            # Smooth Tech Cursor
            if 2.2 <= t < 4.5:
                p = (t - 2.2) / 2.3
                cur_x = int(700 - p * 380)
                cur_y = int(520 + p * 280)
                self.draw_modern_cursor(draw, (cur_x, cur_y), clicking=3.7 <= t <= 4.0)

            # Fade
            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 3. Veritasium Curiosity Loop (8.5s)
    def render_frames_veritasium(self, temp_dir: Path, duration: float = 8.5, fps: int = 30) -> int:
        font_h = self.get_font(42, "roboto_bold")
        font_q = self.get_font(38, "roboto_bold")
        font_card = self.get_font(22, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (10, 15, 30))
            draw = ImageDraw.Draw(bg)

            # Central Inquiry Box
            draw.rounded_rectangle([(160, 130), (1760, 890)], radius=28, fill=(15, 23, 42), outline=(234, 179, 8), width=3)
            # Badge
            draw.rounded_rectangle([(960 - 200, 160), (960 + 200, 215)], radius=14, fill=(234, 179, 8))
            draw.text((960, 187), "QUESTION OF THE DAY", font=font_card, fill=(15, 23, 42), anchor="mm")

            # Main Question Hook
            draw.text((960, 280), "Which international summit resolution from this week", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((960, 340), "will reshape geopolitical trade alliances by 2027?", font=font_q, fill=(250, 204, 21), anchor="mm")

            # Dual Instruction Panels
            draw.rounded_rectangle([(240, 420), (920, 580)], radius=18, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
            draw.text((270, 460), "DROP YOUR PERSPECTIVE IN COMMENTS", font=font_card, fill=(56, 189, 248))
            draw.text((270, 500), "Share your exam insight, rationale, or critique.", font=font_sub, fill=(203, 213, 225))
            draw.text((270, 530), "Debate with thousands of aspirants daily.", font=font_sub, fill=(148, 163, 184))

            draw.rounded_rectangle([(1000, 420), (1680, 580)], radius=18, fill=(30, 41, 59), outline=(225, 29, 72), width=2)
            draw.text((1030, 460), "TOP COMMUNITY PERSPECTIVE PINNED", font=font_card, fill=(244, 63, 94))
            draw.text((1030, 500), "The most rigorous analysis is pinned for 24 hours.", font=font_sub, fill=(203, 213, 225))
            draw.text((1030, 530), "Spotlighted in tomorrow's 06:00 AM debrief.", font=font_sub, fill=(148, 163, 184))

            # Bottom Subscribe Button
            sub_active = t >= 4.0
            sub_scale = 1.0 + (0.16 * math.sin((t - 4.0) * 14) if 4.0 <= t <= 4.7 else 0.0)
            btn_w = int(460 * sub_scale)
            btn_h = int(80 * sub_scale)
            bx1, by1 = 960 - btn_w // 2, 750 - btn_h // 2
            draw.rounded_rectangle([(bx1, by1), (bx1 + btn_w, by1 + btn_h)], radius=16, fill=(15, 23, 42) if sub_active else (225, 29, 72), outline=(34, 197, 94) if sub_active else (239, 68, 68), width=3)
            draw.text((960, 750), "SUBSCRIBED & BELL ACTIVE" if sub_active else "SUBSCRIBE & JOIN DEBATE", font=font_card, fill=(255, 255, 255), anchor="mm")

            if 2.0 <= t < 4.5:
                p = (t - 2.0) / 2.5
                cur_x = int(600 + p * 360)
                cur_y = int(500 + p * 250)
                self.draw_modern_cursor(draw, (cur_x, cur_y), clicking=3.9 <= t <= 4.2)

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 4. Kurzgesagt Stellar Flat Cosmic (8.0s)
    def render_frames_kurzgesagt(self, temp_dir: Path, duration: float = 8.0, fps: int = 30) -> int:
        font_h = self.get_font(48, "luckiest")
        font_sub = self.get_font(26, "luckiest")
        font_btn = self.get_font(34, "luckiest")
        total_frames = int(duration * fps)

        # Star positions
        stars = [(int(1920 * (math.sin(i * 12.3) * 0.5 + 0.5)), int(1080 * (math.cos(i * 7.7) * 0.5 + 0.5))) for i in range(40)]

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGBA", (1920, 1080), (14, 11, 38, 255))
            draw = ImageDraw.Draw(bg)

            # Twinkling Stars
            for i, (sx, sy) in enumerate(stars):
                brightness = int(180 + 75 * math.sin(t * 4.0 + i))
                draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 255, 255, brightness))

            # Giant Wobbling Planet
            planet_wobble = math.sin(t * 2.0) * 15
            px, py = 1580, int(350 + planet_wobble)
            draw.ellipse([px - 140, py - 140, px + 140, py + 140], fill=(244, 63, 94, 255), outline=(251, 113, 133, 255), width=4)
            draw.arc([px - 200, py - 50, px + 200, py + 50], start=-30, end=210, fill=(253, 224, 71, 230), width=6)

            # Main Cosmic Header
            self.draw_comic_text(draw, (960, 180), "DON'T LET THE UNIVERSE FORGET YOU!", font_h, fill_color=(255, 230, 0, 255), anchor="mm")
            self.draw_comic_text(draw, (960, 245), "SUBSCRIBE FOR YOUR DAILY DOSE OF EXISTENTIAL CLARITY", font_sub, fill_color=(255, 255, 255, 240), stroke_width=2, anchor="mm")

            # Candy Buttons
            sub_active = t >= 3.5
            sub_scale = 1.0 + (0.2 * math.sin((t - 3.5) * 12) if 3.5 <= t <= 4.2 else 0.0)
            self.draw_animated_button(draw, (460, 420, 1160, 560), (15, 23, 42, 255) if sub_active else (225, 29, 72, 255), (34, 197, 94, 255) if sub_active else (251, 113, 133, 255), "PLANET DEFENDED!" if sub_active else "SUBSCRIBE NOW!", font_btn, scale=sub_scale)

            # Duck cartoon mascot or cartoon hand
            if 1.5 <= t < 4.0:
                p = (t - 1.5) / 2.5
                hx = int(350 + p * 450)
                hy = int(680 - p * 190 - math.sin(p * math.pi) * 80)
                self.draw_cartoon_hand(draw, (hx, hy), clicking=3.4 <= t <= 3.7)

            self.draw_comic_text(draw, (960, 840), "NEW KNOWLEDGE DROPS TOMORROW AT 06:00 AM IST", font_sub, fill_color=(203, 213, 225, 230), stroke_width=2, anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)), (0, 0), Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)))
            bg.convert("RGB").save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 5. MKBHD Tech Studio Cyber (7.5s)
    def render_frames_mkbhd(self, temp_dir: Path, duration: float = 7.5, fps: int = 30) -> int:
        font_h = self.get_font(46, "roboto_bold")
        font_sub = self.get_font(22, "roboto_regular")
        font_btn = self.get_font(30, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (10, 10, 12))
            draw = ImageDraw.Draw(bg)

            # Sleek matte obsidian backdrop with subtle red glow
            draw.rounded_rectangle([(180, 140), (1740, 880)], radius=32, fill=(18, 18, 22), outline=(40, 40, 48), width=2)
            for gl in range(260, 800, 100):
                draw.line([(240, gl), (1680, gl)], fill=(255, 255, 255, 12), width=1)

            draw.text((960, 240), "PULSE VECTOR // KNOWLEDGE ACCELERATED", font=self.get_font(18, "roboto_bold"), fill=(225, 29, 72), anchor="mm")
            draw.text((960, 320), "SO THAT'S THE BREAKDOWN. WHAT DO YOU THINK?", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((960, 380), "Drop your comments below. Subscribe for tomorrow's morning brief.", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # High-Contrast Matte Red Pill
            sub_active = t >= 3.2
            btn_scale = 1.0 + (0.12 * math.sin((t - 3.2) * 14) if 3.2 <= t <= 3.8 else 0.0)
            bw, bh = int(480 * btn_scale), int(84 * btn_scale)
            draw.rounded_rectangle([(960 - bw // 2, 500 - bh // 2), (960 + bw // 2, 500 + bh // 2)], radius=22, fill=(24, 24, 30) if sub_active else (225, 29, 72), outline=(34, 197, 94) if sub_active else (251, 113, 133), width=2)
            draw.text((960, 500), "SUBSCRIBED" if sub_active else "SUBSCRIBE NOW", font=font_btn, fill=(255, 255, 255), anchor="mm")

            # Tech cursor
            if 1.5 <= t < 4.0:
                p = (t - 1.5) / 2.5
                cx = int(600 + p * 360)
                cy = int(680 - p * 180)
                self.draw_modern_cursor(draw, (cx, cy), clicking=3.1 <= t <= 3.4)

            draw.text((960, 780), "4K ULTRA-HD  •  AI MULTILINGUAL TTS  •  DAILY 06:00 AM IST", font=self.get_font(15, "roboto_bold"), fill=(100, 116, 139), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 6. Ali Abdaal Productivity Ecosystem (8.0s)
    def render_frames_aliabdaal(self, temp_dir: Path, duration: float = 8.0, fps: int = 30) -> int:
        font_h = self.get_font(36, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        font_card = self.get_font(22, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (15, 23, 42))
            draw = ImageDraw.Draw(bg)

            draw.text((960, 120), "JOIN THE PULSE VECTOR KNOWLEDGE ECOSYSTEM", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((960, 170), "Three pillars designed to compound your exam consistency", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # 3 Glassmorphism Columns
            cols = [
                ("YOUTUBE", "Daily 60s Briefings", "Weekly Masterclasses", (225, 29, 72)),
                ("TELEGRAM", "1-Page PDF Capsules", "35,000+ Aspirants", (2, 132, 199)),
                ("DISCORD", "24/7 Study Rooms", "Peer Problem Solving", (124, 58, 237)),
            ]
            for i, (b_title, l1, l2, col) in enumerate(cols):
                cx_start = 160 + i * 550
                draw.rounded_rectangle([(cx_start, 240), (cx_start + 500, 640)], radius=20, fill=(30, 41, 59), outline=col, width=2)
                draw.rounded_rectangle([(cx_start + 30, 270), (cx_start + 470, 320)], radius=10, fill=col)
                draw.text((cx_start + 250, 295), b_title, font=font_card, fill=(255, 255, 255), anchor="mm")
                draw.text((cx_start + 250, 400), l1, font=font_card, fill=(255, 255, 255), anchor="mm")
                draw.text((cx_start + 250, 450), l2, font=font_sub, fill=(203, 213, 225), anchor="mm")
                draw.rounded_rectangle([(cx_start + 60, 530), (cx_start + 440, 590)], radius=12, fill=col)
                draw.text((cx_start + 250, 560), "JOIN NOW", font=font_sub, fill=(255, 255, 255), anchor="mm")

            draw.rounded_rectangle([(160, 720), (1760, 830)], radius=18, fill=(15, 52, 122), outline=(37, 99, 235), width=2)
            draw.text((960, 775), "NEVER MISS A BRIEFING • SUBSCRIBE & PRESS THE BELL", font=font_card, fill=(255, 255, 255), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 7. Think School Exam Resource Hub (8.5s)
    def render_frames_thinkschool(self, temp_dir: Path, duration: float = 8.5, fps: int = 30) -> int:
        font_h = self.get_font(26, "roboto_bold")
        font_card = self.get_font(22, "roboto_bold")
        font_sub = self.get_font(18, "roboto_regular")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (15, 23, 42))
            draw = ImageDraw.Draw(bg)

            # Top Banner
            draw.rounded_rectangle([(120, 60), (1800, 150)], radius=18, fill=(14, 52, 122), outline=(37, 99, 235), width=2)
            draw.text((160, 105), "REVISE SMARTER • FREE PDF STUDY CAPSULE", font=font_h, fill=(250, 204, 21), anchor="lm")
            draw.text((1760, 105), "DOWNLOAD LINK IN DESCRIPTION & TELEGRAM", font=font_card, fill=(255, 255, 255), anchor="rm")

            # 3 Columns
            col_w = (1800 - 120 - 60) // 3
            # Col 1: Telegram
            x1 = 120
            draw.rounded_rectangle([(x1, 190), (x1 + col_w, 710)], radius=20, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
            draw.text((x1 + col_w // 2, 250), "TELEGRAM CAPSULES", font=font_card, fill=(56, 189, 248), anchor="mm")
            draw.text((x1 + col_w // 2, 330), "35,000+ Aspirants", font=font_card, fill=(250, 204, 21), anchor="mm")
            draw.text((x1 + col_w // 2, 380), "Daily 1-Page PDF Infographics", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.rounded_rectangle([(x1 + 40, 600), (x1 + col_w - 40, 660)], radius=12, fill=(2, 132, 199))
            draw.text((x1 + col_w // 2, 630), "JOIN @pulsevector_daily", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Col 2: Next Lecture
            x2 = x1 + col_w + 30
            draw.rounded_rectangle([(x2, 190), (x2 + col_w, 710)], radius=20, fill=(30, 41, 59), outline=(234, 179, 8), width=2)
            draw.text((x2 + col_w // 2, 250), "NEXT SYLLABUS LECTURE", font=font_card, fill=(234, 179, 8), anchor="mm")
            draw.rounded_rectangle([(x2 + 30, 310), (x2 + col_w - 30, 540)], radius=12, fill=(15, 23, 42))
            draw.polygon([(x2 + col_w // 2 - 15, 410), (x2 + col_w // 2 - 15, 450), (x2 + col_w // 2 + 20, 430)], fill=(234, 179, 8))
            draw.rounded_rectangle([(x2 + 40, 600), (x2 + col_w - 40, 660)], radius=12, fill=(225, 29, 72))
            draw.text((x2 + col_w // 2, 630), "SUBSCRIBE TO CHANNEL", font=font_sub, fill=(255, 255, 255), anchor="mm")

            # Col 3: Discord Room
            x3 = x2 + col_w + 30
            draw.rounded_rectangle([(x3, 190), (x3 + col_w, 710)], radius=20, fill=(30, 41, 59), outline=(168, 85, 247), width=2)
            draw.text((x3 + col_w // 2, 250), "24/7 STUDY ROOM", font=font_card, fill=(168, 85, 247), anchor="mm")
            draw.text((x3 + col_w // 2, 330), "Peer Problem Solving", font=font_card, fill=(196, 181, 253), anchor="mm")
            draw.text((x3 + col_w // 2, 380), "Daily MCQs & Time Tests", font=font_sub, fill=(203, 213, 225), anchor="mm")
            draw.rounded_rectangle([(x3 + 40, 600), (x3 + col_w - 40, 660)], radius=12, fill=(109, 40, 217))
            draw.text((x3 + col_w // 2, 630), "ENTER DISCORD HUB", font=font_sub, fill=(255, 255, 255), anchor="mm")

            draw.rounded_rectangle([(120, 750), (1800, 840)], radius=16, fill=(15, 23, 42))
            draw.text((960, 795), "PULSE VECTOR  •  Your Daily Exam Companion  •  Press Bell for 6 AM Alerts", font=font_card, fill=(255, 255, 255), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 8. OverSimplified Cartoon Challenge (8.0s)
    def render_frames_oversimplified(self, temp_dir: Path, duration: float = 8.0, fps: int = 30) -> int:
        font_h = self.get_font(52, "luckiest")
        font_sub = self.get_font(24, "bangers")
        font_btn = self.get_font(34, "luckiest")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGBA", (1920, 1080), (15, 23, 42, 255))
            draw = ImageDraw.Draw(bg)

            # Comic Title
            self.draw_comic_text(draw, (960, 150), "DUDE... UNCOOL! YOU HAVEN'T SUBSCRIBED YET?!", font_h, fill_color=(255, 230, 0, 255), anchor="mm")

            # Yesterday's Champion Quote
            draw.rounded_rectangle([(200, 230), (1720, 430)], radius=20, fill=(30, 41, 59), outline=(234, 179, 8), width=3)
            draw.rounded_rectangle([(240, 255), (600, 305)], radius=10, fill=(234, 179, 8))
            draw.text((420, 280), "YESTERDAY'S EXAM CHAMPION", font=self.get_font(18, "russo"), fill=(15, 23, 42), anchor="mm")
            draw.text((250, 340), "@AspirantRahul_IAS: 'BIMSTEC was founded in 1997 via Bangkok Declaration!'", font=self.get_font(22, "roboto_bold"), fill=(255, 255, 255))
            draw.text((250, 380), "Featured in today's video! Drop your answer today to get featured tomorrow.", font=self.get_font(18, "roboto_regular"), fill=(148, 163, 184))

            # Bouncing Action Button
            sub_active = t >= 3.6
            sub_scale = 1.0 + (0.22 * math.sin((t - 3.6) * 12) if 3.6 <= t <= 4.3 else 0.0)
            self.draw_animated_button(draw, (460, 500, 1460, 640), (15, 23, 42, 255) if sub_active else (220, 38, 38, 255), (34, 197, 94, 255) if sub_active else (239, 68, 68, 255), "REALM DEFENDED! SUBSCRIBED" if sub_active else "SMASH SUBSCRIBE NOW!", font_btn, scale=sub_scale)

            # Cartoon glove pointer
            if 1.5 <= t < 4.2:
                p = (t - 1.5) / 2.7
                hx = int(300 + p * 660)
                hy = int(760 - p * 190 - math.sin(p * math.pi) * 80)
                self.draw_cartoon_hand(draw, (hx, hy), clicking=3.5 <= t <= 3.8)

            self.draw_comic_text(draw, (960, 800), "HEAD TO COMMUNITY TAB TO VOTE ON TODAY'S LIVE POLL!", font_sub, fill_color=(203, 213, 225, 230), stroke_width=2, anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)), (0, 0), Image.new("RGBA", (1920, 1080), (0, 0, 0, alpha)))
            bg.convert("RGB").save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 9. CaspianReport Tactical Intelligence HUD (8.0s)
    def render_frames_caspian(self, temp_dir: Path, duration: float = 8.0, fps: int = 30) -> int:
        font_mono = self.get_font(20, "roboto_bold")
        font_h = self.get_font(26, "roboto_bold")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (5, 12, 10))
            draw = ImageDraw.Draw(bg)

            # Tactical Grid
            for gx in range(0, 1920, 60):
                draw.line([(gx, 0), (gx, 1080)], fill=(16, 185, 129, 20), width=1)
            for gy in range(0, 1080, 60):
                draw.line([(0, gy), (1920, gy)], fill=(16, 185, 129, 20), width=1)

            # Top Telemetry
            draw.rectangle([(80, 50), (1840, 110)], outline=(16, 185, 129), width=2)
            draw.text((110, 80), "// INTELLIGENCE DEBRIEFING: COMPLETE //", font=font_mono, fill=(16, 185, 129), anchor="lm")
            draw.text((1810, 80), "CLEARANCE: STRATEGIC", font=font_mono, fill=(16, 185, 129), anchor="rm")

            # Rotating Radar Reticle on Left
            rcx, rcy = 500, 480
            draw.ellipse([rcx - 200, rcy - 200, rcx + 200, rcy + 200], outline=(16, 185, 129), width=2)
            draw.ellipse([rcx - 120, rcy - 120, rcx + 120, rcy + 120], outline=(16, 185, 129), width=1)
            draw.ellipse([rcx - 40, rcy - 40, rcx + 40, rcy + 40], outline=(16, 185, 129), width=1)
            draw.line([(rcx - 210, rcy), (rcx + 210, rcy)], fill=(16, 185, 129), width=1)
            draw.line([(rcx, rcy - 210), (rcx, rcy + 210)], fill=(16, 185, 129), width=1)
            # Radar sweep line
            sweep_rad = t * 4.0
            sx, sy = rcx + math.cos(sweep_rad) * 200, rcy + math.sin(sweep_rad) * 200
            draw.line([(rcx, rcy), (sx, sy)], fill=(52, 211, 153), width=3)
            draw.text((rcx, 720), "TARGET: GLOBAL ENERGY CORRIDORS", font=font_mono, fill=(52, 211, 153), anchor="mm")

            # Right Dossier Box
            draw.rectangle([(980, 170), (1800, 740)], outline=(56, 189, 248), width=2)
            draw.text((1390, 220), "RECOMMENDED GEOPOLITICAL DOSSIER", font=font_h, fill=(56, 189, 248), anchor="mm")
            draw.polygon([(1370, 420), (1370, 480), (1420, 450)], fill=(56, 189, 248))
            draw.text((1390, 530), "[ CLICK TO WATCH ARCHIVE DOSSIER ]", font=font_mono, fill=(255, 255, 255), anchor="mm")

            # Bottom Command
            draw.rectangle([(80, 800), (1840, 890)], outline=(16, 185, 129), width=2)
            draw.text((120, 845), ">> SUBSCRIBE FOR DAILY 06:00 AM STRATEGIC TRANSMISSION:", font=font_mono, fill=(255, 255, 255), anchor="lm")
            draw.rectangle([(1400, 815), (1780, 875)], fill=(16, 185, 129))
            draw.text((1590, 845), "[+] SUBSCRIBE", font=font_mono, fill=(5, 12, 10), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # 10. Lemmino Cinematic Audio Waveform (9.0s)
    def render_frames_lemmino(self, temp_dir: Path, duration: float = 9.0, fps: int = 30) -> int:
        font_h = self.get_font(34, "roboto_bold")
        font_sub = self.get_font(20, "roboto_regular")
        total_frames = int(duration * fps)

        for f in range(total_frames):
            t = f / fps
            bg = Image.new("RGB", (1920, 1080), (5, 8, 17))
            draw = ImageDraw.Draw(bg)

            # Dual Chapter Portals
            draw.rounded_rectangle([(140, 240), (660, 590)], radius=18, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
            draw.text((400, 400), "PREVIOUS CHAPTER", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((400, 445), "Click to replay", font=font_sub, fill=(148, 163, 184), anchor="mm")

            draw.rounded_rectangle([(1260, 240), (1780, 590)], radius=18, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
            draw.text((1520, 400), "NEXT CHAPTER", font=font_h, fill=(255, 255, 255), anchor="mm")
            draw.text((1520, 445), "Click to continue", font=font_sub, fill=(148, 163, 184), anchor="mm")

            # Animated Undulating Waveform in center
            wcx = 960
            for i in range(-25, 26):
                bar_x = wcx + i * 11
                dist = abs(i) / 25.0
                envelope = math.cos(dist * math.pi / 2)
                h = int(envelope * (40 + 70 * math.sin(t * 5.0 + i * 0.4)))
                draw.line([(bar_x, 415 - h), (bar_x, 415 + h)], fill=(56, 189, 248), width=4)

            # Central Avatar
            draw.ellipse([(wcx - 45, 415 - 45), (wcx + 45, 415 + 45)], fill=(15, 23, 42), outline=(56, 189, 248), width=2)
            draw.text((wcx, 415), "PV", font=self.get_font(24, "roboto_bold"), fill=(255, 255, 255), anchor="mm")

            draw.text((wcx, 690), "PULSE VECTOR", font=self.get_font(32, "roboto_bold"), fill=(255, 255, 255), anchor="mm")
            draw.text((wcx, 740), "K N O W L E D G E   A C C E L E R A T E D", font=font_sub, fill=(56, 189, 248), anchor="mm")
            draw.text((wcx, 810), "Subscribe for the next visual chapter • Press bell for alerts", font=font_sub, fill=(203, 213, 225), anchor="mm")

            if t >= duration - 0.7:
                alpha = int(((t - (duration - 0.7)) / 0.7) * 255)
                bg.paste(Image.new("RGB", (1920, 1080), (0, 0, 0)), (0, 0), Image.new("L", (1920, 1080), alpha))
            bg.save(str(temp_dir / f"frame_{f:04d}.jpg"), format="JPEG", quality=92)
        return total_frames

    # -------------------------------------------------------------------------
    # FFmpeg Video Assembler (LDoE Reference)
    # -------------------------------------------------------------------------
    def compile_video(
        self,
        temp_dir: Path,
        output_file: Path,
        duration: float,
        fps: int = 30,
        audio_filename: str = "electro_cabello.mp3",
        bell_time: Optional[float] = None,
    ) -> Path:
        """Assembles rendered frames + audio music track + synchronized bell chime into MP4."""
        audio_path = self.audio_dir / audio_filename
        if not audio_path.exists():
            for alt in ["carefree.mp3", "clean_soul.mp3", "bossa_antigua.mp3"]:
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

    def generate_single_outro_video(self, channel_key: str, output_path: Optional[Path] = None) -> Path:
        """Renders one of the 10 famous channel animated outro videos."""
        dispatch = {
            "mrbeast": (self.render_frames_mrbeast, 8.5, "electro_cabello.mp3", 5.6),
            "vox": (self.render_frames_vox, 8.0, "clean_soul.mp3", None),
            "veritasium": (self.render_frames_veritasium, 8.5, "decisions.mp3", None),
            "kurzgesagt": (self.render_frames_kurzgesagt, 8.0, "carefree.mp3", 3.5),
            "mkbhd": (self.render_frames_mkbhd, 7.5, "urban_gauntlet.mp3", None),
            "aliabdaal": (self.render_frames_aliabdaal, 8.0, "bossa_antigua.mp3", None),
            "thinkschool": (self.render_frames_thinkschool, 8.5, "clear_waters.mp3", 6.0),
            "oversimplified": (self.render_frames_oversimplified, 8.0, "monkeys_spinning_monkeys.mp3", 3.6),
            "caspian": (self.render_frames_caspian, 8.0, "constance.mp3", None),
            "lemmino": (self.render_frames_lemmino, 9.0, "shores_of_avalon.mp3", None),
        }

        if channel_key not in dispatch:
            raise ValueError(f"Unknown channel_key '{channel_key}'. Choose from: {list(dispatch.keys())}")

        func, duration, audio_file, bell_t = dispatch[channel_key]
        target = output_path or (self.output_dir / f"outro_{channel_key}.mp4")
        temp_dir = self.output_dir / f"temp_{channel_key}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Rendering frames for {channel_key} ({duration}s @ 30fps)...")
            func(temp_dir=temp_dir, duration=duration, fps=30)
            logger.info(f"Assembling video via FFmpeg -> {target.name}...")
            self.compile_video(temp_dir, target, duration=duration, fps=30, audio_filename=audio_file, bell_time=bell_t)
            logger.info(f"Successfully created: {target} ({target.stat().st_size // 1024} KB)")
            return target
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

