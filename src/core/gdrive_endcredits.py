"""
Google Drive Runtime End Credits Manager for Pulse Vector.
Dynamically fetches, samples, and attaches animated Like/Share/Subscribe & Bell Enlargement
Outro videos directly from Google Drive at runtime.
"""

import os
import json
import random
import logging
import pathlib
import subprocess
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger("GDriveEndcredits")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
LOCAL_SAMPLES_DIR = ROOT_DIR / "samples" / "End_Credits_Videos"

# Primary Google Drive Directory for End Credits
DEFAULT_GDRIVE_DIR = pathlib.Path(r"G:\My Drive\antigravity-projects-storage\pulse-vector\End_Credits_Videos")
SECONDARY_GDRIVE_DIR = pathlib.Path(r"G:\My Drive\youtube-projects\LastDayOnEarth\Assets\animations")


def resolve_gdrive_endcredits_dir() -> pathlib.Path:
    """
    Resolves the active Google Drive directory for end credits videos.
    Checks environment overrides, primary Drive mount, and secondary Drive paths.
    """
    env_dir = os.getenv("PULSE_DRIVE_OUTRO_DIR")
    if env_dir and pathlib.Path(env_dir).exists():
        return pathlib.Path(env_dir)

    if DEFAULT_GDRIVE_DIR.exists():
        return DEFAULT_GDRIVE_DIR

    # Try creating primary if parent exists
    if DEFAULT_GDRIVE_DIR.parent.exists():
        try:
            DEFAULT_GDRIVE_DIR.mkdir(parents=True, exist_ok=True)
            return DEFAULT_GDRIVE_DIR
        except Exception:
            pass

    if SECONDARY_GDRIVE_DIR.exists():
        return SECONDARY_GDRIVE_DIR

    # Fallback to local samples directory
    LOCAL_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_SAMPLES_DIR


