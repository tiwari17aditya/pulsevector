"""
Pulse Vector - Modular Testing Suite
Runs unit and integration tests across all pipeline components without burning API quota.
"""

import os
import sys
import unittest
import datetime
import pathlib
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure src/ is on sys.path
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.content_parser import (
    clean_markdown_decorations, strip_metadata_section, extract_news_points,
    extract_metadata_fields, extract_date_str, parse_news_content, parse_teaser_content,
    format_community_poll_text, classify_news_category, format_teaser_challenge_comment,
    format_solution_reveal_comment
)
from core.tts_utils import sanitize_text_for_speech, verify_speech_points_alignment, get_ffmpeg_executable
from core.image_utils import wrap_text, create_slide_image_file, ensure_fonts
from core.video_utils import (
    create_transition_frames, generate_countdown_sfx, merge_brainteaser_audio,
    compute_word_timings, render_karaoke_subtitle_overlay
)
from core.broadcast_utils import broadcast_daily_content
from core.pipeline_engine import PipelineEngine
from core.genai_utils import build_brainteaser_prompt, BRAIN_TEASER_TYPES

class TestContentParser(unittest.TestCase):
    def test_markdown_cleaning(self):
        raw = "### **Breaking News**: __Important Event__ with `code`"
        clean = clean_markdown_decorations(raw)
        self.assertEqual(clean, "Breaking News: Important Event with code")
        
    def test_daily_point_extraction(self):
        sample_text = """
Daily Current Affairs 26 July 2026

1. Global wildfires rage across Europe amidst extreme heat. [Source: BBC News]
2. Alps glaciers melt at record rates. [Source: Reuters]
3. Tech stocks rise following AI announcements. [Source: Bloomberg]

YouTube Metadata:
Title: Daily Current Affairs 26 July 2026
Reel Description: Catch the top headlines...
Hashtags: #CurrentAffairs #PulseVector
Source URLs:
- BBC News: https://bbc.com
- Reuters: https://reuters.com
"""
        points = extract_news_points(sample_text)
        self.assertEqual(len(points), 3)
        self.assertEqual(points[0][0], 1)
        self.assertEqual(points[0][2], "BBC News")
        self.assertEqual(points[1][2], "Reuters")
        
        meta = extract_metadata_fields(sample_text)
        self.assertEqual(meta["title"], "Daily Current Affairs 26 July 2026")
        self.assertIn("#CurrentAffairs", meta["hashtags"])
        self.assertIn("BBC News", meta["source_urls"])
        
    def test_monthly_50_points_parser(self):
        points_lines = "\n".join([f"{i}. Point number {i} news summary content. [Source: Publisher {i}]" for i in range(1, 51)])
        raw_monthly = f"""Monthly Current Affairs - July 2026\n\n{points_lines}\n\nTitle: Monthly Current Affairs - July 2026\nReel Description: Top 50 highlights.\nHashtags: #Monthly #News"""
        payload = parse_news_content(raw_monthly, "monthly", datetime.datetime(2026, 7, 31))
        self.assertEqual(len(payload.points), 50)
    def test_teaser_parser(self):
        teaser_text = """
Daily Brain Teaser - 25 July 2026 🧠
Q. What number comes next in the sequence:
Series: 2, 4, 8, 16, ?
a. 24
b. 32
c. 30
d. 36
Answer: b
#BrainTeaser #Puzzle
"""
        data = parse_teaser_content(teaser_text)
        self.assertEqual(data["series"], "2, 4, 8, 16, ?")
        self.assertIn("What number comes next", data["question_header"])
        self.assertEqual(len(data["options"]), 4)
        self.assertEqual(data["correct_answer"], "b")

    def test_teaser_bodmas_parser(self):
        text = """
Daily Brain Teaser - 01 September 2026 🧠
Q. Solve the equation:-
Equation: 6 ÷ 2(1 + 2) = ?
a. 1
b. 9
c. 6
d. 0
Correct Answer: b
#Math #BODMAS
"""
        data = parse_teaser_content(text)
        self.assertEqual(data["series"], "6 ÷ 2(1 + 2) = ?")
        self.assertIn("Solve the equation", data["question_header"])
        self.assertEqual(data["correct_answer"], "b")
        self.assertEqual(len(data["options"]), 4)

    def test_teaser_grid_parser(self):
        text = """
Daily Brain Teaser - 02 September 2026 🧠
Q. Find the missing number (?):-
Grid:
[ 4  9  2 ]
[ 3  5  7 ]
[ 8  1  ? ]
a. 6
b. 5
c. 9
d. 4
Correct Answer: a
#BrainTeaser #LogicGrid
"""
        data = parse_teaser_content(text)
        self.assertIn("[ 4  9  2 ]", data["series"])
        self.assertIn("[ 8  1  ? ]", data["series"])
        self.assertEqual(data["correct_answer"], "a")
        self.assertEqual(len(data["options"]), 4)

    def test_teaser_cipher_parser(self):
        text = """
Daily Brain Teaser - 03 September 2026 🧠
Q. Decode the missing value:-
Puzzle: If CAT = 24 and DOG = 26, then BIRD = ?
a. 34
b. 36
c. 38
d. 42
Correct Answer: c
#Cipher #Puzzle
"""
        data = parse_teaser_content(text)
        self.assertEqual(data["series"], "If CAT = 24 and DOG = 26, then BIRD = ?")
        self.assertEqual(data["correct_answer"], "c")

    def test_build_brainteaser_prompt(self):
        test_date = datetime.date(2026, 9, 7)  # A Monday -> bodmas
        prompt, key = build_brainteaser_prompt(test_date, "Base prompt instructions", randomize=False)
        self.assertEqual(key, "bodmas")
        self.assertIn("BODMAS", prompt)
        
        # Test forced type
        prompt_cipher, key_cipher = build_brainteaser_prompt(test_date, "Base prompt", teaser_type="cipher")
        self.assertEqual(key_cipher, "cipher")
        self.assertIn("Alphanumeric Ciphers", prompt_cipher)

        # Test randomized selection returns a valid key from BRAIN_TEASER_TYPES
        _, rand_key = build_brainteaser_prompt(test_date, "Base prompt", randomize=True)
        self.assertIn(rand_key, BRAIN_TEASER_TYPES)

    def test_format_community_poll_text(self):
        sample_data = {
            "date": "03 September 2026",
            "question_header": "Q. Solve the equation:-",
            "series": "6 ÷ 2(1 + 2) = ?",
            "options": ["a. 1", "b. 9", "c. 6", "d. 0"],
            "hashtags": ["#BODMAS", "#MathPuzzle"]
        }
        poll_str = format_community_poll_text(sample_data)
        self.assertIn("Daily Brain Teaser", poll_str)
        self.assertIn("6 ÷ 2(1 + 2) = ?", poll_str)
        self.assertIn("• a. 1", poll_str)
        self.assertIn("• b. 9", poll_str)
        self.assertIn("#BODMAS", poll_str)

    def test_classify_news_category(self):
        self.assertEqual(classify_news_category("India procures advanced missile defence system"), "DEFENCE")
        self.assertEqual(classify_news_category("RBI projects 7.2% GDP growth as stock markets rally"), "ECONOMY")
        self.assertEqual(classify_news_category("ISRO launches quantum satellite for deep space mission"), "TECH & AI")
        self.assertEqual(classify_news_category("Global solar energy installations cut carbon emissions"), "ENVIRONMENT")
        self.assertEqual(classify_news_category("Bilateral diplomatic summit concludes with historic peace treaty"), "GEOPOLITICS")
        self.assertEqual(classify_news_category("Parliament passes landmark digital governance bill"), "NATIONAL")

    def test_teaser_challenge_and_solution_reveal(self):
        sample = {
            "date": "04 September 2026",
            "correct_answer": "c",
            "options": ["a. 10", "b. 20", "c. 30", "d. 40"]
        }
        challenge = format_teaser_challenge_comment(sample)
        self.assertIn("04 September 2026", challenge)
        self.assertIn("24 hours", challenge)
        
        reveal = format_solution_reveal_comment(sample)
        self.assertIn("c. 30", reveal)
        self.assertIn("OFFICIAL SOLUTION REVEAL", reveal)

