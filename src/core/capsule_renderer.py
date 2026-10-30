"""
Capsule Renderer Module
Generates high-density, multi-block educational and exam-oriented infographic posters
(JPEG and PNG) inspired by modern high-yield knowledge capsules.
"""

import os
import pathlib
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Font references
FONT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "fonts"
FONT_BOLD = FONT_DIR / "Roboto-Bold.ttf"
FONT_REGULAR = FONT_DIR / "Roboto-Regular.ttf"

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    font_path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
        if not word and current_line:
            current_line.append("")
            continue
        test_line = " ".join(current_line + [word]) if current_line else word
        bbox = font.getbbox(test_line)
        line_w = bbox[2] - bbox[0]
        if line_w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

class CapsuleRenderer:
    """
    Renders high-yield weekly insights and current affairs knowledge capsules.
    Outputs publication-ready JPEG and PNG posters with adaptive layout.
    """
    def __init__(self, width: int = 1200, height: Optional[int] = None):
        self.W = width
        self.custom_h = height
        self.margin_x = 40
        self.content_w = self.W - (self.margin_x * 2)

    def draw_header(self, draw: ImageDraw.ImageDraw, current_y: int, header_data: Dict[str, Any]) -> int:
        # Top utility bar
        top_bar_h = 44
        draw.rectangle([0, 0, self.W, top_bar_h], fill=(15, 23, 42))
        f_brand = get_font(18, bold=True)
        draw.text((self.margin_x, 13), "PULSE VECTOR  •  KNOWLEDGE MATRIX", font=f_brand, fill=(56, 189, 248))
        f_trust = get_font(15, bold=False)
        trust_text = "EXAM FOCUSED   |   EXPERT CURATED   |   HIGH RETENTION"
        t_box = f_trust.getbbox(trust_text)
        draw.text((self.W - self.margin_x - (t_box[2] - t_box[0]), 14), trust_text, font=f_trust, fill=(203, 213, 225))
        
        current_y = 54

        # Main Header Box
        header_h = 175
        draw.rounded_rectangle([self.margin_x, current_y, self.margin_x + self.content_w, current_y + header_h], 
                               radius=16, fill=(15, 52, 122), outline=(37, 99, 235), width=2)
        
        # Pill badge on top center
        badge_text = "WEEKLY HIGH-VALUE INSIGHTS"
        f_badge = get_font(14, bold=True)
        b_box = f_badge.getbbox(badge_text)
        b_w = b_box[2] - b_box[0] + 24
        b_x = (self.W - b_w) // 2
        draw.rounded_rectangle([b_x, current_y + 12, b_x + b_w, current_y + 36], radius=12, fill=(234, 179, 8))
        draw.text((self.W // 2, current_y + 24), badge_text, font=f_badge, fill=(15, 23, 42), anchor="mm")

        # Main Title
        f_head_title = get_font(38, bold=True)
        main_title = header_data.get("main_title", "EXAM RELEVANT CURRENT AFFAIRS 2026")
        draw.text((self.W // 2, current_y + 64), main_title, font=f_head_title, fill=(255, 230, 0), anchor="mm")

        # Subtitle Date Pill
        date_range = header_data.get("date_range", "12 October - 18 October 2026")
        f_date = get_font(20, bold=True)
        date_box = f_date.getbbox(date_range)
        date_w = date_box[2] - date_box[0] + 36
        date_x = (self.W - date_w) // 2
        draw.rounded_rectangle([date_x, current_y + 94, date_x + date_w, current_y + 130], radius=18, fill=(225, 29, 72))
        draw.text((self.W // 2, current_y + 112), date_range, font=f_date, fill=(255, 255, 255), anchor="mm")

        # Target exam line
        sub_desc = header_data.get("subtitle", "High-Value Insights for Competitive Exams (UPSC • SSC • Banking • State PSC)")
        f_sub = get_font(16, bold=True)
        draw.text((self.W // 2, current_y + 152), sub_desc, font=f_sub, fill=(241, 245, 249), anchor="mm")

        return current_y + header_h + 16

    def draw_section_card(self, draw: ImageDraw.ImageDraw, current_y: int, section_data: Dict[str, Any]) -> int:
        sec_num = section_data.get("num", 1)
        theme_color = section_data.get("color", (2, 132, 199))
        card_start_y = current_y
        card_w = self.content_w
        banner_h = 66
        
        # Banner Header
        draw.rounded_rectangle([self.margin_x, current_y, self.margin_x + card_w, current_y + banner_h], 
                               radius=12, fill=theme_color)
        
        # Number badge circle
        f_num = get_font(28, bold=True)
        badge_r = 24
        badge_center = (self.margin_x + 34, current_y + 33)
        draw.ellipse([badge_center[0] - badge_r, badge_center[1] - badge_r, 
                      badge_center[0] + badge_r, badge_center[1] + badge_r], 
                     fill=(255, 255, 255))
        draw.text(badge_center, str(sec_num), font=f_num, fill=theme_color, anchor="mm")

        # Title text
        f_card_title = get_font(26, bold=True)
        title_text = section_data.get("title", "").upper()
        draw.text((self.margin_x + 72, current_y + 20), title_text, font=f_card_title, fill=(255, 255, 255))

        # Subtitle under title
        f_card_sub = get_font(16, bold=False)
        sub_text = section_data.get("subtitle", "")
        if sub_text:
            draw.text((self.margin_x + 72, current_y + 44), sub_text, font=f_card_sub, fill=(254, 240, 138))

        inner_y = current_y + banner_h + 12

        # 1. Metadata Fact Grid
        meta_grid = section_data.get("metadata_grid", [])
        if meta_grid:
            cols = 3
            cell_w = (card_w - ((cols - 1) * 8)) // cols
            cell_h = 58
            
            for idx, item in enumerate(meta_grid):
                r = idx // cols
                c = idx % cols
                cx = self.margin_x + c * (cell_w + 8)
                cy = inner_y + r * (cell_h + 6)

                draw.rounded_rectangle([cx, cy, cx + cell_w, cy + cell_h], radius=7, 
                                       fill=(248, 250, 252), outline=(226, 232, 240), width=1)
                draw.rounded_rectangle([cx, cy, cx + 5, cy + cell_h], radius=2, fill=theme_color)

                f_lbl = get_font(12, bold=True)
                draw.text((cx + 10, cy + 6), item.get("label", "").upper(), font=f_lbl, fill=(100, 116, 139))
                
                f_val = get_font(14, bold=True)
                val_text = item.get("value", "")
                val_lines = wrap_text(val_text, f_val, cell_w - 18)
                if val_lines:
                    draw.text((cx + 10, cy + 22), val_lines[0], font=f_val, fill=(15, 23, 42))
                    if len(val_lines) > 1:
                        draw.text((cx + 10, cy + 38), val_lines[1], font=get_font(12, bold=False), fill=(30, 41, 59))

            rows_count = (len(meta_grid) + cols - 1) // cols
            inner_y += rows_count * (cell_h + 6) + 8

        # 2. Key Statistics Bar (if present)
        stats = section_data.get("stats", [])
        progress_bar = section_data.get("progress_bar", None)
        if stats or progress_bar:
            stat_box_h = 76 if progress_bar else 62
            draw.rounded_rectangle([self.margin_x, inner_y, self.margin_x + card_w, inner_y + stat_box_h],
                                   radius=8, fill=(241, 245, 249), outline=(203, 213, 225), width=1)
            
            # Left accent tag
            f_stat_tag = get_font(12, bold=True)
            draw.rounded_rectangle([self.margin_x + 8, inner_y + 8, self.margin_x + 130, inner_y + 28],
                                   radius=4, fill=(30, 41, 59))
            draw.text((self.margin_x + 14, inner_y + 11), "KEY STATISTICS", font=f_stat_tag, fill=(255, 255, 255))
            
            if stats:
                stat_col_w = (card_w - 150) // len(stats)
                for s_idx, st in enumerate(stats):
                    sx = self.margin_x + 145 + (s_idx * stat_col_w)
                    f_st_lbl = get_font(12, bold=False)
                    draw.text((sx, inner_y + 7), st.get("label", ""), font=f_st_lbl, fill=(71, 85, 105))
                    f_st_val = get_font(17, bold=True)
                    draw.text((sx, inner_y + 24), st.get("value", ""), font=f_st_val, fill=theme_color)

            if progress_bar:
                p_y = inner_y + 49
                p_w = card_w - 24
                p_x = self.margin_x + 12
                pct1 = progress_bar.get("percent1", 50)
                lbl1 = progress_bar.get("label1", "Women")
                lbl2 = progress_bar.get("label2", "Men")
                
                split_px = int(p_w * (pct1 / 100.0))
                draw.rounded_rectangle([p_x, p_y, p_x + p_w, p_y + 12], radius=6, fill=(226, 232, 240))
                draw.rounded_rectangle([p_x, p_y, p_x + split_px, p_y + 12], radius=6, fill=(236, 72, 153))
                draw.rounded_rectangle([p_x + split_px, p_y, p_x + p_w, p_y + 12], radius=6, fill=(59, 130, 246))
                
                f_p_lbl = get_font(12, bold=True)
                draw.text((p_x, p_y - 15), lbl1, font=f_p_lbl, fill=(219, 39, 119))
                t_box2 = f_p_lbl.getbbox(lbl2)
                draw.text((p_x + p_w - (t_box2[2] - t_box2[0]), p_y - 15), lbl2, font=f_p_lbl, fill=(37, 99, 235))

            inner_y += stat_box_h + 10

        # 3. Takeaway Points & Focus Areas
        points_title = section_data.get("points_title", "KEY EXAM POINTS").upper()
        f_pt_title = get_font(12, bold=True)
        pt_box = f_pt_title.getbbox(points_title)
        pt_w = pt_box[2] - pt_box[0] + 20
        draw.rounded_rectangle([self.margin_x, inner_y, self.margin_x + pt_w, inner_y + 24],
                               radius=4, fill=(241, 245, 249), outline=theme_color, width=1)
        draw.text((self.margin_x + 10, inner_y + 5), points_title, font=f_pt_title, fill=theme_color)
        inner_y += 30

        points = section_data.get("points", [])
        side_note = section_data.get("side_note", None)
        points_avail_w = card_w - (300 if side_note else 0)

        f_pt_body = get_font(15, bold=False)
        f_pt_num = get_font(13, bold=True)

        points_start_y = inner_y
        for p_idx, pt_text in enumerate(points):
            pt_num = p_idx + 1
            p_badge_r = 12
            p_badge_center = (self.margin_x + 14, inner_y + 11)
            draw.ellipse([p_badge_center[0] - p_badge_r, p_badge_center[1] - p_badge_r,
                          p_badge_center[0] + p_badge_r, p_badge_center[1] + p_badge_r],
                         fill=theme_color)
            draw.text(p_badge_center, str(pt_num), font=f_pt_num, fill=(255, 255, 255), anchor="mm")

            lines = wrap_text(pt_text, f_pt_body, points_avail_w - 40)
            for l_idx, line in enumerate(lines):
                draw.text((self.margin_x + 36, inner_y + (l_idx * 20)), line, font=f_pt_body, fill=(15, 23, 42))
            
            inner_y += max(len(lines) * 20, 24) + 6

        # Side note rendering
        if side_note:
            sn_x = self.margin_x + card_w - 285
            sn_y = points_start_y - 28
            sn_h = inner_y - sn_y
            draw.rounded_rectangle([sn_x, sn_y, sn_x + 285, sn_y + sn_h], radius=7, 
                                   fill=(254, 242, 242), outline=(248, 113, 113), width=1)
            f_sn_h = get_font(12, bold=True)
            draw.text((sn_x + 10, sn_y + 8), "IMPORTANT EXAM NOTE:", font=f_sn_h, fill=(185, 28, 28))
            f_sn_b = get_font(13, bold=False)
            sn_lines = wrap_text(side_note, f_sn_b, 265)
            for s_l_idx, s_line in enumerate(sn_lines):
                draw.text((sn_x + 10, sn_y + 28 + (s_l_idx * 18)), s_line, font=f_sn_b, fill=(69, 10, 10))

        # Outer card border
        total_card_h = inner_y - card_start_y
        draw.rounded_rectangle([self.margin_x, card_start_y, self.margin_x + card_w, card_start_y + total_card_h],
                               radius=12, outline=(226, 232, 240), width=1)

        return inner_y + 16

    def draw_quiz_box(self, draw: ImageDraw.ImageDraw, current_y: int, quiz_data: Dict[str, Any]) -> int:
        card_w = self.content_w
        box_h = 105
        draw.rounded_rectangle([self.margin_x, current_y, self.margin_x + card_w, current_y + box_h],
                               radius=12, fill=(245, 243, 255), outline=(139, 92, 246), width=2)
        
        # Header Badge
        f_q_badge = get_font(13, bold=True)
        draw.rounded_rectangle([self.margin_x + 14, current_y + 12, self.margin_x + 225, current_y + 34],
                               radius=4, fill=(109, 40, 217))
        draw.text((self.margin_x + 22, current_y + 15), "WEEKLY EXAM CHALLENGE", font=f_q_badge, fill=(255, 255, 255))
        
        # Question text
        q_text = quiz_data.get("question", "Where is the permanent Secretariat of BIMSTEC located?")
        f_q = get_font(16, bold=True)
        draw.text((self.margin_x + 240, current_y + 15), q_text, font=f_q, fill=(15, 23, 42))

        # Options
        options = quiz_data.get("options", ["(A) New Delhi", "(B) Dhaka", "(C) Colombo", "(D) Kathmandu"])
        f_opt = get_font(15, bold=False)
        opt_w = (card_w - 30) // len(options)
        for o_idx, opt in enumerate(options):
            ox = self.margin_x + 15 + (o_idx * opt_w)
            oy = current_y + 50
            draw.rounded_rectangle([ox, oy, ox + opt_w - 10, oy + 36], radius=6, 
                                   fill=(255, 255, 255), outline=(196, 181, 253), width=1)
            draw.text((ox + 12, oy + 9), opt, font=f_opt, fill=(76, 29, 149))

        return current_y + box_h + 16

    def draw_footer(self, draw: ImageDraw.ImageDraw, current_y: int, footer_data: Dict[str, Any]) -> int:
        footer_h = 74
        draw.rounded_rectangle([self.margin_x, current_y, self.margin_x + self.content_w, current_y + footer_h],
                               radius=10, fill=(15, 23, 42))

        # Badge
        f_rev = get_font(15, bold=True)
        draw.rounded_rectangle([self.margin_x + 12, current_y + 12, self.margin_x + 215, current_y + 44],
                               radius=5, fill=(225, 29, 72))
        draw.text((self.margin_x + 20, current_y + 20), "EXAM QUICK REVISION", font=f_rev, fill=(255, 255, 255))

        # Tags
        tags = footer_data.get("tags", [])
        tag_str = "  |  ".join(tags)
        f_tags = get_font(15, bold=False)
        tag_lines = wrap_text(tag_str, f_tags, self.content_w - 235)
        for t_idx, t_line in enumerate(tag_lines):
            draw.text((self.margin_x + 230, current_y + 14 + (t_idx * 22)), t_line, font=f_tags, fill=(226, 232, 240))

        # Bottom copyright strip
        f_bot = get_font(13, bold=False)
        draw.text((self.W // 2, current_y + footer_h + 18), 
                  "PULSE VECTOR  •  Curated Knowledge Intelligence  •  Share & Bookmark for Exam Preparation", 
                  font=f_bot, fill=(100, 116, 139), anchor="mm")

        return current_y + footer_h + 36

    def measure_height(self, capsule_data: Dict[str, Any]) -> int:
        """Calculates total canvas height dynamically to prevent blank space."""
        dummy = Image.new("RGB", (self.W, 3500), (255, 255, 255))
        d_draw = ImageDraw.Draw(dummy)

        curr_y = self.draw_header(d_draw, 54, capsule_data.get("header", {}))
        for sec in capsule_data.get("sections", []):
            curr_y = self.draw_section_card(d_draw, curr_y, sec)

        quiz = capsule_data.get("quiz", {
            "question": "Where is the permanent Secretariat of BIMSTEC located?",
            "options": ["(A) New Delhi", "(B) Dhaka", "(C) Colombo", "(D) Kathmandu"]
        })
        curr_y = self.draw_quiz_box(d_draw, curr_y, quiz)
        curr_y = self.draw_footer(d_draw, curr_y, capsule_data.get("footer", {}))
        return curr_y + 10

    def render_capsule(self, capsule_data: Dict[str, Any], output_path: pathlib.Path) -> pathlib.Path:
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Determine dynamic or custom height
        final_h = self.custom_h if self.custom_h is not None else self.measure_height(capsule_data)

        # 2. Render actual poster
        image = Image.new("RGB", (self.W, final_h), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Draw components
        curr_y = self.draw_header(draw, 54, capsule_data.get("header", {}))
        for sec in capsule_data.get("sections", []):
            curr_y = self.draw_section_card(draw, curr_y, sec)

        quiz = capsule_data.get("quiz", {
            "question": "Where is the permanent Secretariat of BIMSTEC located?",
            "options": ["(A) New Delhi", "(B) Dhaka", "(C) Colombo", "(D) Kathmandu"]
        })
        curr_y = self.draw_quiz_box(draw, curr_y, quiz)
        self.draw_footer(draw, curr_y, capsule_data.get("footer", {}))

        # Save JPEG
        jpeg_path = output_path.with_suffix(".jpeg")
        image.save(str(jpeg_path), "JPEG", quality=95, optimize=True)

        # Save PNG
        png_path = output_path.with_suffix(".png")
        image.save(str(png_path), "PNG", optimize=True)

        return jpeg_path

    def render_vertical_slides(self, capsule_data: Dict[str, Any], output_dir: pathlib.Path) -> List[pathlib.Path]:
        """
        Renders individual 1080x1920 slides for Shorts/Reels video compilation.
        """
        output_dir = pathlib.Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        slide_paths = []

        W, H = 1080, 1920
        header_data = capsule_data.get("header", {})
        sections = capsule_data.get("sections", [])
        quiz = capsule_data.get("quiz", {})

        # --- Slide 1: Hero Overview Slide ---
        img1 = Image.new("RGB", (W, H), (15, 23, 42))
        d1 = ImageDraw.Draw(img1)
        
        # Glow orbs
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dg = ImageDraw.Draw(glow)
        dg.ellipse([(-100, -100), (600, 600)], fill=(56, 189, 248, 80))
        dg.ellipse([(500, 1200), (1200, 1900)], fill=(168, 85, 247, 80))
        img1.paste(Image.alpha_composite(Image.new("RGBA", (W, H), (15, 23, 42, 255)), glow).convert("RGB"))
        d1 = ImageDraw.Draw(img1)

        # Top Badge
        d1.rounded_rectangle([340, 180, 740, 230], radius=25, fill=(234, 179, 8))
        d1.text((540, 205), "WEEKLY EXAM BLUEPRINT", font=get_font(22, bold=True), fill=(15, 23, 42), anchor="mm")

        # Main Title
        d1.text((540, 320), "WEEKLY HIGH-VALUE", font=get_font(52, bold=True), fill=(255, 255, 255), anchor="mm")
        d1.text((540, 390), "EXAM INSIGHTS", font=get_font(58, bold=True), fill=(250, 204, 21), anchor="mm")
        
        # Date Pill
        d1.rounded_rectangle([290, 460, 790, 520], radius=30, fill=(225, 29, 72))
        d1.text((540, 490), header_data.get("date_range", "Weekly Insights"), font=get_font(26, bold=True), fill=(255, 255, 255), anchor="mm")

        # 3 Key Topic Teasers
        card_y = 620
        d1.text((540, 580), "TOP 3 MILESTONES THIS WEEK", font=get_font(22, bold=True), fill=(148, 163, 184), anchor="mm")
        for s_idx, sec in enumerate(sections[:3]):
            sy = card_y + (s_idx * 260)
            color = sec.get("color", (56, 189, 248))
            d1.rounded_rectangle([80, sy, 1000, sy + 220], radius=20, fill=(30, 41, 59), outline=color, width=3)
            
            # Badge
            d1.ellipse([110, sy + 30, 170, sy + 90], fill=color)
            d1.text((140, sy + 60), str(s_idx + 1), font=get_font(32, bold=True), fill=(255, 255, 255), anchor="mm")
            
            d1.text((190, sy + 45), sec.get("title", ""), font=get_font(28, bold=True), fill=(255, 255, 255))
            d1.text((190, sy + 90), sec.get("subtitle", "")[:55] + "...", font=get_font(20, bold=False), fill=(203, 213, 225))
            
            # Quick summary tag
            pts = sec.get("points", [])
            if pts:
                d1.text((115, sy + 155), "Key Focus: " + pts[0][:65] + "...", font=get_font(18, bold=False), fill=(250, 204, 21))

        d1.text((540, 1750), "SWIPE / WATCH TO DECODE ALL 3 TOPICS  >>>", font=get_font(22, bold=True), fill=(56, 189, 248), anchor="mm")
        p1 = output_dir / "slide_01_intro.png"
        img1.save(str(p1), "PNG")
        slide_paths.append(p1)

        # --- Slides 2 to 4: Topic Slides ---
        for s_idx, sec in enumerate(sections[:3]):
            img = Image.new("RGB", (W, H), (248, 250, 252))
            d = ImageDraw.Draw(img)
            color = sec.get("color", (2, 132, 199))

            # Header Banner
            d.rectangle([0, 0, W, 220], fill=color)
            d.text((W // 2, 80), f"TOPIC #{s_idx + 1} • HIGH-YIELD EXAM INSIGHT", font=get_font(22, bold=True), fill=(254, 240, 138), anchor="mm")
            d.text((W // 2, 140), sec.get("title", "").upper(), font=get_font(36, bold=True), fill=(255, 255, 255), anchor="mm")
            d.text((W // 2, 185), sec.get("subtitle", ""), font=get_font(20, bold=False), fill=(241, 245, 249), anchor="mm")

            y_pos = 260
            # Fact Grid (2 columns for vertical phone layout)
            meta_grid = sec.get("metadata_grid", [])
            if meta_grid:
                col_w = (W - 140) // 2
                for m_idx, meta in enumerate(meta_grid[:6]):
                    r = m_idx // 2
                    c = m_idx % 2
                    mx = 60 + c * (col_w + 20)
                    my = y_pos + (r * 110)
                    d.rounded_rectangle([mx, my, mx + col_w, my + 95], radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
                    d.rounded_rectangle([mx, my, mx + 8, my + 95], radius=3, fill=color)
                    d.text((mx + 18, my + 14), meta.get("label", "").upper(), font=get_font(15, bold=True), fill=(100, 116, 139))
                    lines = wrap_text(meta.get("value", ""), get_font(18, bold=True), col_w - 30)
                    for l_idx, line in enumerate(lines[:2]):
                        d.text((mx + 18, my + 38 + (l_idx * 24)), line, font=get_font(18, bold=True), fill=(15, 23, 42))

                y_pos += ((len(meta_grid[:6]) + 1) // 2) * 110 + 20

            # Statistics if present
            stats = sec.get("stats", [])
            if stats:
                d.rounded_rectangle([60, y_pos, 1020, y_pos + 120], radius=14, fill=(241, 245, 249), outline=(148, 163, 184), width=1)
                d.text((90, y_pos + 15), "KEY STATISTICS & METRICS", font=get_font(16, bold=True), fill=color)
                stat_w = 900 // len(stats)
                for st_i, st in enumerate(stats):
                    sx = 90 + (st_i * stat_w)
                    d.text((sx, y_pos + 45), st.get("label", ""), font=get_font(14, bold=False), fill=(71, 85, 105))
                    d.text((sx, y_pos + 70), st.get("value", ""), font=get_font(26, bold=True), fill=(15, 23, 42))
                y_pos += 145

            # Core Exam Points
            d.rounded_rectangle([60, y_pos, 420, y_pos + 40], radius=8, fill=color)
            d.text((80, y_pos + 10), "MUST-REMEMBER EXAM TAKEAWAYS", font=get_font(16, bold=True), fill=(255, 255, 255))
            y_pos += 60

            for p_i, pt in enumerate(sec.get("points", [])[:4]):
                d.ellipse([65, y_pos + 5, 115, y_pos + 55], fill=color)
                d.text((90, y_pos + 30), str(p_i + 1), font=get_font(22, bold=True), fill=(255, 255, 255), anchor="mm")
                
                pt_lines = wrap_text(pt, get_font(22, bold=False), 880)
                for l_i, line in enumerate(pt_lines):
                    d.text((135, y_pos + (l_i * 30)), line, font=get_font(22, bold=False), fill=(15, 23, 42))
                y_pos += max(len(pt_lines) * 30, 60) + 18

            # Footer signature
            d.text((W // 2, 1820), "PULSE VECTOR  •  EXAM INTELLIGENCE", font=get_font(18, bold=True), fill=(148, 163, 184), anchor="mm")
            
            p_topic = output_dir / f"slide_{s_idx + 2:02d}_topic.png"
            img.save(str(p_topic), "PNG")
            slide_paths.append(p_topic)

        # --- Slide 5: Quiz Slide ---
        img_q = Image.new("RGB", (W, H), (15, 23, 42))
        dq = ImageDraw.Draw(img_q)
        
        dq.rounded_rectangle([320, 200, 760, 260], radius=30, fill=(139, 92, 246))
        dq.text((540, 230), "RAPID REVISION QUIZ", font=get_font(24, bold=True), fill=(255, 255, 255), anchor="mm")

        dq.text((540, 380), "QUESTION OF THE WEEK", font=get_font(38, bold=True), fill=(250, 204, 21), anchor="mm")
        
        q_lines = wrap_text(quiz.get("question", "Where is the permanent Secretariat of BIMSTEC located?"), get_font(32, bold=True), 900)
        for q_i, q_l in enumerate(q_lines):
            dq.text((540, 480 + (q_i * 45)), q_l, font=get_font(32, bold=True), fill=(255, 255, 255), anchor="mm")

        q_btn_y = 650
        for opt_i, opt in enumerate(quiz.get("options", ["(A) New Delhi", "(B) Dhaka", "(C) Colombo", "(D) Kathmandu"])):
            by = q_btn_y + (opt_i * 120)
            dq.rounded_rectangle([100, by, 980, by + 90], radius=16, fill=(30, 41, 59), outline=(139, 92, 246), width=2)
            dq.text((150, by + 30), opt, font=get_font(28, bold=True), fill=(241, 245, 249))

        dq.rounded_rectangle([200, 1250, 880, 1340], radius=20, fill=(225, 29, 72))
        dq.text((540, 1295), "COMMENT YOUR ANSWER BELOW!", font=get_font(26, bold=True), fill=(255, 255, 255), anchor="mm")
        dq.text((540, 1380), "Correct answer pinned in comments in 24 hours!", font=get_font(20, bold=False), fill=(148, 163, 184), anchor="mm")

        p_quiz = output_dir / "slide_05_quiz.png"
        img_q.save(str(p_quiz), "PNG")
        slide_paths.append(p_quiz)

        return slide_paths
