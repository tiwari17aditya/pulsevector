#!/usr/bin/env python3
"""
Batch Video Generator for 5 Finalized Famous YouTube Channels Outro Scenes.
Executes OutroVideoEngine to render 5 distinct, broadcast-quality MP4 videos (8.0-8.5s)
complete with animated motion, Like/Share/Subscribe triads, audio music tracks, and bell chimes.
"""

import sys
import shutil
import subprocess
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.outro_video_engine import OutroVideoEngine, FINALIST_CHANNELS

CHANNELS = [
    ("vox", "Vox Kinetic Split (8.0s) — Top Pick: Kinetic Motion Graphics & Animated Like/Share/Subscribe Dock"),
    ("mrbeast", "MrBeast Hype Studio (8.5s) — Maximum Urgency: Oversized Golden Bell Tower & Shockwaves"),
    ("thinkschool", "Think School Exam Hub (8.5s) — High-Yield Civil Services Study Capsule & Resource Dock"),
    ("kurzgesagt", "Kurzgesagt Stellar (8.0s) — Cosmic Starfield, Wobbling Ringed Planet & Candy Triad"),
    ("veritasium", "Veritasium Curiosity Loop (8.5s) — Algorithmic Comment Loop & Question of the Day"),
]

# Sample dynamic context for future pipeline integration demonstration
SAMPLE_CONTEXT = {
    "next_video_title": "ISRO Aditya-L1 Solar Flares Analysis",
    "playlist_title": "Complete UPSC CSE 2026 Foundation",
    "telegram_handle": "@pulsevector_official",
    "question_text": "Should global AI safety frameworks be legally binding across all nations?",
}

def main():
    root_dir = Path(__file__).resolve().parent.parent
    output_dir = root_dir / "samples" / "End_Credits_Videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_dir = Path(r"C:\Users\Admin\.gemini\antigravity\brain\273fb3c7-db9f-4dd2-8fc1-c5e8928665dc\outro_videos")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    engine = OutroVideoEngine(output_dir=output_dir)

    print("==================================================================")
    print("  RENDERING 5 FINALIZED END-CREDIT VIDEOS WITH LIKE/SHARE/SUBSCRIBE")
    print("  (Reference: LastDayOnEarth animated tail generator architecture)")
    print("==================================================================\n")

    rendered_files = []
    for key, desc in CHANNELS:
        print(f"[*] Rendering [{key.upper()}]: {desc}...")
        mp4_path = engine.generate_single_outro_video(key, context=SAMPLE_CONTEXT)

        # Extract poster snapshot at 5.0s (capturing animated states) using ffmpeg
        poster_path = output_dir / f"outro_{key}_poster.jpeg"
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:05.000",
            "-i", str(mp4_path),
            "-vframes", "1",
            "-q:v", "2",
            str(poster_path)
        ]
        subprocess.run(cmd, capture_output=True)

        # Copy mp4 and poster to artifact directory
        shutil.copy2(str(mp4_path), str(artifact_dir / mp4_path.name))
        if poster_path.exists():
            shutil.copy2(str(poster_path), str(artifact_dir / poster_path.name))

        file_size_mb = mp4_path.stat().st_size / (1024 * 1024)
        print(f"    [OK] Saved: {mp4_path.name} ({file_size_mb:.2f} MB)")
        rendered_files.append((key, desc, mp4_path, poster_path))

    print("\n==================================================================")
    print(f"  All 5 Outro Videos generated successfully in:")
    print(f"  - Repository: samples/End_Credits_Videos/")
    print(f"  - Artifacts:  {artifact_dir}")
    print("==================================================================")

if __name__ == "__main__":
    main()