class TestTTSUtils(unittest.TestCase):
    def test_speech_sanitization(self):
        text = "1. Wildfires rage in Spain. [Source: Reuters] Major disaster declared."
        speech_text = sanitize_text_for_speech(text)
        self.assertNotIn("[Source: Reuters]", speech_text)
        self.assertIn("Point 1.", speech_text)
        
    def test_speech_alignment_verification(self):
        valid_points = [(1, "First point text"), (2, "Second point text")]
        self.assertTrue(verify_speech_points_alignment(valid_points, expected_point_count=2))
        
        with self.assertRaises(ValueError):
            verify_speech_points_alignment([])
            
    def test_ffmpeg_resolved(self):
        exe = get_ffmpeg_executable()
        self.assertTrue(bool(exe))

class TestImageAndVideoUtils(unittest.TestCase):
    def test_slide_rendering(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            out_img = tmp_path / "test_slide.png"
            points = [(1, "Test headline one [Source: News]"), (2, "Test headline two")]
            font_reg, font_bold = ensure_fonts(tmp_path)
            
            ok = create_slide_image_file(
                "21 AUGUST 2026", points, 1, 1,
                font_reg, font_bold, out_img, "TEST CURRENT AFFAIRS"
            )
            self.assertTrue(ok)
            self.assertTrue(out_img.exists())
            
            # Verify image properties with context manager
            with Image.open(out_img) as img:
                self.assertEqual(img.size, (1080, 1920))
        

            
    def test_transition_frames(self):
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
        frames = create_transition_frames(img1, img2, num_transition_frames=5, transition_type="fade")
        self.assertEqual(len(frames), 5)
        self.assertEqual(frames[0].shape, (100, 100, 3))

    def test_generate_countdown_sfx(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = pathlib.Path(tmp_dir) / "test_sfx.wav"
            out = generate_countdown_sfx(wav_path, total_duration=2.0, tick_interval=1.0, stop_at=1.0)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 1000)

    def test_compute_word_timings_and_karaoke(self):
        sample_text = "Daily Brain Teaser solve this puzzle"
        timings = compute_word_timings(sample_text, total_duration=3.0, start_offset=0.2)
        self.assertEqual(len(timings), 6)
        self.assertEqual(timings[0]["word"], "Daily")
        self.assertAlmostEqual(timings[0]["start"], 0.2)
        self.assertAlmostEqual(timings[-1]["end"], 3.2)
        
        # Test karaoke overlay rendering onto PIL draw context
        dummy_img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
        draw = ImageDraw.Draw(dummy_img)
        font_reg, _ = ensure_fonts(pathlib.Path("pulse_archive"))
        font_sub = ImageFont.truetype(str(font_reg), 32)
        
        # At t=1.0s, subtitle should render successfully
        rendered = render_karaoke_subtitle_overlay(draw, 1.0, timings, font_sub)
        self.assertTrue(rendered)
        
        # At t=10.0s (past audio), subtitle should return False
        rendered_late = render_karaoke_subtitle_overlay(draw, 10.0, timings, font_sub)
        self.assertFalse(rendered_late)

    def test_brainteaser_all_layouts_rendering(self):
        import brainteaser_pipeline
        font_reg, font_bold = ensure_fonts(pathlib.Path("pulse_archive"))
        fonts = (
            ImageFont.truetype(str(font_bold), 40),
            ImageFont.truetype(str(font_reg), 24),
            ImageFont.truetype(str(font_bold), 38),
            ImageFont.truetype(str(font_reg), 26),
            ImageFont.truetype(str(font_reg), 14),
            ImageFont.truetype(str(font_reg), 15)
        )
        sample_data = {
            "date": "05 September 2026",
            "question_header": "Q. Find the missing number in the sequence:-",
            "series": "2, 6, 12, 20, 30, ?",
            "options": ["a. 40", "b. 42", "c. 44", "d. 46"],
            "correct_answer": "b",
            "hashtags": ["#Math", "#Puzzle"]
        }
        for idx, layout in enumerate(brainteaser_pipeline.LAYOUTS, 1):
            img = Image.new("RGB", (656, 656), color=(20, 20, 30))
            draw = ImageDraw.Draw(img)
            layout(draw, sample_data, fonts)

class TestPipelineEngine(unittest.TestCase):
    def test_dry_run_execution(self):
        engine = PipelineEngine()
        res_daily = engine.run_pipeline("daily", dry_run=True)
        self.assertEqual(len(res_daily.errors), 0)
        
        res_weekly = engine.run_pipeline("weekly", dry_run=True)
        self.assertEqual(len(res_weekly.errors), 0)
        
        res_monthly = engine.run_pipeline("monthly", dry_run=True)
        self.assertEqual(len(res_monthly.errors), 0)

    def test_broadcast_daily_content_graceful(self):
        result = broadcast_daily_content(
            content_type="daily",
            date_obj=datetime.date(2026, 9, 4),
            title="Test Broadcast Title",
            summary_text="• Point 1 summary\n• Point 2 summary"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("telegram", result)
        self.assertIn("discord", result)

def main():
    print("==========================================================")
    print("  🧪 PULSE VECTOR AUTOMATED TEST SUITE                   ")
    print("==========================================================")
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n✅ All automated tests PASSED successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
