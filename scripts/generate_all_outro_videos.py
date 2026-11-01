#!/usr/bin/env python3
"""
Batch Video Generator for 10 Famous YouTube Channels Outro Scenes.
Executes OutroVideoEngine to render 10 distinct, broadcast-quality MP4 videos (7-9.5s)
complete with animated motion, audio music tracks, and bell chimes.
"""

import sys
import shutil
import subprocess
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.outro_video_engine import OutroVideoEngine

CHANNELS = [
    ("mrbeast", "MrBeast Hype Studio (8.5s) — Giant Bell Shockwave & Button Pops"),
    ("vox", "Vox Kinetic Split (8.0s) — Sliding Card Motion Graphics & Tech Cursor"),
    ("veritasium", "Veritasium Curiosity Loop (8.5s) — Question of the Day & Pinned Comment Challenge"),
    ("kurzgesagt", "Kurzgesagt Stellar (8.0s) — Cosmic Starfield, Wobbling Planet & Candy Buttons"),
    ("mkbhd", "MKBHD Tech Studio (7.5s) — Matte Obsidian Cyber Minimalist Pill & Subtle Recoil"),
    ("aliabdaal", "Ali Abdaal Ecosystem (8.0s) — Clean Glassmorphism Study Capsule & Discord Hub"),
    ("thinkschool", "Think School Exam Hub (8.5s) — 1-Page PDF Banner, Lecture Card & Bell Chimes"),
    ("oversimplified", "OverSimplified Cartoon (8.0s) — Playful Glove Cursor & Yesterday's Champion Spotlight"),
    ("caspian", "CaspianReport Intel HUD (8.0s) — Rotating Radar Reticle & Tactical Video Dossier"),
    ("lemmino", "Lemmino Cinematic (9.0s) — Undulating Frequency Audio Waveform & Chapter Flow"),
]

def main():
    root_dir = Path(__file__).resolve().parent.parent
    output_dir = root_dir / "samples" / "End_Credits_Videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_dir = Path(r"C:\Users\Admin\.gemini\antigravity\brain\273fb3c7-db9f-4dd2-8fc1-c5e8928665dc\outro_videos")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    engine = OutroVideoEngine(output_dir=output_dir)

    print("==================================================================")
    print("  RENDERING 10 ANIMATED END-CREDIT VIDEOS OF FAMOUS YOUTUBE CHANNELS")
    print("  (Reference: LastDayOnEarth animated tail generator architecture)")
    print("==================================================================\n")

    rendered_files = []
    for key, desc in CHANNELS:
        print(f"[*] Rendering [{key.upper()}]: {desc}...")
        mp4_path = engine.generate_single_outro_video(key)

        # Extract poster snapshot at 4.0s using ffmpeg
        poster_path = output_dir / f"outro_{key}_poster.jpeg"
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:04.000",
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
    print(f"  All 10 Outro Videos generated successfully in:")
    print(f"  - Repository: samples/End_Credits_Videos/")
    print(f"  - Artifacts:  {artifact_dir}")
    print("==================================================================")

if __name__ == "__main__":
    main()
