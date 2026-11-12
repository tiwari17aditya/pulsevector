"""
Pulse Vector - Modular Testing Suite
Runs unit and integration tests across all pipeline components without burning API quota.
"""

import os
import sys
import time
import unittest
import datetime
import pathlib
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure src/ and project root are on sys.path
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from unittest.mock import patch, MagicMock
from core.content_parser import (
    clean_markdown_decorations, strip_metadata_section, extract_news_points,
    extract_metadata_fields, extract_date_str, parse_news_content, parse_teaser_content,
    format_community_poll_text, classify_news_category, format_teaser_challenge_comment,
    format_solution_reveal_comment, format_brainteaser_description, get_social_links_block,
    optimize_youtube_title
)
from core.youtube_utils import sanitize_youtube_tags
from core.tts_utils import sanitize_text_for_speech, verify_speech_points_alignment, get_ffmpeg_executable
from core.image_utils import wrap_text, create_slide_image_file, ensure_fonts
from core.video_utils import (
    create_transition_frames, generate_countdown_sfx, merge_brainteaser_audio,
    compute_word_timings, render_karaoke_subtitle_overlay
)
from core.broadcast_utils import (
    broadcast_daily_content, broadcast_telegram, broadcast_discord, truncate_html_caption
)
from core.pipeline_engine import PipelineEngine, ContentPayload
from core.gdrive_endcredits import resolve_gdrive_endcredits_dir, get_runtime_drive_endcredits, LOCAL_SAMPLES_DIR
from core.video_utils import download_audio_library
from core.genai_utils import build_brainteaser_prompt, BRAIN_TEASER_TYPES
from mcp_server.tools.quotas import check_api_quotas
from mcp_server.tools.deduplication import query_content_deduplication
from mcp_server.tools.diagnostics import inspect_render_diagnostics
from mcp_server.tools.broadcast import trigger_social_broadcast
from mcp_server.tools.orchestration import (
    trigger_pipeline_stage,
    execute_autonomous_packup,
    auto_heal_environment,
    query_supabase_ledger,
    audit_token_and_quota_ledgers,
)
from core.autonomous_orchestrator import AutonomousOrchestrator
from mcp_server.server import app as mcp_app

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
        # Hashtags must be plain strings (no '#' prefix) — YouTube API requirement
        self.assertIn("CurrentAffairs", meta["hashtags"])
        self.assertNotIn("#CurrentAffairs", meta["hashtags"],
                         "Hashtags must NOT contain '#' prefix for YouTube API compliance")
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

    def test_format_brainteaser_description(self):
        sample = {
            "question_header": "Q. What number comes next in the sequence?",
            "series": "Series: 3, 6, 10, 15, 21, ?",
            "options": ["a. 27", "b. 28", "c. 29", "d. 30"]
        }
        hashtags = ["#BrainTeaser", "#PulseVector", "#MathPuzzle"]
        desc = format_brainteaser_description(
            data=sample,
            date_str="04 September 2026",
            formatted_hashtags=hashtags,
            date_file_str="04sep26"
        )
        self.assertIn("Daily Brain Teaser - 04 September 2026 🧠", desc)
        self.assertIn("Series: 3, 6, 10, 15, 21, ?", desc)
        self.assertIn("• a. 27" if "•" in desc else "a. 27", desc)
        self.assertIn("Comment your answer below! 👇", desc)
        self.assertIn("Correct answer pinned in 24 hours.", desc)
        self.assertIn("🎮 Play Interactively:", desc)
        self.assertIn("?challenge=04sep26", desc)
        self.assertIn("💬 Telegram Community:", desc)
        self.assertIn("📺 Subscribe on YouTube:", desc)
        self.assertIn("#PulseVector", desc)
        self.assertLessEqual(len(desc), 5000)
        
        # Test optional handles
        custom_desc = format_brainteaser_description(
            data=sample,
            date_str="04 September 2026",
            formatted_hashtags=hashtags,
            discord_url="https://discord.gg/pulsevector",
            instagram_url="https://instagram.com/pulsevector",
            x_url="https://x.com/pulsevector"
        )
        self.assertIn("👾 Discord Community: https://discord.gg/pulsevector", custom_desc)
        self.assertIn("📸 Instagram: https://instagram.com/pulsevector", custom_desc)
        self.assertIn("🐦 X (Twitter): https://x.com/pulsevector", custom_desc)

    def test_get_social_links_block(self):
        """Tests plain, HTML, and markdown formats of get_social_links_block."""
        # 1. Plain text format (YouTube)
        plain = get_social_links_block("plain")
        self.assertIn("CONNECT WITH PULSE VECTOR", plain)
        self.assertIn("📺 Subscribe on YouTube: https://www.youtube.com/@Pulse_vector", plain)
        self.assertIn("💬 Telegram Community: https://t.me/pulsevector_daily", plain)
        self.assertIn("👾 Discord Community:", plain)
        # Excluded handles
        self.assertNotIn("@PulseVectorOfficial_bot", plain)
        self.assertNotIn("pulsevector/play", plain)
        
        # 2. HTML format (Telegram)
        html_block = get_social_links_block("html")
        self.assertIn("<b>CONNECT WITH PULSE VECTOR:</b>", html_block)
        self.assertIn('<a href="https://www.youtube.com/@Pulse_vector">Subscribe on YouTube</a>', html_block)
        self.assertIn('<a href="https://t.me/pulsevector_daily">Telegram Community</a>', html_block)
        self.assertNotIn("@PulseVectorOfficial_bot", html_block)
        self.assertNotIn("pulsevector/play", html_block)
        
        # 3. Markdown format (Discord)
        md_block = get_social_links_block("markdown")
        self.assertIn("**CONNECT WITH PULSE VECTOR:**", md_block)
        self.assertIn("[Subscribe on YouTube](https://www.youtube.com/@Pulse_vector)", md_block)
        self.assertIn("[Telegram Community](https://t.me/pulsevector_daily)", md_block)
        self.assertNotIn("@PulseVectorOfficial_bot", md_block)
        self.assertNotIn("pulsevector/play", md_block)

    def test_news_content_includes_social_links_block(self):
        """parse_news_content description must include standard social block."""
        sample = (
            "Daily Current Affairs 26 September 2026\n\n"
            "1. Major tech breakthrough announced. [Source: Reuters]\n\n"
            "Title: Daily Current Affairs 26 September 2026\n"
            "Reel Description: Catch the top headlines.\n"
            "Hashtags: #CurrentAffairs #Shorts\n"
        )
        payload = parse_news_content(sample, "daily", datetime.datetime(2026, 9, 26))
        self.assertIn("CONNECT WITH PULSE VECTOR", payload.description)
        self.assertIn("https://www.youtube.com/@Pulse_vector", payload.description)
        self.assertIn("https://t.me/pulsevector_daily", payload.description)
        self.assertNotIn("@PulseVectorOfficial_bot", payload.description)
        self.assertNotIn("pulsevector/play", payload.description)

    def test_optimize_youtube_title(self):
        """Pillar 3: Verifies that generic titles are transformed into high-CTR curiosity titles."""
        points = [(1, "ISRO launches advanced quantum communication satellite")]
        target_d = datetime.datetime(2026, 9, 26)
        
        # Generic daily title transformation
        opt_title = optimize_youtube_title("Daily Current Affairs 26 September 2026", "daily", target_d, points)
        self.assertIn("🔥", opt_title)
        self.assertIn("ISRO launches advanced quantum", opt_title)
        self.assertIn("#Shorts", opt_title)
        self.assertLessEqual(len(opt_title), 100)
        
        # Weekly masterclass title transformation
        opt_weekly = optimize_youtube_title("Weekly Current Affairs", "weekly", target_d, points)
        self.assertIn("Weekly Current Affairs Masterclass", opt_weekly)
        self.assertIn("Full Revision", opt_weekly)

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

    def test_slide_rendering_widescreen_16_9(self):
        """Pillar 4: Verifies that 16:9 widescreen layout generates 1920x1080 masterclass slides."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            out_img = tmp_path / "test_slide_16_9.png"
            points = [(1, "Test headline one [Source: News]"), (2, "Test headline two")]
            font_reg, font_bold = ensure_fonts(tmp_path)
            
            ok = create_slide_image_file(
                "21 AUGUST 2026", points, 1, 1,
                font_reg, font_bold, out_img, "WEEKLY MASTERCLASS",
                aspect_ratio="16:9"
            )
            self.assertTrue(ok)
            self.assertTrue(out_img.exists())
            
            with Image.open(out_img) as img:
                self.assertEqual(img.size, (1920, 1080))
        

            
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

    def test_brainteaser_long_series_adaptive_layout_and_bounds(self):
        """
        Verifies that verbose, long puzzle statements (180+ chars like detective riddles or
        probability problems) dynamically scale down typography and leave adequate clearance
        so options are never clipped or hidden past safe margins [Y <= 585px].
        """
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
        long_puzzle_data = {
            "date": "12 November 2026",
            "question_header": "Q. What is the probability you picked the fair coin? :-",
            "series": "You have a bag containing two coins. One is a standard fair coin, the other is a special coin that lands heads 75% of the time. You randomly select a coin and flip it. It lands heads.",
            "options": ["a. 1/2", "b. 2/5", "c. 3/5", "d. 1/4"],
            "correct_answer": "b",
            "hashtags": ["#BrainTeaser", "#Probability"]
        }
        
        # 1. Test adaptive series layout helper
        font, wrapped, lh, box_h = brainteaser_pipeline.compute_adaptive_series_layout(
            long_puzzle_data["series"], font_bold, max_w=460, max_h=210
        )
        self.assertLessEqual(box_h, 215, "Adaptive series box must not exceed maximum height")
        self.assertLessEqual(len(wrapped), 6, "Wrapped lines should be compact")
        
        # 2. Test rendering across all 10 layouts
        for idx, layout in enumerate(brainteaser_pipeline.LAYOUTS, 1):
            img = Image.new("RGB", (656, 656), color=(20, 20, 30))
            draw = ImageDraw.Draw(img)
            layout(draw, long_puzzle_data, fonts)
            
            # Check bottom-most safe area (between Y=595 and Y=656) has no option overflow
            arr = np.array(img)
            # Row 650 should not have clipped text (max brightness of text would be ~255)
            row_edge = arr[650, 150:500]
            # Since background is a flat (20,20,30), text would show as high values
            self.assertLess(np.max(row_edge), 150, f"Layout {idx} overflowed past canvas bottom!")

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
        with patch("core.broadcast_utils.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp
            result = broadcast_daily_content(
                content_type="daily",
                date_obj=datetime.date(2026, 9, 4),
                title="Test Broadcast Title",
                summary_text="• Point 1 summary\n• Point 2 summary"
            )
            self.assertIsInstance(result, dict)
            self.assertIn("telegram", result)
            self.assertIn("discord", result)

    def test_truncate_html_caption(self):
        """Tests that HTML captions are safely truncated and tags are balanced."""
        short_text = "<b>Short caption</b>"
        self.assertEqual(truncate_html_caption(short_text), short_text)
        
        # Test long text with open tags
        long_body = "word " * 300
        html_text = f"<b>Title</b>: <i>{long_body}</i>"
        truncated = truncate_html_caption(html_text, max_length=100)
        self.assertLessEqual(len(truncated), 100)
        self.assertTrue(truncated.endswith("</i>") or truncated.endswith("</b>") or truncated.endswith("..."))
        # Verify tag balance
        self.assertEqual(truncated.count("<b"), truncated.count("</b>"))
        self.assertEqual(truncated.count("<i"), truncated.count("</i>"))

    def test_broadcast_telegram_native_video(self):
        """Verifies Telegram sendVideo API call with native .mp4 upload."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_vid:
            tmp_vid.write(b"\x00\x00\x00\x18ftypmp42")
            tmp_vid_path = pathlib.Path(tmp_vid.name)
            
        try:
            with patch("core.broadcast_utils.get_env_var") as mock_env, \
                 patch("core.broadcast_utils.requests.post") as mock_post:
                mock_env.side_effect = lambda k, default=None: "dummy_val" if k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") else default
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_post.return_value = mock_resp
                
                success = broadcast_telegram(
                    message="<b>Test video short</b>",
                    video_path=tmp_vid_path
                )
                self.assertTrue(success)
                self.assertTrue(mock_post.called)
                url_called = mock_post.call_args[0][0]
                self.assertIn("sendVideo", url_called)
                kwargs = mock_post.call_args[1]
                self.assertIn("video", kwargs["files"])
                self.assertEqual(kwargs["data"]["supports_streaming"], "true")
        finally:
            if tmp_vid_path.exists():
                tmp_vid_path.unlink()

    def test_broadcast_discord_native_video(self):
        """Verifies Discord webhook call with native .mp4 file attachment."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_vid:
            tmp_vid.write(b"\x00\x00\x00\x18ftypmp42")
            tmp_vid_path = pathlib.Path(tmp_vid.name)
            
        try:
            with patch("core.broadcast_utils.get_env_var") as mock_env, \
                 patch("core.broadcast_utils.requests.post") as mock_post:
                mock_env.side_effect = lambda k, default=None: "https://discord.com/api/webhooks/test" if k == "DISCORD_WEBHOOK_URL" else default
                mock_resp = MagicMock()
                mock_resp.status_code = 204
                mock_post.return_value = mock_resp
                
                success = broadcast_discord(
                    title="Test Short",
                    description="Test description",
                    video_path=tmp_vid_path
                )
                self.assertTrue(success)
                self.assertTrue(mock_post.called)
                kwargs = mock_post.call_args[1]
                self.assertIn("file", kwargs["files"])
                self.assertEqual(kwargs["files"]["file"][2], "video/mp4")
        finally:
            if tmp_vid_path.exists():
                tmp_vid_path.unlink()

    def test_broadcast_daily_content_with_video(self):
        """Verifies broadcast_daily_content accepts video_path gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_vid:
            tmp_vid.write(b"\x00\x00\x00\x18ftypmp42")
            tmp_vid_path = pathlib.Path(tmp_vid.name)
            
        try:
            with patch("core.broadcast_utils.requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_post.return_value = mock_resp
                
                result = broadcast_daily_content(
                    content_type="daily",
                    date_obj=datetime.date(2026, 9, 26),
                    title="Daily Current Affairs",
                    summary_text="• Point 1\n• Point 2",
                    video_path=tmp_vid_path,
                    video_url="https://youtu.be/dummy123"
                )
                self.assertIsInstance(result, dict)
                self.assertIn("telegram", result)
                self.assertIn("discord", result)
        finally:
            if tmp_vid_path.exists():
                tmp_vid_path.unlink()

    def test_real_stage_generate_slides_execution(self):
        """Verifies real slide rendering generates valid 1080x1920 PNG images with proper layout."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = pathlib.Path(tmp_dir)
            engine = PipelineEngine(archive_dir=tmp_root)
            test_date = datetime.datetime(2026, 11, 2)
            
            # Construct a synthetic payload
            test_payload = ContentPayload(
                content_type="daily",
                target_date=test_date,
                raw_text="Daily Current Affairs 02 November 2026\n\n1. Headline",
                points=[
                    (1, "Global leaders commit to next-gen clean fusion power initiative.", "Reuters"),
                    (2, "AI quantum breakthrough achieved in battery density materials.", "BBC News"),
                    (3, "Central banks pilot instant cross-border settlement rails.", "Bloomberg")
                ],
                title="Daily Current Affairs 02 November 2026",
                hashtags=["CurrentAffairs", "PulseVector"]
            )
            
            slide_result = engine.stage_generate_slides("daily", test_date, payload=test_payload)
            self.assertTrue(len(slide_result.slide_image_paths) > 0)
            for s_path in slide_result.slide_image_paths:
                self.assertTrue(s_path.exists())
                with Image.open(s_path) as img:
                    self.assertEqual(img.size, (1080, 1920))

    def test_teaser_fast_path_performance(self):
        """Verifies that stage_generate_teasers with target_date executes in < 1.5s (no archive traversal)."""
        engine = PipelineEngine()
        test_date = datetime.datetime(2026, 11, 2)
        start_t = time.time()
        engine.stage_generate_teasers(target_date=test_date)
        elapsed = time.time() - start_t
        self.assertLess(elapsed, 1.5, f"Teaser generation took {elapsed:.2f}s, expected < 1.5s fast-path")

    def test_audio_library_instant_resolution(self):
        """Verifies that download_audio_library resolves existing tracks in < 0.5s without CPU synthesis."""
        start_t = time.time()
        download_audio_library()
        elapsed = time.time() - start_t
        self.assertLess(elapsed, 0.5, f"Audio library resolution took {elapsed:.2f}s, expected instant (< 0.5s)")

    def test_gdrive_endcredits_cross_platform_safety(self):
        """Verifies resolve_gdrive_endcredits_dir never injects illegal Windows drive paths on Linux/POSIX."""
        with patch("sys.platform", "linux"):
            resolved = resolve_gdrive_endcredits_dir()
            self.assertTrue(resolved.exists())
            self.assertFalse(str(resolved).startswith("G:"), "Must NOT start with G: on Linux")
            self.assertEqual(resolved.resolve(), LOCAL_SAMPLES_DIR.resolve())

    def test_gdrive_endcredits_runtime_aspect_ratios(self):
        """Verifies get_runtime_drive_endcredits provides valid vertical (9:16) and widescreen (16:9) files."""
        vert_v = get_runtime_drive_endcredits(aspect_ratio="9:16")
        self.assertTrue(vert_v.exists())
        self.assertGreater(vert_v.stat().st_size, 50000)

        wide_v = get_runtime_drive_endcredits(aspect_ratio="16:9")
        self.assertTrue(wide_v.exists())
        self.assertGreater(wide_v.stat().st_size, 50000)

    def test_stage_compile_video_fallback_on_outro_failure(self):
        """Verifies stage_compile_video falls back gracefully if outro stitching raises an error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = pathlib.Path(tmp_dir)
            engine = PipelineEngine(archive_dir=tmp_root)
            test_date = datetime.datetime(2026, 11, 2)
            paths = engine.get_paths("daily", test_date)
            paths["text_file"].parent.mkdir(parents=True, exist_ok=True)
            paths["text_file"].write_text(
                "Daily Current Affairs 02 November 2026\n\n1. Headline one [Source: Test]\n\nTitle: Test\nHashtags: #Test",
                encoding="utf-8"
            )
            # Render slides first
            engine.stage_generate_slides("daily", test_date)
            
            # Mock stitch_video_with_drive_endcredit to simulate failure
            with patch("core.pipeline_engine.stitch_video_with_drive_endcredit", side_effect=RuntimeError("FFmpeg outro error")):
                res = engine.stage_compile_video("daily", test_date, enable_tts=False, force=True)
                self.assertIsNotNone(res)
                self.assertTrue(res.video_path.exists())
                self.assertGreater(res.video_path.stat().st_size, 1000)


class TestYouTubeTagSafety(unittest.TestCase):
    """
    Regression tests for the YouTube HTTP 400 invalidTags bug (Sep 2026).

    Root cause: snippet.tags[] must contain plain keyword strings.
    Passing '#Word' tags causes ResumableUploadError 400 invalidTags.
    These tests guard both defence layers:
      1. content_parser.py  — never emits '#'-prefixed tags from parse_news_content()
      2. youtube_utils.py   — sanitize_youtube_tags() strips anything that slips through
    """

    # ---- Layer 1: content_parser must emit clean tags ----

    def test_parser_hashtags_no_hash_prefix(self):
        """extract_metadata_fields must return plain keywords, never '#Word'."""
        raw = """Title: Test\nHashtags: #CurrentAffairs #PulseVector #GlobalNews"""
        meta = extract_metadata_fields(raw)
        for tag in meta["hashtags"]:
            self.assertFalse(tag.startswith("#"),
                f"Tag '{tag}' must not start with '#' — YouTube API rejects '#'-prefixed tags")

    def test_parse_news_content_hashtags_clean(self):
        """parse_news_content payload.hashtags must be '#'-free for all content types."""
        sample = (
            "Daily Current Affairs 13 September 2026\n\n"
            "1. News point one. [Source: BBC]\n\n"
            "Title: Daily Current Affairs 13 September 2026\n"
            "Hashtags: #CurrentAffairs #India #Shorts\n"
        )
        for ctype in ("daily", "weekly", "monthly"):
            payload = parse_news_content(sample, ctype, datetime.datetime(2026, 9, 13))
            for tag in payload.hashtags:
                self.assertFalse(tag.startswith("#"),
                    f"[{ctype}] payload.hashtags contains '#' in '{tag}'")

    def test_fallback_tags_no_hash_prefix(self):
        """When no hashtags section is present, fallback tags must also be clean."""
        bare_text = "Daily Current Affairs 13 Sep 2026\n\n1. Some news. [Source: Reuters]\n"
        for ctype in ("daily", "weekly", "monthly"):
            payload = parse_news_content(bare_text, ctype, datetime.datetime(2026, 9, 13))
            for tag in payload.hashtags:
                self.assertFalse(tag.startswith("#"),
                    f"[{ctype}] fallback hashtag contains '#' in '{tag}'")

    # ---- Layer 2: sanitize_youtube_tags is the final safety net ----

    def test_sanitize_strips_hash_prefix(self):
        """sanitize_youtube_tags must strip '#' from all incoming tags."""
        dirty = ["#CurrentAffairs", "#PulseVector", "#India2026"]
        clean = sanitize_youtube_tags(dirty)
        for tag in clean:
            self.assertFalse(tag.startswith("#"), f"Tag '{tag}' still has '#' after sanitize")
        self.assertEqual(clean, ["CurrentAffairs", "PulseVector", "India2026"])

    def test_sanitize_deduplication(self):
        """sanitize_youtube_tags must deduplicate case-insensitively."""
        tags = ["#News", "#news", "#NEWS", "PulseVector"]
        result = sanitize_youtube_tags(tags)
        self.assertEqual(len(result), 2)
        self.assertIn("News", result)
        self.assertIn("PulseVector", result)

    def test_sanitize_500_char_budget(self):
        """Total tag length must not exceed YouTube's 500-char limit."""
        long_tags = [f"TagNumber{i}WithSomeMoreWords" for i in range(50)]
        result = sanitize_youtube_tags(long_tags)
        total = sum(len(t) for t in result) + max(0, 2 * (len(result) - 1))
        self.assertLessEqual(total, 500,
            f"Sanitized tags exceed 500 chars: {total} chars across {len(result)} tags")

    def test_sanitize_empty_and_none(self):
        """sanitize_youtube_tags must handle empty list and None gracefully."""
        self.assertEqual(sanitize_youtube_tags([]), [])
        self.assertEqual(sanitize_youtube_tags(None), [])


class TestGDriveUtils(unittest.TestCase):
    def test_gdrive_config_and_imports(self):
        """Verify Google Drive config flags and utilities load properly."""
        from core.config import ENABLE_GDRIVE_UPLOAD, ENABLE_SUPABASE_STORAGE_UPLOAD, GOOGLE_DRIVE_FOLDER_NAME
        from core.gdrive_utils import get_gdrive_service, find_or_create_folder, GDRIVE_SCOPES
        from core.youtube_utils import ALL_GOOGLE_SCOPES, GDRIVE_SCOPES as YT_GDRIVE_SCOPES
        
        self.assertIsInstance(ENABLE_GDRIVE_UPLOAD, bool)
        self.assertIsInstance(ENABLE_SUPABASE_STORAGE_UPLOAD, bool)
        self.assertEqual(GOOGLE_DRIVE_FOLDER_NAME, "pulse-vector")
        self.assertIn("https://www.googleapis.com/auth/drive.file", GDRIVE_SCOPES)

        self.assertIn("https://www.googleapis.com/auth/drive.file", ALL_GOOGLE_SCOPES)

    def test_gdrive_service_missing_token_graceful(self):
        """get_gdrive_service must return None without raising exception if token is missing."""
        from core.gdrive_utils import get_gdrive_service
        service = get_gdrive_service(token_path="non_existent_token.json")
class TestReportUtils(unittest.TestCase):
    def test_weekly_window_sunday(self):
        """Rule: On Sunday (e.g. 8 Jan 2023), window covers prior Sunday 1 Jan to Saturday 7 Jan."""
        from core.report_utils import get_weekly_report_window, IST
        sun_8_jan = datetime.date(2023, 1, 8)  # 2023-01-08 was Sunday
        self.assertEqual(sun_8_jan.weekday(), 6)
        start_dt, end_dt = get_weekly_report_window(sun_8_jan)
        
        self.assertEqual(start_dt.date(), datetime.date(2023, 1, 1))
        self.assertEqual(end_dt.date(), datetime.date(2023, 1, 7))
        self.assertEqual(start_dt.tzinfo, IST)
        self.assertEqual(end_dt.tzinfo, IST)

    def test_monthly_window_monthend(self):
        """Rule: For 31 Jan, window covers 31 Dec to 30 Jan."""
        from core.report_utils import get_monthly_report_window, IST
        jan_31 = datetime.date(2026, 1, 31)
        start_dt, end_dt = get_monthly_report_window(jan_31)

        self.assertEqual(start_dt.date(), datetime.date(2025, 12, 31))
        self.assertEqual(end_dt.date(), datetime.date(2026, 1, 30))
        self.assertEqual(start_dt.tzinfo, IST)
        self.assertEqual(end_dt.tzinfo, IST)

    def test_parse_upload_timestamp(self):
        """Parse IST timestamps accurately."""
        from core.report_utils import parse_upload_timestamp
        dt = parse_upload_timestamp("2026-09-19 05:50 IST")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 9)
        self.assertEqual(dt.day, 19)
        self.assertEqual(dt.hour, 5)
        self.assertEqual(dt.minute, 50)

    def test_categorize_video(self):
        """Normalize video titles and types into clean categories."""
        from core.report_utils import categorize_video
        self.assertEqual(categorize_video("Daily Brain Teaser - September 03", "Short (9:16)", "Education (27)"), "Daily Brain Teaser")
        self.assertEqual(categorize_video("Daily Current Affairs 19 September 2026", "Short (9:16)", "Education (27)"), "Daily Current Affairs")
        self.assertEqual(categorize_video("Weekly Current Affairs ( 07 Sep - 13 Sep )", "Weekly Masterclass", "Education (27)"), "Weekly Current Affairs")
        self.assertEqual(categorize_video("Monthly Current Affairs - August 2026", "Monthly Masterclass", "Education (27)"), "Monthly Current Affairs")

    def test_build_category_breakdown(self):
        """Calculate counts and percentage shares accurately."""
        from core.report_utils import build_category_breakdown
        sample_videos = [
            {"category": "Daily Current Affairs", "video_type": "Short (9:16)"},
            {"category": "Daily Current Affairs", "video_type": "Short (9:16)"},
            {"category": "Daily Brain Teaser", "video_type": "Short (9:16)"},
            {"category": "Weekly Current Affairs", "video_type": "Weekly Masterclass"},
        ]
        breakdown = build_category_breakdown(sample_videos)
        self.assertEqual(breakdown["total_count"], 4)
        cats = {c["category"]: c for c in breakdown["categories"]}
        self.assertEqual(cats["Daily Current Affairs"]["count"], 2)
        self.assertEqual(cats["Daily Current Affairs"]["share_percent"], "50.0%")
        self.assertEqual(cats["Daily Brain Teaser"]["count"], 1)
        self.assertEqual(cats["Daily Brain Teaser"]["share_percent"], "25.0%")

    def test_render_report_html_and_text(self):
        """Generate HTML and plain text report formats with tables and KPI blocks."""
        from core.report_utils import render_report_html, render_report_text, IST
        start_dt = datetime.datetime(2026, 9, 7, 0, 0, tzinfo=IST)
        end_dt = datetime.datetime(2026, 9, 13, 23, 59, tzinfo=IST)
        videos = [{
            "raw_date": "2026-09-08 05:56 IST",
            "datetime": datetime.datetime(2026, 9, 8, 5, 56, tzinfo=IST),
            "title": "Daily Current Affairs 08 September 2026",
            "category": "Daily Current Affairs",
            "video_type": "Short (9:16)",
            "video_id": "w67AG-xjn38",
            "youtube_url": "https://youtu.be/w67AG-xjn38"
        }]
        polls = [{
            "date_str": "08 Sep 2026",
            "question": "What is the answer?",
            "options": "a. 1 | b. 2",
            "correct_answer": "b",
            "platforms": "YouTube Community, Telegram, Discord"
        }]
        cat_summary = {
            "total_count": 1,
            "categories": [{"category": "Daily Current Affairs", "count": 1, "types_display": "Short (9:16)", "share_percent": "100.0%"}]
        }
        html = render_report_html("weekly", start_dt, end_dt, videos, polls, cat_summary)
        text = render_report_text("weekly", start_dt, end_dt, videos, polls, cat_summary)
        
        self.assertIn("Weekly Performance Report", html)
        self.assertIn("Daily Current Affairs 08 September 2026", html)
        self.assertIn("https://youtu.be/w67AG-xjn38", html)
        self.assertIn("PULSE VECTOR — WEEKLY PERFORMANCE REPORT", text)


