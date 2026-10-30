"""
Unit tests for the Knowledge Capsule pipeline and renderer.
"""

import unittest
import pathlib
import tempfile
from PIL import Image

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from core.capsule_renderer import CapsuleRenderer
from capsule_pipeline import get_sample_weekly_insights, generate_social_post, run_capsule_pipeline

class TestCapsulePipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = pathlib.Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sample_weekly_insights_structure(self):
        data = get_sample_weekly_insights("12 October - 18 October 2026")
        self.assertIn("header", data)
        self.assertIn("sections", data)
        self.assertIn("footer", data)
        self.assertEqual(len(data["sections"]), 3)

    def test_render_capsule_jpeg_and_png(self):
        data = get_sample_weekly_insights("12 October - 18 October 2026")
        renderer = CapsuleRenderer(width=1200)
        out_base = self.output_dir / "test_capsule"
        jpeg_path = renderer.render_capsule(data, out_base)

        self.assertTrue(jpeg_path.exists())
        self.assertTrue(out_base.with_suffix(".png").exists())

        # Verify image validity and dimensions
        with Image.open(jpeg_path) as img:
            self.assertEqual(img.size[0], 1200)
            self.assertGreater(img.size[1], 1500)
            self.assertEqual(img.format, "JPEG")

    def test_render_vertical_slides(self):
        data = get_sample_weekly_insights("12 October - 18 October 2026")
        renderer = CapsuleRenderer(width=1200)
        slides_dir = self.output_dir / "slides"
        slides = renderer.render_vertical_slides(data, slides_dir)

        self.assertEqual(len(slides), 5)
        for s in slides:
            self.assertTrue(s.exists())
            with Image.open(s) as img:
                self.assertEqual(img.size, (1080, 1920))

    def test_generate_social_post(self):
        data = get_sample_weekly_insights("12 October - 18 October 2026")
        post = generate_social_post(data)
        self.assertIn("EXAM RELEVANT CURRENT AFFAIRS CAPSULE", post)
        self.assertIn("BRICS 2026", post)
        self.assertIn("BIMSTEC", post)
        self.assertIn("e-SHRAM", post)
        self.assertIn("QUICK EXAM CHALLENGE", post)

    def test_run_capsule_pipeline_dry_run(self):
        result = run_capsule_pipeline(output_dir=self.output_dir, dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertIn("jpeg_path", result)
        self.assertIn("post_path", result)

if __name__ == "__main__":
    unittest.main()

