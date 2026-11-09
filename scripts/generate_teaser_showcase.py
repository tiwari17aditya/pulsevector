"""
Pulse Vector Brain Teaser Format Showcase Engine (Revision 2)
Renders 20 high-fidelity format templates across 5 categories with:
- Zero emoji tofu / missing glyph boxes
- Zero excessive square brackets (clean letter badge pills A, B, C, D)
- High-contrast graphical vector elements (grid cells, vector arrows, formula capsules)
- Dynamic 2x2 or 1x4 layout for option buttons based on length
"""

import os
import sys
import math
import pathlib
import datetime
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "src"))

from core.config import ARCHIVE_DIR
from core.image_utils import ensure_fonts
from core.video_utils import (
    create_base_background_with_glow, draw_watermark_on_image,
    draw_text_with_shadow_helper, download_audio_library,
    get_random_audio_track, merge_audio_video,
    generate_countdown_sfx
)
from core.youtube_utils import (
    get_authenticated_service, create_playlist,
    upload_video_to_youtube, add_video_to_playlist
)

REPORTS_DIR = ROOT_DIR / "reports"
PREVIEW_DIR = REPORTS_DIR / "templates_preview"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

FONT_MONO_PATH = pathlib.Path("C:/Windows/Fonts/consola.ttf")
FONT_BOLD_PATH = ROOT_DIR / "fonts" / "Roboto-Bold.ttf"
FONT_REG_PATH = ROOT_DIR / "fonts" / "Roboto-Regular.ttf"