def probe_video_dimensions(video_path: pathlib.Path) -> Tuple[int, int, float]:
    """
    Uses ffprobe to extract width, height, and duration of a video.
    Returns (width, height, duration).
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        stream = data.get("streams", [{}])[0]
        w = int(stream.get("width", 1080))
        h = int(stream.get("height", 1920))
        
        # Duration can be in stream or format
        dur_str = stream.get("duration") or data.get("format", {}).get("duration", "8.0")
        dur = float(dur_str)
        return w, h, dur
    except Exception as e:
        logger.warning(f"ffprobe probe failed for {video_path}: {e}. Using defaults.")
        return 1080, 1920, 8.0


def list_drive_endcredit_videos(drive_dir: Optional[pathlib.Path] = None) -> List[pathlib.Path]:
    """
    Scans the Google Drive end credits directory for all valid video files.
    """
    target_dir = drive_dir or resolve_gdrive_endcredits_dir()
    if not target_dir.exists():
        return []

    valid_exts = {".mp4", ".mov", ".webm", ".mkv"}
    videos = []
    for item in target_dir.glob("*"):
        if item.is_file() and item.suffix.lower() in valid_exts and item.stat().st_size > 50000:
            videos.append(item)
    return videos


def seed_drive_endcredits_library(drive_dir: Optional[pathlib.Path] = None, force: bool = False) -> List[pathlib.Path]:
    """
    Renders high-impact end credit videos featuring Like/Share/Subscribe,
    bell progressive enlargement, and clean fade-out, saving them directly to Google Drive.
    """
    target_dir = drive_dir or resolve_gdrive_endcredits_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    LOCAL_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    from .outro_video_engine import OutroVideoEngine

    engine = OutroVideoEngine(output_dir=target_dir)
    seeded = []

    # 1. Pulse Vector Vertical 9:16 (Shorts - matches user screenshot)
    vert_path = target_dir / "pulse_vector_vertical_bell_zoom.mp4"
    if force or not vert_path.exists() or vert_path.stat().st_size < 50000:
        logger.info(f"Rendering Pulse Vector Vertical 9:16 Outro to Google Drive: {vert_path.name}...")
        try:
            rendered = engine.generate_single_outro_video("pulse_vertical", output_path=vert_path)
            seeded.append(rendered)
            # Mirror to local samples
            import shutil
            shutil.copy2(rendered, LOCAL_SAMPLES_DIR / rendered.name)
        except Exception as e:
            logger.error(f"Failed to render vertical outro: {e}")

    # 2. Widescreen Archetypes (16:9 Masterclass)
    for key in ["vox", "mrbeast", "thinkschool"]:
        wide_path = target_dir / f"outro_{key}_bell_zoom.mp4"
        if force or not wide_path.exists() or wide_path.stat().st_size < 50000:
            logger.info(f"Rendering {key.upper()} 16:9 Outro to Google Drive: {wide_path.name}...")
            try:
                rendered = engine.generate_single_outro_video(key, output_path=wide_path)
                seeded.append(rendered)
                import shutil
                shutil.copy2(rendered, LOCAL_SAMPLES_DIR / rendered.name)
            except Exception as e:
                logger.warning(f"Could not seed {key}: {e}")

    return seeded


def get_runtime_drive_endcredits(
    aspect_ratio: str = "9:16",
    preferred_style: Optional[str] = None,
    drive_dir: Optional[pathlib.Path] = None
) -> pathlib.Path:
    """
    Dynamically fetches and samples an endcredits video directly from Google Drive at runtime.
    If the Drive directory is empty or missing matching formats, it automatically seeds it.
    """
    target_dir = drive_dir or resolve_gdrive_endcredits_dir()
    logger.info(f"Checking Google Drive for endcredits at runtime: {target_dir}")

    videos = list_drive_endcredit_videos(target_dir)

    # If Drive is empty, seed it immediately!
    if not videos:
        logger.info("Google Drive End_Credits_Videos is empty. Auto-seeding fresh broadcast endcredits...")
        videos = seed_drive_endcredits_library(target_dir)

    is_vertical_target = (aspect_ratio == "9:16")

    # Filter by aspect ratio
    matching_videos = []
    for v in videos:
        w, h, _ = probe_video_dimensions(v)
        v_is_vertical = (h > w)
        if is_vertical_target == v_is_vertical:
            matching_videos.append(v)

    # If no exact aspect ratio match found on Drive, fall back to any available Drive video
    pool = matching_videos if matching_videos else videos

    if not pool:
        # Ultimate fallback: generate single on the fly
        logger.warning("No valid videos found in Drive pool. Generating on the fly...")
        from .outro_video_engine import OutroVideoEngine
        engine = OutroVideoEngine(output_dir=target_dir)
        ch_key = "pulse_vertical" if is_vertical_target else "vox"
        out_v = target_dir / f"{ch_key}_runtime.mp4"
        return engine.generate_single_outro_video(ch_key, output_path=out_v)

    # Filter by preferred style if specified
    if preferred_style:
        style_matches = [v for v in pool if preferred_style.lower() in v.name.lower()]
        if style_matches:
            chosen = random.choice(style_matches)
            logger.info(f"[RUNTIME GDRIVE RESOLVED] Preferred Style '{preferred_style}': {chosen}")
            return chosen

    chosen = random.choice(pool)
    logger.info(f"[RUNTIME GDRIVE RESOLVED] Selected Sample Endcredit: {chosen} (from {len(pool)} available on Drive)")
    return chosen


def stitch_video_with_drive_endcredit(
    main_video_path: pathlib.Path,
    output_video_path: pathlib.Path,
    aspect_ratio: str = "9:16",
    preferred_style: Optional[str] = None,
    main_fadeout_sec: float = 0.5,
    outro_fadein_sec: float = 0.3
) -> pathlib.Path:
    """
    Seamlessly attaches a Google Drive runtime endcredits clip to the main video.
    
    Sequence:
    1. Main video finishes and fades out to black (main_fadeout_sec).
    2. Endcredits clip begins with smooth fade-in from black (outro_fadein_sec).
    3. Endcredits plays animated Like/Share/Subscribe, executes the bell enlargement,
       and fades out cleanly to pure black at the end.
    """
    if not main_video_path.exists():
        raise FileNotFoundError(f"Main video not found: {main_video_path}")

    # 1. Fetch endcredit directly from Google Drive at runtime
    endcredit_path = get_runtime_drive_endcredits(aspect_ratio=aspect_ratio, preferred_style=preferred_style)
    logger.info(f"Stitching main video ({main_video_path.name}) with Google Drive endcredit ({endcredit_path.name})...")

    # 2. Probe dimensions and durations
    main_w, main_h, main_dur = probe_video_dimensions(main_video_path)
    ec_w, ec_h, ec_dur = probe_video_dimensions(endcredit_path)

    # Calculate fade out point for main video
    fade_start = max(0.1, main_dur - main_fadeout_sec)

    # Ensure output directory exists
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Build FFmpeg filter complex
    # Handle scaling if endcredit does not match main video dimensions
    scale_filter = ""
    if (main_w, main_h) != (ec_w, ec_h):
        scale_filter = f"scale={main_w}:{main_h}:force_original_aspect_ratio=decrease,pad={main_w}:{main_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
    else:
        scale_filter = "setsar=1,"

    filter_complex = (
        f"[0:v]fade=t=out:st={fade_start:.3f}:d={main_fadeout_sec:.3f},setsar=1,format=yuv420p[v0];"
        f"[0:a]afade=t=out:st={fade_start:.3f}:d={main_fadeout_sec:.3f}[a0];"
        f"[1:v]{scale_filter}fade=t=in:st=0:d={outro_fadein_sec:.3f},format=yuv420p[v1];"
        f"[1:a]afade=t=in:st=0:d={outro_fadein_sec:.3f}[a1];"
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[vout][aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(main_video_path),
        "-i", str(endcredit_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-movflags", "+faststart",
        str(output_video_path)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(f"FFmpeg stitching failed: {res.stderr}")
        raise RuntimeError(f"Failed to stitch video with Drive endcredits: {res.stderr[-300:]}")

    logger.info(f"Successfully generated stitched video with Drive endcredit: {output_video_path} ({output_video_path.stat().st_size // 1024} KB)")
    return output_video_path