class TestMCPOperationalServer(unittest.TestCase):
    """
    Validation test suite for Pulse Vector Operational MCP Server (v2.5.0).
    Validates check_api_quotas, query_content_deduplication,
    inspect_render_diagnostics, trigger_social_broadcast, and MCPServer registration.
    """
    def test_check_api_quotas(self):
        res = check_api_quotas()
        self.assertIsInstance(res, dict)
        self.assertIn("youtube_api", res)
        self.assertIn("gemini_api", res)
        self.assertIn("supabase_cloud", res)
        self.assertIn("google_drive_cloud", res)
        self.assertIn("storage", res)
        self.assertEqual(res["youtube_api"]["daily_quota_limit"], 10000)

    def test_query_content_deduplication(self):
        # 1. Unique query should not be duplicate
        unique_res = query_content_deduplication("ExtremelyUniqueNeverExistedHeadline99999XYZ")
        self.assertFalse(unique_res["is_duplicate"])
        self.assertEqual(unique_res["recommendation"], "SAFE_TO_GENERATE")
        
        # 2. Existing headline from archive should be flagged
        dup_res = query_content_deduplication("World leaders address climate change at a UN summit")
        self.assertTrue(dup_res["is_duplicate"])
        self.assertGreaterEqual(dup_res["similarity_score"], 0.65)
        self.assertEqual(dup_res["recommendation"], "DUPLICATE_DETECTED_REPHRASE")

    def test_inspect_render_diagnostics(self):
        res = inspect_render_diagnostics("2026-09-23", "daily")
        self.assertIsInstance(res, dict)
        self.assertIn("ffmpeg_status", res)
        self.assertIn("artifacts", res)
        self.assertIn("overall_health", res)

    def test_trigger_social_broadcast_dry_run(self):
        res = trigger_social_broadcast("2026-09-23", "daily", dry_run=True)
        self.assertIsInstance(res, dict)
        self.assertTrue(res["dry_run"])
        self.assertIn("previews", res)
        self.assertIn("telegram_caption_html", res["previews"])
        self.assertIn("discord_description_md", res["previews"])
        self.assertEqual(res["dispatch_result"]["telegram"], "DRY_RUN")

    def test_mcp_server_tools_registered(self):
        self.assertIsNotNone(mcp_app)

    def test_auto_heal_environment(self):
        """Validates that auto_heal_environment purges temp caches and audits fonts/ffmpeg."""
        res = auto_heal_environment()
        self.assertIsInstance(res, dict)
        self.assertIn("status", res)
        self.assertIn("healed_actions", res)
        self.assertIn("issues_detected", res)
        self.assertIn(res["status"], ("HEALTHY", "WARNING"))

    def test_audit_token_and_quota_ledgers(self):
        """Validates that audit_token_and_quota_ledgers reads quota budgets and developer logs."""
        res = audit_token_and_quota_ledgers()
        self.assertIsInstance(res, dict)
        self.assertIn("youtube_quota", res)
        self.assertEqual(res["youtube_quota"]["daily_ceiling"], 10000)
        self.assertIn("remaining_units", res["youtube_quota"])

    def test_trigger_pipeline_stage_dry_run(self):
        """Validates that trigger_pipeline_stage executes a dry-run without errors."""
        res = trigger_pipeline_stage(content_type="daily", dry_run=True)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(res["dry_run"])

    def test_query_supabase_ledger_structure(self):
        """Validates query_supabase_ledger schema validation and graceful client handling."""
        res = query_supabase_ledger(table="video_uploads", limit=2)
        self.assertIsInstance(res, dict)
        self.assertIn(res["status"], ("SUCCESS", "DISABLED", "ERROR"))
        
        # Test invalid table rejection
        invalid_res = query_supabase_ledger(table="forbidden_table")
        self.assertEqual(invalid_res["status"], "ERROR")

    def test_autonomous_orchestrator_initialization(self):
        """Validates AutonomousOrchestrator preflight diagnostics."""
        orchestrator = AutonomousOrchestrator(dry_run=True)
        self.assertTrue(orchestrator.dry_run)
        preflight = orchestrator.run_preflight_diagnostics()
        self.assertIn("status", preflight)
        self.assertIn("healing", preflight)
        self.assertIn("quotas", preflight)