# Helper for drawing resolution-independent vector arrows
def draw_vector_arrow(draw, x1, y, x2, color, width=3, head_size=10):
    draw.line([(x1, y), (x2, y)], fill=color, width=width)
    draw.polygon([(x2, y), (x2 - head_size, y - head_size//2 - 2), (x2 - head_size, y + head_size//2 + 2)], fill=color)

# 20 Standardized Format Templates (Free of emojis and square brackets)
TEMPLATES = [
    # CATEGORY 1: 3x3 Matrices & Spatial Grids
    {
        "id": "1.1",
        "category": "3X3 MATRICES & SPATIAL GRIDS",
        "name": "Graphic Matrix Grid",
        "badge": "MATRIX LOGIC // LEVEL: MEDIUM",
        "question": "Find the missing number to solve the matrix:",
        "type": "matrix_cells",
        "grid": [
            ["4", "9", "2"],
            ["3", "5", "7"],
            ["8", "1", "?"]
        ],
        "footer_note": "Hint: Check row and column interactions.",
        "options": [("A", "6"), ("B", "5"), ("C", "9"), ("D", "8")],
        "accent_color": (56, 189, 248),  # Sky blue
        "card_bg": (15, 23, 42, 235)
    },
    {
        "id": "1.2",
        "category": "3X3 MATRICES & SPATIAL GRIDS",
        "name": "Minimalist Pill Matrix",
        "badge": "NUMBER GRID CHALLENGE",
        "question": "Which number replaces the question mark?",
        "type": "matrix_pills",
        "rows": [
            ["07", "14", "28"],
            ["05", "10", "20"],
            ["09", "18", "?"]
        ],
        "footer_note": "Rule: Progression moves horizontally left to right.",
        "options": [("A", "32"), ("B", "36"), ("C", "45"), ("D", "54")],
        "accent_color": (168, 85, 247),  # Purple
        "card_bg": (24, 24, 38, 235)
    },
    {
        "id": "1.3",
        "category": "3X3 MATRICES & SPATIAL GRIDS",
        "name": "Row-by-Row Algebraic Step Grid",
        "badge": "SOLVE THE PATTERN",
        "question": "Complete the third line equation:",
        "type": "matrix_arrow_steps",
        "steps": [
            ("Row 1", ["3", "12", "48"]),
            ("Row 2", ["5", "20", "80"]),
            ("Row 3", ["7", "28", "?"])
        ],
        "footer_note": "Logic: Each step multiplies by constant factor.",
        "options": [("A", "96"), ("B", "104"), ("C", "112"), ("D", "128")],
        "accent_color": (234, 179, 8),  # Amber
        "card_bg": (28, 25, 23, 235)
    },
    {
        "id": "1.4",
        "category": "3X3 MATRICES & SPATIAL GRIDS",
        "name": "Magic Square Perimeter Sum",
        "badge": "TARGET SUM: 15",
        "question": "Fill the missing cell so every line equals 15:",
        "type": "matrix_sums",
        "lines": [
            ("2  |  7  |  6", "Sum = 15"),
            ("9  |  5  |  1", "Sum = 15"),
            ("4  |  ?  |  8", "Sum = 15")
        ],
        "footer_note": "Every row, column, and diagonal equals 15.",
        "options": [("A", "2"), ("B", "3"), ("C", "5"), ("D", "7")],
        "accent_color": (34, 197, 94),  # Emerald
        "card_bg": (15, 30, 25, 235)
    },

    # CATEGORY 2: BODMAS & Arithmetic Traps
    {
        "id": "2.1",
        "category": "BODMAS & ARITHMETIC TRAPS",
        "name": "Hero Formula (90% Fail This)",
        "badge": "ORDER OF OPERATIONS TRAP",
        "question": "What is the exact value of this expression?",
        "type": "hero_formula",
        "formula": "50 - 50 × 0 + 2 + 2 = ?",
        "footer_note": "Warning: Apply standard BODMAS / PEMDAS precedence rules!",
        "options": [("A", "4"), ("B", "54"), ("C", "0"), ("D", "2")],
        "accent_color": (239, 68, 68),  # Red
        "card_bg": (35, 15, 20, 235)
    },
    {
        "id": "2.2",
        "category": "BODMAS & ARITHMETIC TRAPS",
        "name": "Digital Matchstick Challenge",
        "badge": "MATCHSTICK LOGIC PUZZLE",
        "question": "Rule: Move ONLY 1 matchstick to make it true.",
        "type": "hero_formula",
        "formula": "6 + 4 = 4",
        "footer_note": "Which single stick movement fixes the equation?",
        "options": [
            ("A", "Change 6 to 0: gives 0 + 4 = 4"),
            ("B", "Change + to -: gives 6 - 4 = 2"),
            ("C", "Change 4 to 1: gives 6 + 1 = 7"),
            ("D", "Change 6 to 5: gives 5 + 4 = 9")
        ],
        "accent_color": (249, 115, 22),  # Orange
        "card_bg": (35, 22, 15, 235)
    },
    {
        "id": "2.3",
        "category": "BODMAS & ARITHMETIC TRAPS",
        "name": "Balance Scale Equilibrium",
        "badge": "THE BALANCE SCALE DILEMMA",
        "question": "Find the weight that balances the final scale:",
        "type": "scale_balance",
        "lines": [
            "Scale 1:  2 Apples  =  3 Oranges",
            "Scale 2:  2 Oranges =  4 Bananas",
            "Scale 3:  1 Apple + 1 Orange =  ? Bananas"
        ],
        "footer_note": "Substitute the equivalent values to solve Scale 3.",
        "options": [("A", "4 Bananas"), ("B", "5 Bananas"), ("C", "6 Bananas"), ("D", "7 Bananas")],
        "accent_color": (16, 185, 129),  # Green
        "card_bg": (15, 30, 22, 235)
    },
    {
        "id": "2.4",
        "category": "BODMAS & ARITHMETIC TRAPS",
        "name": "10-Second Mental Math Sprint",
        "badge": "10-SECOND SPEED TEST",
        "question": "Solve before the timer hits zero:",
        "type": "hero_formula",
        "formula": "6 ÷ 2(1 + 2) = ?",
        "footer_note": "Most people answer 1. Are they correct?",
        "options": [("A", "1"), ("B", "6"), ("C", "9"), ("D", "12")],
        "accent_color": (245, 158, 11),  # Gold
        "card_bg": (30, 25, 15, 235)
    },

    # CATEGORY 3: Detective Deduction & Micro-Mysteries
    {
        "id": "3.1",
        "category": "DETECTIVE DEDUCTION",
        "name": "Police Case File Dossier",
        "badge": "CASE FILE #1109 // MUSEUM HEIST",
        "question": "Incident: Compass stolen between 1:00 PM and 1:30 PM.",
        "type": "detective_dossier",
        "suspects": [
            ("Alex (Curator)", "Live radio interview from 12:50 to 1:40 PM."),
            ("Lisa (Assistant)", "Heard Alex talking in his office at 1:15 PM."),
            ("Mark (Guard)", "Patrolling gallery, saw nobody enter.")
        ],
        "footer_note": "Who is caught in a direct contradiction?",
        "options": [("A", "Alex"), ("B", "Lisa"), ("C", "Mark"), ("D", "None of them")],
        "accent_color": (14, 165, 233),  # Cyan
        "card_bg": (15, 25, 35, 235)
    },
    {
        "id": "3.2",
        "category": "DETECTIVE DEDUCTION",
        "name": "Interrogation Room Dialogue",
        "badge": "WHO IS LYING?",
        "question": "A ring vanished during an 8:00 PM blackout.",
        "type": "detective_dossier",
        "suspects": [
            ("Chef", "I was cooking soup in the kitchen."),
            ("Maid", "I was reading a book in the living room."),
            ("Driver", "I was changing a flat tire outside.")
        ],
        "footer_note": "One alibi is physically impossible in the dark!",
        "options": [("A", "The Chef"), ("B", "The Maid"), ("C", "The Driver"), ("D", "All innocent")],
        "accent_color": (244, 63, 94),  # Rose
        "card_bg": (35, 15, 25, 235)
    },
    {
        "id": "3.3",
        "category": "DETECTIVE DEDUCTION",
        "name": "Timeline Inconsistency Card",
        "badge": "SPOT THE CONTRADICTION",
        "question": "Snowstorm hit at 3:00 PM. Safe opened at 4:00 PM.",
        "type": "detective_dossier",
        "suspects": [
            ("Suspect 1", "Arrived on foot at 3:30 PM (No footprints in snow)"),
            ("Suspect 2", "Shoveling snow outside from 3:15 to 4:15 PM"),
            ("Suspect 3", "Asleep by the warm fireplace inside")
        ],
        "footer_note": "Which suspect gave themselves away to the detective?",
        "options": [("A", "Suspect 1"), ("B", "Suspect 2"), ("C", "Suspect 3"), ("D", "Suspect 2 & 3")],
        "accent_color": (139, 92, 246),  # Violet
        "card_bg": (25, 18, 35, 235)
    },
    {
        "id": "3.4",
        "category": "DETECTIVE DEDUCTION",
        "name": "3-Badge Witness Cards",
        "badge": "WHO STOLE THE VAULT KEY?",
        "question": "Time of Theft: 10:00 PM (Heavy Rain Outside)",
        "type": "detective_dossier",
        "suspects": [
            ("GARDENER", "I was watering the flower beds outside."),
            ("BUTLER", "I was polishing silverware in the pantry."),
            ("CHAUFFEUR", "I was wiping down the car in the garage.")
        ],
        "footer_note": "Who told a blatant lie to the officer?",
        "options": [("A", "Gardener"), ("B", "Butler"), ("C", "Chauffeur"), ("D", "No one lied")],
        "accent_color": (20, 184, 166),  # Teal
        "card_bg": (15, 30, 30, 235)
    },

    # CATEGORY 4: Sequences, Ciphers & Pattern Pickers
    {
        "id": "4.1",
        "category": "SEQUENCES & PATTERNS",
        "name": "Connected Node Sequence",
        "badge": "NUMBER SERIES CHALLENGE",
        "question": "What number comes next in the sequence?",
        "type": "sequence_nodes",
        "nodes": ["2", "5", "12", "27", "58", "?"],
        "footer_note": "Pattern clue: Look at double and add progression.",
        "options": [("A", "116"), ("B", "119"), ("C", "121"), ("D", "125")],
        "accent_color": (59, 130, 246),  # Blue
        "card_bg": (15, 25, 45, 235)
    },
    {
        "id": "4.2",
        "category": "SEQUENCES & PATTERNS",
        "name": "Secret Word Decoder (Cipher)",
        "badge": "DECODE THE CIPHER",
        "question": "Rule: Letter values follow alphabet positions (A=1...)",
        "type": "cipher_box",
        "lines": [
            "Given:  C A T   =  24   (3 + 1 + 20)",
            "Given:  D O G   =  26   (4 + 15 + 7)",
            "Target: B I R D =  ?"
        ],
        "footer_note": "Calculate the exact letter-sum for BIRD.",
        "options": [("A", "30"), ("B", "32"), ("C", "34"), ("D", "36")],
        "accent_color": (236, 72, 153),  # Pink
        "card_bg": (35, 18, 30, 235)
    },
    {
        "id": "4.3",
        "category": "SEQUENCES & PATTERNS",
        "name": "Spot the Impostor (Odd One Out)",
        "badge": "SPOT THE ODD ONE OUT",
        "question": "Three numbers share a hidden property. One does not.",
        "type": "odd_one_out",
        "items": ["24", "36", "52", "13"],
        "footer_note": "Which number breaks the mathematical rule?",
        "options": [
            ("A", "24 (Multiple of 6)"),
            ("B", "36 (Perfect square)"),
            ("C", "52 (Even composite)"),
            ("D", "13 (Prime number)")
        ],
        "accent_color": (168, 85, 247),  # Purple
        "card_bg": (25, 18, 40, 235)
    },
    {
        "id": "4.4",
        "category": "SEQUENCES & PATTERNS",
        "name": "Dual Letter-Number Matrix",
        "badge": "DUAL PROGRESSION",
        "question": "Find the missing pair in alternating progression:",
        "type": "dual_progression",
        "tokens": ["A-2", "C-4", "F-8", "J-16", "?"],
        "footer_note": "Letters step +2, +3, +4... Numbers double each step.",
        "options": [("A", "O-32"), ("B", "N-32"), ("C", "O-24"), ("D", "P-32")],
        "accent_color": (14, 165, 233),  # Sky
        "card_bg": (15, 25, 38, 235)
    },

    # CATEGORY 5: Lateral Riddles, Family Relations & Paradoxes
    {
        "id": "5.1",
        "category": "LATERAL & RELATIONS",
        "name": "Family Relation Decoder",
        "badge": "BLOOD RELATIONS PUZZLE",
        "question": "Pointing to a woman in a photograph, Rohit says:",
        "type": "quote_riddle",
        "quote": "\"Her mother is the only daughter of my mother-in-law.\"",
        "footer_note": "How is the woman in the photo related to Rohit?",
        "options": [("A", "Sister"), ("B", "Daughter"), ("C", "Wife"), ("D", "Niece")],
        "accent_color": (245, 158, 11),  # Amber
        "card_bg": (30, 22, 15, 235)
    },
    {
        "id": "5.2",
        "category": "LATERAL & RELATIONS",
        "name": "The Well Escape Trap",
        "badge": "THE WELL ESCAPE TRAP",
        "question": "A frog is at the bottom of a 30-meter well.",
        "type": "scenario_riddle",
        "lines": [
            "• Climbs UP 3 meters each day",
            "• Slips DOWN 2 meters each night"
        ],
        "footer_note": "How many days will it take to reach the top?",
        "options": [("A", "30 Days"), ("B", "28 Days"), ("C", "27 Days"), ("D", "29 Days")],
        "accent_color": (34, 197, 94),  # Emerald
        "card_bg": (15, 30, 20, 235)
    },
    {
        "id": "5.3",
        "category": "LATERAL & RELATIONS",
        "name": "Clock Mirror Reflection",
        "badge": "MIRROR TIME PUZZLE",
        "question": "An analog wall clock displays 3:40.",
        "type": "scenario_riddle",
        "lines": [
            "Viewed directly in a vertical mirror:",
            "What time do the clock hands appear to show?"
        ],
        "footer_note": "Mental Shortcut: Subtract time from 11:60.",
        "options": [("A", "8:20"), ("B", "9:20"), ("C", "8:40"), ("D", "7:20")],
        "accent_color": (99, 102, 241),  # Indigo
        "card_bg": (20, 20, 38, 235)
    },
    {
        "id": "5.4",
        "category": "LATERAL & RELATIONS",
        "name": "The Truth & Lie Paradox",
        "badge": "THE TRUTH & LIE PARADOX",
        "question": "Two guards: One always lies, one always tells truth.",
        "type": "scenario_riddle",
        "lines": [
            "You can ask ONLY ONE question to find the right path.",
            "What question guarantees the correct road?"
        ],
        "footer_note": "A classic logic problem solved by double negation.",
        "options": [
            ("A", "Which way is your home?"),
            ("B", "What would the other guard say is correct?"),
            ("C", "Are you telling the truth?"),
            ("D", "Is this the right path?")
        ],
        "accent_color": (236, 72, 153),  # Fuchsia
        "card_bg": (35, 18, 32, 235)
    }
]

def draw_option_button(draw, ox, oy, b_w, b_h, letter, text, f_bold, f_reg, accent):
    """Draws a sleek option button with a circular letter badge (Zero square brackets)."""
    # Background pill container
    draw.rounded_rectangle(
        [(ox, oy), (ox + b_w, oy + b_h)],
        radius=16,
        fill=(15, 23, 42, 230),
        outline=(255, 255, 255, 60),
        width=2
    )
    # Circle badge on the left for the letter
    circle_r = 17
    circle_cx = ox + 30
    circle_cy = oy + b_h / 2
    draw.ellipse(
        [(circle_cx - circle_r, circle_cy - circle_r), (circle_cx + circle_r, circle_cy + circle_r)],
        fill=(accent[0], accent[1], accent[2], 65),
        outline=accent,
        width=2
    )
    draw.text((circle_cx, circle_cy), letter, font=f_bold, fill=(255, 255, 255), anchor="mm")
    
    # Text label cleanly offset
    draw.text((circle_cx + circle_r + 14, circle_cy), text, font=f_reg, fill=(243, 244, 246), anchor="lm")

def render_template_card(tmpl, w=920, h=1060):
    """Renders a single high-impact 920x1060 card for a template."""
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    accent = tmpl["accent_color"]
    bg_color = tmpl["card_bg"]
    
    # Outer Card Background with rounded corners & glowing border
    draw.rounded_rectangle([(0, 0), (w, h)], radius=32, fill=bg_color, outline=(accent[0], accent[1], accent[2], 140), width=3)
    draw.line([(60, 4), (w - 60, 4)], fill=(accent[0], accent[1], accent[2], 220), width=4)
    
    f_badge = ImageFont.truetype(str(FONT_BOLD_PATH), 24)
    f_title = ImageFont.truetype(str(FONT_BOLD_PATH), 32)
    f_body = ImageFont.truetype(str(FONT_REG_PATH), 26)
    f_body_bold = ImageFont.truetype(str(FONT_BOLD_PATH), 26)
    f_hero = ImageFont.truetype(str(FONT_BOLD_PATH), 44)
    f_grid_num = ImageFont.truetype(str(FONT_BOLD_PATH), 38)
    f_opt_letter = ImageFont.truetype(str(FONT_BOLD_PATH), 24)
    f_opt_text = ImageFont.truetype(str(FONT_REG_PATH), 24)
    f_note = ImageFont.truetype(str(FONT_REG_PATH), 24)
    
    # 1. Category & Template Header Badge
    badge_text = tmpl["badge"]
    b_len = f_badge.getlength(badge_text)
    badge_w = b_len + 44
    badge_x = (w - badge_w) / 2
    badge_y = 35
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + 44)], radius=22, fill=(accent[0], accent[1], accent[2], 55), outline=accent, width=2)
    draw.text((badge_x + 22, badge_y + 8), badge_text, font=f_badge, fill=(255, 255, 255))
    
    # 2. Question / Context Header
    q_text = tmpl["question"]
    draw.text((w/2, 115), q_text, font=f_title, fill=(243, 244, 246), anchor="mt")
    
    # 3. Main Hero Area (y: 180 to 540)
    t_type = tmpl["type"]
    
    if t_type == "matrix_cells":
        # Render clean graphical 3x3 rounded cells
        grid = tmpl["grid"]
        c_w, c_h = 130, 95
        gap_x, gap_y = 25, 18
        tot_w = 3 * c_w + 2 * gap_x
        start_x = (w - tot_w) / 2
        for r_idx, row in enumerate(grid):
            r_y = 190 + r_idx * (c_h + gap_y)
            for c_idx, val in enumerate(row):
                cx = start_x + c_idx * (c_w + gap_x)
                is_target = val == "?"
                fill_c = (accent[0], accent[1], accent[2], 70) if is_target else (30, 41, 59, 190)
                border_c = accent if is_target else (255, 255, 255, 70)
                draw.rounded_rectangle([(cx, r_y), (cx + c_w, r_y + c_h)], radius=18, fill=fill_c, outline=border_c, width=3 if is_target else 2)
                f_color = accent if is_target else (255, 255, 255)
                draw.text((cx + c_w/2, r_y + c_h/2), val, font=f_grid_num, fill=f_color, anchor="mm")
                
    elif t_type == "matrix_pills":
        rows = tmpl["rows"]
        p_w, p_h = 160, 75
        gap_x, gap_y = 30, 20
        total_w = 3 * p_w + 2 * gap_x
        start_x = (w - total_w) / 2
        for r_idx, row in enumerate(rows):
            r_y = 195 + r_idx * (p_h + gap_y)
            for c_idx, val in enumerate(row):
                c_x = start_x + c_idx * (p_w + gap_x)
                is_target = val == "?"
                p_border = accent if is_target else (255, 255, 255, 80)
                p_fill = (accent[0], accent[1], accent[2], 65) if is_target else (30, 41, 59, 180)
                draw.rounded_rectangle([(c_x, r_y), (c_x + p_w, r_y + p_h)], radius=18, fill=p_fill, outline=p_border, width=3 if is_target else 2)
                f_color = accent if is_target else (255, 255, 255)
                draw.text((c_x + p_w/2, r_y + p_h/2), val, font=f_hero, fill=f_color, anchor="mm")

    elif t_type == "matrix_arrow_steps":
        steps = tmpl["steps"]
        for idx, (label, tokens) in enumerate(steps):
            l_y = 195 + idx * 85
            # Label
            draw.text((80, l_y + 35), label + ":", font=f_title, fill=(209, 213, 219), anchor="lm")
            # 3 pills with vector arrows between them
            start_x = 210
            p_w, p_h = 100, 65
            arrow_gap = 55
            for t_idx, tok in enumerate(tokens):
                px = start_x + t_idx * (p_w + arrow_gap)
                is_target = tok == "?"
                p_fill = (accent[0], accent[1], accent[2], 70) if is_target else (30, 41, 59, 190)
                p_border = accent if is_target else (255, 255, 255, 70)
                draw.rounded_rectangle([(px, l_y), (px + p_w, l_y + p_h)], radius=16, fill=p_fill, outline=p_border, width=2)
                draw.text((px + p_w/2, l_y + p_h/2), tok, font=f_title, fill=accent if is_target else (255, 255, 255), anchor="mm")
                if t_idx < len(tokens) - 1:
                    ax1 = px + p_w + 10
                    ax2 = ax1 + arrow_gap - 20
                    draw_vector_arrow(draw, ax1, l_y + p_h/2, ax2, accent, width=3)

    elif t_type == "matrix_sums":
        lines = tmpl["lines"]
        for idx, (grid_row, sum_label) in enumerate(lines):
            l_y = 200 + idx * 80
            draw.rounded_rectangle([(70, l_y), (w - 70, l_y + 65)], radius=16, fill=(30, 41, 59, 180), outline=(255, 255, 255, 50), width=2)
            draw.text((120, l_y + 32), grid_row, font=f_hero, fill=(243, 244, 246), anchor="lm")
            # Arrow
            draw_vector_arrow(draw, 530, l_y + 32, 600, accent, width=3)
            # Sum pill
            draw.rounded_rectangle([(620, l_y + 10), (w - 100, l_y + 55)], radius=12, fill=(accent[0], accent[1], accent[2], 60), outline=accent, width=2)
            draw.text((680, l_y + 32), sum_label, font=f_title, fill=(255, 255, 255), anchor="lm")

    elif t_type == "hero_formula":
        formula = tmpl["formula"]
        f_box_w = 760
        f_box_h = 130
        bx = (w - f_box_w) / 2
        by = 240
        draw.rounded_rectangle([(bx, by), (bx + f_box_w, by + f_box_h)], radius=24, fill=(15, 23, 42, 210), outline=accent, width=3)
        draw.text((w/2, by + f_box_h/2), formula, font=f_hero, fill=accent, anchor="mm")

    elif t_type == "scale_balance":
        lines = tmpl["lines"]
        for idx, l in enumerate(lines):
            l_y = 200 + idx * 80
            is_target = "?" in l
            draw.rounded_rectangle([(70, l_y), (w - 70, l_y + 65)], radius=16, fill=(30, 41, 59, 180), outline=accent if is_target else (255, 255, 255, 45), width=2)
            draw.text((w/2, l_y + 32), l, font=f_title, fill=accent if is_target else (243, 244, 246), anchor="mm")

    elif t_type == "detective_dossier":
        suspects = tmpl["suspects"]
        for idx, (name, alibi) in enumerate(suspects):
            s_y = 190 + idx * 88
            draw.rounded_rectangle([(60, s_y), (w - 60, s_y + 75)], radius=16, fill=(15, 23, 42, 210), outline=accent if idx == 0 else (255, 255, 255, 45), width=2)
            # Role / Name tag
            draw.text((85, s_y + 24), name, font=f_body_bold, fill=accent if idx == 0 else (255, 255, 255), anchor="lm")
            # Quote
            draw.text((85, s_y + 52), f'"{alibi}"', font=f_body, fill=(209, 213, 219), anchor="lm")

    elif t_type == "sequence_nodes":
        nodes = tmpl["nodes"]
        n_w, n_h = 90, 80
        gap = 45
        total_w = len(nodes) * n_w + (len(nodes) - 1) * gap
        start_x = (w - total_w) / 2
        n_y = 240
        for idx, n in enumerate(nodes):
            nx = start_x + idx * (n_w + gap)
            is_target = n == "?"
            n_border = accent if is_target else (255, 255, 255, 80)
            n_fill = (accent[0], accent[1], accent[2], 70) if is_target else (30, 41, 59, 190)
            draw.rounded_rectangle([(nx, n_y), (nx + n_w, n_y + n_h)], radius=20, fill=n_fill, outline=n_border, width=3 if is_target else 2)
            draw.text((nx + n_w/2, n_y + n_h/2), n, font=f_hero, fill=accent if is_target else (255, 255, 255), anchor="mm")
            if idx < len(nodes) - 1:
                ax1 = nx + n_w + 8
                ax2 = ax1 + gap - 16
                draw_vector_arrow(draw, ax1, n_y + n_h/2, ax2, accent, width=3)

    elif t_type == "dual_progression":
        tokens = tmpl["tokens"]
        n_w, n_h = 110, 75
        gap = 45
        total_w = len(tokens) * n_w + (len(tokens) - 1) * gap
        start_x = (w - total_w) / 2
        n_y = 240
        for idx, t_val in enumerate(tokens):
            nx = start_x + idx * (n_w + gap)
            is_target = t_val == "?"
            draw.rounded_rectangle([(nx, n_y), (nx + n_w, n_y + n_h)], radius=18, fill=(accent[0], accent[1], accent[2], 70) if is_target else (30, 41, 59, 190), outline=accent if is_target else (255, 255, 255, 80), width=2)
            draw.text((nx + n_w/2, n_y + n_h/2), t_val, font=f_title, fill=accent if is_target else (255, 255, 255), anchor="mm")
            if idx < len(tokens) - 1:
                ax1 = nx + n_w + 8
                ax2 = ax1 + gap - 16
                draw_vector_arrow(draw, ax1, n_y + n_h/2, ax2, accent, width=3)

    elif t_type == "cipher_box":
        lines = tmpl["lines"]
        for idx, l in enumerate(lines):
            l_y = 200 + idx * 75
            is_target = "Target" in l
            draw.rounded_rectangle([(70, l_y), (w - 70, l_y + 62)], radius=16, fill=(30, 41, 59, 180), outline=accent if is_target else (255, 255, 255, 45), width=2)
            draw.text((w/2, l_y + 31), l, font=f_title, fill=accent if is_target else (243, 244, 246), anchor="mm")

    elif t_type == "odd_one_out":
        items = tmpl["items"]
        box_w, box_h = 170, 95
        gap = 35
        total_w = 4 * box_w + 3 * gap
        start_x = (w - total_w) / 2
        by = 240
        for idx, item in enumerate(items):
            ix = start_x + idx * (box_w + gap)
            draw.rounded_rectangle([(ix, by), (ix + box_w, by + box_h)], radius=20, fill=(30, 41, 59, 200), outline=accent if item == "13" else (255, 255, 255, 70), width=2)
            draw.text((ix + box_w/2, by + box_h/2), item, font=f_hero, fill=(255, 255, 255), anchor="mm")

    elif t_type == "quote_riddle":
        quote = tmpl["quote"]
        q_box_w = 780
        q_box_h = 130
        bx = (w - q_box_w) / 2
        by = 220
        draw.rounded_rectangle([(bx, by), (bx + q_box_w, by + q_box_h)], radius=22, fill=(30, 41, 59, 210), outline=accent, width=2)
        draw.text((w/2, by + q_box_h/2), quote, font=f_title, fill=accent, anchor="mm")

    elif t_type == "scenario_riddle":
        lines = tmpl["lines"]
        for idx, l in enumerate(lines):
            l_y = 220 + idx * 65
            draw.text((w/2, l_y), l, font=f_title, fill=(243, 244, 246), anchor="mt")

    # 4. Footer Note / Clue Bar
    note_text = tmpl["footer_note"]
    draw.rounded_rectangle([(60, 560), (w - 60, 615)], radius=14, fill=(15, 23, 42, 160), outline=(255, 255, 255, 30), width=1)
    draw.text((w/2, 587), note_text, font=f_note, fill=(209, 213, 219), anchor="mm")

    # 5. Options: Dynamic Layout (1 column if long text, 2x2 grid if short text)
    options = tmpl["options"]
    max_len = max(len(opt_text) for _, opt_text in options)
    use_single_column = max_len > 18 or len(options) != 4
    
    if use_single_column:
        b_w = w - 140
        b_h = 58
        start_y = 650
        gap_y = 12
        for idx, (letter, opt_text) in enumerate(options[:4]):
            oy = start_y + idx * (b_h + gap_y)
            draw_option_button(draw, 70, oy, b_w, b_h, letter, opt_text, f_opt_letter, f_opt_text, accent)
    else:
        b_w = (w - 180) // 2
        b_h = 70
        gap_x = 24
        gap_y = 18
        opt_y = 660
        positions = [
            (70, opt_y),
            (70 + b_w + gap_x, opt_y),
            (70, opt_y + b_h + gap_y),
            (70 + b_w + gap_x, opt_y + b_h + gap_y)
        ]
        for idx, (letter, opt_text) in enumerate(options[:4]):
            ox, oy = positions[idx]
            draw_option_button(draw, ox, oy, b_w, b_h, letter, opt_text, f_opt_letter, f_opt_text, accent)
        
    draw.text((w/2, h - 35), "PULSE VECTOR DESIGN LAB // PROTOTYPE", font=f_note, fill=(156, 163, 175, 160), anchor="mm")
    return card

