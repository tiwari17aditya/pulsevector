"""
Pulse Vector - Modular Pipeline Stage Interfaces & Data Models
Allows each pipeline component to be detachable, pluggable, and individually testable.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import datetime

@dataclass
class ContentPayload:
    """Represents generated text content for Daily, Weekly, Monthly, or Brain Teasers."""
    content_type: str  # 'daily', 'weekly', 'monthly', 'brainteaser'
    target_date: datetime.datetime
    raw_text: str
    points: List[tuple] = field(default_factory=list)  # (number, text, source)
    title: str = ""
    description: str = ""
    hashtags: List[str] = field(default_factory=list)
    source_urls: Dict[str, str] = field(default_factory=dict)
    text_file_path: Optional[Path] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SlidePayload:
    """Represents rendered slide images and metadata."""
    content_type: str
    target_date: datetime.datetime
    slide_image_paths: List[Path] = field(default_factory=list)
    thumbnail_path: Optional[Path] = None
    animated_frame_paths: List[Path] = field(default_factory=list)
    output_dir: Optional[Path] = None

@dataclass
class AudioPayload:
    """Represents synthesized voiceover and audio tracks."""
    full_voice_path: Optional[Path] = None
    background_track_path: Optional[Path] = None
    per_slide_durations: List[float] = field(default_factory=list)
    total_duration: float = 0.0

@dataclass
class VideoPayload:
    """Represents compiled video."""
    video_path: Path
    duration: float
    has_audio: bool = True
    has_voiceover: bool = True

@dataclass
class PublishResult:
    """Represents outcome of YouTube, Database, and Git actions."""
    youtube_video_id: Optional[str] = None
    youtube_playlist_id: Optional[str] = None
    db_uploaded_files: int = 0
    git_committed: bool = False
    backup_successful: bool = False
    errors: List[str] = field(default_factory=list)
