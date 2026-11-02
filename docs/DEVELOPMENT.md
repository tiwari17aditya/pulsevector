# Pulse Vector — Developer Guide

## 1. Environment & Setup
- **Python**: 3.10+ (tested on Python 3.12).
- **FFmpeg**: Required on system PATH (with `libx264` and `aac` codecs).
- **Dependencies**: Install required packages via `pip install -r requirements.txt`.

## 2. Branching Strategy
- **`main`**: Production-only branch. Scheduled GitHub Actions crons execute strictly on `main`.
- **`v<version>-dev`**: Active feature development branch (e.g., `v2.9.0-dev`). Never develop directly on `main`.
- Merging to `main` happens only after full test pass and milestone sign-off.

## 3. Running Automated Tests
Run the complete component test suite and dry-runs:
```powershell
python scripts/test_pipeline.py
```
Ensure all 57 automated tests pass before committing.

## 4. Generating Outro Videos
To re-render all 5 finalized animated YouTube end credit scenes:
```powershell
python scripts/generate_all_outro_videos.py
```

To regenerate the interactive Video Theater:
```powershell
python scripts/build_video_theater.py
```

To test random outro assembly and upload as a private YouTube video:
```powershell
python scripts/upload_random_outro_test.py
```

## 5. Master Packup Sign-Off Workflow
To run full diagnostics, clean temporary frames, audit all 6 skills, and push changes:
```powershell
python scripts/packup_pipeline.py
```

