---
description: Run system health diagnostics for Gemini API, YouTube OAuth, Supabase, FFmpeg, and storage
---

# Pulse Vector System Monitoring & Diagnostics

Check the health and operational readiness of all cloud services, API quotas, media processing engines, and authentication tokens.

## Step 1: Run Full System Health Check
// turbo
Execute the diagnostic monitor script:
```powershell
python scripts/monitor_health.py
```

## Step 2: Interpret Diagnostic Results
- **FFmpeg Media Engine**: Verifies that FFmpeg is available and executable for video encoding and audio muxing.
- **Typography & Fonts**: Validates that Roboto-Regular, Roboto-Bold, and Poppins font files exist in `fonts/`.
- **Background Audio Library**: Checks for the 15 synthetic royalty-free audio tracks in `samples/Audio/`.
- **Edge-TTS Voiceover**: Confirms Edge-TTS engine is ready for dynamic voiceover synthesis.
- **Gemini AI API & Quota**: Sends a ping to Gemini 2.5 Flash to ensure `GEMINI_API_KEY` is valid and active.
- **Supabase Cloud DB**: Validates connection to Supabase and query access to `pipeline_runs`.
- **YouTube OAuth 2.0 Auth**: Inspects `credentials/token.json` to verify refresh token validity.
- **Archive Directory Health**: Verifies that `pulse_archive/` is accessible and indexed properly.
