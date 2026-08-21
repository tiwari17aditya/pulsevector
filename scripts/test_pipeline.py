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
from PIL import Image

# Ensure src/ is on sys.path
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.content_parser import (
    clean_markdown_decorations, strip_metadata_section, extract_news_points,
    extract_metadata_fields, extract_date_str, parse_news_content, parse_teaser_content
)
from core.tts_utils import sanitize_text_for_speech, verify_speech_points_alignment, get_ffmpeg_executable
from core.image_utils import wrap_text, create_slide_image_file, ensure_fonts
from core.video_utils import create_transition_frames
from core.pipeline_engine import PipelineEngine

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

class TestPipelineEngine(unittest.TestCase):
    def test_dry_run_execution(self):
        engine = PipelineEngine()
        res_daily = engine.run_pipeline("daily", dry_run=True)
        self.assertEqual(len(res_daily.errors), 0)
        
        res_weekly = engine.run_pipeline("weekly", dry_run=True)
        self.assertEqual(len(res_weekly.errors), 0)
        
        res_monthly = engine.run_pipeline("monthly", dry_run=True)
        self.assertEqual(len(res_monthly.errors), 0)

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