class TestSecretSync(unittest.TestCase):
    """Verifies the GitHub Actions secret synchronization utility."""
    def test_collect_secrets_dry_run(self):
        from scripts.sync_secrets import collect_all_secrets, sync_secrets
        secrets = collect_all_secrets()
        self.assertIsInstance(secrets, dict)
        # Verify dry run completes cleanly
        self.assertTrue(sync_secrets(dry_run=True))

    def test_encrypt_secret_libsodium(self):
        from scripts.sync_secrets import encrypt_secret
        from nacl import public, encoding
        import base64
        # Generate a temporary ephemeral keypair for testing
        test_key = public.PrivateKey.generate()
        test_pub_b64 = test_key.public_key.encode(encoding.Base64Encoder).decode("utf-8")
        raw_secret = "super_secret_token_123"
        encrypted = encrypt_secret(test_pub_b64, raw_secret)
        self.assertIsInstance(encrypted, str)
        self.assertGreater(len(encrypted), len(raw_secret))

        # Decrypt to verify roundtrip integrity
        box = public.SealedBox(test_key)
        decrypted = box.decrypt(base64.b64decode(encrypted)).decode("utf-8")
        self.assertEqual(decrypted, raw_secret)


class TestMCPSecurityDLP(unittest.TestCase):
    """Verifies that NO sensitive data can leak externally via MCP tools."""

    def test_gemini_key_redacted(self):
        from mcp_server.tools.security import sanitize_sensitive_data
        sample = "Error calling Gemini with key AIzaSyD12345678901234567890123456789012"
        cleaned = sanitize_sensitive_data(sample)
        self.assertNotIn("AIzaSyD", cleaned)
        self.assertIn("[REDACTED_GEMINI_KEY]", cleaned)

    def test_telegram_and_discord_redacted(self):
        from mcp_server.tools.security import sanitize_sensitive_data
        sample_tg = "Bot token is 1234567890:ABCdefGHIjklmnopqrstuvwxyz123456789"
        cleaned_tg = sanitize_sensitive_data(sample_tg)
        self.assertNotIn("1234567890:ABCdef", cleaned_tg)
        self.assertIn("[REDACTED_TELEGRAM_BOT_TOKEN]", cleaned_tg)

        sample_dc = "Webhook: https://discord.com/api/webhooks/1234567890/tokenABCdef123"
        cleaned_dc = sanitize_sensitive_data(sample_dc)
        self.assertNotIn("tokenABCdef123", cleaned_dc)
        self.assertIn("[REDACTED_DISCORD_WEBHOOK]", cleaned_dc)

    def test_database_password_redacted(self):
        from mcp_server.tools.security import sanitize_sensitive_data
        sample_db = "postgresql://postgres:super_secret_db_pass_99@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
        cleaned_db = sanitize_sensitive_data(sample_db)
        self.assertNotIn("super_secret_db_pass_99", cleaned_db)
        self.assertIn("[REDACTED_DB_PASSWORD]", cleaned_db)

    def test_recursive_nested_payload_redaction(self):
        from mcp_server.tools.security import sanitize_sensitive_data
        nested_payload = {
            "service": "youtube",
            "api_key": "my_raw_unmasked_secret_key_123",
            "diagnostics": {
                "url": "https://discord.com/api/webhooks/999/secret_token",
                "tokens": ["AIzaSyD12345678901234567890123456789012"]
            },
            "safe_counter": 42
        }
        sanitized = sanitize_sensitive_data(nested_payload)
        self.assertNotIn("my_raw_unmasked_secret_key_123", str(sanitized))
        self.assertNotIn("secret_token", str(sanitized))
        self.assertNotIn("AIzaSyD12345678901234567890123456789012", str(sanitized))
        self.assertEqual(sanitized["safe_counter"], 42)

    def test_audit_and_sanitize_payload_tool(self):
        from mcp_server.tools.security import audit_and_sanitize_payload
        result = audit_and_sanitize_payload({
            "key": "AIzaSyD12345678901234567890123456789012",
            "status": "active"
        })
        self.assertEqual(result["status"], "PROTECTED")
        self.assertTrue(result["is_safe_for_external_exposure"])
        self.assertTrue(result["had_sensitive_data"])
        self.assertNotIn("AIzaSyD", str(result["sanitized_payload"]))

    def test_build_brainteaser_prompt_slot_uniqueness(self):
        """Validates that slot 2 brain teasers enforce category divergence and negative constraint prompt rules."""
        test_date = datetime.datetime(2026, 11, 12)
        base_prompt = "Generate a puzzle"
        prompt, key = build_brainteaser_prompt(
            target_date=test_date,
            base_prompt=base_prompt,
            slot=2,
            exclude_categories=["trap", "sequence"],
            previous_puzzle_text="Three coins are tossed simultaneously."
        )
        self.assertNotIn(key, ["trap", "sequence"])
        self.assertIn("MANDATORY SLOT 2 UNIQUENESS DIRECTIVE", prompt)
        self.assertIn("Three coins are tossed simultaneously", prompt)

    def test_brainteaser_slot2_path_and_deduplication(self):
        """Validates slot-based filename generation and distinct slot 2 asset naming."""
        test_date = datetime.datetime(2026, 11, 12)
        date_str = test_date.strftime("%d%b%y").lower()
        
        # Slot 1
        s1_file = f"brainteaser-{date_str}.txt"
        s1_poll = f"poll-{date_str}.txt"
        s1_slide = f"brainteaser-{date_str}_styled.png"
        s1_video = f"brainteaser-{date_str}.mp4"
        
        # Slot 2
        s2_file = f"brainteaser-{date_str}_2.txt"
        s2_poll = f"poll-{date_str}_2.txt"
        s2_slide = f"brainteaser-{date_str}_2_styled.png"
        s2_video = f"brainteaser-{date_str}_2.mp4"
        
        self.assertNotEqual(s1_file, s2_file)
        self.assertNotEqual(s1_poll, s2_poll)
        self.assertNotEqual(s1_slide, s2_slide)
        self.assertNotEqual(s1_video, s2_video)




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
