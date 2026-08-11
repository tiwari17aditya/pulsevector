---
name: media-rendering
description: Domain skill for PIL image slide creation, MoviePy/FFmpeg video rendering, TTS audio synthesis, and visual layout.
---

# Media & Video Rendering Domain Skill

## Scope & Target Files
- `src/core/image_utils.py`
- `src/core/video_utils.py`
- `src/core/tts_utils.py`
- `POC/enhance_video_poc.py`

## Instructions & Core Operations
1. **Visual Slide Generation**:
   - Aspect ratio: Vertical 9:16 (`1080x1920` px resolution).
   - Style: Dark mode glassmorphism UI card aesthetic with clean, modern typography.
   - Text safety: Keep text within safe margin bounds (top 150px and bottom 250px avoided to prevent overlap with YouTube Shorts overlay UI).
2. **Video Compilation**:
   - Frame rate: Standardized 30 FPS (`fps=30`).
   - Transitions: Apply dynamic visual transitions (`slide_left`, `zoom_fade`, `fade`).
   - Audio overlay: Blend TTS narration voice track with background music (`samples/Audio/`) at balanced decibel levels (-14 dB to -18 dB for background track).

## Domain Constraints
- Never produce stretched or non-standard aspect ratio videos for YouTube Shorts.
- Always clean up temporary slide PNGs and scratch audio files after MP4 compilation.
- Ensure FFmpeg binaries or system MoviePy backends do not block main thread event loops.

## Verification Checklist
- [ ] Check rendered slide image dimensions (`1080x1920`).
- [ ] Verify output video plays cleanly at 30 FPS with synchronous audio track.
- [ ] Confirm background music volume does not drown out TTS narration voice.