def render_countdown_timer(draw, cx, cy, radius, seconds_left, progress, accent=(56, 189, 248)):
    """Draws an animated circular countdown timer with progress arc."""
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(255, 255, 255, 40), width=6)
    start_angle = -90
    end_angle = start_angle + (360 * max(0.01, progress))
    draw.arc([(cx - radius, cy - radius), (cx + radius, cy + radius)], start=start_angle, end=end_angle, fill=accent, width=8)
    
    f_num = ImageFont.truetype(str(FONT_BOLD_PATH), 50)
    draw.text((cx, cy), str(seconds_left), font=f_num, fill=(255, 255, 255), anchor="mm")

def build_showcase_video():
    """Builds the 1080x1920 Showcase Video featuring all 20 templates."""
    W_canvas, H_canvas = 1080, 1920
    fps = 10
    
    intro_dur = 3.0
    tmpl_dur = 5.0
    outro_dur = 4.0
    total_dur = intro_dur + len(TEMPLATES) * tmpl_dur + outro_dur
    total_frames = int(fps * total_dur)
    
    print(f"🎬 Compiling 20-Template Master Showcase Video: {total_dur:.1f}s ({total_frames} frames @ {fps}fps)...")
    
    # Pre-render all 20 cards and save previews
    cards = []
    for tmpl in TEMPLATES:
        c = render_template_card(tmpl, w=920, h=1060)
        out_p = PREVIEW_DIR / f"template_{tmpl['id']}.png"
        c.save(out_p, "PNG")
        cards.append((tmpl, c))
    print(f"✅ Rendered preview PNGs for all {len(TEMPLATES)} templates in: {PREVIEW_DIR}")
        
    raw_video_path = REPORTS_DIR / "brainteaser_showcase_raw.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(raw_video_path), fourcc, fps, (W_canvas, H_canvas))
    
    f_hdr_cat = ImageFont.truetype(str(FONT_BOLD_PATH), 28)
    f_hdr_tmpl = ImageFont.truetype(str(FONT_BOLD_PATH), 40)
    f_sub = ImageFont.truetype(str(FONT_REG_PATH), 28)
    f_intro_hero = ImageFont.truetype(str(FONT_BOLD_PATH), 64)
    f_intro_sub = ImageFont.truetype(str(FONT_REG_PATH), 36)
    f_logo = ImageFont.truetype(str(FONT_BOLD_PATH), 26)
    
    intro_frames = int(fps * intro_dur)
    tmpl_frames = int(fps * tmpl_dur)
    
    card_x = (W_canvas - 920) // 2
    card_y = 310
    
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        
        # 1. Base gradient background
        frame_img = create_base_background_with_glow(W_canvas, H_canvas, t=t)
        draw = ImageDraw.Draw(frame_img)
        
        # Phase A: Intro (0 to 3s)
        if frame_idx < intro_frames:
            draw.text((W_canvas/2, 600), "PULSE VECTOR", font=f_logo, fill=(56, 189, 248), anchor="mm")
            draw.text((W_canvas/2, 700), "BRAIN TEASER", font=f_intro_hero, fill=(255, 255, 255), anchor="mm")
            draw.text((W_canvas/2, 780), "DESIGN LAB", font=f_intro_hero, fill=(234, 179, 8), anchor="mm")
            
            draw.rounded_rectangle([(140, 920), (W_canvas - 140, 1100)], radius=24, fill=(15, 23, 42, 210), outline=(255, 255, 255, 40), width=2)
            draw.text((W_canvas/2, 970), "20 Standardized Format Templates", font=f_intro_sub, fill=(243, 244, 246), anchor="mm")
            draw.text((W_canvas/2, 1030), "5 Core Categories • Clean Typography & Zero Tofu", font=f_sub, fill=(156, 163, 175), anchor="mm")
            
            draw.text((W_canvas/2, 1300), "Reviewing Templates 1.1 through 5.4", font=f_sub, fill=(56, 189, 248), anchor="mm")

        # Phase B: Template Showcase (3s to 103s)
        elif frame_idx < intro_frames + len(TEMPLATES) * tmpl_frames:
            rel_idx = frame_idx - intro_frames
            t_idx = rel_idx // tmpl_frames
            t_subframe = rel_idx % tmpl_frames
            
            tmpl, card_img = cards[t_idx]
            accent = tmpl["accent_color"]
            
            # Top Breadcrumbs & Header
            draw.text((W_canvas/2, 130), f"CATEGORY {tmpl['id'][0]} OF 5: {tmpl['category']}", font=f_hdr_cat, fill=(156, 163, 175), anchor="mm")
            draw.text((W_canvas/2, 190), f"Template {tmpl['id']}: {tmpl['name']}", font=f_hdr_tmpl, fill=accent, anchor="mm")
            draw.line([(200, 240), (W_canvas - 200, 240)], fill=(255, 255, 255, 30), width=2)
            
            # Paste Center Card
            frame_img.paste(card_img, (card_x, card_y), card_img)
            
            # Bottom Countdown Ring & Callout
            secs_left = math.ceil((tmpl_frames - t_subframe) / fps)
            progress = (tmpl_frames - t_subframe) / float(tmpl_frames)
            
            timer_cx = W_canvas // 2
            timer_cy = 1490
            render_countdown_timer(draw, timer_cx, timer_cy, radius=55, seconds_left=secs_left, progress=progress, accent=accent)
            
            draw.text((W_canvas/2, 1590), "Pause to Solve! Next format in 5s...", font=f_sub, fill=(229, 231, 235), anchor="mm")
            draw.text((W_canvas/2, 1640), f"Template {t_idx + 1} of 20", font=f_hdr_cat, fill=(156, 163, 175), anchor="mm")

        # Phase C: Outro (103s to 107s)
        else:
            draw.text((W_canvas/2, 600), "DESIGN LAB SIGN-OFF", font=f_logo, fill=(56, 189, 248), anchor="mm")
            draw.text((W_canvas/2, 700), "WHICH FORMATS", font=f_intro_hero, fill=(255, 255, 255), anchor="mm")
            draw.text((W_canvas/2, 780), "DID YOU LIKE BEST?", font=f_intro_hero, fill=(34, 197, 94), anchor="mm")
            
            draw.rounded_rectangle([(140, 920), (W_canvas - 140, 1140)], radius=24, fill=(15, 23, 42, 210), outline=(255, 255, 255, 40), width=2)
            draw.text((W_canvas/2, 975), "Drop your favorite template numbers in the comments!", font=f_intro_sub, fill=(243, 244, 246), anchor="mm")
            draw.text((W_canvas/2, 1040), "(e.g. 1.1 for Matrices, 2.1 for BODMAS, 3.1 for Detective)", font=f_sub, fill=(234, 179, 8), anchor="mm")
            draw.text((W_canvas/2, 1095), "We will bake your chosen templates into the production engine.", font=f_sub, fill=(156, 163, 175), anchor="mm")
            
            draw.text((W_canvas/2, 1300), "Subscribe to @Pulse_vector for Daily Mind Challenges", font=f_sub, fill=(56, 189, 248), anchor="mm")
        
        # Watermark
        draw.text((W_canvas/2, 1850), "P U L S E   V E C T O R   D E S I G N   L A B", font=f_logo, fill=(255, 255, 255, 90), anchor="mm")
        
        frame_cv = cv2.cvtColor(np.array(frame_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        out.write(frame_cv)
        
        if frame_idx % 100 == 0:
            print(f"  > Rendered frame {frame_idx}/{total_frames} ({int(frame_idx/total_frames*100)}%)...")
            
    out.release()
    print(f"✅ Video frames rendered cleanly to: {raw_video_path}")
    
    # Audio Muxing
    audio_path = ROOT_DIR / "samples" / "Audio" / "track_01.mp3"
    final_video_path = REPORTS_DIR / "brainteaser_templates_showcase.mp4"
    
    if audio_path.exists():
        print(f"🎵 Muxing background audio track '{audio_path.name}' into final video...")
        merge_audio_video(str(raw_video_path), str(audio_path), str(final_video_path), video_duration=total_dur)
    else:
        print("⚠️ Background audio track not found; copying raw video to final...")
        import shutil
        shutil.copyfile(raw_video_path, final_video_path)
        
    print(f"🎉 Final Master Showcase Video complete: {final_video_path}")
    return final_video_path

def upload_showcase_to_private_youtube(video_path):
    """Publishes the Master Showcase Video to a private YouTube playlist."""
    print("\n🚀 Authenticating with YouTube Data API v3...")
    youtube = get_authenticated_service()
    
    title = "🧠 20 Brain Teaser Format Showcase (V2 Clean) | Pulse Vector Design Lab (Private)"
    
    chapters = [
        "00:00 - Introduction & Lab Overview"
    ]
    cur_secs = 3
    for tmpl in TEMPLATES:
        m = cur_secs // 60
        s = cur_secs % 60
        chapters.append(f"{m:02d}:{s:02d} - Template {tmpl['id']}: {tmpl['name']} ({tmpl['category']})")
        cur_secs += 5
    m_out = cur_secs // 60
    s_out = cur_secs % 60
    chapters.append(f"{m_out:02d}:{s_out:02d} - Outro: Format Voting & Next Steps")
    
    description = (
        "🧠 Pulse Vector Brain Teaser Format Showcase (20 Standardized Templates — V2 Clean)\n\n"
        "This private design review video presents 20 standardized, high-engagement formatting templates "
        "across 5 brain teaser categories, updated with clean typography (zero missing glyphs/tofu) and stylish letter badges (zero square brackets).\n\n"
        "⏱️ CHAPTER TIMESTAMPS:\n" +
        "\n".join(chapters) +
        "\n\n🎯 Channel: https://www.youtube.com/@Pulse_vector\n"
        "#BrainTeasers #Shorts #Puzzles #PulseVector #DesignLab #Private"
    )
    
    tags = [
        "BrainTeaser", "Shorts", "Puzzles", "PulseVector", "DesignLab",
        "MathPuzzle", "DetectiveRiddle", "BODMAS", "LogicPuzzle"
    ]
    
    print("📤 Uploading Master Showcase Video as PRIVATE...")
    video_id = upload_video_to_youtube(
        youtube=youtube,
        file_path=str(video_path),
        title=title,
        description=description,
        tags=tags,
        category_id="27",
        privacy_status="private"
    )
    print(f"✅ Video Upload Success! Video ID: {video_id}")
    
    playlist_title = "Pulse Vector - Brain Teaser Format Showcase (Private)"
    print(f"📂 Adding Video to Private Playlist: '{playlist_title}'...")
    add_video_to_playlist(youtube, video_id, playlist_title, playlist_privacy="private")
    
    video_url = f"https://youtu.be/{video_id}"
    print(f"\n🎉 ALL COMPLETE! Private YouTube Video: {video_url}")
    return video_id, video_url

if __name__ == "__main__":
    v_path = build_showcase_video()
    v_id, v_url = upload_showcase_to_private_youtube(v_path)
    print(f"\nFinal Result: Video ID {v_id} | Link: {v_url}")
