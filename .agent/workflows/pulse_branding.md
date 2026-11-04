---
description: Trigger the YouTube channel branding review, live update, ledger archiving, and safe development branch restoration
---

# Pulse Vector YouTube Channel Branding Workflow

Execute the end-to-end branding synchronization cycle: switch to `channel-branding-update`, review live channel details and Home Tab shelves, confirm changes, apply updates via YouTube API, archive visual assets to ledger, push to GitHub, and return to the active development branch.

## Step 1: Execute Safe Branding Switcher & Review
// turbo
Run the automated orchestrator to switch branch and display the review dashboard:
```powershell
python channel_branding/switch_and_update_branding.py --review
```

## Step 2: Review & Confirmation Gate
Inspect the printed comparison dashboard:
- Description length (max 1000 chars) & keywords.
- Banner & 3D icon asset status.
- 7 Home Tab shelves & verify no broken sections.

## Step 3: Apply Live Changes (Upon Confirmation)
When ready to deploy live to YouTube and push to GitHub:
```powershell
python channel_branding/switch_and_update_branding.py --apply
```
*(Optionally include `--upload-banner` to upload and activate a new master banner)*

## Step 4: Verification & Branch Restoration
The script automatically:
1. Deploys approved metadata and Home Tab shelves via YouTube API.
2. Snapshots previous release into `channel_branding/history/`.
3. Commits and pushes to `origin/channel-branding-update`.
4. Switches back to the original development branch and restores any stashed files.
