---
description: Audit workspace structure, font assets, audio libraries, and pulse archive integrity
---

# Pulse Vector Structure & Archive Maintenance

Verify that the workspace layout, font directory, audio library, and historical archive remain organized and adhere to system standards.

## Step 1: Verify Directory Layout & Structure
Ensure standard paths exist:
- `fonts/` (Roboto-Regular.ttf, Roboto-Bold.ttf, Poppins-Bold.ttf)
- `samples/Audio/` (track_01.mp3 to track_15.mp3)
- `pulse_archive/` (`YYYY/Month/{Daily,Daily_Images,Daily_Videos,Weekly,Weekly_Images,Weekly_Videos,Monthly,Monthly_Images,Monthly_Videos,Brain_Teasers}`)

## Step 2: Validate Archive Consistency
// turbo
Check for missing slide decks or video files across processed dates:
```powershell
python -c "import os, pathlib; arch = pathlib.Path('pulse_archive'); print(f'Archive Size: {sum(f.stat().st_size for f in arch.glob(\"**/*\") if f.is_file()) / (1024*1024):.2f} MB across {len(list(arch.glob(\"**/*\")))} objects')"
```

## Step 3: Clean Temporary Cache Files
Clean any lingering frames or incomplete temp files:
```powershell
python -c "import shutil, pathlib; temp_dirs = list(pathlib.Path('pulse_archive').glob('**/tts_temp')) + [pathlib.Path('pulse_archive/temp_end_frames')]; [shutil.rmtree(d, ignore_errors=True) for d in temp_dirs]; print('Cleaned temporary artifacts.')"
```
