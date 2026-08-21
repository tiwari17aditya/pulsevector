---
description: Run comprehensive automated tests across all Pulse Vector components (parsers, slides, audio, video, engine)
---

# Pulse Vector Automated Testing Workflow

Execute unit tests and pipeline dry runs across all modular components to verify pipeline health without burning API quota or touching production channels.

## Step 1: Run Automated Component Unit Tests
// turbo
Execute the test runner covering parsers, image rendering, TTS formatting, and video frame transitions:
```powershell
python scripts/test_pipeline.py
```

## Step 2: Test Modular Pipeline Dry Runs
Verify that all file paths, fonts, templates, and stage dependencies resolve cleanly for each content type:

1. **Daily Current Affairs & Brain Teaser Dry Run**:
   ```powershell
   python src/pipeline.py --daily --dry-run
   ```

2. **Weekly Masterclass Dry Run**:
   ```powershell
   python src/pipeline.py --weekly --dry-run
   ```

3. **Monthly Masterclass Dry Run**:
   ```powershell
   python src/pipeline.py --monthly --dry-run
   ```

## Step 3: Single-Stage Isolated Testing (Optional)
To test a specific stage for a given date without running the entire pipeline:
```powershell
# Only test slide rendering for a specific date
python src/pipeline.py --daily --date 2026-07-26 --stages slides --force

# Only test video assembly without TTS or uploading
python src/pipeline.py --daily --date 2026-07-26 --stages video --no-tts
```
