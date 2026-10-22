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
- `POC/qr_minigame_poc.py`
- `docs/play/index.html`

## Instructions & Core Operations
1. **Visual Slide Generation**:
   - Current Affairs Slides: Vertical 9:16 (`1080x1920` px resolution) or Widescreen 16:9 (`1920x1080` px for Masterclasses). Safe margin bounds: avoid top 150px and bottom 250px for Shorts UI overlay.
   - Brain Teaser Slide Cards: Square `656x656` px card.
   - Brain Teaser Boundary Constraints:
     - Vertical safety: Total height of questions, series block, and options must never exceed `Y = 585px` (guaranteeing >= 30px clearance above watermark at 620px).
     - Horizontal fit: Option text must dynamically auto-shrink if width exceeds `box_w - 45px` to prevent pill spillage or clipping.
     - Automated Verification: Mandatory execution of `verify_brainteaser_visual_boundaries()` after rendering to confirm resolution, margin clearance, and zero element distortion.
2. **Video Compilation & Overlays**:
   - Frame rate: Standardized 30 FPS (`fps=30`) for masterclass / 10 FPS for brain teaser shorts loops.
   - Transitions: Apply dynamic visual transitions (`slide_left`, `zoom_fade`, `fade`).
   - Audio overlay: Blend TTS narration voice track with background music (`samples/Audio/`) at balanced decibel levels (-14 dB to -18 dB for background track).
   - QR Code Integration: Overlay a `150x150` QR code at position `(820, 1405)` next to the countdown timer, pointing to the interactive HTML game in `docs/play/index.html` with query parameters.

## Domain Constraints
- Never produce stretched or non-standard aspect ratio videos for YouTube Shorts.
- Never output brain teaser cards with text bleeding over the card edges or overlapping the watermark.
- Always verify rendered cards with `verify_brainteaser_visual_boundaries()` before video compilation.
- Always clean up temporary slide PNGs and scratch audio files after MP4 compilation.
- Ensure FFmpeg binaries or system MoviePy backends do not block main thread event loops.

## Verification Checklist
- [ ] Check rendered slide image dimensions (`1080x1920` for Shorts, `656x656` for Brain Teaser cards).
- [ ] Confirm Brain Teaser card elements satisfy `Y <= 585px` clearance without text overflow.
- [ ] Verify output video plays cleanly with synchronous audio track.
- [ ] Confirm background music volume does not drown out TTS narration voice.

